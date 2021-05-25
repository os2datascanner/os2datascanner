// test connection and authentication

var btnConnection = document.querySelector('#button-connection')
var btnAuth = document.querySelector('#button-auth')
var textConnection = document.querySelector('#responseConnection')
var textAuth = document.querySelector('#responseAuth')
var responseSuccessCon = document.querySelector('#responseSuccessCon')
var responseErrorCon = document.querySelector('#responseErrorCon')
var responseSuccessAuth = document.querySelector('#responseSuccessAuth')
var responseErrorAuth = document.querySelector('#responseErrorAuth')

// button - test connection
btnConnection.addEventListener('click', testConnection)

function testConnection(e) {
    e.preventDefault()

    // Get values from connection protocol and connection url
    var connection_protocol = document.getElementById("id_connection_protocol").value;
    var connection_url = document.getElementById("id_connection_url").value;

    var oReq = new XMLHttpRequest();

    // Get Http request with params
    oReq.open("GET", urlConnection + "?url=" + connection_protocol + connection_url);

    oReq.onreadystatechange = function () {
        if (oReq.readyState === 4) {
            // if connection succeeded
            if (oReq.status === 200) {
                responseSuccessCon.style.display = "block"
                responseErrorCon.style.display = "none"
                textConnection.innerText = gettext('Connection succeeded')
            } else {
            // else connection failed
                responseErrorCon.style.display = "block"
                responseSuccessCon.style.display = "none"
                textConnection.innerText = gettext('Connection failed')
            }
        }
    }
    
    oReq.send();
}


// button - test auth
btnAuth.addEventListener('click', testAuth)

function testAuth(e) {
    e.preventDefault()

    // Get values from connection protocol, connection url, bind_dn and credential
    var connection_protocol = document.getElementById("id_connection_protocol").value;
    var connection_url = document.getElementById("id_connection_url").value;
    var bind_dn = document.getElementById("id_bind_dn").value;
    var credential = document.getElementById("id_ldap_password").value;

    var oReq = new XMLHttpRequest();

    // Get Http request with params
    oReq.open("GET", urlAuth + "?url=" + connection_protocol + connection_url + "&bind_dn=" + bind_dn  + "&bind_credential=" + credential);

    oReq.onreadystatechange = function () {
        if (oReq.readyState === 4) {
            if (oReq.status === 200) {
                // if connection succeeded
                responseSuccessAuth.style.display = "block"
                responseErrorAuth.style.display = "none"
                textAuth.innerText = gettext('Authentication succeeded')
            } else {
                // else connection failed
                responseErrorAuth.style.display = "block"
                responseSuccessAuth.style.display = "none"
                textAuth.innerText = gettext('Authentication failed')
            }
        }
    }
    
    oReq.send();
}