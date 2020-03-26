#!/usr/bin/env bash

# Important files that should not be overwritten:
# .secret, pika_settings, local_settings, service files.

# *Note: At the moment pipeline_collector uses var/debug.log as log file.
# It has not rotation enabled and will quickly fill up the system.
set -e

repo_dir="`dirname "$BASH_SOURCE[0]"`/../../../"


source "$repo_dir/contrib/system-scripts/production/.env"
source "$repo_dir/contrib/system-scripts/utils/common.sh"
echo "$PRODUCTION_DIR"

echo -e '\n************* Copy *************\n'
# Copy to prod dir
update_prod_dir "$PRODUCTION_DIR"

# Run installation
echo -e '\n************* Installation *************\n'
# Install system dependencies and python-env
source ""$PRODUCTION_DIR"/install.sh"

if [ "$INSTALL_WEB_PROJECTS" = True ]
then
    echo -e '\n************* Admin module *************\n'
    # Make migrations
    perform_django_migrations 'admin' "$PRODUCTION_DIR"

    # Collect static & Make messages
    collectstatic_and_makemessages 'admin' "$PRODUCTION_DIR"

    # TODO: Npm build

    echo -e '\n************* Report module *************\n'
    # Make migrations
    perform_django_migrations 'report' "$PRODUCTION_DIR"

    # Collect static & Make messages
    collectstatic_and_makemessages 'report' "$PRODUCTION_DIR"


    # TODO: Npm build
fi

echo -e '\n************* Reloading os2ds-services *************\n'
# Restart os2ds-*
systemctl reload os2ds-*

echo -e '\n************* Reloading apache2 *************\n'
# Restart apache
systemctl reload apache2.service

echo -e '\n************* Success *************\n'

echo -e '\n************* Simple Verification *************\n'

systemctl status os2ds-*

systemctl status apache2.service