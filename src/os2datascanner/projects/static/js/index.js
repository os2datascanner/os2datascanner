import '../scss/master.scss';

htmx.onLoad(function (content) {

  $(content).find("a[data-modal='modal:open']").click(function (e) {
    e.preventDefault();

    // Find the target element (same as our href)
    const target = $(this).attr("href");

    // Find the src to set
    const src = $(this).attr("data-src");

    // Find the iframe in our target and set its src
    $(target).find("iframe").attr("src", src);
  });

  // Toggle visiblity of expandable rows, start
  $(document).on("click", "[data-toggle]", function () {
    let expandTarget = $(this).attr("data-toggle");

    if ($(expandTarget).is('[hidden]')) {
      $(expandTarget).removeAttr('hidden');
    } else {
      $(expandTarget).attr('hidden', '');
    }
  });
  // Toggle visiblity of expandable rows, stop

  // Hides the "Let's go" button when starting scans after a click
  // to prevent users accidentally starting multiple.
  $('.run-scan-button').on("click", function () {
    $(this).hide();
    $("#waiting-scanner-run-btn").show();
  });

});


