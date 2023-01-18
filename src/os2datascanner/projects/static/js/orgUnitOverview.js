
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

function setAddButtons(buttons) {
  buttons.forEach(element => {
    element.addEventListener("click", function (e) {
      let targ = e.target;
      let selectField = targ.parentNode.querySelector(".select_manager");
      targ.style.display = "none";
      selectField.hidden = false;
    });
  });
}

htmx.onLoad(function () {
  let expandButtons = document.querySelectorAll(".has_children");
  let addButtons = document.querySelectorAll(".add_manager_button");
  setExpandButtons(expandButtons);
  setAddButtons(addButtons);
});