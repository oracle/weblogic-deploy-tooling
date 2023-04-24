pipeline {
    agent any

    environment {
        wdt_tenancy = "${env.WKT_TENANCY}"
        alias_test_job_name = 'wdt-alias-test-verify'
        jenkins_uid = sh(returnStdout: true, script: 'id -u').trim()
        jenkins_gid = sh(returnStdout: true, script: 'id -g').trim()
        docker_gid = sh(returnStdout: true, script: 'getent group docker | cut -d: -f3').trim()
    }
    triggers {
        // timer trigger for "nightly build" on main branch
        cron( env.BRANCH_NAME.equals('main') ? 'H H(0-3) * * 1-5' : '')
    }
    stages {
        stage ('Environment') {
            tools {
                maven 'maven-3.8.7'
                jdk 'jdk8'
            }
            steps {
                sh 'env|sort'
                sh 'mvn -v'
            }
        }
        stage ('Build') {
            tools {
                maven 'maven-3.8.7'
                jdk 'jdk8'
            }
            steps {
                // Using Maven batch mode to suppress download progress lines in Jenkins output
                //
                withMaven(globalMavenSettingsConfig: 'wkt-maven-settings-xml', publisherStrategy: 'EXPLICIT') {
                    sh "mvn -B -DskipTests clean package"
                }
            }
        }
        stage ('Test') {
            agent {
                docker {
                    alwaysPull true
                    reuseNode true
                    image 'phx.ocir.io/devweblogic/wdt/jenkins-slave:122130'
                    args "-u ${jenkins_uid}:${jenkins_gid} --group-add oracle --group-add opc -v /var/run/docker.sock:/var/run/docker.sock"
                }
            }
            steps {
                // Using Maven batch mode to suppress download progress lines in Jenkins output
                //
                sh 'mvn -B -Dunit-test-wlst-dir=${WLST_DIR} test'
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
                    image "phx.ocir.io/${wdt_tenancy}/wdt/jenkins-slave:122130"
                    args "-u ${jenkins_uid}:${docker_gid} --group-add oracle --group-add opc --group-add docker -v /var/run/docker.sock:/var/run/docker.sock"
                }
            }
            steps {
                // Using Maven batch mode to suppress download progress lines in Jenkins output
                //
                sh 'mvn -B -DskipITs=false -Dmw_home=${ORACLE_HOME} -Ddb.use.container.network=true install'
            }
        }
        stage ('Sync') {
            when {
                branch 'main'
                anyOf {
                    not { triggeredBy 'TimerTrigger' }
                    tag 'release-*'
                }
            }
            steps {
                build job: "wkt-sync", parameters: [ string(name: 'REPOSITORY', value: 'weblogic-deploy-tooling') ]
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
            steps {
                build job: "${alias_test_job_name}"
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
                    oci os object put --namespace=${wdt_tenancy} --bucket-name=wko-system-test-files --force \
                        --auth=instance_principal --file=installer/target/weblogic-deploy.zip \
                        --name=weblogic-deploy-main.zip
                '''
            }
        }
    }
}
