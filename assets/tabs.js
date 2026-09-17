// Tabs by subject. Without JS every panel shows, stacked. The URL hash holds
// the open tab, so a project page's back link returns to the right shelf.
(function () {
  document.documentElement.classList.add("js");
  var buttons = Array.prototype.slice.call(document.querySelectorAll('.tabs [role="tab"]'));
  if (!buttons.length) return;

  function show(id, focus) {
    buttons.forEach(function (b) {
      var on = b.dataset.tab === id;
      b.setAttribute("aria-selected", on ? "true" : "false");
      b.tabIndex = on ? 0 : -1;
      var panel = document.getElementById("panel-" + b.dataset.tab);
      if (panel) panel.hidden = !on;
      if (on && focus) b.focus();
    });
  }

  var ids = buttons.map(function (b) { return b.dataset.tab; });
  var start = location.hash.slice(1);
  show(ids.indexOf(start) >= 0 ? start : ids[0]);

  buttons.forEach(function (b, i) {
    b.addEventListener("click", function () {
      show(b.dataset.tab);
      history.replaceState(null, "", "#" + b.dataset.tab);
    });
    b.addEventListener("keydown", function (e) {
      var j = e.key === "ArrowRight" ? i + 1 : e.key === "ArrowLeft" ? i - 1 : null;
      if (j === null) return;
      var next = buttons[(j + buttons.length) % buttons.length];
      show(next.dataset.tab, true);
      history.replaceState(null, "", "#" + next.dataset.tab);
    });
  });
})();
