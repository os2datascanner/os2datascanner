#!/usr/bin/env bash

set -e

# Generel settings
domain=*
from_email='(Magenta Bibos Info) info@magenta.dk'
admin_email='(Magenta Bibos Admin) info@magenta.dk'
institution="Magenta Aps"
# Admin defaults
webscan=true
filescan=true
exchangescan=true

# Report defaults
saml2_auth=false

repo_dir="`dirname "$BASH_SOURCE[0]"`/../../../"

source "$repo_dir/install.sh"

source "$repo_dir/contrib/system-scripts/utils/admin_setup.sh" "$domain" "$webscan" "$filescan" "$exchangescan" "$repo_dir" true "$from_email" "$admin_email" "$institution"

source "$repo_dir/contrib/system-scripts/utils/report_setup.sh" "$domain" "$saml2_auth" "$repo_dir" true "$from_email" "$admin_email" "$institution"

source "$repo_dir/contrib/system-scripts/utils/engine_setup.sh" "$repo_dir"