# A11y Scanner service

WIP. A Node.js application that manages a cluster of Puppeteer instances
and performs a11y analysis on incoming URLs.

## TODO

- [ ] Integrate other a11y engines
- [ ] Find a way to generate EARL reports ([perhaps not easily doable?](https://github.com/dequelabs/axe-core-npm/issues/88#issuecomment-811232521))
- [ ] Integrate in OS2DS!
- [ ] Tracing/metrics/etc.

## Running the service

Start the container with `docker-compose up -d [--build] a11y_scanner`.

## Usage

Use the service by querying the `/axe` endpoint with a basic auth header
and a POST payload structured as follows:

```json
{
    "url": "https://www.example.com/path"
}
```

See the [smoke test section](#smoke-testing) for a way to quickly check
that the service is functioning as expected.

## Configuration

All configuration is provided via envvars in accordance with
[12factor principles](https://12factor.net/config). Sane defaults are
provided where applicable.

See `./src/settings.js` for a complete list of settings.

## API spec

The service currently returns the following responses:

- 401 on bad/missing credentials
- 400 on missing url in post body
- 404 on requests to non-existing endpoints
- 200 for everything else

A 200 OK does not mean all is well, simply that the application
successfully parsed and processed the request. The response will look
like one of the following:

```json
{
  "error": "<error message>"
}
```

```json
{
  "data": {
    "testEngine": {
      "name": "axe-core",
      "version": "4.1.3"
    },
    "testRunner": {
      "name": "axe"
    },
    "testEnvironment": {
      "userAgent": "<User agent string>",
      "windowWidth": 800,
      "windowHeight": 600,
      "orientationAngle": 0,
      "orientationType": "portrait-primary"
    },
    "timestamp": "2021-03-31T13:23:53.501Z",
    "url": "<The url which was checked>",
    "toolOptions": {
      "reporter": "v1"
    },
    "violations": [],
    "passes": [],
    "incomplete": [],
    "inapplicable": []
  }
}
```

## Testing

### Smoke testing

The following `curl` one-liner will request an a11y scan on
https://www.magenta.dk and print the resulting Axe report to STDOUT.

```bash
curl --user 'test:testpassword' \
    -H "Content-Type: application/json" \
    --data-binary @tests/request_bodies/magenta.json \
    http://localhost:8888/axe
```

### Load testing

- Make sure the service is running
- Install [vegeta](https://github.com/tsenart/vegeta)
- Run the following command:

```bash
echo 'POST http://test:testpassword@localhost:8888/axe' |\
vegeta attack -header "Content-Type: application/json" -body tests/request_bodies/magenta.json \
-rate=20 -timeout=100s -duration=3s | tee results.bin | vegeta report
```

Tweak the `-rate` and `-duration` as needed and pick the request body
file you want. 

## Security

The service is based on Puppeteer which in turn is a wrapper around a
(headless) Chrome. By default, Chrome/Chromium uses kernel-like
sandboxing to prevent security vulnerabilities. This is a good thing!
However, Chrome needs escalated privileges in order to set up sandboxing
in addition to the [default privileges](https://github.com/moby/moby/blob/master/profiles/seccomp/default.json)
provided by Docker.

There are several workarounds for this: running the process
with root privileges, disabling the sandbox feature and providing more
granulated privileges via a seccomp profile. We make use of the latter
two options:

- Sandboxing can be disabled in CI where we have full control of the URLs
  that are crawled
- A [seccomp profile](https://github.com/Zenika/alpine-chrome/blob/master/chrome.json)
  is used locally and in production cf.
  [3 ways to securely use Chrome headless](https://github.com/Zenika/alpine-chrome#-the-best-with-seccomp).

The seccomp profile is located in `./chrome_seccomp.json`.
