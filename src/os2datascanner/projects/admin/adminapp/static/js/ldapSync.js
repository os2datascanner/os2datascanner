// check sync
var btnSync = document.querySelector('#button-sync')
var text = document.querySelector('#response')
var responseSuccess = document.querySelector('#responseSuccess')
var responseError = document.querySelector('#responseError')

// button - check sync
btnSync.addEventListener('click', ldapSync)

function ldapSync(e) {
    e.preventDefault()

    // Get organization pk value
    var syncUrl = document.getElementById("button-sync").value;

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