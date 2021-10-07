// Listen for click on toggle checkbox
$("#select-all").change(function() {
  $("input[name='match-checkbox']").prop("checked", $(this).prop("checked"));
  handleChecked();
});

// Handle checkboxes
function handleChecked() {
  var numChecked = $("input[name='match-checkbox']:checked").length;
  $(".selected-cb .num-selected").text(numChecked);
  $(".handle-match__action").prop("disabled", !Boolean(numChecked))

  $("input[name='match-checkbox']:not(:checked)").closest("tr").removeClass("highlighted");
  $("input[name='match-checkbox']:checked").closest("tr").addClass("highlighted");
}
// Iterate each checkbox
$("input[name='match-checkbox']").change(handleChecked);

// attach click handler to document to be prepared for the scenario
// where we dynamically add more rows
document.addEventListener("click", function (e) {
  var targ = e.target;

  if (hasClass(targ, "matches-expand")) {
    // toggle the matches of a single row
    var row = closestElement(targ, "tr[data-type]");
    toggleMatchesList([row], targ);
  }

  if (hasClass(targ, "matches-expand-all")) {
    // toggle the matches of all rows
    var rows = document.querySelectorAll("tr[data-type]");
    toggleMatchesList(rows, targ);

    // store the user's preference in window.localStorage
    var preference = hasClass(targ, "open") ? "expanded" : "collapsed";
    setStorage("os2ds-prefers-expanded-results", preference);
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
    var preference = isPressed ? "hide" : "show";
    setStorage("os2ds-prefers-probability", preference);
  }
});

document.addEventListener("DOMContentLoaded", function () {
  // if user prefers to have all rows expanded, do that.
  var prefersExpanded = window.localStorage.getItem("os2ds-prefers-expanded-results")
  if (prefersExpanded && prefersExpanded == "expanded") {
    document.querySelector(".matches-expand-all").click();
  }

  // if user prefers to see probability, do that.
  var prefersExpanded = window.localStorage.getItem("os2ds-prefers-probability")
  if (prefersExpanded && prefersExpanded == "show") {
    document.querySelector(".probability-toggle").click();
  }
});

Array.prototype.forEach.call(document.querySelectorAll(".tooltip"), function (element) {
  element.addEventListener("mouseenter", showTooltip);
  element.addEventListener("mouseleave", hideTooltip);
});

// function to use localStorage
function setStorage (item, value) {
  try {
    window.localStorage.setItem(item, value);
  } catch (e) {
    console.error("Could not save " + item + " with value " + value + " to localStorage", e)
  }
}

// IE11 way of doing Element.closest
function closestElement(elm, selector) {
  var parent = elm.parentElement;
  while (parent) {
    if (parent.matches(selector)) {
      break;
    }
    parent = parent.parentElement;
  }
  return parent;
}

function toggleMatchesList(objectRows, toggleButton) {
  toggleClass(toggleButton, "open");
  var buttonOpen = hasClass(toggleButton, "open");

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
      addClass(row, "open");
      if (rowButton !== toggleButton) {
        addClass(rowButton, "open");
      }
    } else {
      removeClass(row, "open");
      if (rowButton !== toggleButton) {
        removeClass(rowButton, "open");
      }
    }
  })
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
  var classList = elm.className ? elm.className.split(" ") : [];
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
    tip.setAttribute("style", "top:" + y  + "px;left:" + x + "px;");
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

function getCookie(name) {
  var cookieValue = null;
  if (document.cookie && document.cookie !== "") {
      var cookies = document.cookie.split(";");
      for (var i = 0; i < cookies.length; i++) {
          var cookie = cookies[i].trim();
          // Does this cookie string begin with the name we want?
          if (cookie.substring(0, name.length + 1) === (name + "=")) {
              cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
              break;
          }
      }
  }
  return cookieValue;
}

// Handle matches
function handleMatches(pks) {
  if (pks.length > 0) {
    $(".datatable").addClass("disabled");
    $.ajax({
      url: "/api",
      method: "POST",
      data: JSON.stringify({
        "action": "set-status-2",
        "report_id": pks,
        "new_status": 0
      }),
      contentType: "application/json; charset=utf-8",
      dataType: "json",
      beforeSend: function(xhr, settings) {
        xhr.setRequestHeader("X-CSRFToken", getCookie("csrftoken"))
      }
    }).done(function(body) {
      $(".datatable").removeClass("disabled");
      if (body["status"] == "ok") {
        location.reload(true)
      } else if (body["status"] == "fail") {
        console.log(
            "Attempt to call set-status-2 failed: "
            + body["message"])
      }
    })
  }
}

$(".handle-match__action").click(function() {
  // get pks from checked checkboxes
  var pks = $.map($("input[name='match-checkbox']:checked"), function (e) {
    return $(e).attr("data-report-pk")
  });
  handleMatches(pks);
})

$(".matches-handle").click(function() {
  var pk = $(this).closest("tr[data-type]").find("input[name='match-checkbox']").attr("data-report-pk");
  handleMatches([pk])
})
