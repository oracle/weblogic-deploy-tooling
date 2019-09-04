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
                    ls -al /root/.m2
                '''
            }
        }
        stage ('Build') {
            steps {
                sh 'mvn -B -DskipTests clean package'
            }
        }
    }
}