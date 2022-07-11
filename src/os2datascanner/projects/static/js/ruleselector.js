(function (os2web, $) {
  // initialize tooltips
  $("[data-toggle=\"tooltip\"]").tooltip();

  // listen to tooltip events dynamically in order to calculate proper tooltip size
  $("body").on("inserted.bs.tooltip", ".select-rules__available li a, .select-rules__selected > .selected_rule span", function () {
    var elm = $(this);
    var tooltipElm = elm.next(".tooltip");
    var textLength = elm.attr("title").length || elm.attr("data-original-title").length;
    var boxWidth = Math.min(textLength, 30); // whatever is smallest of text length and 30 characters
    tooltipElm.css({
      width: "calc(" + boxWidth + "ch + 5px)"
    });
  });

  // adding a rule to the list of selected rules
  $(".select-rules__available").on("click", "> li[data-rule-id]:not([data-disabled])", function () {
    var $this = $(this);
    console.log($this.attr("data-rule-id"));
    var ruleId = $this.attr("data-rule-id");
    var ruleAnchor = $this.find("a");
    if ($this.attr("class").includes("inclusion")) {
      $("#rules_list").before($("<div/>", {
        class: "selected_rule inclusion rule rule--selected",
        "data-rule-id": ruleId,
        html: $("<a/>", {
          text: "",
          class: "remove-rule-button",
          href: "#",
          "title": "Fjern denne regel"
        }).add($("<span/>", {
          text: ruleAnchor.text(),
          title: ruleAnchor.attr("title") || ruleAnchor.attr("data-original-title")
        }))
      }));


      $("#selected_rules [data-rule-id=\"" + ruleId + "\"] [data-toggle=\"tooltip\"]").tooltip(); // enable tooltipping on new element
      $this.attr("data-disabled", ""); // set the data-disabled attribute, so we can't add the item again.
      ruleAnchor.tooltip("destroy"); // disable tooltip

      // onclick show warning message
      $("#available_rules li[data-rule-id]:not([data-disabled])").on("click", function () {
        $("#changed_rules").show(); // show warning
        $("#messageColorId").addClass("has-warning");
      });

      $this.closest("form").append($("<input/>", { // add a hidden input field to the form
        type: "hidden",
        name: "rules",
        value: ruleId
      }));
    } else if ($this.attr("class").includes("exclusion")) {
      $("#exclusion_rules_list").before($("<div/>", {
        class: "selected_rule exclusion rule rule--selected",
        "data-rule-id": ruleId,
        html: $("<a/>", {
          text: "",
          class: "remove-rule-button",
          href: "#",
          "title": "Fjern denne regel"
        }).add($("<span/>", {
          text: ruleAnchor.text(),
          title: ruleAnchor.attr("title") || ruleAnchor.attr("data-original-title")
        }))
      }));

      $("#selected_exclusion_rules [data-rule-id=\"" + ruleId + "\"] [data-toggle=\"tooltip\"]").tooltip(); // enable tooltipping on new element
      $this.attr("data-disabled", ""); // set the data-disabled attribute, so we can't add the item again.
      ruleAnchor.tooltip("destroy"); // disable tooltip

      // onclick show warning message
      $("#available_exclusion_rules li[data-rule-id]:not([data-disabled])").on("click", function () {
        $("#changed_exclusion_rules").show(); // show warning
        $("#messageColorId_exclusion").addClass("has-warning");
      });

      $this.closest("form").append($("<input/>", { // add a hidden input field to the form
        type: "hidden",
        name: "exclusion_rules",
        value: ruleId
      }));
    }
  });

  // removing a rule from the list of selected rules
  $(".select-rules__selected").on("click", ".remove-rule-button:not(.disabled)", function () {
    var elm = $(this).closest("div"); // we want the actual parent div, not the a itself
    var ruleId = elm.attr("data-rule-id");
    var ruleLi = null;
    if (elm.attr("class").includes("inclusion")) {
      ruleLi = $("#available_rules").find("li[data-rule-id=\"" + ruleId + "\"]");

      $("#changed_rules").show(); // show warning
      $("#messageColorId").addClass("has-warning"); // add css class

      $(this).closest("form").find("input[type=\"hidden\"][name=\"rules\"][value=\"" + ruleId + "\"]").remove(); // remove the hidden input field corresponding to the rule we removed
      elm.remove();
    } else if (elm.attr("class").includes("exclusion")) {
      ruleLi = $("#available_exclusion_rules").find("li[data-rule-id=\"" + ruleId + "\"]");

      $("#changed_exclusion_rules").show(); // show warning
      $("#messageColorId_exclusion").addClass("has-warning"); // add css class

      $(this).closest("form").find("input[type=\"hidden\"][name=\"exclusion_rules\"][value=\"" + ruleId + "\"]").remove(); // remove the hidden input field corresponding to the rule we removed
      elm.remove();
    }

    var ruleAnchor = ruleLi.find("a");
    ruleLi.removeAttr("data-disabled");
    ruleAnchor.tooltip(); // re-enable tooltip

    return false;
  });

})(os2web, jQuery);
