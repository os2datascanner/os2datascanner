// Remove rounds corners of table when stuck on top of screen.
function handleTableCorners() {
  const stickyElm = document.querySelector('.table-topbar');

  const observer = new IntersectionObserver(
    ([e]) => e.target.classList.toggle('stuck', e.intersectionRatio < 1),
    { rootMargin: '-1px 0px 0px 0px', threshold: [1] }
  );

  if (stickyElm) {
    observer.observe(stickyElm);
  }
}

// Handle checkboxes
function handleChecked() {
  var numChecked = $("input[name='table-checkbox']:checked").length;
  $(".selected-cb .num-selected").text(numChecked);
  $(".table-checkbox__action").prop("disabled", !Boolean(numChecked));

  $("input[name='table-checkbox']:not(:checked)").closest("tr").removeClass("highlighted");
  $("input[name='table-checkbox']:checked").closest("tr").addClass("highlighted");
}

// attach click handler to document to be prepared for the scenario
// where we dynamically add more rows
document.addEventListener("click", function (e) {
  let row;
  var targ = e.target;

  if (hasClass(targ, "matches-expand")) {
    // toggle the matches of a single row
    row = closestElement(targ, "tr[data-type]");
    toggleMatchesList([row], targ);
  }

  if (hasClass(targ, "matches-expand-all")) {
    // toggle the matches of all rows
    var rows = document.querySelectorAll("tr[data-type]");
    toggleMatchesList(rows, targ);

    // store the user's preference in window.localStorage
    var preferenceExpand = hasClass(targ, "up") ? "expanded" : "collapsed";
    setStorage("os2ds-prefers-expanded-results", preferenceExpand);
  }

  if (hasClass(targ, "toggle-next-row")) {
    // toggle the matches of a single row
    row = closestElement(targ, "tr");
    if (row) {
      toggleMatchesList([row], targ);
    }
  }

  if (hasClass(targ, "probability-toggle")) {
    var isPressed = targ.getAttribute("aria-pressed") === "true";
    if (isPressed) {
      targ.setAttribute("aria-pressed", "false");
    } else {
      targ.setAttribute("aria-pressed", "true");
    }

    Array.prototype.forEach.call(document.querySelectorAll(".matches-list__column--probability"), function (col) {
      if (isPressed) {
        col.setAttribute("hidden", "");
      } else {
        col.removeAttribute("hidden");
      }
    });

    // store the user's preference in window.localStorage
    var preferenceProbability = isPressed ? "hide" : "show";
    setStorage("os2ds-prefers-probability", preferenceProbability);
  }

  if (hasClass(targ, "order-by")) {
    document.getElementById('order').value = targ.value;
    document.getElementById('order_by').value = targ.name;
  }

});

// function to use localStorage
function setStorage(item, value) {
  try {
    window.localStorage.setItem(item, value);
  } catch (e) {
    console.error("Could not save " + item + " with value " + value + " to localStorage", e);
  }
}

// IE11 way of doing Element.closest
function closestElement(elm, selector) {
  var parent = elm;
  while (parent) {
    if (parent.matches(selector)) {
      break;
    }
    parent = parent.parentElement;
  }
  return parent;
}

function toggleMatchesList(objectRows, toggleButton) {
  toggleClass(toggleButton, "up");
  var buttonOpen = hasClass(toggleButton, "up");

  Array.prototype.forEach.call(objectRows, function (row) {
    var matchesList = row.nextElementSibling;

    // show/hide the matches. We can't just toggle their state as
    // we may have clicked the matches-expand-all button, so we need to read
    // the state from the button that was clicked.
    // toggleButton may be the button that belongs to the row we're iterating
    // or it may be the matches-expand-all button. If the latter is the case,
    // we also need to toggle the button that belongs to the row.
    matchesList.hidden = !buttonOpen;
    rowButton = row.querySelector(".matches-expand");
    if (buttonOpen) {
      addClass(row, "up");
      if (rowButton !== toggleButton) {
        addClass(rowButton, "up");
      }
    } else {
      removeClass(row, "up");
      if (rowButton !== toggleButton) {
        removeClass(rowButton, "up");
      }
    }
  });
}

// IE11 way of doing Element.classList.add and Element.classList.remove
function toggleClass(elm, className) {
  if (!hasClass(elm, className)) {
    addClass(elm, className);
  } else {
    removeClass(elm, className);
  }
}

function addClass(elm, className) {
  if (!hasClass(elm, className)) {
    elm.className = (elm.className + " " + className).trim();
  }
}

function removeClass(elm, className) {
  elm.className = elm.className.replace(className, "").trim();
}

// IE11 way of doing elm.classList.contains
function hasClass(elm, className) {
  classList = [];
  if (typeof (elm.className) === "string") {
    classList = elm.className ? elm.className.split(" ") : [];
  } else {
    classList = Array.from(elm.classList);
  }
  return classList.indexOf(className) > -1;
}

// show a tooltip based on an event and its target. Assumes a DOM structure
// where event.target has a descendant [data-tooltip-text]
function showTooltip(event) {
  var wrapper = event.target;
  var tooltipElm = wrapper.querySelector("[data-tooltip-text]");
  var textWidth = tooltipElm.offsetWidth;
  var wrapperStyle = getComputedStyle(wrapper);
  var wrapperWidth = wrapper.offsetWidth - parseFloat(wrapperStyle.paddingLeft) - parseFloat(wrapperStyle.paddingRight);

  if (textWidth > wrapperWidth) {
    addClass(wrapper, "cursor-help");
    var tip = document.createElement("div");
    var rect = wrapper.getBoundingClientRect();
    var x = Math.round(event.pageX - rect.left - window.scrollX);
    var y = Math.round(event.pageY - rect.top - window.scrollY);
    tip.innerText = tooltipElm.innerText;
    tip.setAttribute("data-tooltip", "");
    tip.setAttribute("style", "top:" + y + "px;left:" + x + "px;");
    wrapper.appendChild(tip);
  }
}

function hideTooltip(event) {
  // delete the [data-tooltip] element from the DOM
  var targ = event.target;
  var tooltip = document.querySelector("[data-tooltip]");
  if (tooltip) {
    targ.removeChild(tooltip);
  }
  // Remove the .cursor-help class from the mouseout'ed tooltip
  removeClass(targ, "cursor-help");
}

function prepareTable() {
  // if user prefers to have all rows expanded, do that.
  const prefersExpanded = window.localStorage.getItem("os2ds-prefers-expanded-results");
  if (prefersExpanded && prefersExpanded === "expanded") {
    document.querySelector(".matches-expand-all").click();
  }

  // Uncheck checkboxes on load.
  $("input[name='table-checkbox']").prop("checked", false);
  $("#select-all").prop("checked", false);
  $(".table-checkbox__action").prop("disabled", true);

  // if user prefers to see probability, do that.
  const prefersProbability = window.localStorage.getItem("os2ds-prefers-probability");
  if (prefersProbability && prefersProbability === "show") {
    document.querySelector(".probability-toggle").click();
  }

  handleTableCorners();
}

// Add tooltips
function addTooltipListeners(element) {
  element.addEventListener("mouseenter", showTooltip);
  element.addEventListener("mouseleave", hideTooltip);
}

document.addEventListener("DOMContentLoaded", function () {
  prepareTable();

  htmx.onLoad(function (content) {

    if (hasClass(content, 'page') || hasClass(content, 'datatable-wrapper') || hasClass(content, 'content')) {

      prepareTable();
      
      var tooltips = document.querySelectorAll(".tooltip");
      tooltips.forEach(addTooltipListeners);

      // Listen for click on toggle checkbox
      $("#select-all").change(function () {
        $("input[name='table-checkbox']").prop("checked", $(this).prop("checked"));
        handleChecked();
      });

      // Iterate each checkbox
      $("input[name='table-checkbox']").change(handleChecked);

      // Copy Path function
      if (typeof ClipboardJS !== 'undefined') {
        new ClipboardJS(document.querySelectorAll('[data-clipboard-text]'));
      }
    }

  });
});
