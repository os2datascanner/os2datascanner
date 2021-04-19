// Get more result options
var x, i, j, l, ll, selElmnt, a, b, c;

/* look for any elements with the class "get-results" */
x = document.getElementsByClassName("get-results");
l = x.length;

for (i = 0; i < l; i++) {
  selElmnt = x[i].getElementsByTagName("select")[0];
  ll = selElmnt.length;

  /* for each element, create a new DIV that will act as the selected item */
  a = document.createElement("DIV");
  a.setAttribute("class", "select-page");
  a.innerHTML = selElmnt.options[selElmnt.selectedIndex].innerHTML;
  x[i].appendChild(a)

  /* for each element, create a new DIV that will contain the option list */
  b = document.createElement("DIV");
  b.setAttribute("class", "select-page-items select-page-hide");
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
            y = this.parentNode.getElementsByClassName("same-as-selected-page");
            yl = y.length;
            for (k = 0; k < yl; k++) {
              y[k].removeAttribute("class");
            }
            this.setAttribute("class", "same-as-selected-page");
            break;
          }
        }
        h.click();
        
        // add parameter 'paginate_by' to url
        function addParameterToURL(){
          if ('URLSearchParams' in window) {
            var searchParams = new URLSearchParams(window.location.search);
            searchParams.set("paginate_by", s.value);
            window.location.search = searchParams.toString();
          }
        }
        addParameterToURL();
    });
    b.appendChild(c);
  }
  x[i].appendChild(b);

  a.addEventListener("click", function(e) {
      /* when the select box is clicked, close any other select boxes,
      and open/close the current select box */
      e.stopPropagation();
      closeAllSelect(this);
      this.nextSibling.classList.toggle("select-page-hide");
      this.classList.toggle("select-page-arrow-active");
    });
}

function closeAllSelect(elmnt) {
  /* a function that will close all select boxes in the document,
  except the current select box */
  var x, y, i, xl, yl, arrNo = [];
  x = document.getElementsByClassName("select-page-items");
  y = document.getElementsByClassName("select-page");
  xl = x.length;
  yl = y.length;
  for (i = 0; i < yl; i++) {
    if (elmnt == y[i]) {
      arrNo.push(i)
    } else {
      y[i].classList.remove("select-page-arrow-active");
    }
  }
  for (i = 0; i < xl; i++) {
    if (arrNo.indexOf(i)) {
      x[i].classList.add("select-page-hide");
    }
  }
}

/* if the user clicks anywhere outside the select box,
then close all select boxes */
document.addEventListener("click", closeAllSelect);