pipeline {
    agent any

    environment {
        alias_test_job_name = 'wdt-alias-test-verify'
    }

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
                sh 'env|sort'
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
                    image 'phx.ocir.io/weblogick8s/wdt/jenkins-slave:122130'
                    args '-u jenkins -v /var/run/docker.sock:/var/run/docker.sock'
                }
            }
            steps {
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
                    image 'phx.ocir.io/weblogick8s/wdt/jenkins-slave:122130'
                    args '-u jenkins -v /var/run/docker.sock:/var/run/docker.sock'
                }
            }
            steps {
                sh 'mvn -B -DskipITs=false -Dmw_home=${ORACLE_HOME} -Ddb.use.container.network=true install'
            }
        }
        stage ('Analyze') {
            when {
                anyOf {
                    changeRequest()
                    branch "main"
                }
            }
            tools {
                maven 'maven-3.6.0'
                jdk 'jdk11'
            }
            steps {
                withSonarQubeEnv('SonarCloud') {
                    withCredentials([string(credentialsId: 'encj_github_token', variable: 'GITHUB_TOKEN')]) {
                        runSonarScanner()
                    }
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
                    oci os object put --namespace=weblogick8s --bucket-name=wko-system-test-files --config-file=/dev/null --auth=instance_principal --force --file=installer/target/weblogic-deploy.zip --name=weblogic-deploy-main.zip
                '''
            }
        }
    }
}

void runSonarScanner() {
    def changeUrl = env.GIT_URL.split("/")
    def org = changeUrl[3]
    def repo = changeUrl[4].substring(0, changeUrl[4].length() - 4)
    if (env.CHANGE_ID != null) {
        sh "mvn -B sonar:sonar \
            -Dsonar.projectKey=${org}_${repo} \
            -Dsonar.pullrequest.provider=GitHub \
            -Dsonar.pullrequest.github.repository=${org}/${repo} \
            -Dsonar.pullrequest.key=${env.CHANGE_ID} \
            -Dsonar.pullrequest.branch=${env.CHANGE_BRANCH} \
            -Dsonar.pullrequest.base=${env.CHANGE_TARGET}"
    } else {
       sh "mvn -B sonar:sonar \
           -Dsonar.projectKey=${org}_${repo} \
           -Dsonar.branch.name=${env.BRANCH_NAME}"
    }
}
