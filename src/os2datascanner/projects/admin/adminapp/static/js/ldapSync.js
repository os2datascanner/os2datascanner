// check sync
// Disabled until websockets arrive or we introduce polling.
// var btnSync = document.querySelectorAll('button[data-sync-for]')
//
// for (let i = 0; i < btnSync.length; i++)
//     btnSync[i].addEventListener('click', ldapSync)

function ldapSync(e) {
    e.preventDefault()

    var button = e.target;
    button.disabled = true;

    var responseWaiting = button.parentElement.querySelector(
            ".response-icon--waiting[data-sync-for]");
    var responseSuccess = button.parentElement.querySelector(
            ".response-icon--success[data-sync-for]");
    var responseError = button.parentElement.querySelector(
            ".response-icon--error[data-sync-for]");
    var text = button.parentElement.querySelector(
            ".response-text[data-sync-for]")

    responseWaiting.style.display = "block"
    responseSuccess.style.display = "none"
    responseError.style.display = "none"
    text.innerText = gettext('Pending...')

    // Get organization pk value
    var syncUrl = button.value;

    var oReq = new XMLHttpRequest();

    // Get Http request
    oReq.open("GET", syncUrl);

    oReq.onreadystatechange = function () {
        if (oReq.readyState === 4) {
            responseWaiting.style.display = "none"
            if (oReq.status === 200) {
                // if sync succeeded
                responseSuccess.style.display = "block"
                responseError.style.display = "none"
                text.innerText = gettext('Synchronization succeeded')
            } else {
                // else sync failed
                responseError.style.display = "block"
                responseSuccess.style.display = "none"
                text.innerText = gettext('Synchronization failed')
            }
            button.enabled = true;
        }
    }

    oReq.send();
}
