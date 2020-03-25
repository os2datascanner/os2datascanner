#!/usr/bin/env bash

set -e

# Generel settings
prod_dir=%PRODUCTION_DIR%
domain=%DOMAIN%

# Admin defaults
webscan=False
filescan=True
exchangescan=True

# Report defaults
saml2_auth=False

repo_dir="`dirname "$BASH_SOURCE[0]"`/../../../"

echo "$repo_dir"
# Load common lib
source "$repo_dir/contrib/system-scripts/utils/common.sh"

echo -e '\n************* Copy *************\n'
# Copy to prod dir
copy_to_prod_dir "$prod_dir"

echo -e '\n************* Installation *************\n'
# Install system dependencies and python-env
source "$prod_dir/install.sh"

echo -e '\n************* Admin module *************\n'
# Setup administrations module
source "$prod_dir/contrib/system-scripts/utils/admin_setup.sh" "$domain" "$webscan" "$filescan" "$exchangescan" "$prod_dir" False

collectstatic_and_makemessages 'admin' $prod_dir

# Configure apache for the administrations module
apache_setup $prod_dir $domain 'admin'

echo -e '\n************* Report module *************\n'
# Setup report module
source "$prod_dir/contrib/system-scripts/utils/report_setup.sh" "$domain-report.dk" "$saml2_auth" "$prod_dir" False

collectstatic_and_makemessages 'report' "$prod_dir"

# Configure apache for the administrations module
apache_setup "$prod_dir" "$domain-report.dk" 'report'

# deploy pipeline_collector
systemd_dir="$prod_dir/contrib/systemd"
systemd_template="$systemd_dir/os2ds-template@.service"

name='pipeline_collector'

service_name="os2ds-$name@.service"
cp "$systemd_template" "$systemd_dir/$service_name"
new_service="$systemd_dir/$service_name"

command="$prod_dir/bin/manage-report pipeline_collector"
short_name="$(echo $name | cut -c1-4)"

sed -i "s#COMMAND_LINE#$command#g" "$new_service"
sed -i "s/SERVICE_NAME/$name/g" "$new_service"
sed -i "s/SERVICE_SHORTNAME/$short_name/g" "$new_service"

ln -sf "$new_service" "/etc/systemd/system/"

systemctl daemon-reload

echo -e '\n************* Engine2 setup *************\n'
# Setup engine2 services
source "$prod_dir/contrib/system-scripts/production/engine_deploy.sh" "$prod_dir"

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
