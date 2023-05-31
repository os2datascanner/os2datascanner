// jshint unused:false
function sortByErrorMessage() {
    // Loads the values from the clicked caret into hidden buttons
    // and triggers a change event programmatically on the sort by form.
    const sortValue = document.getElementById("error-caret").value;
    document.getElementById("order_by").value = "error_message";
    document.getElementById("order").value = sortValue;

    document.getElementById("errorlog_filters").dispatchEvent(new Event("change"));
}

function sortByPath() {
    // Loads the values from the clicked caret into hidden buttons
    // and triggers a change event programmatically on the sort by form.
    const sortValue = document.getElementById("path-caret").value;
    document.getElementById("order_by").value = "path";
    document.getElementById("order").value = sortValue;

    document.getElementById("errorlog_filters").dispatchEvent(new Event("change"));
}

function sortByScanStatus() {
    // Loads the values from the clicked caret into hidden buttons
    // and triggers a change event programmatically on the sort by form.
    const sortValue = document.getElementById("scan-caret").value;
    document.getElementById("order_by").value = "scan_status";
    document.getElementById("order").value = sortValue;

    document.getElementById("errorlog_filters").dispatchEvent(new Event("change"));
}
