var x, i, j, l, ll, selElmnt, a, b, c;

/* look for any elements with the class "dropdown" */
x = document.getElementsByClassName("dropdown");
l = x.length;

for (i = 0; i < l; i += 1) {
  selElmnt = x[i].getElementsByTagName("select")[0];
  ll = selElmnt.length;

  /* for each element, create a new DIV that will act as the selected item */
  a = document.createElement("DIV");
  a.setAttribute("class", "select-selected");
  a.innerHTML = selElmnt.options[selElmnt.selectedIndex].innerHTML;
  a.value = selElmnt.options[selElmnt.selectedIndex].value;

  /* change color if value is not equal to the value-to-compare-to */
  if (x[i].getAttribute("data-compareto") && selElmnt.options[selElmnt.selectedIndex].value !== x[i].getAttribute("data-compareto")) {
    a.style.color = '#00496e';
    a.style.fontWeight = 'bold';
  }
  
  x[i].appendChild(a);

  /* for each element, create a new DIV that will contain the option list */
  b = document.createElement("DIV");
  b.setAttribute("class", "select-items select-hide");
  for (j = 0; j < ll; j += 1) {
    /* for each option in the original select element,
    create a new DIV that will act as an option item */
    c = document.createElement("DIV");
    c.innerHTML = selElmnt.options[j].innerHTML;
    c.value = selElmnt.options[j].value;

    /* jshint -W083 */
    c.addEventListener("click", function() {
        /* when an item is clicked, update the original select box,
        and the selected item */
        var y, i, k, s, h, sl, yl;
        s = this.parentNode.parentNode.getElementsByTagName("select")[0];
        sl = s.length;
        h = this.parentNode.previousSibling;
        for (i = 0; i < sl; i += 1) {
          if (s.options[i].innerHTML === this.innerHTML) {
            s.selectedIndex = i;
            h.innerHTML = this.innerHTML;
            y = this.parentNode.getElementsByClassName("same-as-selected");
            yl = y.length;
            for (k = 0; k < yl; k += 1) {
              y[k].removeAttribute("class");
            }
            this.setAttribute("value", this.value);
            this.setAttribute("class", "same-as-selected");
            break;
          }
        }
        h.click();
        
        var dropdown = $(this).closest(".dropdown");
        var form = dropdown.closest("form");
        var autosubmit = dropdown.attr("data-autosubmit");
        if (autosubmit) {
          if (autosubmit === "preserve") {
            // if we need to preserve the other URL params of the page we're on,
            // first get all params from window.location.search (no support for
            // URLSearchParams in IE11 :'-()
            var params = {};
            window.location.search.replace(/[?&]+([^=&]+)=([^&]*)/gi,
              function(_, key, value) {
                params[key] = value;
              }
            );
            
            // since we're changing settings, we don't want to persist the 'page'
            // param, if it exists. Otherwise you'd end up in scenarios where skipping
            // from e.g. page 2 of 'all scans' to 'only scan ID xyz' would still be
            // on page 2. Or changing page size from 10 to 50 while on page 2
            // would still attempt to load page 2 with a page size of 50
            delete params.page;
            
            // now append hidden form fields corresponding to all the params
            // to the parent form we're within
            var hiddenFields = $('');
            for (var param in params) {
              if (params.hasOwnProperty(param)) { // filter out prototype properties
                var existingField = form.find('[name="' + param + '"]');
                if (!existingField.length) {
                  hiddenFields = hiddenFields.add($('<input/>', {
                    type: 'hidden',
                    name: param,
                    value: params[param]
                  }));
                }
              }
            }
            form.append(hiddenFields);
          }
          form.submit();
        }
    });
    /* jshint +W083 */
    b.appendChild(c);
  }
  x[i].appendChild(b);
  /* jshint -W083 */
  a.addEventListener("click", function(e) {
      /* when the select box is clicked, close any other select boxes,
      and open/close the current select box */
      e.stopPropagation();
      closeAllSelect(this);
      this.nextSibling.classList.toggle("select-hide");
      this.classList.toggle("select-arrow-active");
    });
  /* jshint +W083 */
}

function closeAllSelect(elmnt) {
  /* a function that will close all select boxes in the document,
  except the current select box */
  var x, y, i, xl, yl, arrNo = [];
  x = document.getElementsByClassName("select-items");
  y = document.getElementsByClassName("select-selected");
  xl = x.length;
  yl = y.length;
  for (i = 0; i < yl; i += 1) {
    if (elmnt === y[i]) {
      arrNo.push(i);
    } else {
      y[i].classList.remove("select-arrow-active");
    }
  }
  for (i = 0; i < xl; i += 1) {
    if (arrNo.indexOf(i)) {
      x[i].classList.add("select-hide");
    }
  }
}

/* if the user clicks anywhere outside the select box,
then close all select boxes */
document.addEventListener("click", closeAllSelect);
