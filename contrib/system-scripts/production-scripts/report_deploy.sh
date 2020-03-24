#!/usr/bin/env bash

set -e

if [ $# -lt 2 ]
then
    echo "usage: report_deploy.sh [DOMAIN] [ENABLE_SAML2] [PROD_DIR]"
    exit 1
fi

domain=$1
site_username=os2
site_useremail=os2@$1
enable_saml2=$2
prod_dir=$3

repo_conf="$prod_dir/contrib/config/report-module"
report_local_settings="$repo_conf/local_settings.py.report"
cp "$report_local_settings" "$repo_conf/local_settings.py"
local_settings_file="$repo_conf/local_settings.py"

source "$prod_dir/contrib/system-scripts/production-scripts/common.sh"

setup_local_settings "$prod_dir" 'report' "$domain" "$local_settings_file"
perform_django_migrations 'report' "$prod_dir"
create_superuser 'report' "$prod_dir" "$site_username" "$site_useremail"
collectstatic_and_makemessages 'report' "$prod_dir"

# Configure apache for the administrations module
apache_setup "$prod_dir" "$domain" 'report'

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

# TODO: Remember npm - npm install . && npm run build. Is waiting on [#34571]