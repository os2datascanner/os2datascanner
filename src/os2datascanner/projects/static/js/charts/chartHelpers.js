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

  const sourceTypes = JSON.parse(document.getElementById('source_types').textContent);

  const resolutionStatus = JSON.parse(document.getElementById('resolution_status').textContent);

  const matchData = JSON.parse(document.getElementById('match_data').textContent);

  let matchStatusByOrgUnit = JSON.parse(document.getElementById('match_status_by_org_unit').textContent);

  let newMatchesByMonth = JSON.parse(document.getElementById('new_matches_by_month').textContent);

  let unhandledMatchesByMonth = JSON.parse(document.getElementById('unhandled_matches_by_month').textContent);

  // Finds the total number matches in the array
  totalArrayValue = function (array, index) {
    let number = 0;
    for (let i = 0; i < array.length; i++) {
      number += array[i][index];
    }
    return number;
  };

  // Prepare data for doughnut chart
  const totalHandledMatches = matchData.handled;
  const totalMatches = matchData.handled + matchData.unhandled;
  var handledPercentage = totalHandledMatches / totalMatches * 100;

  // Percentage of handled matches
  drawDoughnut(totalHandledMatches, totalMatches, handledPercentage);

  // Distribution of data types and resolution status
  drawPie(
    sourceTypes,
    'datasources',
    ['#fed149', '#5ca4cd', '#21759c', '#00496e']
  );
  drawPie(
    // Change the order of the data structure
    [3, 2, 1, 4, 0].map(i => resolutionStatus[i]),
    'resolution_status',
    ['#80ab82', '#a2e774', '#35bd57', '#1b512d', '#7e4672']
  );

  // Department distribution
  drawBar(matchStatusByOrgUnit, 'department_distribution', ["Handled matches", "Total matches"], true, true);

  // New and unhandled matches by month
  drawBar(newMatchesByMonth, 'new_matches_by_month');
  drawBar(unhandledMatchesByMonth, 'unhandled_matches');
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