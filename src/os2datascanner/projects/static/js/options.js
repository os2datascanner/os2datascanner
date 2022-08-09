function setDropdownEvent() {
  Array.prototype.forEach.call(document.querySelectorAll('.dropdown > select'), function (dropdown) {
    dropdown.addEventListener('change', function (e) {
      if (e.target.hasAttribute('data-autosubmit')) {
        var form = e.target.form;
        if (form) {
          form.submit();
        }
      }
    });
  });
}

function clearFilter(elementid) { // jshint ignore:line
  var element = document.querySelector('#' + elementid + ' [value="all"]').selected = true;
  document.getElementById("filter_form", element).submit();
}
function checkedBox() {
  var checkbox = document.getElementById('30-days-toggle');
  var thirtyDays = document.getElementById('30-days');
  if (checkbox.checked) {
    thirtyDays.value = 'true';
  } else {
    thirtyDays.value = 'false';
  }
  document.getElementById("filter_form").submit();
}
function setCheckEvent() { // jshint ignore:line
  document.getElementById('30-days-toggle').addEventListener('click', checkedBox);
}

document.addEventListener('DOMContentLoaded', function () {
  setDropdownEvent();
});
