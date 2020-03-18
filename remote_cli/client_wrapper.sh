#!/bin/bash

#
# Copyright (c) 2019 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

KUBE_CFG_PATH="/root/.kube/config"

SHELL_TYPE=$(uname -s)

if [[ "$CONFIG_TYPE" = "platform" ]]; then
    CLIENT_IMAGE_NAME="${PLATFORM_DOCKER_IMAGE}"
    # We only need to configure the kubernetes authentication file on the platform container
    if [[ "${SHELL_TYPE}" == *"CYGWIN"* ]]; then
        # On Windows 10, native docker needs the full windows path, not the UNIX one,
        # so we pass the UNIX path through cygpath
        VOLUME_LIST="--volume $(cygpath -m ${OSC_WORKDIR}):/wd --volume $(cygpath -m ${K8S_CONFIG_FILE}):${KUBE_CFG_PATH}"
    else
        VOLUME_LIST="--volume ${OSC_WORKDIR}:/wd --volume ${K8S_CONFIG_FILE}:${KUBE_CFG_PATH}"
    fi
else
    CLIENT_IMAGE_NAME="${APPLICATION_DOCKER_IMAGE}"
    if [[ "${SHELL_TYPE}" == *"CYGWIN"* ]]; then
        VOLUME_LIST="--volume $(cygpath -m ${OSC_WORKDIR}):/wd"
    else
        VOLUME_LIST="--volume ${OSC_WORKDIR}:/wd"
    fi
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

if [[ "${SHELL_TYPE}" == *"CYGWIN"* ]]; then
    # To fully support interactive shell in docker under cygwin
    # we need to prefix the docker command with winpty
    SHELL_COMMAND="winpty docker"
else
    SHELL_COMMAND="docker"
fi

if [[ "$FORCE_SHELL" == "true" ]]; then
    exec ${SHELL_COMMAND} run --rm -ti ${COMMAND_ENV} ${VOLUME_LIST} --workdir /wd ${CLIENT_IMAGE_NAME} "$@"
elif [[ "$FORCE_NO_SHELL" == "true" ]]; then
    exec ${SHELL_COMMAND} run --rm -t ${COMMAND_ENV} ${VOLUME_LIST} --workdir /wd ${CLIENT_IMAGE_NAME} "$@"
elif [ -z "$2" ]; then
    exec ${SHELL_COMMAND} run --rm -ti ${COMMAND_ENV} ${VOLUME_LIST} --workdir /wd ${CLIENT_IMAGE_NAME} "$@"
else
    exec ${SHELL_COMMAND} run --rm -t ${COMMAND_ENV} ${VOLUME_LIST} --workdir /wd ${CLIENT_IMAGE_NAME} "$@"
fi
