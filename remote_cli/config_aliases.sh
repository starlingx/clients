#!/bin/bash

#
# Copyright (c) 2019 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

# The script may be called from locations other
# than its own folder, so build the full path to
# the script.
if [[ $BASH_SOURCE = '/'* ]]; then
    PATH_TO_SCRIPT="$(dirname $BASH_SOURCE)"
else
    PATH_TO_SCRIPT="$(pwd)/$(dirname $BASH_SOURCE)"
fi

if [[ "$CONFIG_TYPE" = "platform" ]]; then
    SERVICES="system fm openstack kubectl helm"
    alias "platform_shell"="${PATH_TO_SCRIPT}/client_wrapper.sh /bin/bash"
else
    SERVICES="openstack nova cinder glance heat"
    alias "application_shell"="${PATH_TO_SCRIPT}/client_wrapper.sh /bin/bash"
fi

for service in $SERVICES; do
    alias "$service"="${PATH_TO_SCRIPT}/client_wrapper.sh $service"
done
