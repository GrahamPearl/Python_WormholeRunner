"""Network helper for Wormhole Runner (works on Windows and Linux).

    python lan_check.py             show this PC's addresses and test discovery
    python lan_check.py host        act as a host so another PC can try to find it
    python lan_check.py scan        look for hosts on the network
    python lan_check.py connect IP  try a real connection to a host (IP or IP:port)
"""
import sys
import time

from game import net
from game.config import settings


def show_addresses(port):
    print("This PC's IPv4 addresses:", ", ".join(net.local_ipv4_addresses()) or "none found")
    print(f"Game port: {port} (TCP for the game, UDP for finding hosts)")
    print("Broadcast targets used for discovery:", ", ".join(net.broadcast_targets()))


def scan(port):
    scanner = net.LanScanner(port)
    scanner.scan(2.0)
    while scanner.scanning:
        time.sleep(0.1)
    hosts = scanner.results()
    if not hosts:
        print("No hosts found. Check that the host is running and that its firewall allows port", port)
    for h in hosts:
        print(f"  found: {h.get('name')}  {h['ip']}:{h.get('port')}  level {h.get('level')}  "
              f"{h.get('players')}/{h.get('max')} players")


def host(port):
    server = net.GameServer(port, "lan_check host")
    print(f"Hosting a test game on port {port}. Press Ctrl+C to stop.")
    try:
        while True:
            joined = server.poll_join()
            if joined:
                print("A player connected:", joined[1].get("name"))
                joined[0].send({"t": "welcome", "pid": 2, "name": "lan_check", "settings": {}})
                time.sleep(1)
                server.drop_client()
            time.sleep(0.1)
    except KeyboardInterrupt:
        server.stop()


def connect(addr, port):
    ip, port = net.parse_address(addr, port)
    try:
        conn, _ = net.connect(ip, port, "lan_check")
    except net.NetError as exc:
        print("FAILED:", exc)
        return
    print(f"Connected to {ip}:{port} - the network path works.")
    conn.close()


if __name__ == "__main__":
    port = int(settings.get("net.port"))
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode == "host":
        show_addresses(port)
        host(port)
    elif mode == "scan":
        scan(port)
    elif mode == "connect" and len(sys.argv) > 2:
        connect(sys.argv[2], port)
    else:
        show_addresses(port)
        scan(port)
