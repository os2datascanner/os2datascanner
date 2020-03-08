#!/usr/bin/env bash

if [ $# -lt 4 ]
then
    echo "usage: admin_deploy.sh [DOMAIN] [ENABLE_WEBSCAN] [ENABLE_FILESCAN] [ENABLE_MAILSCAN]"
    exit 1
fi

domain=$1
site_username=os2
site_useremail=os2@$1

pwd > .pwd

repo_dir=`cat .pwd`
repo_conf=$repo_dir/contrib/config/admin-module
admin_local_settings=$repo_conf/local_settings.py.admin
cp $admin_local_settings $repo_conf/local_settings.py
local_settings_file=$repo_conf/local_settings.py

source $repo_dir/contrib/system-scripts/production-scripts/common.sh

setup_local_settings $repo_dir 'admin' $domain $local_settings_file
setup_local_settings_sources $2 $3 $4 $local_settings_file
perform_django_migrations 'admin' $repo_dir
create_superuser 'admin' $repo_dir $site_username $site_useremail
collectstatic_and_makemessages 'admin' $repo_dir