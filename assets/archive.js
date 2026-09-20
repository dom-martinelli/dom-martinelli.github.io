// archive page: filter rows by bucket and by a text query. no dependencies.
(function () {
  var rows = Array.prototype.slice.call(document.querySelectorAll(".archive tbody tr"));
  var chips = Array.prototype.slice.call(document.querySelectorAll(".fchip"));
  var q = document.getElementById("q");
  var bucket = "all";

  function apply() {
    var needle = (q.value || "").toLowerCase();
    rows.forEach(function (r) {
      var okBucket = bucket === "all" || r.dataset.bucket === bucket;
      var okText = !needle || r.textContent.toLowerCase().indexOf(needle) >= 0;
      r.hidden = !(okBucket && okText);
    });
  }
  chips.forEach(function (c) {
    c.addEventListener("click", function () {
      chips.forEach(function (o) { o.classList.remove("on"); });
      c.classList.add("on");
      bucket = c.dataset.bucket;
      apply();
    });
  });
  q.addEventListener("input", apply);
})();
