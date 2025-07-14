#!/bin/bash

#
# Copyright (c) 2019,2025 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

KUBE_CFG_PATH="/root/.kube/config"
HELM_CONFIG_PATH="/root/.config/helm"
HELM_CACHE_PATH="/root/.cache/helm"

SHELL_TYPE=$(uname -s)

if [[ "$CONFIG_TYPE" = "platform" ]]; then
    CLIENT_IMAGE_NAME="${PLATFORM_DOCKER_IMAGE}"
    # We only need to configure the kubernetes authentication file on the platform container
    if [[ "${SHELL_TYPE}" == *"CYGWIN"* ]]; then
        # On Windows 10, native docker needs the full windows path, not the UNIX one,
        # so we pass the UNIX path through cygpath
        VOLUME_LIST="--volume $(cygpath -m ${OSC_WORKDIR}):/wd --volume $(cygpath -m ${K8S_CONFIG_FILE}):${KUBE_CFG_PATH} --volume $(cygpath -m ${OSC_WORKDIR}/.helm):${HELM_CONFIG_PATH} --volume $(cygpath -m ${OSC_WORKDIR}/.cache):${HELM_CACHE_PATH}"
    else
        VOLUME_LIST="--volume ${OSC_WORKDIR}:/wd --volume ${K8S_CONFIG_FILE}:${KUBE_CFG_PATH} --volume ${OSC_WORKDIR}/.helm:${HELM_CONFIG_PATH} --volume ${OSC_WORKDIR}/.cache:${HELM_CACHE_PATH}"
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
OS_AUTH_TYPE OS_CACERT
EOF

# Append CLI-specific environment variables
EXPORTS+=" CLI_CONFIRMATIONS"

# We initialize the environment variable list with the OS_ENDPOINT_TYPE set
# "publicURL" because dcmanager defaults to "internalURL" if not overridden
# by a parameter to the command itself or by the environment variable.
# For remote access the endpoint-type must always be publicURL, but the
# environment variable is not part of the set of variables present in the
# platform RC file downloaded from Horizon.
# In order for dcmanager to work properly, we manually set this variable
# to the correct value.
COMMAND_ENV="-e OS_ENDPOINT_TYPE=publicURL"

# the REQUESTS_CA_BUNDLE is required to the fm client
if [[ ! -z "$(printenv "OS_CACERT")" ]]; then
    COMMAND_ENV="$COMMAND_ENV -e REQUESTS_CA_BUNDLE=$(printenv "OS_CACERT")"
fi

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

cmd=""
for arg in "$@"; do
    printf -v esc '%q ' "$arg"
    cmd+="$esc"
done

if [[ "$FORCE_SHELL" == "true" ]]; then
    exec ${SHELL_COMMAND} run --rm --network host -ti ${COMMAND_ENV} ${VOLUME_LIST} --entrypoint /bin/bash --workdir /wd ${CLIENT_IMAGE_NAME} -c "${cmd}"
elif [[ "$FORCE_NO_SHELL" == "true" ]]; then
    exec ${SHELL_COMMAND} run --rm --network host -t ${COMMAND_ENV} ${VOLUME_LIST} --entrypoint /bin/bash --workdir /wd ${CLIENT_IMAGE_NAME} -c "${cmd}"
elif [ -z "$2" ]; then
    exec ${SHELL_COMMAND} run --rm --network host -ti ${COMMAND_ENV} ${VOLUME_LIST} --entrypoint /bin/bash --workdir /wd ${CLIENT_IMAGE_NAME} -c "${cmd}"
else
    exec ${SHELL_COMMAND} run --rm --network host -t ${COMMAND_ENV} ${VOLUME_LIST} --entrypoint /bin/bash --workdir /wd ${CLIENT_IMAGE_NAME} -c "${cmd}"
fi
