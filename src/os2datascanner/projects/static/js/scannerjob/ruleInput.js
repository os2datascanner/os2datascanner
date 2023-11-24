const ruleItems = document.getElementsByTagName("tr");
const selectedRule = document.getElementById("selectedRule");

const ruleSelected = e => {
  const ruleField = e.target.querySelector("#json").textContent;
  let watcher = document.querySelector('.watcher');
  watcher.textContent = ruleField;
  let selector = watcher.getAttribute("data-selector"),
        target = document.querySelector(selector);
  const jsonField = JSON.parse(watcher.textContent);
  selectOptions(jsonField, target);
};

for (let ruleItem of ruleItems) {
  ruleItem.addEventListener("click", ruleSelected);
}

/* exported saveName */
function saveName(name) {
  selectedRule.innerHTML = name;
}