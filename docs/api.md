# Scan API

This document is a short guide to making use of OS2datascanner services from
external systems.


## The scan server

The `os2datascanner.server` package implements a WSGI-based web server that
lets external systems run OS2datascanner scans. The results that it returns are
equivalent to those sent to the report module by a normal pipeline scan.

> Implementation note: the API server presently *simulates* the pipeline
> internally in order to produce results, but this is not guaranteed to remain
> the case. In future the server might simply become a middleman, passing scan
> specifications to a real pipeline instance and forwarding the results.

The messages expected by the API server are documented using the OpenAPI
specification language. This includes a subset of OS2datascanner's `Rule`s
(including the logical rules) and `Source`s.

> The API server supports *all* of OS2datascanner's `Rule`s and `Source`s, not
> just those present in the OpenAPI documentation. By default, however, only
> the documented `Source`s are enabled. (This can be changed in the API
> server's settings.)

The Docker development environment starts the API server on port 8070 along
with a Swagger UI server on port 8075. The latter can be used to experiment
with the API and to view its documentation.

For safety reasons, the API server requires that scan requests carry a bearer
token. Until a value for this token has been specified in the server's
settings, all scan requests will be rejected.


### Uploading files to scan

To upload a file to the API server, package it in a `"data"` `Source`.  This is
a Base64-encoded representation of the file, accompanied by its media type.
(See the OpenAPI specification file, served by the API server as
`/openapi.yaml`, for more information.)

You can scan multiple files at once by first archiving them in a Zip file or
tarball; OS2datascanner recognises these as explorable containers and will scan
the files that they contain.


### Examples

Start the server `docker-compose --profile api up -d`. For development, the
bearer token is set in `dev-environment/api/dev-settings.toml` as

```toml
[server]
token = "thisIsNotASecret"
```

Then interact with the API endpoints {`openapi.yaml`, `dummy/1`, `scan/1`} or
use the swaggerUI on <http://localhost:8075>.

For example using `httpie`:

```bash
http localhost:8070/openapi.yaml -d
http POST localhost:8070/dummy/1 AUTHORIZATION:'Bearer thisIsNotASecret'
# post a base64 encoded string and use a regex rule
echo '{"rule":{"type":"regex","expression":"[Tt]est"},"source":{"type":"data","content":"VGhpcyBpcyBvbmx5IGEgdGVzdA==","mime":"text/plain"}}' | \
http post localhost:8070/scan/1 AUTHORIZATION:'Bearer thisIsNotASecret'
# scan a domain
echo '{"rule":{"type":"regex","expression":"[Mm]agenta"},"source":{"type":"web","url":"https://www.magenta.dk"}}' | \
http post localhost:8070/scan/1 AUTHORIZATION:'Bearer thisIsNotASecret'
```

The content is `base64` encoded

```bash
# base64 encode
echo -n "This is only a test" | base64 -w 0
> VGhpcyBpcyBvbmx5IGEgdGVzdA==
# decode
echo "VGhpcyBpcyBvbmx5IGEgdGVzdA==" | base64 --decode
> This is only a test
```


#### Use a more complicated regex rule

The API expects valid JSON which is using `"` and not `'`. Also backslash needs
to be escaped, so \"\\\" becomes \"\\\\\". `\b` (regex word-boundary) is
interpreted as a literal backspace and have to be escaped as well.

```bash
echo '{"rule":{"type":"regex", "expression": "\\b(\d{2}(?:\d{2})?[\s]?\d{2}[\s]?\d{2})(?:[\s\-/\.]|\s\-\s)?(\d{4})\\b"},"source":{"type":"data","content":"'$(base64 -w 0 < FILE_TO_ENCODE.txt)'","mime":"text/plain"}}' | \
sed 's/\\/\\\\/g' | \
http post localhost:8070/scan/1 AUTHORIZATION:'Bearer thisIsNotASecret' | \
jq
```


#### Follow the logs

```bash
docker-compose logs --follow api_server
```

## The administration system API

The OS2datascanner administration system also has an API, available at the
`/api/` path. This API grants limited access to the scanners and rules that
have been defined in the administration system.

> For safety, the `Source`s produced by the administration system API are
> *censored* -- they do not contain privileged information such as API keys and
> service account passwords.

Using the administration system API requires that an *API key* UUID be passed
as a bearer token. API key objects must presently be created through the Django
administration interface, and give access only to the objects associated with a
specific `Organization`.

See the OpenAPI specification file, served by the administration system as
`/api/openapi.yaml`, for more information.
