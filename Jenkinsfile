node {
    checkout scm

    docker.image('phx.ocir.io/weblogick8s/wdt/jenkinsslave:wls12213').withRun('-u jenkins:oracle') { c ->
        sh '''
            echo "PATH = ${PATH}"
            echo "JAVA_HOME = ${JAVA_HOME}"
            echo "M2_HOME = ${M2_HOME}"
            mvn --version
            mvn -B -DskipTests -Dunit-test-wlst-dir=${WLST_DIR} clean package
        '''

    }
}
