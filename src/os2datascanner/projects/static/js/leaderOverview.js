function showOverview(row, toggleButton) {

  let overviewRow = row.nextElementSibling;
  toggleClass(toggleButton, "up");
  let buttonOpen = hasClass(toggleButton, "up");

  overviewRow.hidden = !buttonOpen;
}

document.addEventListener("DOMContentLoaded",
  () => {
    htmx.onLoad(function (content) {
      if (hasClass(content, "content") || hasClass(content, "page") || hasClass(content, "employee_row")) {

        let expandButtons = content.querySelectorAll(".overview-expand");

        expandButtons.forEach(element => {
          element.addEventListener("click", function (e) {
            targ = e.target;
            let row = closestElement(targ, "tr");
            showOverview(row, targ);
          });
        });
      }
    });
  }
);
