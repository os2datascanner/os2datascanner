function noCheckmarksDisableButton() {
  const form = document.getElementById('cleanup-accounts-form');
  const inputs = form.querySelectorAll('input');
  const button = form.querySelector('button');
  let isChecked = false;
  for (let input of inputs) {
    isChecked = input.checked;
    if (isChecked) { break; }
  }
  if (isChecked) {
    button.disabled = false;
  } else {
    button.disabled = true;
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const inputs = document.getElementById('cleanup-accounts-form').querySelectorAll('input');
  inputs.forEach((input) => { input.addEventListener('click', noCheckmarksDisableButton); });
});