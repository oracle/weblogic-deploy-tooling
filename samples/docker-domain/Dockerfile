#Copyright (c) 2014-2018 Oracle and/or its affiliates. All rights reserved.
#
#Licensed under the Universal Permissive License v 1.0 as shown at http://oss.oracle.com/licenses/upl.
#
# ORACLE DOCKERFILES PROJECT
# --------------------------
# This Dockerfile extends the Oracle WebLogic image by creating a sample domain.
#
# Util scripts are copied into the image enabling users to plug NodeManager
# automatically into the AdminServer running on another container.
#
# HOW TO BUILD THIS IMAGE
# -----------------------
# Put all downloaded files in the same directory as this Dockerfile
# Build the deployment archive file using the build-archive.sh script.
#      $ ./build-archive.sh
#
# Run:
#      $ sudo docker build \
#            --build-arg WDT_MODEL=simple-topology.yaml \
#            --build-arg WDT_ARCHIVE=archive.zip \
#            --build-arg WDT_VARIABLE=simple-topology.properties \
#            --force-rm=true \
#            -t 12213-domain-wdt .
#
# Pull base image
# ---------------
# FROM store/oracle/weblogic:12.2.1.3
FROM store/oracle/weblogic:12.2.1.3-dev

# Maintainer
# ----------
MAINTAINER Richard Killen <richard.killen@oracle.com>

ARG WDT_ARCHIVE
ARG WDT_VARIABLE
ARG WDT_MODEL
ARG ADMIN_HOST
ARG ADMIN_PORT
ARG MS_PORT
ARG DOMAIN_DIR
ARG DEBUG_PORT

# WLS Configuration - oracle home and domain home
# The boot.properties will be created under the DOMAIN_HOME when the AdminServer container is run 
# ---------------------------
ENV ORACLE_HOME=/u01/oracle \
    PROPERTIES_FILE_DIR="$ORACLE_HOME/properties" \
    DOMAIN_PARENT="${ORACLE_HOME}/user_projects/domains" \
    DOMAIN_HOME="${DOMAIN_PARENT}/${DOMAIN_DIR:-TESTDOMAON}" \
    ADMIN_HOST="${ADMIN_HOST:-wlsadmin}" \
    ADMIN_PORT="${ADMIN_PORT:-7001}" \
    MS_PORT="${MS_PORT:-8001}" \
    DEBUG_PORT="${DEBUG_PORT:-8453}" \
    PATH=$PATH:${ORACLE_HOME}/oracle_common/common/bin:${ORACLE_HOME}/wlserver/common/bin:$DOMAIN_HOME/bin:${ORACLE_HOME}
    
# WDT install and WDT user files
# ------------------------------------------------------------
ENV WDT_HOME="/u01" \
    SCRIPT_HOME="${ORACLE_HOME}" 

# Add files required to build this image and run a container from the image
COPY weblogic-deploy.zip ${WDT_HOME}
COPY container-scripts/* ${SCRIPT_HOME}/

# Create the properties file directory and the domain home parent with the correct permissions / owner. 
# Unzip and install the WDT image.
# Export variable file values into the environment
USER root
RUN chmod +xw ${SCRIPT_HOME}/*.sh && \ 
    mkdir -p +xwr ${PROPERTIES_FILE_DIR} && \
    mkdir -p $DOMAIN_PARENT && \
    chmod -R a+xwr $DOMAIN_PARENT && \
    cd ${WDT_HOME} && \
    $JAVA_HOME/bin/jar xf ./weblogic-deploy.zip && \
    rm weblogic-deploy.zip && \
    chmod +xw weblogic-deploy/bin/*.sh && \
    chmod -R +xw weblogic-deploy/lib/python  

# Copy the WDT model, archive file, variable file and credential secrets to the property file directory.
# These files will be removed after the image is built.
# Be sure to build with --force-rm to eliminate this container layer

COPY ${WDT_MODEL} ${WDT_ARCHIVE} ${WDT_VARIABLE} properties/docker_build/*.properties ${PROPERTIES_FILE_DIR}/
         
# Create the domain home in the docker image.
#
# The create domain tool creates a domain at the DOMAIN_HOME location
# The domain name is set using the value in the model / variable files 
# The domain name can be different from the DOMAIN_HOME domain folder name.

ENV WDT_HOME=$WDT_HOME/weblogic-deploy 

# Set WORKDIR for @@PWD@@ global token in model file
WORKDIR $ORACLE_HOME
RUN if [ -n "$WDT_MODEL" ]; then MODEL_OPT="-model_file $PROPERTIES_FILE_DIR/$WDT_MODEL"; fi && \
    if [ -n "$WDT_ARCHIVE" ]; then ARCHIVE_OPT="-archive_file $PROPERTIES_FILE_DIR/$WDT_ARCHIVE"; fi && \
    if [ -n "$WDT_VARIABLE" ]; then VARIABLE_OPT="-variable_file $PROPERTIES_FILE_DIR/$WDT_VARIABLE"; fi && \ 
    ${WDT_HOME}/bin/createDomain.sh \
        -oracle_home ${ORACLE_HOME} \
        -java_home ${JAVA_HOME} \
        -domain_home ${DOMAIN_HOME} \
        -domain_type WLS \
        $VARIABLE_OPT  \
        $MODEL_OPT \
        $ARCHIVE_OPT && \
    chown -R oracle:oracle ${DOMAIN_PARENT} && \
    rm -rf ${PROPERTIES_FILE_DIR} 

VOLUME $DOMAIN_HOME

# Expose admin server, managed server port and domain debug port
EXPOSE $ADMIN_PORT $MS_PORT $DEBUG_PORT

# Define default command to start bash.
WORKDIR $SCRIPT_HOME
USER oracle

CMD ["./startWLSDomain.sh"]
