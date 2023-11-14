/* jshint -W098 */ //disable check is used ( called from html )
/* jshint -W083 */
/** disable lintcheck for: 
 * Functions declared within loops referencing an outer scoped 
 * variable may lead to confusing semantics. 
*/

function getSelectorAndSelect(element, index, selector) {
  const sels = selector.querySelectorAll('[data-template-instance="rule_selector"]');
  const sel = sels[sels.length - 1];
  selectOptions(element, sel);
}

function setCheckbox(index, value, selector) {
  if (value) {
    selector.querySelectorAll("input")[index].setAttribute("checked", value);
  } else {
    selector.querySelectorAll("input")[index].removeAttribute("checked");
  }
}

function setTextbox(id, value, selector) {
  if (value) {
    selector.querySelector("#"+id).setAttribute("value", value);
  }
}

function selectOptions(obj, selector) {
  /*jshint camelcase: false */

  // This function recursively builds the array of select elements in the UI
  // based on the content of the JSON field.

  const type = obj.type;
  const selectElem = selector.querySelector(".rule_selector");

  valueMap = {
    "and": "AndRule",
    "or": "OrRule",
    "not": "NotRule",
    "cpr": "CPRRule",
    "regex": "RegexRule",
    "ordered-wordlist": "CustomRule_Health",
    "name": "CustomRule_Name",
    "address": "CustomRule_Address",
    "cpr_turbo": "TurboCPRRule",
    "health_turbo": "TurboHealthRule",
    "email-header": "EmailHeader",
  };

  selectElem.value = valueMap[type];
  const event = new Event("input");
  selectElem.dispatchEvent(event);

  if (["and", "or"].includes(type)) {
    let components = obj.components;
    components.forEach((element, index) => {
      getSelectorAndSelect(element, index, selector);
      if (index < components.length - 1) {
        const inserters = selector.querySelectorAll(".inserter");
        const click = new Event("click");
        inserters[inserters.length - 1].dispatchEvent(click);
      }
    });
  } else if (["not", "email-header"].includes(type)) {
    let rule = obj.rule;
    getSelectorAndSelect(rule, index = 0, selector);
  }

  let inputs = Array.from(selector.querySelectorAll("input, select")).slice(1);
  switch (type) {
    case "cpr":
      setCheckbox(0, obj.modulus_11, selector);
      setCheckbox(1, obj.ignore_irrelevant, selector);
      setCheckbox(2, obj.examine_context, selector);
      setTextbox("exceptions_input", obj.exceptions, selector);
      break;
    case "name":
      setCheckbox(0, obj.expansive, selector);
      break;
    case "cpr_turbo":
      setCheckbox(0, obj.modulus_11, selector);
      setCheckbox(1, obj.examine_context, selector);
      break;
    case "regex":
      inputs[0].value = obj.expression;
      break;
    case "email-header":
      inputs[0].value = obj.property;
      break;
  }

}

function instantiateTemplate(templateName) {
  let instance = document.getElementById(
      templateName ? templateName : "blank").cloneNode(true);
  instance.removeAttribute("id");
  instance.setAttribute("data-template-instance", templateName);
  patchHierarchy(instance);
  return instance;
}


function switchOut(elem, templateName) {
  let template = instantiateTemplate(templateName);
  // Copy the id value, if there is one, from our template target to the new
  // element
  let id = elem.getAttribute("id");
  elem.removeAttribute("id");
  if (id !== null) {
    template.setAttribute("id", id);
  }
  elem.replaceWith(template);
}

function patchHierarchy(h) {
  for (let elem
      of h.getElementsByClassName("rule_selector")) {
    elem.addEventListener(
        "input", _ => switchOut(elem.nextElementSibling, elem.value));
  }

  for (let elem of h.getElementsByClassName("inserter")) {
    elem.addEventListener("click", function(ev) {
      let templateName = elem.getAttribute("data-template-name");
      let target = (
            elem.getAttribute("data-template-insert") || "").split(" ", 2);
      switch (target[0]) {
        case "before-sibling":
          let query = target[1];
          let parent = elem.parentElement;
          let matches = parent.querySelectorAll(query);
          let match = Array.from(matches || []).find(
              el => el.parentElement === parent);
          if (match) {
            match.insertAdjacentElement(
                "beforebegin", instantiateTemplate(templateName));
          }
          break;
        case "before":  /* fall through */
        default:
          elem.insertAdjacentElement(
              "beforebegin", instantiateTemplate(templateName));
      }
    });
  }

  for (let elem of
      h.getElementsByClassName("destroyer")) {
    elem.addEventListener("click", _ => elem.parentNode.remove());
  }

  elements = Array.from(h.getElementsByTagName("*"));
  for (let elem of
      elements.filter(elem => elem.hasAttribute("data-template"))) {
    switchOut(elem, elem.getAttribute("data-template"));
  }
}

document.addEventListener("DOMContentLoaded", _ => patchHierarchy(document));

function makeRule(elem) {
  if (elem === null) {
    return null;
  }

  let type = elem.getAttribute("data-template-instance");
  let children = Array.from(elem.children);
  switch (type) {
    /* Directly convertible rules */
    case "AndRule":
      return {
        "type": "and",
        "components": children.map(makeRule).filter(c => c !== null)
      };
    case "OrRule":
      return {
        "type": "or",
        "components": children.map(makeRule).filter(c => c !== null)
      };
    case "NotRule":
      return {
        "type": "not",
        "rule": makeRule(children[0])
      };
    case "CPRRule":
      tickboxes = elem.querySelectorAll("input[type='checkbox']");
      exceptions = elem.querySelector("#exceptions_input");
      return {
        "type": "cpr",
        "modulus_11": tickboxes[0].checked,
        "ignore_irrelevant": tickboxes[1].checked,
        "examine_context": tickboxes[2].checked,
        "exceptions": exceptions.value
      };
    case "RegexRule":
      return {
        "type": "regex",
        "expression": elem.children[0].value
      };
    case "CustomRule_Health":
      return {
        "type": "ordered-wordlist",
        "dataset": "da_20211018_laegehaandbog_stikord"
      };
    case "CustomRule_Name":
      tickboxes = elem.querySelectorAll("input[type='checkbox']");
      return {
        "type": "name",
        "whitelist": [],
        "blacklist": [],
        "expansive": tickboxes[0].checked,
      };
    case "CustomRule_Address":
      return {
        "type": "address",
        "whitelist": [],
        "blacklist": [],
      };
    case "EmailHeader":
      let inputs = elem.querySelectorAll("input");
      return {
        "type": "email-header",
        "property": inputs[0].value,
        "rule": children.map(makeRule).filter(c => c !== null)[0],
      };

    case "TurboCPRRule":
      tickboxes = elem.querySelectorAll("input[type='checkbox']");
      return {
        "type": "cpr_turbo",
        "modulus_11": tickboxes[0].checked,
        "examine_context": tickboxes[1].checked,
      };
    case "TurboHealthRule":
      return {
        "type": "health_turbo",
        "dataset": "da_20211018_laegehaandbog_stikord"
      };

    /* Glue template fragments to consume */
    case "rule_selector":  /* fall through */
    case "and_fragment":  /* fall through */
    case "or_fragment": /* fall through */

    default:
      for (let child of children) {
        let rv = makeRule(child);
        if (rv) {
          return rv;
        }
      }
      return null;
  }
}

function stringifyRule(elem) {
  return JSON.stringify(makeRule(elem));
}

document.addEventListener("DOMContentLoaded", _ => {
  for (let watcher
      of document.getElementsByClassName("watcher")) {
    let selector = watcher.getAttribute("data-selector"),
        target = document.querySelector(selector),
        functionId = watcher.getAttribute("data-function"),
        functino = window[functionId];
    target.addEventListener("change", _ => {
      watcher.textContent = functino(target);
    });
    const jsonField = JSON.parse(watcher.textContent);
    if (jsonField) {
      selectOptions(jsonField, target);
    }
  }
});
