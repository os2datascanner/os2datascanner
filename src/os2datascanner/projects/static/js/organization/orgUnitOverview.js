
function showChildren(ul, toggleButton) {
  toggleButton.classList.toggle("up");
  let buttonOpen = toggleButton.classList.contains("up");
  ul.hidden = !buttonOpen;
}

function showParent(el) {
  if (!el.parentNode.classList.contains("root")) {
    const parentUl = el.parentNode;
    parentUl.hidden = false;
    const parentLi = parentUl.parentNode;
    parentLi.classList.add("up");
    showParent(parentLi);
  }
}

function revealHighlighted(content) {
  const highlighted = content.querySelectorAll(".highlighted");
  for (let el of highlighted) {
    showParent(el);
  }
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

htmx.onLoad(function (content) {
  let expandButtons = content.querySelectorAll(".has_children");
  if (content.classList.contains("has_children")) {
    expandButtons = [content];
  }
  let addButtons = content.querySelectorAll(".add_manager_button");
  setExpandButtons(expandButtons);
  setAddButtons(addButtons);

  revealHighlighted(content);
});