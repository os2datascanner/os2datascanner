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
var stepSizeFunction = function(array, steps) {
  "use strict";
  return (Math.ceil(Math.max.apply(null, array)/100)*100)/steps;
};

// isNan function

var avoidZero = function(a, b) {
  "use strict";
  return isNaN(((a/b)*100)) ? 0 + '%' : ((a/b)*100).toFixed(0) + '%';
};

// Set default animation duration on charts - this can be changed for each chart if needed.
Chart.defaults.global.animation.easing = 'easeOutQuad';
Chart.defaults.global.animation.duration = 1700;

document.addEventListener('DOMContentLoaded', function () {
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
});