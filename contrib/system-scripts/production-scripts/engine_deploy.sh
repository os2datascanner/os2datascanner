#!/usr/bin/env bash

if [ $# -lt 1 ]
then
    echo "usage: engine_deploy.sh [PRODUCTION_PATH] "
    exit 1
fi

prod_path=$1
echo "$prod_path"
declare -a pipeline_names=("explorer" "processor" "matcher" "tagger" "exporter")

pwd > .pwd

repo_dir=`cat .pwd`
systemd_dir=$repo_dir/contrib/systemd
systemd_template=$systemd_dir/os2ds-template@.service
for name in ${pipeline_names[@]}; do
    short_name=$(echo $name | cut -c1-4)
    cp $systemd_template $systemd_dir/os2ds-$name.service
    new_service=$systemd_dir/os2ds-$name.service
    sed -i "s#PRODUCTION_PATH#$prod_path#g" $new_service
    sed -i "s/SERVICE_NAME/$name/g" $new_service
    sed -i "s/SERVICE_SHORTNAME/$short_name/g" $new_service

    ln -sf $new_service /etc/systemd/system/os2ds-$name.service
done

systemctl daemon-reload

