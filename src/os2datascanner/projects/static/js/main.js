os2web = window.os2web || {};
(function(os2web, $) {
    // Enable iframe-based modal dialogs
    $('.modal.iframe').on('shown.bs.modal', function() {
      var $this = $(this), src = $this.attr("data-href");
      if (src) {
          $this.find('iframe').first().attr("src", src);
      }
    });

    // Validation radio buttons in the domain dialog
    $('input.validateradio').on("click", function() {
        var $this = $(this),
            id = '#validation_method_desc_' + $this.attr('value');
        $this.attr('data-target', id);
        $this.tab('show');
    });

    // Resize iframe according to content height
    $('.modal-body iframe').on('load',function(){
      var $this = $(this);
      $this.height($this.contents().find('body').height());
      $this.contents().on('click','.nav-tabs a',function(){
        $this.height($this.contents().find('body').height());
      });
    });

    $.extend(os2web, {
        iframeDialog: function(idOrElem, url, title) {
            $elem = $(idOrElem);
            $elem.find('iframe').first().attr('src', 'about:blank');
            $elem.attr('data-href', url);
            if(title) {
                labelId = $elem.attr('aria-labelledby');
                if(labelId) {
                    $('#' + labelId).html(title);
                }
            }
            $elem.modal({show: true});
        }
    });
})(os2web, jQuery);

/* debounce function from https://davidwalsh.name/javascript-debounce-function */
// Returns a function, that, as long as it continues to be invoked, will not
// be triggered. The function will be called after it stops being called for
// N milliseconds. If `immediate` is passed, trigger the function on the
// leading edge, instead of the trailing.
// this method is used globally, so instruct JSHint to ignore W098 which enforces
// that functions must be used
/* jshint -W098 */
function os2debounce(func, wait, immediate) {
	var timeout;
	return function() {
		var context = this, args = arguments;
		var later = function() {
			timeout = null;
			if (!immediate) {
                func.apply(context, args);
            }
		};
		var callNow = immediate && !timeout;
		clearTimeout(timeout);
		timeout = setTimeout(later, wait);
		if (callNow) {
            func.apply(context, args);
        }
	};
}
/* jshint +W098 */
