// Small helpers: GitHub links, copy buttons, mobile menu. No libraries.
(function () {
  var S = window.SITE || { user: "YOUR-USER", repo: "wormhole-runner", branch: "main", folder: "" };
  function repoBase() {
    return "https://github.com/" + S.user + "/" + S.repo + "/blob/" + S.branch + "/" + (S.folder ? S.folder + "/" : "");
  }
  function fixLinks() {
    document.querySelectorAll("a.code-link").forEach(function (a) {
      var url = repoBase() + a.dataset.file;
      if (a.dataset.start) url += "#L" + a.dataset.start + (a.dataset.end && a.dataset.end !== a.dataset.start ? "-L" + a.dataset.end : "");
      a.href = url; a.target = "_blank"; a.rel = "noopener";
    });
    if (S.user === "YOUR-USER") {
      var main = document.querySelector("main");
      if (main && /index\.html$|\/$/.test(location.pathname)) {
        var n = document.createElement("aside"); n.className = "box warn";
        n.innerHTML = "<h3>Teacher: one quick set-up step</h3><p>The code links still point to <code>YOUR-USER</code>. " +
          "Open <code>docs/site-config.js</code> and type your GitHub user name and repository name. That's all.</p>";
        main.insertBefore(n, main.children[1]);
      }
    }
  }
  function copyButtons() {
    document.querySelectorAll("button.copy").forEach(function (b) {
      b.addEventListener("click", function () {
        var text = b.parentElement.querySelector("code").textContent;
        (navigator.clipboard ? navigator.clipboard.writeText(text) : Promise.reject()).then(function () {
          b.textContent = "Copied!"; setTimeout(function () { b.textContent = "Copy"; }, 1500);
        }, function () { b.textContent = "Select and copy"; });
      });
    });
  }
  function menu() {
    var btn = document.querySelector(".menu-btn"), nav = document.getElementById("sidenav");
    if (!btn) return;
    btn.addEventListener("click", function () {
      var open = nav.classList.toggle("open"); btn.setAttribute("aria-expanded", open);
    });
  }
  document.addEventListener("DOMContentLoaded", function () { fixLinks(); copyButtons(); menu(); });
})();
