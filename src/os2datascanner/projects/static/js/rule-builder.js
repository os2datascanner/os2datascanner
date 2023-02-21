/* jshint -W098 */ //disable check is used ( called from html )
/* jshint -W083 */
/** disable lintcheck for: 
 * Functions declared within loops referencing an outer scoped 
 * variable may lead to confusing semantics. 
*/

function selectOptions(obj, selector) {
  // This function has it all! Imbedded switch cases and recursion!
  for (let [key, value] of Object.entries(obj)) {
    const selectElem = selector.querySelector(".rule_selector");
    switch (key) {
      case "type":
        switch (value) {
          case "and":
            selectElem.value = "AndRule";
            break;
          case "or":
            selectElem.value = "OrRule";
            break;
          case "not":
            selectElem.value = "NotRule";
            break;
          case "cpr":
            selectElem.value = "CPRRule";
            break;
          case "regex":
            selectElem.value = "RegexRule";
            break;
          case "ordered-wordlist":
            selectElem.value = "CustomRule_Health";
            break;
          case "name":
            selectElem.value = "CustomRule_Name";
            break;
          case "address":
            selectElem.value = "CustomRule_Address";
            break;
        }
        const event = new Event("input");
        selectElem.dispatchEvent(event);
        break;
      case "components":
        value.forEach((el, index) => {
          const sel = selector.querySelector("span").querySelectorAll("select")[index].parentNode;
          selectOptions(el, sel);
          if (index < value.length - 1) {
            const prepender = selector.querySelector(".prepender");
            const click = new Event("click");
            prepender.dispatchEvent(click);
          }
        });
        break;
      case "expression":
        selector.querySelector("input").value = value;
        break;
      case "expansive":
        selector.querySelector("input").setAttribute("checked", value);
        break;
      case "modulus_11":
        if (value) {
          selector.querySelectorAll("input")[0].setAttribute("checked", value);
        } else {
          selector.querySelectorAll("input")[0].removeAttribute("checked");
        }
        break;
      case "ignore_irrelevant":
        if (value) {
          selector.querySelectorAll("input")[1].setAttribute("checked", value);
        } else {
          selector.querySelectorAll("input")[1].removeAttribute("checked");
        }
        break;
      case "examine_context":
        if (value) {
          selector.querySelectorAll("input")[2].setAttribute("checked", value);
        } else {
          selector.querySelectorAll("input")[2].removeAttribute("checked");
        }
        break;
    }
  }
}

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
    elem.addEventListener("click", function (_) {
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
  if (elem) {
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

    selectOptions(JSON.parse(watcher.textContent), target);
  }
});