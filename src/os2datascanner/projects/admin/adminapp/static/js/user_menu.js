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
}