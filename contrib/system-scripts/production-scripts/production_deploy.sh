#!/usr/bin/env bash

set -e

# Generel settings
prod_dir=/srv/datascanner
domain=danni.dk

# Admin defaults
webscan=False
filescan=True
exchangescan=True

# Report defaults
saml2_auth=False

repo_dir="`dirname "$BASH_SOURCE[0]"`/../../../"

# Load common lib
source "$repo_dir/contrib/system-scripts/production-scripts/common.sh"

echo -e '\n************* Copy *************\n'
# Copy to prod dir
copy_to_prod_dir "$prod_dir"

echo -e '\n************* Installation *************\n'
# Install system dependencies and python-env
source "$prod_dir/install.sh"

echo -e '\n************* Admin module *************\n'
# Setup administrations module
source "$prod_dir/contrib/system-scripts/production-scripts/admin_deploy.sh" "$domain" "$webscan" "$filescan" "$exchangescan" "$prod_dir"

echo -e '\n************* Report module *************\n'
# Setup report module
source "$prod_dir/contrib/system-scripts/production-scripts/report_deploy.sh" "$domain-report.dk" "$saml2_auth" "$prod_dir"

echo -e '\n************* Engine2 setup *************\n'
# Setup engine2 services
source "$prod_dir/contrib/system-scripts/production-scripts/engine_deploy.sh" "$prod_dir"

echo -e '\n************* Success *************\n'

echo -e '\n************* Simple Verification *************\n'

echo -e "$prod_dir"
ls -l "$prod_dir"

echo -e "\n"$prod_dir"/contrib/systemd/"
ls -l "$prod_dir/contrib/systemd/"

echo -e "\n$prod_dir/src/os2datascanner/projects/admin/"
ls -l "$prod_dir/src/os2datascanner/projects/admin/"

echo -e "\n$prod_dir/src/os2datascanner/projects/report/"
ls -l "$prod_dir/src/os2datascanner/projects/report/"

echo -e "\n/etc/systemd/system/os2ds-*"
ls -l /etc/systemd/system/os2ds-*

echo -e "\n/etc/apache2/certs/datascanner"
ls -l /etc/apache2/certs/datascanner
