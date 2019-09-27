node {
    checkout scm

    def dbimage = docker.image('phx.ocir.io/weblogick8s/database/enterprise:12.2.0.1-slim')
    def osimage = docker.image('phx.ocir.io/weblogick8s/wdt/jenkinsslave:wls12213')

    dbimage.withRun('-e "DB_PDB=InfraPDB1" -e "DB_DOMAIN=us.oracle.com" -e "DB_BUNDLE=basic"') { c ->
        dbimage.inside("--link ${c.id}:db") {
            /* Wait until db service is up */
            sh '''
                echo "waiting for the db to be ready ..."
                sleep 3
            '''
        }
        osimage.inside("--link ${c.id}:db") {
            /*
             * Run some tests which require MySQL, and assume that it is
             * available on the host name `db`
             */
            sh '''
                echo "PATH = ${PATH}"
                echo "JAVA_HOME = ${JAVA_HOME}"
                echo "M2_HOME = ${M2_HOME}"
                mvn --version
                mvn -B -DskipTests -Dunit-test-wlst-dir=/u01/oracle/oracle_common/common/bin -Dmw_home=/u01/oracle clean package
            '''
        }
    }
}