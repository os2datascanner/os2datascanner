#!/usr/bin/env bash

set -e

# Generel settings
domain=*

# Admin defaults
webscan=True
filescan=True
exchangescan=True

# Report defaults
saml2_auth=False

repo_dir="`dirname "$BASH_SOURCE[0]"`/../../../"

source "$repo_dir/install.sh"

source "$repo_dir/contrib/system-scripts/utils/admin_setup.sh" "$domain" "$webscan" "$filescan" "$exchangescan" "$repo_dir" True

source "$repo_dir/contrib/system-scripts/utils/report_setup.sh" "$domain" "$saml2_auth" "$repo_dir" True