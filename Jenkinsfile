node {
    checkout scm

    docker.image('phx.ocir.io/weblogick8s/database/enterprise:12.2.0.1-slim') { c->
        docker.image('phx.ocir.io/weblogick8s/database/enterprise:12.2.0.1-slim').inside("--link ${c.id}:db") {
            sh '''
                echo "waiting for the db to be ready"
                sleep 3m
            '''
        }
        docker.image('phx.ocir.io/weblogick8s/wdt/jenkinsslave:wls12213').withRun('-u jenkins:oracle').inside("--link ${c.id}:db") {
            sh '''
                echo "PATH = ${PATH}"
                echo "JAVA_HOME = ${JAVA_HOME}"
                echo "M2_HOME = ${M2_HOME}"
                mvn --version
                mvn -B -DskipTests -Dunit-test-wlst-dir=/u01/oracle/oracle_common/common/bin -Dmw_home=/u01/oracle clean package
            '''
        }
    }
}
