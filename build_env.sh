#!/bin/sh
# Export git info as env vars to be passed on to docker build args
OS2DS_COMMIT_SHA="$(git rev-parse HEAD)"
OS2DS_COMMIT_TAG="$(git describe --tags)"
OS2DS_CURRENT_BRANCH="$(git rev-parse --abbrev-ref HEAD)"

export OS2DS_COMMIT_SHA
export OS2DS_COMMIT_TAG
export OS2DS_CURRENT_BRANCH
