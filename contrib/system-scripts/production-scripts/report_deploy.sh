#!/usr/bin/env bash

if [ $# -lt 2 ]
then
    echo "usage: report_deploy.sh [DOMAIN] [ENABLE_SAML2]"
    exit 1
fi

domain=$1
site_username=os2
site_useremail=os2@$1
enable_saml2=$2

pwd > .pwd

prod_dir=/srv/os2datascanner
repo_dir=`cat .pwd`
repo_conf=$repo_dir/contrib/config/report-module
report_local_settings=$repo_conf/local_settings.py.report
cp $report_local_settings $repo_conf/local_settings.py
local_settings_file=$repo_conf/local_settings.py

source $repo_dir/contrib/system-scripts/production-scripts/common.sh

setup_local_settings $repo_dir 'report' $domain $local_settings_file
perform_django_migrations 'report' $repo_dir
create_superuser 'report' $repo_dir $site_username $site_useremail
collectstatic_and_makemessages 'report' $repo_dir