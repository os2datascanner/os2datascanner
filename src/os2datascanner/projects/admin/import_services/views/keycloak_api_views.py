from requests.exceptions import ReadTimeout

from django.http import JsonResponse

from ..keycloak_services import check_ldap_connection
from ..keycloak_services import check_ldap_authentication
from ..keycloak_services import request_access_token


def process_request(request, parameter_keys, kc_call):
    token_response = request_access_token()
    if not token_response.status_code == 200:
        return JsonResponse(
            token_response.json(), status=token_response.status_code)
    token = token_response.json()['access_token']
    parameters = []
    missing_parameters = []
    for key in parameter_keys:
        parameter = request.GET.get(key, None)
        if parameter:
            parameters.append(parameter)
        else:
            missing_parameters.append(key)
    if missing_parameters:
        error = "parameters missing: {keys}".format(keys=missing_parameters)
        return JsonResponse(
            {'errorMessage': error}, status=400
        )
    status = 400
    json_data = {'errorMessage': "LDAP test error"}
    try:
        check_response = kc_call(
            'master', token, *parameters, timeout=0.4)
        if check_response.status_code == 204:
            status = 200
            json_data = {'successMessage': "LDAP test success"}
        else:
            status = check_response.status_code
            json_data = check_response.json()
    except ReadTimeout:
        status = 408
        json_data['errorMessage'] = "Keycloak: no response"
    finally:
        return JsonResponse(json_data, status=status)


def verify_connection(request):
    return process_request(request, ['url'], check_ldap_connection)


def verify_authentication(request):
    return process_request(
        request,
        ['url', 'bind_dn', 'bind_credential'],
        check_ldap_authentication,
    )
