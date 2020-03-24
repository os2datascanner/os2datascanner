#!/usr/bin/env bash

set -e

if [ $# -lt 1 ]
then
    echo "usage: engine_deploy.sh [PRODUCTION_PATH] "
    exit 1
fi

prod_dir=$1
declare -a pipeline_names=("explorer" "processor" "matcher" "tagger" "exporter")

systemd_dir=$prod_dir/contrib/systemd
systemd_template="$systemd_dir"/os2ds-template@.service
for name in ${pipeline_names[@]}; do
    short_name=$(echo $name | cut -c1-4)
    service_name=os2ds-"$name"@.service
    cp "$systemd_template" "$systemd_dir"/"$service_name"
    new_service="$systemd_dir"/"$service_name"
    sed -i "s#PRODUCTION_PATH#"$prod_dir"#g" "$new_service"
    sed -i "s/SERVICE_NAME/"$name"/g" "$new_service"
    sed -i "s/SERVICE_SHORTNAME/"$short_name"/g" "$new_service"

    ln -sf "$new_service" /etc/systemd/system/"$service_name"
done

systemctl daemon-reload

