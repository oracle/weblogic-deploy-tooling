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
                sh pwd
                sh 'mvn -B -DskipTests -Dunit-test-wlst-dir=${WLST_DIR} clean package'
            }
        }
        stage ('Test') {
            steps {
                sh pwd
                sh 'mvn -Dunit-test-wlst-dir=${WLST_DIR}  test'
            }
            post {
                always {
                    junit 'imagetool/target/surefire-reports/*.xml'
                }
            }
        }
    }
}