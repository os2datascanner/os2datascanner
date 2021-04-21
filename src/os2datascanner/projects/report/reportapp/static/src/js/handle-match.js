// Changes 'x of x' on load, to avoid showing 0 of 10
// while having less than 10 matches.
window.addEventListener('load', function () {
  showChecked();
});

// Listen for click on toggle checkbox
$('#select-all').click(function() {
  if(this.checked) {
      // Iterate each checkbox
      $('td input:checkbox').each(function() {
        this.checked = true;
      });
  } else {
      $('td input:checkbox').each(function() {
        this.checked = false;                   
      });
  }
});

// Show selected checkboxes
function showChecked(){
  var selected = $("td input:checked").length
      + " af " + $("td .datatable-checkbox").length + " valgt";
  $(".selected-cb").text(selected);
}
// Iterate each checkbox
$("input[name=match-checkbox]").each(function( i ) {
  $(this).on("click", function(){
    i = showChecked();
  });
});

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

// Handle matches
const actions = $('.handle-match__action')

$(actions).unbind('click').click(function() {
  const sel = document.getElementById('match-handle'); // get handle match element
  const checkbox_nodelist = document.querySelectorAll('#match-checkbox:checked') // get list of checked checkboxes
  const new_status = parseInt(sel.options[sel.selectedIndex].value); // get value of selected match-handling

  // Create a list of report_ids, populate it and POST it to api.py action
  var report_ids = [];
    for (i = 0; i < checkbox_nodelist.length; i++){
        report_ids.push(parseInt(checkbox_nodelist[i].getAttribute('data-report-pk')));
    }
    if (report_ids.length > 0 && !isNaN(new_status)) {
        $.ajax({
          url: "/api",
          method: "POST",
          data: JSON.stringify({
            "action": "set-status-2",
              
            "report_id": report_ids,
            "new_status": new_status
          }),
          contentType: "application/json; charset=utf-8",
          dataType: "json",
          beforeSend: function(xhr, settings) {
            xhr.setRequestHeader("X-CSRFToken", getCookie("csrftoken"))
          }
        }).done(function(body) {
          if (body["status"] == "ok") {
            location.reload(true)
              // Removes the handled match row.
              for (i = 0; i < checkbox_nodelist.length; i++) {
                  checkbox_nodelist[i].closest('tr').remove();
              }
          } else if (body["status"] == "fail") {
            console.log(
                "Attempt to call set-status-1 failed: "
                + body["message"])
          }
        })
      }
})


// Handle match options

var x, i, j, l, ll, selElmnt, a, b, c;

/* look for any elements with the class "handle-match" */
x = document.getElementsByClassName("handle-match");
l = x.length;

for (i = 0; i < l; i++) {
  selElmnt = x[i].getElementsByTagName("select")[0];
  ll = selElmnt.length;

  /* for each element, create a new DIV that will act as the selected item */
  a = document.createElement("DIV");
  a.setAttribute("class", "select-handle");
  a.innerHTML = selElmnt.options[selElmnt.selectedIndex].innerHTML;
  x[i].appendChild(a)

  /* for each element, create a new DIV that will contain the option list */
  b = document.createElement("DIV");
  b.setAttribute("class", "select-handle-items select-handle-hide");
  for (j = 1; j < ll; j++) {
    /* for each option in the original select element,
    create a new DIV that will act as an option item */
    c = document.createElement("DIV");
    c.innerHTML = selElmnt.options[j].innerHTML;

    c.addEventListener("click", function(e) {
        /* when an item is clicked, update the original select box,
        and the selected item */
        var y, i, k, s, h, sl, yl;
        s = this.parentNode.parentNode.getElementsByTagName("select")[0];
        sl = s.length;
        h = this.parentNode.previousSibling;
        for (i = 0; i < sl; i++) {
          if (s.options[i].innerHTML == this.innerHTML) {
            s.selectedIndex = i;
            h.innerHTML = this.innerHTML;
            y = this.parentNode.getElementsByClassName("same-as-selected-handle");
            yl = y.length;
            for (k = 0; k < yl; k++) {
              y[k].removeAttribute("class");
            }
            this.setAttribute("class", "same-as-selected-handle");
            break;
          }
        }
        h.click();
    });
    b.appendChild(c);
  }
  x[i].appendChild(b);

  a.addEventListener("click", function(e) {
      /* when the select box is clicked, close any other select boxes,
      and open/close the current select box */
      e.stopPropagation();
      closeAllSelect(this);
      this.nextSibling.classList.toggle("select-handle-hide");
      this.classList.toggle("select-handle-arrow-active");
    });
}

function closeAllSelect(elmnt) {
  /* a function that will close all select boxes in the document,
  except the current select box */
  var x, y, i, xl, yl, arrNo = [];
  x = document.getElementsByClassName("select-handle-items");
  y = document.getElementsByClassName("select-handle");
  xl = x.length;
  yl = y.length;
  for (i = 0; i < yl; i++) {
    if (elmnt == y[i]) {
      arrNo.push(i)
    } else {
      y[i].classList.remove("select-handle-arrow-active");
    }
  }
  for (i = 0; i < xl; i++) {
    if (arrNo.indexOf(i)) {
      x[i].classList.add("select-handle-hide");
    }
  }
}

/* if the user clicks anywhere outside the select box,
then close all select boxes */
document.addEventListener("click", closeAllSelect);