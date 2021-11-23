/* jshint -W098 */ //disable check is used ( called from html )
// toggle scan details
function toggleDetails() {
  var x = document.getElementById("scan-details");
  var down = document.getElementById("expand_more");
  var right = document.getElementById("chevron_right");

  if (x.style.display === "none") {
    x.style.display = "block";
    down.style.display = "inline";
    right.style.display = "none";
  } else {
    x.style.display = "none";
    down.style.display = "none";
    right.style.display = "inline";
  }
}
