node {
    checkout scm

    def dbimage = docker.image('mysql:5')
    def osimage = docker.image('centos:7')

    dbimage.withRun('-e "MYSQL_ROOT_PASSWORD=my-secret-pw"') { c ->
        dbimage.inside("--link ${c.id}:db") {
            /* Wait until mysql service is up */
            sh 'while ! mysqladmin ping -hdb --silent; do sleep 1; done'
        }
        osimage.inside("--link ${c.id}:db") {
            /*
             * Run some tests which require MySQL, and assume that it is
             * available on the host name `db`
             */
            sh "echo ${c.id}"
        }
    }
}