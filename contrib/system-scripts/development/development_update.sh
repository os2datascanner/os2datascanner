#!/usr/bin/env bash

# This script is intented to be executed everytime you do git pull on the development branch.
set -e

repo_dir="`dirname "$BASH_SOURCE[0]"`/../../../"

source "$repo_dir/install.sh"

source "$repo_dir/contrib/system-scripts/utils/common.sh"

perform_django_migrations 'admin' "$repo_dir"
perform_django_migrations 'report' "$repo_dir"

# TODO: Add webpack build.