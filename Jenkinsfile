pipeline {
    agent {
        docker {
            alwaysPull true
            reuseNode true
            image 'phx.ocir.io/weblogick8s/wdt/jenkinsslave:wls12213'
            args '-u jenkins -v /var/run/docker.sock:/var/run/docker.sock'
        }
    }

    triggers {
        // timer trigger for "nightly build" on master branch
        cron( env.BRANCH_NAME.equals('master') ? 'H H(0-3) * * 1-5' : '')
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
                anyOf {
                    changeRequest()
                    triggeredBy 'TimerTrigger'
                    tag "release-*"
                }
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
        stage ('Save Nightly Installer'){
            when {
                allOf {
                    triggeredBy 'TimerTrigger'
                    branch "master"
                }
            }
            steps {
                sh '''
                    oci os object put --namespace=weblogick8s --bucket-name=wko-system-test-files --config-file=/dev/null --auth=instance_principal --force --file=installer/target/weblogic-deploy.zip --name=weblogic-deploy-master.zip
                '''
            }
        }

    }
}
