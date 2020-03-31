#!/usr/bin/env bash

set -e

if [ $# -lt 4 ]
then
    echo "usage: admin_deploy.sh [DOMAIN] [ENABLE_WEBSCAN] [ENABLE_FILESCAN] [ENABLE_MAILSCAN] [SETUP_DIR] [DEBUG]"
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

repo_conf="$setup_dir/contrib/config/admin-module"
admin_local_settings="$repo_conf/local_settings.py.admin"
cp "$admin_local_settings" "$repo_conf/local_settings.py"
local_settings_file="$repo_conf/local_settings.py"

source "$setup_dir/contrib/system-scripts/utils/common.sh"

setup_local_settings "$setup_dir" 'admin' "$domain" "$local_settings_file" "$debug"
sed -i "s/ENABLE_WEBSCAN = False/ENABLE_WEBSCAN = $enable_webscan/g" "$local_settings_file"
sed -i "s/ENABLE_EXCHANGESCAN = False/ENABLE_EXCHANGESCAN = $enable_mailscan/g" "$local_settings_file"
sed -i "s/ENABLE_FILESCAN = False/ENABLE_FILESCAN = $enable_filescan/g" "$local_settings_file"
perform_django_migrations 'admin' "$setup_dir"
create_superuser 'admin' "$setup_dir" "$site_username" "$site_useremail"

# TODO: Remember npm - npm install . && npm run build. Is waiting on [#34571]

