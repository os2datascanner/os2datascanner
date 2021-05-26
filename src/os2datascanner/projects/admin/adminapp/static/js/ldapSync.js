// check sync
var btnSync = document.querySelector('button[data-sync-for]')

// button - check sync
btnSync.addEventListener('click', ldapSync)

function ldapSync(e) {
    e.preventDefault()

    button = e.target;
    var responseSuccess = button.parentElement.querySelector(
            ".response-icon--success[data-sync-for]");
    var responseError = button.parentElement.querySelector(
            ".response-icon--error[data-sync-for]");
    var text = button.parentElement.querySelector(
            ".response-text[data-sync-for]")

    // Get organization pk value
    var syncUrl = button.value;

    var oReq = new XMLHttpRequest();

    // Get Http request
    oReq.open("GET", syncUrl);

    oReq.onreadystatechange = function () {
        if (oReq.readyState === 4) {
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
        }
    }

    oReq.send();
}
