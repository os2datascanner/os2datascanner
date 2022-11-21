function showOverview(row, toggleButton) {
  console.log("HIT");
  let overviewRow = row.nextElementSibling;
  toggleClass(toggleButton, "up");
  let buttonOpen = hasClass(toggleButton, "up");

  overviewRow.hidden = !buttonOpen;
}

htmx.onLoad(function (content) {
  if (hasClass(content, "content") || hasClass(content, "page")) {

    expandButtons = document.querySelectorAll(".overview-expand");

    expandButtons.forEach(element => {
      element.addEventListener("click", function (e) {
        targ = e.target;
        let row = closestElement(targ, "tr");
        showOverview(row, targ);
      });
    });
  }
});