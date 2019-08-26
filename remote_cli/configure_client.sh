#!/bin/bash

#
# Copyright (c) 2019 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

# Default values
RC_FILE="admin-openrc.sh"
CONF_FILE=remote_client_config.sh
ALIAS_FILE=config_aliases.sh
K8S_FILE="temp-kubeconfig"
TAG_FILE=docker_image_version.sh
WORK_DIR='.'
custom_conf_file=0
explicit_client_type=0

# The script may be called from locations other
# than its own folder, so build the full path to
# the script.
if [[ $BASH_SOURCE = '/'* ]]; then
    PATH_TO_SCRIPT="$(dirname $BASH_SOURCE)"
else
    PATH_TO_SCRIPT="$(pwd)/$(dirname $BASH_SOURCE)"
fi

usage(){
    echo "Usage:"
    echo "configure_client [-t client_type] [-h] [-w workdir] [-o outputfile] [-r RC_FILE] [-k k8s_file]"
    echo "-h                show help options"
    echo "-t client_type    type of client configuration (platform/openstack)"
    echo "                  (default value is platform)"
    echo "-w workdir        local directory to be mounted in docker container"
    echo "                  (default is local directory)"
    echo "-o output         output RC file"
    echo "                  (default is remote_client_<app/platform>.sh)"
    echo "-r RC_FILE        tenant RC file"
    echo "                  (default value is admin-openrc.sh)"
    echo "-k k8s_file       kubernetis config file"
    echo "                  (default value is temp-kubeconfig)"
}

while getopts ":hr:w:o:t:k:" opt; do
    case $opt in
        h)
            usage
            exit 1
            ;;
        r)
            RC_FILE=${OPTARG}
            ;;
        w)
            WORK_DIR=${OPTARG}
            ;;
        o)
            CUSTOM_CONF_FILE=${OPTARG}
            custom_conf_file=1
            ;;
        t)
            CLIENT_TYPE=${OPTARG}
            explicit_client_type=1
            ;;
        k)
            K8S_FILE=${OPTARG}
            ;;
        *)
            echo "Invalid parameter provided"
            usage
            exit 1
            ;;
    esac
done

# Check if we configure a platform or an application client
if [[ $explicit_client_type -eq 1 ]]; then
    if [[ "$CLIENT_TYPE" == "platform" ]]; then
        CONFIG_TYPE="platform"
        CONF_FILE="remote_client_platform.sh"
    elif [[ "$CLIENT_TYPE" == "openstack" ]]; then
        CONFIG_TYPE="application"
        CONF_FILE="remote_client_openstack.sh"
    else
        echo "ERROR: Invalid client type option."
        echo "Valid options are platform or openstack."
        exit 1
    fi
else
    CONFIG_TYPE="platform"
    CONF_FILE="remote_client_platform.sh"
fi

# If custom output RC_FILE is given, use that instead
if [[ $custom_conf_file -eq 1 ]]; then
    CONF_FILE=$CUSTOM_CONF_FILE
fi

# Check if input RC file path actually exists
if [[ ! -f "$RC_FILE" ]]; then
    echo "ERROR: File at location $RC_FILE does NOT exist"
    exit 1
fi

# Check if input RC file path actually exists
if [[ "$CONFIG_TYPE" = "platform" && ! -f "$K8S_FILE" ]]; then
    echo "ERROR: File at location $K8S_FILE does NOT exist"
    exit 1
fi

# Delete previous config file
rm -f $CONF_FILE

# We output a complete path for the scripts, so first determine
# if the given path is relative or absolute
if [[ $RC_FILE = '/'* ]]; then
    echo "source $RC_FILE" >> $CONF_FILE
else
    echo "source $(pwd)/$RC_FILE" >> $CONF_FILE
fi

echo "export CONFIG_TYPE=${CONFIG_TYPE}" >> $CONF_FILE

if [[ $WORK_DIR = '/'* ]]; then
    echo "export OSC_WORKDIR=${WORK_DIR}" >> $CONF_FILE
else
    echo "export OSC_WORKDIR=$(pwd)/${WORK_DIR}" >> $CONF_FILE
fi

if [[ "$CONFIG_TYPE" = "platform" ]]; then
    if [[ $K8S_FILE = '/'* ]]; then
        echo "export K8S_CONFIG_FILE=${K8S_FILE}" >> $CONF_FILE
    else
        echo "export K8S_CONFIG_FILE=$(pwd)/${K8S_FILE}" >> $CONF_FILE
    fi
fi

echo "source ${PATH_TO_SCRIPT}/$ALIAS_FILE" >> $CONF_FILE
echo "source ${PATH_TO_SCRIPT}/$TAG_FILE" >> $CONF_FILE
