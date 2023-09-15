function enableDPOOptions() {
  const contactStyle = document.getElementById('id_dpo_contact_style');
  if (contactStyle.value !== 'NO' && contactStyle.value !== 'UD') {
    [
      'id_dpo_name',
      'id_dpo_value'
    ].forEach(id => {
      const field = document.getElementById(id);
      field.disabled = false;
    });
  }
}

function disableDPOOptions() {
  [
    'id_dpo_name',
    'id_dpo_value'
  ].forEach(id => {
    const field = document.getElementById(id);
    field.disabled = true;
  });
}

function enableSupportOptions() {
  const contactStyle = document.getElementById('id_support_contact_style');
  if (contactStyle.value !== 'NO') {
    [
      'id_support_name',
      'id_support_value'
    ].forEach(id => {
      const field = document.getElementById(id);
      field.disabled = false;
    });
  }
}

function disableSupportOptions() {
  [
    'id_support_name',
    'id_support_value'
  ].forEach(id => {
    const field = document.getElementById(id);
    field.disabled = true;
  });
}

function hideSupportOption() {
  [
    'id_support_contact_style',
    'id_support_name',
    'id_support_value',
    'id_dpo_contact_style',
    'id_dpo_name',
    'id_dpo_value'
  ].forEach(id => {
    const field = document.getElementById(id);
    field.disabled = true;
  });
}

function showSupportOption() {
  [
    'id_support_contact_style',
    'id_dpo_contact_style',
  ].forEach(id => {
    const field = document.getElementById(id);
    field.disabled = false;
  });
  enableDPOOptions();
  enableSupportOptions();
}

function supportOptionChange(checkmark) {
  if (checkmark.checked) {
    showSupportOption();
  } else {
    hideSupportOption();
  }
}

function DPOOptionChange(input) {
  if (input.value === 'NO' || input.value === 'UD') {
    disableDPOOptions();
  } else {
    enableDPOOptions();
  }
}

function SupportOptionChange(input) {
  if (input.value === 'NO') {
    disableSupportOptions();
  } else {
    enableSupportOptions();
  }
}

document.addEventListener('DOMContentLoaded', () => {
  const showSupportButtonCheck = document.getElementById('id_show_support_button');
  supportOptionChange(showSupportButtonCheck);
  showSupportButtonCheck.addEventListener('change', () => {
    supportOptionChange(showSupportButtonCheck);
  });

  const DPOStyleInput = document.getElementById('id_dpo_contact_style');
  DPOOptionChange(DPOStyleInput);
  DPOStyleInput.addEventListener('change', () => {
    DPOOptionChange(DPOStyleInput);
  });

  const SupportStyleInput = document.getElementById('id_support_contact_style');
  SupportOptionChange(SupportStyleInput);
  SupportStyleInput.addEventListener('change', () => {
    SupportOptionChange(SupportStyleInput);
  });
});