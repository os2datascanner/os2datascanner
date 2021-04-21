import "core-js"

// import css
import '../css/master.scss';

// import js files
import './handle-match.js';
import './show-more.js';
import './filter-options.js';
import './pagination.js';
import './results.js';

// Copy Path function
new ClipboardJS(document.querySelectorAll('[data-clipboard-text]'));

//Change background color after scroll
$(window).on("scroll", function() {
  if($(window).scrollTop() > 200) {
      $(".datatable th").addClass("scrollActive");
  } else {
     $(".datatable th").removeClass("scrollActive");
  }
});
