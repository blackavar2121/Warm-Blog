// Bricolage theme — light/dark toggle (persisted) + mobile nav.
(function () {
  var root = document.documentElement;

  function current() {
    var set = root.getAttribute("data-mode");
    if (set) return set;
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  }

  document.querySelectorAll("[data-toggle-theme]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var next = current() === "dark" ? "light" : "dark";
      root.setAttribute("data-mode", next);
      try { localStorage.setItem("bricolage-mode", next); } catch (e) {}
    });
  });

  var head = document.querySelector(".mhead");
  document.querySelectorAll("[data-toggle-nav]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var open = head ? head.classList.toggle("nav-open") : false;
      btn.setAttribute("aria-expanded", open ? "true" : "false");
    });
  });
})();
