#!/usr/bin/env bash

set -e

if [ $# -lt 1 ]
then
    echo "usage: engine_deploy.sh [SETUP_PATH] "
    exit 1
fi

setup_dir=$1
declare -a pipeline_names=("explorer" "processor" "matcher" "tagger" "exporter")

systemd_dir="$setup_dir/contrib/systemd"
systemd_template="$systemd_dir/os2ds-template@.service"
for name in ${pipeline_names[@]}; do
    short_name="$(echo $name | cut -c1-4)"
    service_name="os2ds-$name@.service"
    cp "$systemd_template" "$systemd_dir/$service_name"
    new_service="$systemd_dir/$service_name"
    command="$setup_dir/bin/pex python -m os2datascanner.engine2.pipeline.$name"
    sed -i "s/SERVICE_NAME/$name/g" "$new_service"
    sed -i "s/SERVICE_SHORTNAME/$short_name/g" "$new_service"
    sed -i "s#COMMAND_LINE#$command#g" "$new_service"

    sudo ln -svrf "$new_service" "/etc/systemd/system/$service_name"
done

sudo systemctl daemon-reload

