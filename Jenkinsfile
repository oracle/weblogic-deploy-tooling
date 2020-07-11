pipeline {
    agent {
        docker {
            label "VM.Standard2.2"
            alwaysPull true
            reuseNode true
            image 'phx.ocir.io/weblogick8s/wdt/jenkinsslave:wls12213'
            args '-u jenkins -v /var/run/docker.sock:/var/run/docker.sock'
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
                sh '''
                    mvn -B -DskipTests clean package
                '''
            }
        }
        stage ('Test') {
            steps {
                sh 'mvn -Dunit-test-wlst-dir=${WLST_DIR} test'
            }
            post {
                always {
                    junit 'core/target/surefire-reports/*.xml'
                }
            }
        }
        stage ('Verify') {
            when {
                changeRequest()
            }
            steps {
                sh 'mvn -P system-test -Dmw_home=${ORACLE_HOME} test-compile failsafe:integration-test'
            }
            post {
                always {
                    junit 'system-test/target/failsafe-reports/*.xml'
                }
            }
        }
    }
}
