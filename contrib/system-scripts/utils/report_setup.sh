#!/usr/bin/env bash

set -e

if [ $# -lt 2 ]
then
    echo "usage: report_deploy.sh [DOMAIN] [ENABLE_SAML2] [SETUP_DIR] [DEBUG] [DEFAULT_FROM_EMAIL] [ADMIN_EMAIL] [NOTIFICATION_INSTITUTION]"
    exit 1
fi

domain=$1
site_username=os2
site_useremail=os2@$1
enable_saml2=$2
setup_dir=$3
debug=$4
from_email=$5
admin_email=$6
institution=$7

repo_conf="$setup_dir/contrib/config/report-module"
report_local_settings="$repo_conf/local_settings.py.report"
cp "$report_local_settings" "$repo_conf/local_settings.py"
local_settings_file="$repo_conf/local_settings.py"

source "$setup_dir/contrib/system-scripts/utils/common.sh"

setup_local_settings "$setup_dir" 'report' "$domain" "$local_settings_file" "$debug" "$from_email" "$admin_email" "$institution"
perform_django_migrations 'report' "$setup_dir"
create_superuser 'report' "$setup_dir" "$site_username" "$site_useremail"
