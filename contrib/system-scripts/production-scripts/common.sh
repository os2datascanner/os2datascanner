#!/usr/bin/env bash

#
# DJANGO SETUP
#

function setup_local_settings()
{
    echo 'Django setup'

    repo_dir=$1
    module=$2
    db_name=os2datascanner_$2
    db_user=os2datascanner_$2
    domain=$3
    local_settings_file=$4

    secret_key=$(xxd -c 64 -l 64 -p /dev/urandom)
    db_pass=$(pwgen -s -1 12)

    create_database "$db_name" "$db_user" "$db_pass"

    cd "$repo_dir"

    # Insert secret key and database information
    sed -i "s/INSERT_SECRET_KEY/$secret_key/g" "$local_settings_file"
    sed -i "s/INSERT_DB_NAME/$db_name/g" "$local_settings_file"
    sed -i "s/INSERT_DB_USER/$db_user/g" "$local_settings_file"
    sed -i "s/INSERT_DB_PASSWD/$db_pass/g" "$local_settings_file"
    sed -i "s/DEBUG = True/DEBUG = False/g" "$local_settings_file"
    sed -i "s/INSERT_DOMAIN_NAME/$domain/g" "$local_settings_file"

    # Link local settings file to administration modules local settings
    ln -sf "$local_settings_file" "$repo_dir/src/os2datascanner/projects/$2/local_settings.py"

}

function setup_local_settings_sources()
{
    enable_webscan=$1
    enable_mailscan=$2
    enable_filescan=$3
    local_settings_file=$4

    sed -i "s/ENABLE_WEBSCAN = False/ENABLE_WEBSCAN = $enable_webscan/g" "$local_settings_file"
    sed -i "s/ENABLE_EXCHANGESCAN = False/ENABLE_EXCHANGESCAN = $enable_mailscan/g" "$local_settings_file"
    sed -i "s/ENABLE_FILESCAN = False/ENABLE_FILESCAN = $enable_filescan/g" "$local_settings_file"
}

perform_django_migrations()
{
    module=$1
    repo_dir=$2
    echo "$0: applying Django migrations"
    if "$repo_dir/bin/manage-$module" showmigrations | sponge | grep --quiet '\[ \]'; then
        "$repo_dir/bin/manage-$module" migrate
    else
        echo "$0: all Django migrations have been applied"
    fi
}

function create_superuser()
{
    module=$1
    repo_dir=$2
    site_username=$3
    site_useremail=$4
    echo "Create new password for superuser ($site_username)"
    "$repo_dir/bin/manage-$module" createsuperuser --username "$site_username" --email "$site_useremail"
    "$repo_dir/bin/manage-$module" migrate --run-syncdb

}

function collectstatic_and_makemessages()
{
    module=$1
    repo_dir=$2
    echo "Collecting static files"
    "$repo_dir/bin/manage-$module" collectstatic

    echo "Making and compiling messages."
    "$repo_dir/bin/manage-$module" makemessages --ignore=python-env/*
    "$repo_dir/bin/manage-$module" compilemessages
}

function npm_install_and_build()
{
    module=$1
    repo_dir=$2
    echo "Installing npm packages"
    cd "$repo_dir/src/os2datascanner/$module/"$module"app/"
    npm install .
    npm run build
}

#
# DATABASE SETUP
#

function create_database()
{
    db_name=$1
    db_user=$2
    db_pass=$3
    # Login as postgres user
    as_postgres="sudo -u postgres"

    # Create new database
    $as_postgres createdb "$db_name"

    # Create new user with priviligies
    $as_postgres psql -c "CREATE USER $db_user WITH PASSWORD '$db_pass';"
    $as_postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $db_name TO $db_user;"
    $as_postgres psql -c "ALTER USER $db_user WITH SUPERUSER;"

}

#
# APACHE
#

function apache_setup()
{
    prod_dir=$1
    domain=$2
    module=$3
    vhost="$prod_dir/contrib/config/vhost"

    module_vhost="$prod_dir/contrib/config/$module-module/$module-vhost.conf"
    cp "$prod_dir/contrib/config/vhost" "$module_vhost"
    # Add install path and domainname in vhost
    sed -i "s|INSERT_INSTALL_PATH|$prod_dir|g" "$module_vhost"
    sed -i "s|INSERT_DOMAIN|$domain|g" "$module_vhost"
    sed -i "s|INSERT_CERT_FILE|/etc/apache2/certs/datascanner|g" "$module_vhost"
    sed -i "s|INSERT_CERT_KEY|/etc/apache2/certs/datascanner|g" "$module_vhost"
    sed -i "s|INSERT_CACERT_FILE|/etc/apache2/certs/datascanner|g" "$module_vhost"
    sed -i "s|INSERT_MODULE|$module|g" "$module_vhost"

    # Create os2datascanner ssl certs dir
    sudo mkdir -p /etc/apache2/certs/datascanner

    # Create log dir
    sudo mkdir -p "/var/log/$domain"

    # Copy the vhost
    sudo ln -sv "$module_vhost" "/etc/apache2/sites-available/$domain.conf"

    # Until ssl-certificates are on the server we cannot reload the apache2 service.
}

#
# PRODUCTION SETUP
#

function copy_to_prod_dir()
{
    prod_dir=$1
    echo "Copying to production dir $prod_dir..."
    sudo -H mkdir -p "$prod_dir"
    sudo -H rsync \
        --progress --recursive --delete  \
        --links --safe-links \
        --exclude ".*/" \
        --exclude ".*" \
        --exclude ".git/" \
        --exclude "python-env/" \
        --exclude '*.pyc' \
        "$repo_dir"/ "$prod_dir"
    echo 'Done Copying.'
}

install_python_environment()
{
    virtualenv=$1
    repo_dir=$2
    # Setup virtualenv, install Python packages.
    echo "$0: installing Python environment and dependencies"

    if [ -e "$virtualenv/bin/python3" ]
    then
        echo "$0: Python environment already installed" 1>&2
    else
        python3 -m venv --system-site-packages "$virtualenv"
    fi &&

    "$virtualenv/bin/pip" install -U setuptools wheel pip &&
    "$virtualenv/bin/pip" install -r "$repo_dir/requirements/requirements.txt"
}
