// jshint unused:false

/*
  This function registers a handler for the rule selector component,
  that updates the value of a hidden input upon changing the selected
  rule in a form.

  Params:
  
  `selectorId`: id attribute of the rule selector <select> form.
  `changed_id`: id attribute of the rule selector changed warning message.

 */
function registerRuleSelectorHandler(selectorId, changedId, isEdit) {
      let selectorElement = document.getElementById(`${selectorId}_id`);
      let ruleInput = document.getElementById(`${selectorId}_input`);

      const selectorValue = selectorElement.value;
      ruleInput.value = selectorValue;

      selectorElement.addEventListener("change", (event) => {
          if (isEdit) {
              let messageColorId = document.querySelector(`#${changedId}_message_color`);
              let changedTag = document.querySelector(`#${changedId}`);

              if (selectorValue !== event.target.value) {
                  changedTag.style.display = 'inline';
                  messageColorId.classList.add("has-warning");
              } else {
                  changedTag.style.display = '';
                  messageColorId.classList.remove("has-warning");
              }
          }

          ruleInput.value = event.target.value;
      });
  }
