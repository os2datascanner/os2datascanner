$('#cleanup-accounts-modal').on($.modal.CLOSE, function () {
  let wrapp = document.querySelector('.datatable-wrapper');
  wrapp.dispatchEvent(new Event('modal-closed'));
});