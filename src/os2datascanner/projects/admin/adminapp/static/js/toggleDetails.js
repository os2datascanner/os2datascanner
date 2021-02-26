// toggle scan details
function toggleDetails() {
  var x = document.getElementById("scan-details");
  var down = document.getElementById("arrow_drop_down");
  var right = document.getElementById("arrow_right");

  if (x.style.display === "none") {
    x.style.display = "block";
    down.style.display = "block";
    right.style.display = "none";
  } else {
    x.style.display = "none";
    down.style.display = "none";
    right.style.display = "block";
  }
}
