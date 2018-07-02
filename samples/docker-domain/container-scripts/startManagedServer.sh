#!/bin/bash
#
#Copyright (c) 2014-2018 Oracle and/or its affiliates. All rights reserved.
#
#Licensed under the Universal Permissive License v 1.0 as shown at http://oss.oracle.com/licenses/upl.
#
# Start the Domain.

#Define DOMAIN_HOME
export DOMAIN_HOME=/u01/oracle/user_projects/domains/$DOMAIN_NAME

mkdir -p $DOMAIN_HOME/servers/$MS_NAME/security
echo username=$ADMIN_USER > $DOMAIN_HOME/servers/$MS_NAME/security/boot.properties
echo password=$ADMIN_PASSWORD >> $DOMAIN_HOME/servers/$MS_NAME/security/boot.properties

# Start Managed Server and tail the logs
${DOMAIN_HOME}/bin/startManagedWebLogic.sh $MS_NAME http://$ADMIN_HOST:$ADMIN_PORT
touch ${DOMAIN_HOME}/servers/$MS_NAME/logs/${MS_NAME}.log
tail -f ${DOMAIN_HOME}/servers/$MS_NAME/logs/${MS_NAME}.log &

childPID=$!
wait $childPID
