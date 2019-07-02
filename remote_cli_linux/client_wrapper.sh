#!/bin/bash

#
# Copyright (c) 2019 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

if [[ "$CONFIG_TYPE" = "platform" ]]; then
    CLIENT_IMAGE_NAME="docker.io/starlingx/stx-platformclients:master-centos-stable-latest"
else
    CLIENT_IMAGE_NAME="docker.io/starlingx/stx-openstackclients:master-centos-stable-latest"
fi

# Environment variables related to keystone authentication
# Note: Keep this list up-to-date
read -d '' EXPORTS << EOF
OS_PASSWORD OS_PROJECT_DOMAIN_ID OS_PROJECT_ID OS_REGION_NAME
OS_USER_DOMAIN_NAME OS_PROJECT_NAME OS_IDENTITY_API_SERVICE
OS_AUTH_URL OS_USERNAME OS_INTERFACE OS_PROJECT_DOMAIN_NAME
OS_AUTH_TYPE
EOF

COMMAND_ENV=""

for exp in $EXPORTS; do
    # If variable is not defined, don't pass it over to the container
    if [[ ! -z "$(printenv $exp)" ]]; then
        COMMAND_ENV="$COMMAND_ENV -e $exp=$(printenv $exp)"
    fi
done

if [ -z "$2" ]; then
    exec docker run -ti ${COMMAND_ENV} --volume ${OSC_WORKDIR}:/wd --workdir /wd ${CLIENT_IMAGE_NAME} "$@"
else
    exec docker run -t ${COMMAND_ENV} --volume ${OSC_WORKDIR}:/wd --workdir /wd ${CLIENT_IMAGE_NAME} "$@"
fi
