#!/usr/bin/env bash

if [ $# -lt 6 ]
then
    printf "The script is used like this:\n\n    deploy.sh [ DOMAIN ] [ DB-NAME ] [ DB-USER ]  [ DB-PASSWD ] [ SITE-USER ] [ SITE-USER-EMAIL ] [ENABLE_FILESCAN] [ENABLE_MAILSCAN]\n\n"
    exit
fi

domain=$1
db_name=$2
db_user=$3
db_pass=$4
site_username=$5
site_useremail=$6
enable_filescan=$7
enable_mailscan=$8

secret_key=$(echo `openssl rand -base64 100 | head -c100 | tac`)

echo `pwd` > .pwd

prod_dir=/var/www/os2datascanner
repo_dir=`cat .pwd`
repo_conf=$repo_dir/conf
install_dir=$repo_dir
settings_file=$repo_conf/settings.py
default_local_settings=$repo_conf/local_settings.py.default
cp $default_local_settings $repo_conf/local_settings.py
local_settings_file=$repo_conf/local_settings.py
vhost_file=$repo_conf/vhost


#
# DJANGO
#

function django()
{

    # Run installation
    ./install.sh

    cd $repo_dir

    # Insert secret key and database information
    sed -i "s/INSERT_SECRET_KEY/$secret_key/g" $local_settings_file
    sed -i "s/INSERT_DB_NAME/$db_name/g" $local_settings_file
    sed -i "s/INSERT_DB_USER/$db_user/g" $local_settings_file
    sed -i "s/INSERT_DB_PASSWD/$db_pass/g" $local_settings_file
    sed -i "s/DEBUG = True/DEBUG = False/g" $local_settings_file
    sed -i "s/INSERT_DOMAIN_NAME/$domain/g" $local_settings_file

    # Link settings file to webscanner settings
    ln -sf $settings_file $install_dir/webscanner_site/webscanner/settings.py
    ln -sf $local_settings_file $install_dir/webscanner_site/webscanner/local_settings.py

}

#
# DATABASE SETUP
#

function database()
{

    # Login as postgres user
    postgres_user="sudo -u postgres"

    # Create new database
    $postgres_user createdb $db_name

    # Create new user with priviligies
    $postgres_user psql -c "CREATE USER $db_user WITH PASSWORD '$db_pass';"
    $postgres_user psql -c "GRANT ALL PRIVILEGES ON DATABASE $db_name TO $db_user;"
    $postgres_user psql -c "ALTER USER $db_user WITH SUPERUSER;"


    # Migrate
    source $install_dir/python-env/bin/activate

    managepy=$install_dir/webscanner_site/manage.py

    $managepy collectstatic
    $managepy makemigrations --merge
    $managepy migrate

    echo 'Type in superuser password'
    $managepy createsuperuser --username $site_username --email $site_useremail
    $managepy migrate --run-syncdb

    $managepy makemessages --ignore=scrapy-webscanner/* --ignore=python-env/*
    $managepy compilemessages

}


#
# PRODUCTION SETUP
#

function copy_to_prod_dir()
{

    sudo mkdir $prod_dir

    sudo cp --recursive conf cron django-os2webscanner python-env scrapy-webscanner var webscanner_client webscanner_site xmlrpc_clients $prod_dir
    sudo cp NEWS LICENSE README VERSION $prod_dir

    sudo chown --recursive www-data:www-data $prod_dir

    # Link settings file to webscanner settings
    sudo ln -sf /var/www/os2datascanner/conf/settings.py $prod_dir/webscanner_site/webscanner/settings.py
    sudo ln -sf /var/www/os2datascanner/conf/local_settings.py $prod_dir/webscanner_site/webscanner/local_settings.py

}

#
# APACHE
#

function apache()
{

    vhost=$prod_dir/conf/vhost

    # Copy the vhost
    sudo ln -sv $vhost /etc/apache2/sites-available/$domain.conf

    # Add install path and domainname in vhost
    sed -i "s|INSERT_INSTALL_PATH|$prod_dir|g" $vhost
    sed -i "s|INSERT_DOMAIN|$domain|g" $vhost

    # Create log dir
    sudo mkdir -p /var/log/$domain

    # Disable old site, disable wsgi and enable new vhos
    sudo a2dissite 000-default
    sudo a2dismod index
    sudo a2enmod rewrite wsgi headers ssl
    sudo a2ensite $domain

    sudo service apache2 reload
}


#
# SCANNERMANAGER
#

function scannermanager_setup()
{

    DATASCANNER_SERVICE="/etc/systemd/system/datascanner-manager.service"

    cat <<EOT >> "$DATASCANNER_SERVICE"
        [Unit]
        Description=Datascanner-manager service
        After=network.target

        [Service]
        Type=simple
        User=www-data
        WorkingDirectory=$prod_dir
        ExecStart=$prod_dir/python-env/bin/python  $prod_dir/scrapy-webscanner/scanner_manager.py
        Restart=on-failure

        [Install]
        WantedBy=multi-user.target
EOT

    sudo systemctl enable datascanner-manager
    sudo systemctl start datascanner-manager
}

#
# SUPERVISOR
#

function setup_supervisor()
{

    sudo apt install -y supervisor

    SUPERVISOR_CONF="/etc/supervisor/conf.d/start_process_manager.conf"

    cat <<EOT >> "$SUPERVISOR_CONF"
        [program:process_manager]
        command=./var/www/os2datascanner/scrapy-webscanner/start_process_manager.sh
        user=www-data
        autostart=true
        autorestart=true
        stderr_logfile=/var/log/process.err.log
        stdout_logfile=/var/log/process.out.log
        exitcode=0

EOT

    sudo service supervisor reload
}

#
# FILESCAN
#

function filescan_setup()
{

    sudo mkdir /tmp/mnt
    sudo chown -R www-data:www-data /tmp/mnt

    sudoers_file=/etc/sudoers.d/www-data

    sudo echo "www-data ALL= NOPASSWD: /bin/mount" >> $sudoers_file
    sudo echo "www-data ALL= NOPASSWD: /bin/umount" >> $sudoers_file

    sed -i "s/PRODUCTION_MODE = False/PRODUCTION_MODE = True/g" $local_settings_file
    sed -i "s/ENABLE_FILESCAN = False/ENABLE_FILESCAN = True/g" $local_settings_file
    sed -i "s/ENABLE_WEBSCAN = True/ENABLE_WEBSCAN = False/g" $local_settings_file

}

#
# MAILSCAN
#

function mailscan_setup()
{

    sed -i "s/ENABLE_EXCHANGESCAN = False/ENABLE_EXCHANGESCAN = True/g" $local_settings_file
    sed -i "s/ENABLE_FILESCAN = False/ENABLE_FILESCAN = True/g" $local_settings_file
    sed -i "s/ENABLE_WEBSCAN = True/ENABLE_WEBSCAN = False/g" $local_settings_file

}

#
# CRON
#

function cron_setup()
{
    if [ "$enable_mailscan" == "true" ]; then
        echo '* 17 * * fri /var/www/os2datascanner/cron/exchange_cron.sh' >> $prod_dir/conf/www-data
    fi
    sudo cp $prod_dir/conf/www-data /var/spool/cron/crontabs/
    sudo chown www-data:crontab /var/spool/cron/crontabs/www-data
    sudo -u www-data crontab -l

}

django
database
if [ "$enable_filescan" == "true" ]; then
    filescan_setup
fi
if [ "$enable_mailscan" == "true" ]; then
    mailscan_setup
fi
copy_to_prod_dir
cron_setup
scannermanager_setup
setup_supervisor
apache
