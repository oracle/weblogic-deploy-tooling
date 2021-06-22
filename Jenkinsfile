pipeline {
    agent any

    triggers {
        // timer trigger for "nightly build" on main branch
        cron( env.BRANCH_NAME.equals('main') ? 'H H(0-3) * * 1-5' : '')
    }

    stages {
        stage ('Environment') {
            tools {
                maven 'maven-3.6.0'
                jdk 'jdk8'
            }
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
            tools {
                maven 'maven-3.6.0'
                jdk 'jdk8'
            }
            steps {
                sh '''
                    mvn -B -DskipTests clean package
                '''
            }
        }
        stage ('Test') {
            agent {
                docker {
                    alwaysPull true
                    reuseNode true
                    image 'phx.ocir.io/weblogick8s/wdt/jenkinsslave:wls12213'
                    args '-u jenkins -v /var/run/docker.sock:/var/run/docker.sock'
                }
            }
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
            agent {
                docker {
                    alwaysPull true
                    reuseNode true
                    image 'phx.ocir.io/weblogick8s/wdt/jenkinsslave:wls12213'
                    args '-u jenkins -v /var/run/docker.sock:/var/run/docker.sock'
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
       stage ('Alias Test') {
            // only run this stage when triggered by a cron timer and the commit does not have []skip-ci in the message
            // for example, only run integration tests during the timer triggered nightly build
            when {
                allOf {
                    triggeredBy 'TimerTrigger'
                    branch "main"
                }
            }
            matrix {
                // run verify tests for each version in parallel.
                axes {
                    axis {
                        name 'WLS_VERSION'
                        values '10.3.6.0', '12.1.1.0', '12.1.2.0.0', '12.1.3.0.0', '12.2.1.0.0', '12.2.1.1.0', '12.2.1.2.0', '12.2.1.3.0', '12.2.1.4.0', '14.1.1.0.0', '14.1.2.0.0'
                    }
                }
                stages {
                    stage('Test') {
                        agent {
                            docker {
                                alwaysPull true
                                reuseNode true
                                image 'phx.ocir.io/weblogick8s/wdt/jenkinsslave:aliastest'
                                args '-u jenkins -v /var/run/docker.sock:/var/run/docker.sock'
                            }
                        }
                        steps {
                           sh  '/u01/verify/alias-test/src/test/resources/runIntegrationTest.sh -wls_version ${WLS_VERSION} -testfiles_path /u01/verify/testfiles;cp /u01/verify/testfiles/report* $WORKSPACE'
                        }
                    }
                }

            }
            // after all sets are complete, the job will continue here.
            post {
               always {
                 archiveArtifacts artifacts: 'report*', fingerprint: true
               }
            }
        }
        stage ('Save Nightly Installer'){
            when {
                allOf {
                    triggeredBy 'TimerTrigger'
                    branch "main"
                }
            }
            steps {
                sh '''
                    oci os object put --namespace=weblogick8s --bucket-name=wko-system-test-files --config-file=/dev/null --auth=instance_principal --force --file=installer/target/weblogic-deploy.zip --name=weblogic-deploy-main.zip
                '''
            }
        }

    }
}
