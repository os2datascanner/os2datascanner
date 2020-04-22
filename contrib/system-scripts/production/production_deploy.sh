#!/usr/bin/env bash

set -e

repo_dir="`dirname "$BASH_SOURCE[0]"`/../../../"

echo "$repo_dir"
# Load .env file
source "$repo_dir/contrib/system-scripts/production/.env"
if [ "$PRODUCTION_DIR" = "%INSERT_PRODUCTION_DIR%" ]
then
    echo "Production directory has not been changed and is still the deafult string $PRODUCTION_DIR. Please go to the .env file and add a new path."
    exit -1
fi
if [ "$ADMIN_DOMAIN" = "%INSERT_ADMIN_DOMAIN%" ]
then
    echo "The domain for the Admin module has not been changed and is still the deafault string $ADMIN_DOMAIN. Please go to the .enb file and add a new domain."
    exit -1
fi
if [ "$REPORT_DOMAIN" = "%INSERT_REPORT_DOMAIN%" ]
then
    echo "The domain for the Report module has not been changed and is still the deafault string $REPORT_DOMAIN. Please go to the .enb file and add a new domain."
    exit -1
fi
# Load common lib
source "$repo_dir/contrib/system-scripts/utils/common.sh"

echo -e '\n************* Copy *************\n'
# Copy to prod dir
copy_to_prod_dir "$PRODUCTION_DIR"

echo -e '\n************* Installation *************\n'
# Install system dependencies and python-env
source "$PRODUCTION_DIR/install.sh"

if [ "$INSTALL_WEB_PROJECTS" = True ]
then
    echo -e '\n************* Admin module *************\n'
    # Setup administrations module
    source "$PRODUCTION_DIR/contrib/system-scripts/utils/admin_setup.sh" "$ADMIN_DOMAIN" "$ENABLE_WEBSCAN" "$ENABLE_FILESCAN" "$ENABLE_EXCHANGESCAN" "$PRODUCTION_DIR" False

    npm_install_and_build 'admin' "$PRODUCTION_DIR" 'prod'
    collectstatic_and_makemessages 'admin' "$PRODUCTION_DIR"

    # Configure apache for the administrations module
    apache_setup "$PRODUCTION_DIR" "$ADMIN_DOMAIN" 'admin'

    echo -e '\n************* Report module *************\n'
    # Setup report module
    source "$PRODUCTION_DIR/contrib/system-scripts/utils/report_setup.sh" "$REPORT_DOMAIN" "$ENABLE_SAML2" "$PRODUCTION_DIR" False

    npm_install_and_build 'report' "$PRODUCTION_DIR" 'prod'
    collectstatic_and_makemessages 'report' "$PRODUCTION_DIR"

    # Configure apache for the administrations module
    apache_setup "$PRODUCTION_DIR" "$REPORT_DOMAIN" 'report'

    # deploy pipeline_collector
    systemd_dir="$PRODUCTION_DIR/contrib/systemd"
    systemd_template="$systemd_dir/os2ds-template@.service"

    name='pipeline_collector'

    service_name="os2ds-$name@.service"
    cp "$systemd_template" "$systemd_dir/$service_name"
    new_service="$systemd_dir/$service_name"

    command="$PRODUCTION_DIR/bin/manage-report pipeline_collector"
    short_name="$(echo $name | cut -c1-4)"

    sed -i "s#COMMAND_LINE#$command#g" "$new_service"
    sed -i "s/SERVICE_NAME/$name/g" "$new_service"
    sed -i "s/SERVICE_SHORTNAME/$short_name/g" "$new_service"

    ln -sf "$new_service" "/etc/systemd/system/"

     systemctl daemon-reload
fi

if [ "$INSTALL_ENGINE_PIPELINE" = True ]
then
    echo -e '\n************* Engine2 setup *************\n'
    # Setup engine2 services
    source "$PRODUCTION_DIR/contrib/system-scripts/utils/engine_setup.sh" "$PRODUCTION_DIR"
fi

sudo chown --recursive www-data:www-data "$PRODUCTION_DIR"

echo -e '\n************* Success *************\n'

echo -e '\n************* Simple Verification *************\n'

echo -e "$PRODUCTION_DIR"
ls -l "$PRODUCTION_DIR"

if [ "$INSTALL_WEB_PROJECTS" = True ]
then
    echo -e "\n$PRODUCTION_DIR/src/os2datascanner/projects/admin/"
    ls -l "$PRODUCTION_DIR/src/os2datascanner/projects/admin/"

    echo -e "\n$PRODUCTION_DIR/src/os2datascanner/projects/report/"
    ls -l "$PRODUCTION_DIR/src/os2datascanner/projects/report/"

    echo -e "\n/etc/apache2/certs/datascanner"
    ls -l /etc/apache2/certs/datascanner
fi

if [ "$INSTALL_ENGINE_PIPELINE" = True ]
then
    echo -e "\n$PRODUCTION_DIR/contrib/systemd/"
    ls -l "$PRODUCTION_DIR/contrib/systemd/"

    echo -e "\n/etc/systemd/system/os2ds-*"
    ls -l /etc/systemd/system/os2ds-*
fi
