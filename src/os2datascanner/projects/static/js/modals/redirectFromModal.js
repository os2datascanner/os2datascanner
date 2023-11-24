/* jshint -W098 */ //disable check is used ( called from html )
//Ask parent window outside iframe to redirect user and close modal
function redirectFromModal(filepath) {
  window.parent.location.href = filepath;
  window.parent.$.modal.close();
}