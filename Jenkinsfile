pipeline {
    agent {
        docker {
            alwaysPull true
            image 'phx.ocir.io/weblogick8s/wdt/jenkinsslave:wls12213'
        }
    }

    stages {
        stage ('Environment') {
            steps {
                sh '''
                    echo "PATH = ${PATH}"
                    echo "JAVA_HOME = ${JAVA_HOME}"
                    echo "M2_HOME = ${M2_HOME}"
                    mvn --version
                '''
            }
        }
        stage ('Build') {
            steps {
                sh 'mvn -B -DskipTests -Dunit-test-wlst-dir=${ORACLE_HOME}/oracle_common/common/bin clean package'
            }
        }
    }
}