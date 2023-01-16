
function showChildren(ul, toggleButton) {
  toggleButton.classList.toggle("up");
  let buttonOpen = toggleButton.classList.contains("up");
  ul.hidden = !buttonOpen;
}

function setExpandButtons(buttons) {
  buttons.forEach(element => {
    element.querySelector(".orgunit_name").addEventListener("click", function (e) {
      let targ = e.target.parentNode;
      let ul = targ.querySelector(".children");
      showChildren(ul, targ);
    });
  });
}

htmx.onLoad(function () {
  let expandButtons = document.querySelectorAll(".has_children");
  setExpandButtons(expandButtons);
});