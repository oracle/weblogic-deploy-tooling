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
#            --force-rm=true \
#            -t 12213-domain-wdt .
#
# Pull base image
# ---------------
# FROM store/oracle/weblogic:12.2.1.3
FROM oracle/weblogic:12.2.1.3-developer

# Maintainer
# ----------
MAINTAINER Richard Killen <richard.killen@oracle.com>

ARG WDT_MODEL
ARG WDT_ARCHIVE
ARG WDT_VARIABLE

# WLS Configuration
# ---------------------------
ENV ORACLE_HOME=/u01/oracle \
    PROPERTIES_FILE_DIR="${ORACLE_HOME}/properties" \
    SCRIPT_FILE=${ORACLE_HOME}/createAndStartWLSDomain.sh \
    DOMAIN_HOME_PARENT=${ORACLE_HOME}/user_projects/domains \
    DOMAIN_HOME="${DOMAIN_HOME_PARENT}/${DOMAIN_NAME}-base_domain}" \
    PATH=$PATH:${ORACLE_HOME}/oracle_common/common/bin:${ORACLE_HOME}/wlserver/common/bin:${DOMAIN_HOME}/bin:${ORACLE_HOME}

# WDT install and WDT user files
# COPY
# ------------------------------------------------------------
ENV COPY_PROPERTIES="poperties/docker_build" \
    INSTALL_HOME="/u01" \
    WDT_MODEL="$WDT_MODEL" \
    WDT_ARCHIVE="$WDT_ARCHIVE" \
    WDT_VARIABLE="WDT_VARIABLE"

# Add files required to build this image
COPY container-scripts/* ${INSTALL_HOME}
COPY weblogic-deploy.zip ${INSTALL_HOME}

USER root
RUN chmod +xw ${INSTALL_HOME}/*.sh && \
    mkdir +xwr ${PROPERTIES_FILE_DIR} && \
    chown -R oracle:oracle ${PROPERTIES_FILE_DIR} && \
    mkdir -p $DOMAIN_HOME_PARENT && \
    chown -R oracle:oracle $DOMAIN_HOME_PARENT && \
    chmod -R a+xwr $DOMAIN_HOME_PARENT

COPY ${WDT_MODEL} ${WDT_ARCHIVE} ${WDT_VARIABLE} ${COPY_PROPERTIES}/*.properties ${PROPERTIES_FILE_DIR}/

# export domain and server specific variables into environment
RUN /bin/sh ${INSTALL_HOME}/setEnv.sh

# Default values - these values will be replaced by the values in the properties file
# The DOMAIN_NAME in the variable file can be different than the DOMAIN NAME in the DOMAIN_HOME
ENV DOMAIN_NAME="${DOMAIN_NAME:-base-domain}" \
    ADMIN_HOST="${ADMIN_HOST:-wlsadmin}" \
    ADMIN_PORT="${ADMIN_PORT:-7001}" \
    MS_PORT="${MS_PORT:-8001}" \
    DEBUG_PORT="${DEBUG_PORT:-8453}" \
    DOMAIN_HOME="${DOMAIN_PARENT}\${DOMAIN
    PATH=${PATH}:

# Run the WDT createDomain to create the domain home in the image
RUN cd ${INSTALL_HOME} && \
    $JAVA_HOME/bin/jar xf ${INSTALL_HOME_BASE}/weblogic-deploy.zip && \
    chmod +xw ${INSTALL_HOME_BASE}/weblogic-deploy/bin/*.sh && \
    chmod -R +xw ${INSTALL_HOME_BASE}/weblogic-deploy/lib/python && \
    if [ -n "$WDT_MODEL" ]; then MODEL_OPT="-archive_file ${INSTALL_HOME_BASE}/$WDT_ARCHIVE"; fi && \
    if [ -n "$WDT_ARCHIVE" ]; then ARCHIVE_OPT="-archive_file ${INSTALL_HOME_BASE}/$WDT_ARCHIVE"; fi && \
    if [ -n "$WDT_VARIABLE" ]; then VARIABLE_OPT="-variable_file ${INSTALL_HOME_BASE}/$WDT_VARIABLE"; fi && \
    /u01/weblogic-deploy/bin/createDomain.sh \
        -oracle_home $ORACLE_HOME \
        -java_home ${JAVA_HOME} \
        -domain_home ${DOMAIN_HOME} \
        -domain_type WLS \
        $VARIABLE_OPT \
        $MODEL_OPT \
        $ARCHIVE_OPT && \
    rm ${PROPERTIES_FILE_DIR}/*

VOLUME $PRE_DOMAIN_HOME
# Expose Node Manager default port, and also default for admin and managed server
EXPOSE $ADMIN_PORT $MS_PORT $DEBUG_PORT

USER oracle
WORKDIR $ORACLE_HOME

# Define default command to start bash.
CMD ["${ORACLE_HOME}/startWLSDomain.sh"]
