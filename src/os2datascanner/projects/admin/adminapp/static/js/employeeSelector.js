(function($) {
  // initialize tooltips
  $("[data-toggle=\"tooltip\"]").tooltip();

  // listen to tooltip events dynamically in order to calculate proper tooltip size
  $("body").on("inserted.bs.tooltip", "#available_employees li a, #selected_employees > .selected_employee span", function() {
    var elm = $(this);
    var tooltipElm = elm.next(".tooltip");
    var textLength = elm.attr("title").length || elm.attr("data-original-title").length;
    var boxWidth = Math.min(textLength, 30); // whatever is smallest of text length and 30 characters
    tooltipElm.css({
      width: "calc(" + boxWidth + "ch + 5px)"
    });
  });

  // adding a employee to the list of selected employees
  $("#available_employees").on("click", "> li[data-employee-id]:not([data-disabled])", function() {
    var $this = $(this);
    var employeeId = $this.attr("data-employee-id");
    var employeeAnchor = $this.find("a");
    $("#employees_list").before($("<div/>", {
      class: "selected_employee employee employee--selected",
      "data-employee-id": employeeId,
      html: $("<a/>", {
        text: "",
        class: "remove-employee-button",
        href: "#",
        "title": "Fjern denne medarbejder"
      }).add($("<span/>", {
        text: employeeAnchor.text(),
        title: employeeAnchor.attr("title") || employeeAnchor.attr("data-original-title")
      }))
    }));

    $("#selected_employees [data-employee-id=\"" + employeeId + "\"] [data-toggle=\"tooltip\"]").tooltip(); // enable tooltipping on new element
    $this.attr("data-disabled", ""); // set the data-disabled attribute, so we can't add the item again.
    employeeAnchor.tooltip("destroy"); // disable tooltip

    // onclick show warning message
    $("#available_employees li[data-employee-id]:not([data-disabled])").on("click", function() {
      $("#changed_employees").show(); // show warning
      $("#messageColorId").addClass("has-warning");
    })

    $this.closest("form").append($("<input/>", { // add a hidden input field to the form
      type: "hidden",
      name: "employees",
      value: employeeId
    }));
  });

  // removing a employee from the list of selected employees
  $("#selected_employees").on("click", ".remove-employee-button:not(.disabled)", function() {
    var elm = $(this).closest("div"); // we want the actual parent div, not the a itself
    var employeeId = elm.attr("data-employee-id");
    var employeeLi = $("#available_employees").find("li[data-employee-id=\"" + employeeId + "\"]");
    var employeeAnchor = employeeLi.find("a");
    employeeLi.removeAttr("data-disabled");
    employeeAnchor.tooltip(); // re-enable tooltip

    $("#changed_rules").show(); // show warning
    $("#messageColorId").addClass("has-warning"); // add css class

    $(this).closest("form").find("input[type=\"hidden\"][name=\"employees\"][value=\"" + employeeId + "\"]").remove(); // remove the hidden input field corresponding to the employee we removed
    elm.remove();

    return false;
  });

  // filter the list of employees when search field changes value
  $("#employee-filter").on("textInput input", os2debounce(function() {
    var value = $(this).val().trim();
    if(value.length < 2) {
      $("#available_employees li").show(); // reset all li to shown
      return; // return early!
    }
    var needle = new RegExp(value, "gi");
    $("#available_employees .employee").each(function() {
      var haystack = $(this);
      if(!haystack.text().match(needle)) {
        haystack.hide();
      } else {
        haystack.show();
      }
    });
    // we also need to hide headings and separators if an entire section becomes invisible.
    $("#available_employees .dropdown-header").each(function() {
      var header = $(this);
      var nextEmployees = header.nextUntil(".dropdown-header", ".employee"); // check to see if we're in a section of the list that actually contains employees (i.e. not filter box at the top)
      if(nextEmployees.length > 0) {
        var isEmpty = true;
        nextEmployees.each(function() {
          if($(this).is(":visible")) {
            isEmpty = false;
            return;
          }
        });
        if(isEmpty) {
          header.hide();
        } else {
          header.show();
        }
      }
    });
  }, 150));

})(jQuery);
