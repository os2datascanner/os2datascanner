// Jump to specific page
var formButton = document.querySelector("#form-button");
if (formButton) {
  document.querySelector("#form-button").addEventListener("click", function(e) {
    e.preventDefault();
    var page_number = document.querySelector('input[type="number"]').value;

    if ('URLSearchParams' in window) {
        var searchParams = new URLSearchParams(window.location.search);
        searchParams.set("page", page_number);
        window.location.search = searchParams.toString();
    }
  });
}
