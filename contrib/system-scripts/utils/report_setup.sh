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
template_user_settings_file="$repo_conf/user-settings.toml.report"
cp "$template_user_settings_file" "$repo_conf/user-settings.toml"
user_settings_file="$repo_conf/user-settings.toml"

source "$setup_dir/contrib/system-scripts/utils/common.sh"

export OS2DS_REPORT_USER_CONFIG_PATH="$user_settings_file"
export OS2DS_REPORT_SYSTEM_CONFIG_PATH=""

echo "export OS2DS_REPORT_USER_CONFIG_PATH=$user_settings_file" >> /etc/apache/envvars
echo 'export OS2DS_REPORT_SYSTEM_CONFIG_PATH=""' >> /etc/apache/envvars

setup_local_settings "$setup_dir" 'report' "$domain" "$user_settings_file" "$debug" "$from_email" "$admin_email" "$institution"
perform_django_migrations 'report' "$setup_dir"
create_superuser 'report' "$setup_dir" "$site_username" "$site_useremail"
