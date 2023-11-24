function highlightAnchorElement(id) {
  document.querySelectorAll("h2,h1").forEach(el => {
    el.classList.remove("highlighted");
  });
  const requestedEl = document.querySelector(id);
  requestedEl.classList.add("highlighted");
}

document.addEventListener("DOMContentLoaded", () => {
  if (window.location.hash) { highlightAnchorElement(window.location.hash); }
  const links = document.querySelectorAll("a");
  links.forEach(a => {
    a.addEventListener('click', () => {
      highlightAnchorElement(a.hash);
    });
  });
});