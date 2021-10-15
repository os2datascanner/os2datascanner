/* jshint -W098 */ //disable check is used ( called from html )
/* When the user clicks on the button,
toggle between hiding and showing the dropdown content */
function dropMenu() {
  document.getElementById("userMenu").classList.toggle("show");
}

// Close the dropdown if the user clicks outside of it
window.onclick = function(e) {
  if (!e.target.matches('.dropbtn, .user__name, .material-icons')) {
    var dropdown = document.getElementById("userMenu");
      if (dropdown.classList.contains('show')) {
        dropdown.classList.remove('show');
      }
  }
};

// Toggle side navigation on small display sizes
document.addEventListener('DOMContentLoaded', function () {
  document.getElementById("navigation-toggle").addEventListener("click", function (e) {
    var menu = document.getElementById("sidemenu");
    var toggle = e.target;
    var isHidden = !toggle.hasAttribute("aria-expanded") || toggle.getAttribute("aria-expanded") === "false";
    if (isHidden) {
      menu.style.display = "block";
      toggle.setAttribute("aria-expanded", "");
    } else {
      menu.style.display = "none";
      toggle.removeAttribute("aria-expanded");
    }
  });
});
