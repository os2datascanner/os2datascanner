#!/usr/bin/env bash

if [ $# -lt 4 ]
then
    echo "usage: admin_deploy.sh [DOMAIN] [ENABLE_WEBSCAN] [ENABLE_FILESCAN] [ENABLE_MAILSCAN] [PROD_DIR]"
    exit 1
fi

domain=$1
site_username=os2
site_useremail=os2@$1
prod_dir=$5

repo_conf=$prod_dir/contrib/config/admin-module
admin_local_settings=$repo_conf/local_settings.py.admin
cp $admin_local_settings $repo_conf/local_settings.py
local_settings_file=$repo_conf/local_settings.py

source $prod_dir/contrib/system-scripts/production-scripts/common.sh

setup_local_settings $prod_dir 'admin' $domain $local_settings_file
setup_local_settings_sources $2 $3 $4 $local_settings_file
perform_django_migrations 'admin' $prod_dir
create_superuser 'admin' $prod_dir $site_username $site_useremail
collectstatic_and_makemessages 'admin' $prod_dir

# Configure apache for the administrations module
apache_setup $prod_dir $domain 'admin'
# TODO: Remember npm - npm install . && npm run build. Is waiting on [#34571]