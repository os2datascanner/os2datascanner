import '../css/master.scss';

// Copy Path function
new ClipboardJS(document.querySelectorAll('[data-clipboard-text]'));

// Handle matches, start
const button = $('.handle-match-button');
const actions = $('.handle-match__action')
const buttonWidth = button.outerWidth(false);
const tooltip = $('.handle-match');

var offsetTop = 10

$(tooltip).css({
  marginTop: offsetTop,
  marginLeft: -buttonWidth/2
});

$(button).click(function() {
  $(this).toggleClass("is-active");
  $(this).siblings(tooltip).toggleClass("show");
})

function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

$(actions).click(function() {
  const button = $(this)

  const report_id = parseInt(button.attr("data-report-pk"))
  const new_status = parseInt(button.attr("data-status"))

  if (!isNaN(report_id) && !isNaN(new_status)) {
    $.ajax({
      url: "/api",
      method: "POST",
      data: JSON.stringify({
        "action": "set-status-1",

        "report_id": report_id,
        "new_status": new_status
      }),
      contentType: "application/json; charset=utf-8",
      dataType: "json",
      beforeSend: function(xhr, settings) {
        xhr.setRequestHeader("X-CSRFToken", getCookie("csrftoken"))
      }
    }).done(function(body) {
      if (body["status"] == "ok") {
        button.closest("tr").remove()
      } else if (body["status"] == "fail") {
        console.log(
            "Attempt to call set-status-1 failed: "
            + body["message"])
      }
    })
  }
})

function openMatchHandler() {
  $(tooltip).addClass("show");
}

function closeMatchHandler() {
  $(tooltip).removeClass("show");
}
// Handle matches, stop
