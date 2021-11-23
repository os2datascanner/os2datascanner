"use strict"
// Color function
// reads colors from :root
var colorFunction = function (color) {
  return getComputedStyle(document.querySelector(':root')).getPropertyValue(color);
}

// Step size function
// Array = values
// steps = how many steps on y-axis ( 0 doesn't count)
var stepSizeFunction = function(array, steps) {
  return (Math.ceil(Math.max.apply(null, array)/100)*100)/steps;
}

// isNan function

var avoidZero = function(a, b) {
  return isNaN(((a/b)*100)) ? 0 + '%' : ((a/b)*100).toFixed(0) + '%'
}

// Set default animation duration on charts - this can be changed for each chart if needed.
Chart.defaults.global.animation.easing = 'easeOutQuad';
Chart.defaults.global.animation.duration = 1700;


// Select list
$('.dropdown').click(function () {
  $(this).attr('tabindex', 1).focus();
  $(this).toggleClass('active');
  $(this).find('.dropdown-menu').slideToggle(300);
});

$('.dropdown').focusout(function () {
    $(this).removeClass('active');
  $(this).find('.dropdown-menu').slideUp(300);
});

$('.dropdown .dropdown-menu li').click(function () {
  if($(this).text() != $(this).parents('.dropdown').find('.select_span').text()) {
    $(this).parents('.dropdown').find('span')[0].firstChild.data = $(this).text();
    // Was part of the solution - haven't found a use for it
    // $(this).parents('.dropdown').find('input').attr('value', $(this).attr('id'));
  }
});

// Toggle the class 'hidden' on change from the select list
$(document).ready(function(){
  $(".select_span").on('DOMSubtreeModified',function(){
    $($(this).parents('.statistic').find('.chart_container, .chart_description').toggleClass("hidden"));
  });
});
