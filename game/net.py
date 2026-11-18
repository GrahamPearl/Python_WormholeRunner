"""LAN networking, standard library only (works the same on Windows and Linux).

* Game connection: one TCP socket carrying newline-delimited JSON. The host
  simulates the world and sends snapshots; the joiner sends its key presses.
* Discovery: hosts answer a UDP broadcast ("who is hosting?") on the same port.
"""
import collections
import json
import os
import queue
import socket
import threading
import time

PROTO_VERSION = 2
DEFAULT_PORT = 5555
DISCOVERY_MAGIC = b"WORMHOLE-RUNNER-DISCOVER-1"
GAME_ID = "wormhole-runner"


class NetError(Exception):
    pass


# ------------------------------------------------------------------ addresses
def local_ipv4_addresses():
    """This machine's IPv4 addresses, LAN ones first (never raises)."""
    ips = set()
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            ips.add(info[4][0])
    except OSError:
        pass
    try:                                    # finds the default-route address; sends nothing
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("10.255.255.255", 1))
        ips.add(s.getsockname()[0])
        s.close()
    except OSError:
        pass
    ips.discard("0.0.0.0")
    return sorted(ips, key=lambda ip: (ip.startswith("127."), ip))


def lan_ipv4_addresses():
    return [ip for ip in local_ipv4_addresses() if not ip.startswith("127.")]


def parse_address(text, default_port=DEFAULT_PORT):
    """'192.168.1.20' or '192.168.1.20:6000' -> (ip, port). Raises ValueError."""
    text = text.strip()
    ip, _, port = text.partition(":")
    parts = ip.split(".")
    if len(parts) != 4 or not all(p.isdigit() and 0 <= int(p) <= 255 for p in parts):
        raise ValueError("Enter an IPv4 address like 192.168.1.20")
    if port:
        if not port.isdigit() or not 1 <= int(port) <= 65535:
            raise ValueError("Port must be 1-65535")
        return ip, int(port)
    return ip, int(default_port)


def broadcast_targets():
    targets = {"255.255.255.255", "127.0.0.1"}
    for ip in lan_ipv4_addresses():
        a, b, c, _ = ip.split(".")
        targets.add(f"{a}.{b}.{c}.255")      # assumes a /24 home/office network
    return sorted(targets)


# ------------------------------------------------------------------ connection
class Connection:
    """Reliable message pipe with reader/writer threads (the game loop never blocks)."""

    def __init__(self, sock):
        self.sock = sock
        try:
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        except OSError:
            pass
        sock.settimeout(0.5)
        self.alive = True
        self.created = time.time()
        self.last_recv = time.time()
        self.inbox = queue.Queue()
        self._ctrl = collections.deque()
        self._latest = None
        self._lock = threading.Lock()
        self._evt = threading.Event()
        threading.Thread(target=self._reader, daemon=True).start()
        threading.Thread(target=self._writer, daemon=True).start()

    @staticmethod
    def _encode(msg):
        return json.dumps(msg, separators=(",", ":")).encode("utf-8") + b"\n"

    def _reader(self):
        buf = b""
        try:
            while self.alive:
                try:
                    chunk = self.sock.recv(65536)
                except socket.timeout:
                    continue
                if not chunk:
                    break
                self.last_recv = time.time()
                buf += chunk
                if len(buf) > 4_000_000:
                    break
                while b"\n" in buf:
                    line, buf = buf.split(b"\n", 1)
                    if line:
                        try:
                            self.inbox.put(json.loads(line))
                        except ValueError:
                            pass
        except OSError:
            pass
        finally:
            self.alive = False
            self._evt.set()

    def _writer(self):
        try:
            while self.alive:
                self._evt.wait(0.5)
                with self._lock:
                    self._evt.clear()
                    ctrl = list(self._ctrl)
                    self._ctrl.clear()
                    latest, self._latest = self._latest, None
                for data in ctrl:
                    self.sock.sendall(data)
                if latest is not None:
                    self.sock.sendall(latest)
        except OSError:
            pass
        finally:
            self.alive = False

    def send(self, msg):
        """Queue a message that must arrive."""
        with self._lock:
            self._ctrl.append(self._encode(msg))
        self._evt.set()

    def send_latest(self, msg):
        """Queue a state message; an older one that has not gone out yet is replaced."""
        data = self._encode(msg)
        with self._lock:
            self._latest = data
        self._evt.set()

    def send_now(self, msg):
        try:
            self.sock.sendall(self._encode(msg))
        except OSError:
            pass

    def poll(self):
        out = []
        while True:
            try:
                out.append(self.inbox.get_nowait())
            except queue.Empty:
                return out

    def close(self, bye=True):
        if bye and self.alive:
            self.send_now({"t": "bye"})
        self.alive = False
        self._evt.set()
        for op in (lambda: self.sock.shutdown(socket.SHUT_RDWR), self.sock.close):
            try:
                op()
            except OSError:
                pass


# ------------------------------------------------------------------ host side
class GameServer:
    """Listens for one joining player and answers LAN discovery broadcasts."""

    def __init__(self, port, host_name):
        self.port = int(port)
        self.info = {"game": GAME_ID, "v": PROTO_VERSION, "name": host_name,
                     "port": self.port, "players": 1, "max": 2, "level": 1}
        self.client = None
        self.pending = []
        self.running = True
        self._accepted = queue.Queue()
        self.listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if os.name != "nt":      # on Windows SO_REUSEADDR would allow port hijacking
            self.listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.listener.bind(("", self.port))
        self.listener.listen(4)
        self.listener.settimeout(0.5)
        self.udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        if os.name != "nt":
            self.udp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.udp.bind(("", self.port))
        except OSError:
            self.udp = None      # hosting still works; players must use the IP address
        else:
            self.udp.settimeout(0.5)
            threading.Thread(target=self._discovery_loop, daemon=True).start()
        threading.Thread(target=self._accept_loop, daemon=True).start()

    @property
    def discoverable(self):
        return self.udp is not None

    def _accept_loop(self):
        while self.running:
            try:
                sock, _addr = self.listener.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            self._accepted.put(sock)

    def _discovery_loop(self):
        while self.running:
            try:
                data, addr = self.udp.recvfrom(256)
            except socket.timeout:
                continue
            except OSError:
                if not self.running:
                    break
                time.sleep(0.2)      # e.g. Windows ICMP "connection reset" noise
                continue
            if data == DISCOVERY_MAGIC:
                try:
                    self.udp.sendto(json.dumps(self.info).encode("utf-8"), addr)
                except OSError:
                    pass

    def poll_join(self):
        """Return (connection, hello_message) when a player completes the handshake."""
        while True:
            try:
                self.pending.append(Connection(self._accepted.get_nowait()))
            except queue.Empty:
                break
        joined = None
        for conn in list(self.pending):
            handled = False
            for msg in conn.poll():
                if msg.get("t") != "hello":
                    continue
                handled = True
                if msg.get("v") != PROTO_VERSION:
                    conn.send_now({"t": "reject", "why": "Different game versions"})
                    conn.close(bye=False)
                elif self.client is not None or joined is not None:
                    conn.send_now({"t": "reject", "why": "Game is full"})
                    conn.close(bye=False)
                else:
                    joined = (conn, msg)
                    self.client = conn
                break
            timed_out = time.time() - conn.created > 5
            if handled or timed_out or not conn.alive:
                self.pending.remove(conn)
                if timed_out and not handled:
                    conn.close(bye=False)
        return joined

    def client_messages(self):
        return self.client.poll() if self.client else []

    def client_lost(self, timeout):
        c = self.client
        return c is not None and (not c.alive or time.time() - c.last_recv > timeout)

    def drop_client(self, bye=True):
        if self.client:
            self.client.close(bye)
            self.client = None

    def stop(self):
        self.running = False
        self.drop_client()
        for c in self.pending:
            c.close(bye=False)
        self.pending.clear()
        for s in (self.listener, self.udp):
            try:
                if s:
                    s.close()
            except OSError:
                pass


# ------------------------------------------------------------------ joiner side
def connect(ip, port, name, ship="scout", timeout=3.0):
    """Blocking: connect and shake hands. Returns (Connection, welcome). Raises NetError."""
    try:
        sock = socket.create_connection((ip, port), timeout=timeout)
    except OSError as exc:
        raise NetError(f"Could not reach {ip}:{port} ({exc.strerror or exc})")
    conn = Connection(sock)
    conn.send({"t": "hello", "v": PROTO_VERSION, "name": name, "ship": ship})
    deadline = time.time() + timeout
    while time.time() < deadline:
        for msg in conn.poll():
            if msg.get("t") == "welcome":
                return conn, msg
            if msg.get("t") == "reject":
                conn.close(bye=False)
                raise NetError(msg.get("why", "Host refused the connection"))
        if not conn.alive:
            break
        time.sleep(0.02)
    conn.close(bye=False)
    raise NetError("The host did not answer")


class Connector:
    """Runs connect() in a thread so the menu stays responsive."""

    def __init__(self, ip, port, name, ship="scout"):
        self.ip, self.port = ip, port
        self.done = False
        self.result = None
        self.error = None
        threading.Thread(target=self._run, args=(name, ship), daemon=True).start()

    def _run(self, name, ship):
        try:
            self.result = connect(self.ip, self.port, name, ship)
        except NetError as exc:
            self.error = str(exc)
        except Exception as exc:                 # never leave the menu hanging
            self.error = str(exc)
        self.done = True


class LanScanner:
    """Broadcasts a discovery request and collects the hosts that answer."""

    def __init__(self, port):
        self.port = int(port)
        self.hosts = {}
        self.scanning = False

    def scan(self, duration=1.2):
        if self.scanning:
            return
        self.scanning = True
        threading.Thread(target=self._run, args=(duration,), daemon=True).start()

    def _run(self, duration):
        found = {}
        sock = None
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.settimeout(0.2)
            sock.bind(("", 0))
            for target in broadcast_targets():
                try:
                    sock.sendto(DISCOVERY_MAGIC, (target, self.port))
                except OSError:
                    pass
            end = time.time() + duration
            while time.time() < end:
                try:
                    data, addr = sock.recvfrom(2048)
                except socket.timeout:
                    continue
                except OSError:
                    continue
                try:
                    info = json.loads(data)
                except ValueError:
                    continue
                if isinstance(info, dict) and info.get("game") == GAME_ID:
                    info["ip"] = addr[0]
                    found[(addr[0], info.get("port", self.port))] = info
        except OSError:
            pass
        finally:
            if sock:
                sock.close()
            self.hosts = found
            self.scanning = False

    def results(self):
        """Hosts found by the last scan (a host seen on both 127.0.0.1 and its LAN address is listed once)."""
        items = sorted(self.hosts.values(), key=lambda h: h["ip"].startswith("127."))
        seen, out = set(), []
        for info in items:
            key = (info.get("name"), info.get("port"))
            if key in seen:
                continue
            seen.add(key)
            out.append(info)
        return out
