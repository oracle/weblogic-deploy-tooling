pipeline {
    agent {
        docker {
            alwaysPull true
            image 'phx.ocir.io/weblogick8s/wdt/jenkinsslave:wls12213'
            args '-v /root/.m2:/root/.m2'
        }
    }

    stages {
        stage ('Environment') {
            steps {
                sh '''
                    echo "PATH = ${PATH}"
                    echo "JAVA_HOME = ${JAVA_HOME}"
                    echo "M2_HOME = ${M2_HOME}"
                    whoami
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