pipeline {
    agent {
        docker {
            alwaysPull true
            reuseNode true
            image 'phx.ocir.io/weblogick8s/wdt/jenkinsslave:wls12213'
            args '--user jenkins:oracle'
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
                    mvn -B -DskipTests -Dunit-test-wlst-dir=${WLST_DIR} clean package
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

            -Dmw_home=/u01/oracle -Dfmw_home=/u01/oracle
        }
        stage ('Verify') {
            steps {
                sh 'mvn -Dunit-test-wlst-dir=${WLST_DIR} -Dmw_home=${ORACLE_HOME} -Dfmw_home=${ORACLE_HOME} verify'
            }
        }
    }
}