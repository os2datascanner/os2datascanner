#!/usr/bin/env bash

set -e

if [ $# -lt 4 ]
then
    echo "usage: admin_deploy.sh [DOMAIN] [ENABLE_WEBSCAN] [ENABLE_FILESCAN] [ENABLE_MAILSCAN] [SETUP_DIR] [DEBUG] [DEFAULT_FROM_EMAIL] [ADMIN_EMAIL] [NOTIFICATION_INSTITUTION]"
    exit 1
fi

domain=$1
enable_webscan=$2
enable_mailscan=$3
enable_filescan=$4
site_username=os2
site_useremail=os2@$1
setup_dir=$5
debug=$6
from_email=$7
admin_email=$8
institution=$9

repo_conf="$setup_dir/contrib/config/admin-module"
template_user_settings_file="$repo_conf/user-settings.toml.admin"
cp "$template_user_settings_file" "$repo_conf/user-settings.toml"
user_settings_file="$repo_conf/user-settings.toml"

source "$setup_dir/contrib/system-scripts/utils/common.sh"

setup_local_settings "$setup_dir" 'admin' "$domain" "$user_settings_file" "$debug" "$from_email" "$admin_email" "$institution"
sed -i "s/ENABLE_WEBSCAN = false/ENABLE_WEBSCAN = $enable_webscan/g" "$user_settings_file"
sed -i "s/ENABLE_EXCHANGESCAN = false/ENABLE_EXCHANGESCAN = $enable_mailscan/g" "$user_settings_file"
sed -i "s/ENABLE_FILESCAN = false/ENABLE_FILESCAN = $enable_filescan/g" "$user_settings_file"

export OS2DS_ADMIN_USER_CONFIG_PATH="$user_settings_file"
export OS2DS_ADMIN_SYSTEM_CONFIG_PATH=""

echo "export OS2DS_ADMIN_USER_CONFIG_PATH=$user_settings_file" >> /etc/apache/envvars
echo 'export OS2DS_ADMIN_SYSTEM_CONFIG_PATH=""' >> /etc/apache/envvars

perform_django_migrations 'admin' "$setup_dir"
create_superuser 'admin' "$setup_dir" "$site_username" "$site_useremail"
