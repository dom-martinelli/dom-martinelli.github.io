// click any figure to see it full size. esc, click, or the close button to
// dismiss. without JS the link just opens the raw image, which also works.
(function () {
  var box, img, cap;
  function build() {
    box = document.createElement("div");
    box.className = "lightbox";
    box.setAttribute("role", "dialog");
    box.setAttribute("aria-modal", "true");
    box.innerHTML = '<button class="lb-close" aria-label="close">&times;</button>' +
      '<img alt=""><p class="lb-cap"></p><a class="lb-raw" target="_blank" rel="noopener">open the file</a>';
    img = box.querySelector("img");
    cap = box.querySelector(".lb-cap");
    box.addEventListener("click", function (e) {
      if (e.target === box || e.target.classList.contains("lb-close")) close();
    });
    document.body.appendChild(box);
  }
  function open(href, alt) {
    if (!box) build();
    img.src = href;
    img.alt = alt || "";
    cap.textContent = alt || "";
    box.querySelector(".lb-raw").href = href;
    box.classList.add("on");
    document.documentElement.style.overflow = "hidden";
    box.querySelector(".lb-close").focus();
  }
  function close() {
    box.classList.remove("on");
    document.documentElement.style.overflow = "";
  }
  document.addEventListener("click", function (e) {
    var a = e.target.closest && e.target.closest("a.zoom");
    if (!a || e.metaKey || e.ctrlKey) return;   // cmd-click still opens a tab
    e.preventDefault();
    var i = a.querySelector("img");
    open(a.getAttribute("href"), i ? i.alt : "");
  });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && box && box.classList.contains("on")) close();
  });
})();
