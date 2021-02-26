FROM phx.ocir.io/weblogick8s/wdt/jenkinsslave:wls12213

ENV PYTHON_BASE=/u01/jython \
    VERIFY_HOME=/u01/verify \
	WLSDEPLOY_BASE=/u01/wlsdeploy
	
ENV	TESTFILES_HOME=${VERIFY_HOME}/testfiles \
	WLSDEPLOY_HOME=${WLSDEPLOY_BASE}/weblogic-deploy \
	TEST_HOME=${VERIFY_HOME}/alias-test/src/test \
	PYTHON_HOME=${PYTHON_BASE} \
	MODE=online \
	WLS_VERSION=12.2.1.4.0
	
COPY --chown=oracle jython-installer-2.7.2.jar ${PYTHON_BASE}/
COPY --chown=oracle alias-test ${VERIFY_HOME}/alias-test
COPY --chown=oracle alias-test/src/test/python ${VERIFY_HOME}/alias-test/src/test/python
COPY --chown=oracle alias-test/src/test/resources ${VERIFY_HOME}/alias-test/src/test/resources
COPY --chown=oracle alias-test/src/test/resources ${VERIFY_HOME}/alias-test/src/test/resources/
COPY --chown=oracle generatedfiles.zip ${TESTFILES_HOME}/

USER oracle
RUN cd ${TESTFILES_HOME} && \
    ls && \
    unzip generatedfiles.zip && \
	cd ${PYTHON_BASE} && \
	ls && \
	unzip jython-installer-2.7.2.jar && \
	cd ${TEST_HOME}/resources && \
	sed -i 's/\r//g' runIntegrationTest.sh && \
	sed -i 's/\r//g' doVerifyOnline.sh && \
	sed -i 's/\r//g' doVerifyOffline.sh && \
	chmod 777 *.sh && \
	mkdir ${WLSDEPLOY_BASE} && \
	chmod 777 ${WLSDEPLOY_BASE}

	
USER oracle
WORKDIR ${TEST_HOME}/python
CMD  /u01/verify/alias-test/src/test/resources/runIntegrationTest.sh -wls_version ${WLS_VERSION} -testfiles_path ${TESTFILES_HOME}
