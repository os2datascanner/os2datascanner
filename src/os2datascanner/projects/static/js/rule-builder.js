/* jshint -W098 */ //disable check is used ( called from html )
/* jshint -W083 */ 
/** disable lintcheck for: 
 * Functions declared within loops referencing an outer scoped 
 * variable may lead to confusing semantics. 
*/

function instantiateTemplate(templateName) {
  let template = document.getElementById(
      templateName ? templateName : "blank").cloneNode(true);

  template.removeAttribute("id");

  template.setAttribute("data-template-instance", templateName);

  patchHierarchy(template);

  return template;
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

  for (let elem of h.getElementsByClassName("prepender")) {
    elem.addEventListener("click", function(_) {
      let templateName = elem.getAttribute("data-template-name");

      elem.insertAdjacentElement(
          "beforebegin", instantiateTemplate(templateName));
    });
  }

  for (let elem of h.getElementsByClassName("destroyer")) {
    elem.addEventListener("click", _ => elem.parentNode.remove());
  }

  elements = Array.from(h.getElementsByTagName("*"));

  for (let elem of elements.filter(elem => elem.hasAttribute("data-template"))) {
    switchOut(elem, elem.getAttribute("data-template"));
  }
}


document.addEventListener("DOMContentLoaded", _ => patchHierarchy(document));

function makeRule(elem) {
  if(elem){
    let type = elem.getAttribute("data-template-instance");

    let children = Array.from(elem.children).filter(
        e => e.hasAttribute("data-template-instance"));

    switch (type) {

      /* Directly convertible rules */
      case "AndRule":
        return {
          "type": "and",
          "components": children.map(makeRule)
        };

      case "OrRule":
        return {
          "type": "or",
          "components": children.map(makeRule)
        };

      case "NotRule":
        return {
          "type": "not",
          "rule": makeRule(children[0])
        };

      case "CPRRule":
        tickboxes = elem.querySelectorAll("input[type='checkbox']");

        return {
          "type": "cpr",
          "modulus_11": tickboxes[0].checked,
          "ignore_irrelevant": tickboxes[1].checked,
          "examine_context": tickboxes[2].checked,
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
        return {
          "type": "name",
          "whitelist": [],
          "blacklist": []
        };

      case "CustomRule_Address":
        return {
          "type": "address",
          "whitelist": [],
          "blacklist": []
        };

      /* Glue template fragments to consume */

      case "rule_selector":  /* fall through */

      case "and_fragment":  /* fall through */

      case "or_fragment":
        return makeRule(children[0]);

      default:
        return null;
    }
  }
}

function stringifyRule(elem) {
  return JSON.stringify(makeRule(elem));
}

document.addEventListener("DOMContentLoaded", _ => {
  for (let watcher of document.getElementsByClassName("watcher")) {

    let selector = watcher.getAttribute("data-selector"),
    target = document.querySelector(selector),
    functionId = watcher.getAttribute("data-function"),
    functionEvent = window[functionId];

    target.addEventListener("change", _ => {
      watcher.textContent = functionEvent(target);
    });
  }
});