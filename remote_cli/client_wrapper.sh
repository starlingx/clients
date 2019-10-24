#!/bin/bash

#
# Copyright (c) 2019 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

KUBE_CFG_PATH="/root/.kube/config"

if [[ "$CONFIG_TYPE" = "platform" ]]; then
    CLIENT_IMAGE_NAME="docker.io/starlingx/stx-platformclients:${PLATFORM_DOCKER_IMAGE_TAG}"
    # We only need to configure the kubernetes authentication file on the platform container
    VOLUME_LIST="--volume ${OSC_WORKDIR}:/wd --volume ${K8S_CONFIG_FILE}:${KUBE_CFG_PATH}"
else
    CLIENT_IMAGE_NAME="docker.io/starlingx/stx-openstackclients:${APPLICATION_DOCKER_IMAGE_TAG}"
    VOLUME_LIST="--volume ${OSC_WORKDIR}:/wd"
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

if [[ -z "$FORCE_SHELL" ]] || [[ "$FORCE_SHELL" != "true" ]]; then
    FORCE_SHELL="false"
fi

if [[ -z "$FORCE_NO_SHELL" ]] || [[ "$FORCE_NO_SHELL" != "true" ]]; then
    FORCE_NO_SHELL="false"
fi

if [[ "$FORCE_SHELL" == "true" ]] && [[ "$FORCE_NO_SHELL" == "true" ]]; then
    echo "Error: cannot set both FORCE_SHELLL and FORCE_NO_SHELL variables at the same time".
    echo "Unset one of them and re-run the command"
    exit 1
fi


if [[ "$FORCE_SHELL" == "true" ]]; then
    exec docker run --rm -ti ${COMMAND_ENV} ${VOLUME_LIST} --workdir /wd ${CLIENT_IMAGE_NAME} "$@"
elif [[ "$FORCE_NO_SHELL" == "true" ]]; then
    exec docker run --rm -t ${COMMAND_ENV} ${VOLUME_LIST} --workdir /wd ${CLIENT_IMAGE_NAME} "$@"
elif [ -z "$2" ]; then
    exec docker run --rm -ti ${COMMAND_ENV} ${VOLUME_LIST} --workdir /wd ${CLIENT_IMAGE_NAME} "$@"
else
    exec docker run --rm -t ${COMMAND_ENV} ${VOLUME_LIST} --workdir /wd ${CLIENT_IMAGE_NAME} "$@"
fi
