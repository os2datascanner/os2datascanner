/* exported colorFunction, stepSizeFunction, avoidZero */

// Color function
// reads colors from :root
var colorFunction = function (color) {
  "use strict";
  return getComputedStyle(document.querySelector(':root')).getPropertyValue(color);
};

// Step size function
// Array = values
// steps = how many steps on y-axis ( 0 doesn't count)
var stepSizeFunction = function (array, steps) {
  "use strict";
  return (Math.ceil(Math.max.apply(null, array) / 100) * 100) / steps;
};

// isNan function

var avoidZero = function (a, b) {
  "use strict";
  return isNaN(((a / b) * 100)) ? 0 + '%' : ((a / b) * 100).toFixed(0) + '%';
};

// Set default animation duration on charts - this can be changed for each chart if needed.
Chart.defaults.animation.easing = 'easeOutQuad';
Chart.defaults.animation.duration = 1700;

function drawCharts() {
  // json_script solution - Safe from in-page script execution

  var sensitivities = JSON.parse(document.getElementById('sensitivities').textContent);

  var handledMatches = JSON.parse(document.getElementById('handled_matches').textContent);

  var sourceTypes = JSON.parse(document.getElementById('source_types').textContent);

  var newMatchesByMonth = JSON.parse(document.getElementById('new_matches_by_month').textContent);

  var unhandledMatchesByMonth = JSON.parse(document.getElementById('unhandled_matches_by_month').textContent);

  var handledMatchesStatus = JSON.parse(document.getElementById('handled_matches_status').textContent);

  // Finds the total number matches in the array
  totalArrayValue = function (array, index) {
    let number = 0;
    for (let i = 0; i < array.length; i++) {
      number += array[i][index];
    }
    return number;
  };

  // Calculates the percentage for 'Håndterede matches -> Alle matches'
  var totalMatches = totalArrayValue(sensitivities, 1);
  var totalHandledMatches = totalArrayValue(handledMatches, 1);
  var handledPercentage = totalHandledMatches / totalMatches * 100;
  // To fixed decimal point
  handledPercentageFixed = handledPercentage.toFixed(1);

  drawDoughnuts(totalHandledMatches, totalMatches, handledPercentage);
  drawPies(sensitivities, sourceTypes, handledMatchesStatus[0]);
  drawLines(newMatchesByMonth, unhandledMatchesByMonth);
}

function setStatDropdownEvent() {
  // capture the change event on the .statistic wrappers for easier DOM manipulation
  // when the dropdowns change values
  var statistics = document.querySelectorAll('.statistic');
  Array.prototype.forEach.call(statistics, function (statistic) {
    statistic.addEventListener('change', function (e) {
      var chartTarget = e.target.value;

      // hide the elements to be hidden
      Array.prototype.forEach.call(
        statistic.querySelectorAll('.chart_description:not([data-chartid="' + chartTarget + '"]), .chart_container:not([data-chartid="' + chartTarget + '"])'),
        function (elmToHide) {
          elmToHide.className = (elmToHide.className + ' hidden').trim();
        }
      );

      // show the elements to be shown
      Array.prototype.forEach.call(statistic.querySelectorAll('[data-chartid="' + chartTarget + '"]'), function (elmToShow) {
        elmToShow.className = elmToShow.className.replace(/hidden\s?/gi, '').trim();
      });
    });
  });
}

function clearCharts() {
  for (let chart of charts) {
    chart.destroy();
  }
  charts.length = 0;
}

document.addEventListener('DOMContentLoaded', function () {
  window.charts = [];
});

htmx.onLoad(function (content) {
  if (content.className.includes("content") || content.className.includes("page")) {
    clearCharts();
    setStatDropdownEvent();
    setDropdownEvent();
    drawCharts();
  }

});