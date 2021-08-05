#!/bin/bash

ROOT_DIR_FALLBACK=$(git rev-parse --show-toplevel)
ROOT_DIR=${CI_PROJECT_DIR:-$ROOT_DIR_FALLBACK}

A11Y_DIR="${ROOT_DIR}/services/a11y-scanner"
A11Y_PORT=8888

# Load credentials
# shellcheck disable=SC1091
source "${ROOT_DIR}/dev-environment/a11y-scanner/a11y-scanner.env"

curl --user "$A11Y_SCANNER_USERNAME:$A11Y_SCANNER_PASSWORD" \
	-H "Content-Type: application/json" \
	--data-binary "@${A11Y_DIR}/tests/request_bodies/magenta.json" \
	http://localhost:${A11Y_PORT}/qualweb
