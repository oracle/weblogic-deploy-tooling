/*
 * Copyright (c) 2023, Oracle Corporation and/or its affiliates.  All rights reserved.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.tool;

public class ArchiveHelperTestConstants {
    static final String[] MY_APP_WAR_CONTENTS = new String[] {
        "wlsdeploy/applications/my-app.war"
    };

    static final String[] MY_APP_DEPLOYMENT_PLAN_CONTENTS = new String[] {
        "wlsdeploy/applications/my-app.xml"
    };

    static final String[] MY_OTHER_APP_WAR_CONTENTS = new String[] {
        "wlsdeploy/applications/my-other-app.war"
    };

    static final String[] MY_OTHER_APP_DIR_CONTENTS = new String[] {
        "wlsdeploy/applications/my-other-app/",
        "wlsdeploy/applications/my-other-app/META-INF/",
        "wlsdeploy/applications/my-other-app/META-INF/maven/",
        "wlsdeploy/applications/my-other-app/META-INF/maven/oracle.jcs.lifecycle/",
        "wlsdeploy/applications/my-other-app/META-INF/maven/oracle.jcs.lifecycle/get-listen-address-app/",
        "wlsdeploy/applications/my-other-app/META-INF/maven/oracle.jcs.lifecycle/get-listen-address-app/pom.properties",
        "wlsdeploy/applications/my-other-app/META-INF/maven/oracle.jcs.lifecycle/get-listen-address-app/pom.xml",
        "wlsdeploy/applications/my-other-app/META-INF/MANIFEST.MF",
        "wlsdeploy/applications/my-other-app/WEB-INF/",
        "wlsdeploy/applications/my-other-app/WEB-INF/classes/",
        "wlsdeploy/applications/my-other-app/WEB-INF/classes/com/",
        "wlsdeploy/applications/my-other-app/WEB-INF/classes/com/oracle/",
        "wlsdeploy/applications/my-other-app/WEB-INF/classes/com/oracle/platform/",
        "wlsdeploy/applications/my-other-app/WEB-INF/classes/com/oracle/platform/GetListenAddressServlet.class",
        "wlsdeploy/applications/my-other-app/WEB-INF/classes/com/oracle/platform/ListenAddressAndPort.class",
        "wlsdeploy/applications/my-other-app/WEB-INF/web.xml",
        "wlsdeploy/applications/my-other-app/WEB-INF/weblogic.xml"
    };

    static final String[] APPLICATIONS_CONTENT = mergeStringArrays(
        new String[] { "wlsdeploy/applications/" },
        MY_OTHER_APP_DIR_CONTENTS,
        MY_APP_WAR_CONTENTS,
        MY_APP_DEPLOYMENT_PLAN_CONTENTS,
        MY_OTHER_APP_WAR_CONTENTS
    );

    static final String[] CLASSPATH_LIB_BAR_JAR_CONTENTS = new String[] {
        "wlsdeploy/classpathLibraries/bar.jar"
    };

    static final String[] CLASSPATH_LIBS_CONTENT = new String[] {
        "wlsdeploy/classpathLibraries/",
        "wlsdeploy/classpathLibraries/bar.jar"
    };

    static final String[] COHERENCE_MYCLUSTER_CONFIG_FILE_CONTENTS = new String[] {
        "wlsdeploy/coherence/mycluster/cache-config.xml"
    };

    static final String[] COHERENCE_MYCLUSTER_PERSISTENT_DIR_CONTENTS = new String[] {
        "wlsdeploy/coherence/mycluster/active/",
        "wlsdeploy/coherence/mycluster/snapshot/",
        "wlsdeploy/coherence/mycluster/trash/"
    };

    static final String[] COHERENCE_MYCLUSTER_CONTENTS = mergeStringArrays(
        new String[] { "wlsdeploy/coherence/mycluster/" },
        COHERENCE_MYCLUSTER_PERSISTENT_DIR_CONTENTS,
        COHERENCE_MYCLUSTER_CONFIG_FILE_CONTENTS
    );

    static final String[] COHERENCE_MYCLUSTER2_CONFIG_FILE_CONTENTS = new String[] {
        "wlsdeploy/coherence/mycluster2/cache-config.xml"
    };

    static final String[] COHERENCE_MYCLUSTER2_PERSISTENT_DIR_CONTENTS = new String[] {
        "wlsdeploy/coherence/mycluster2/snapshot/"
    };

    static final String[] COHERENCE_MYCLUSTER2_CONTENTS = mergeStringArrays(
        new String[] { "wlsdeploy/coherence/mycluster2/" },
        COHERENCE_MYCLUSTER2_PERSISTENT_DIR_CONTENTS,
        COHERENCE_MYCLUSTER2_CONFIG_FILE_CONTENTS
    );

    static final String[] COHERENCE_CONTENT = mergeStringArrays(
        new String[] { "wlsdeploy/coherence/" },
        COHERENCE_MYCLUSTER_CONTENTS,
        COHERENCE_MYCLUSTER2_CONTENTS
    );

    static final String[] MIME_MAPPING_PROPERTIES_CONTENTS = new String[] {
        "wlsdeploy/config/mimemappings.properties"
    };

    static final String[] MIME_MAPPINGS_CONTENT = new String[] {
        "wlsdeploy/config/",
        "wlsdeploy/config/mimemappings.properties"
    };

    static final String[] CUSTOM_MYDIR_BAR_PROPERTIES_CONTENTS = new String[] {
        "wlsdeploy/custom/mydir/bar.properties"
    };

    static final String[] CUSTOM_MYDIR_CONTENTS = mergeStringArrays(
        new String[] { "wlsdeploy/custom/mydir/" },
        CUSTOM_MYDIR_BAR_PROPERTIES_CONTENTS
    );

    static final String[] CUSTOM_FOO_PROPERTIES_CONTENTS = {
        "wlsdeploy/custom/foo.properties"
    };

    static final String[] CUSTOM_CONTENT = mergeStringArrays(
        new String[] { "wlsdeploy/custom/" },
        CUSTOM_MYDIR_CONTENTS,
        CUSTOM_FOO_PROPERTIES_CONTENTS
    );

    static final String[] DATABASE_WALLET_RCU_CONTENTS = new String[] {
        "wlsdeploy/dbWallets/rcu/",
        "wlsdeploy/dbWallets/rcu/cwallet.sso",
        "wlsdeploy/dbWallets/rcu/ewallet.p12",
        "wlsdeploy/dbWallets/rcu/ewallet.pem",
        "wlsdeploy/dbWallets/rcu/keystore.jks",
        "wlsdeploy/dbWallets/rcu/ojdbc.properties",
        "wlsdeploy/dbWallets/rcu/README",
        "wlsdeploy/dbWallets/rcu/sqlnet.ora",
        "wlsdeploy/dbWallets/rcu/tnsnames.ora",
        "wlsdeploy/dbWallets/rcu/truststore.jks"
    };

    static final String[] DATABASE_WALLET_WALLET1_CONTENTS = new String[] {
        "wlsdeploy/dbWallets/wallet1/",
        "wlsdeploy/dbWallets/wallet1/atpwallet.zip"
    };

    static final String[] DATABASE_WALLETS_CONTENT = mergeStringArrays(
        new String[] { "wlsdeploy/dbWallets/" },
        DATABASE_WALLET_RCU_CONTENTS,
        DATABASE_WALLET_WALLET1_CONTENTS
    );

    static final String[] DOMAIN_BIN_SET_USER_OVERRIDES_SH_CONTENTS = new String[] {
        "wlsdeploy/domainBin/setUserOverrides.sh"
    };

    static final String[] DOMAIN_BIN_CONTENT = mergeStringArrays(
        new String[] { "wlsdeploy/domainBin/" },
        DOMAIN_BIN_SET_USER_OVERRIDES_SH_CONTENTS
    );

    static final String[] DOMAIN_LIB_FOO_JAR_CONTENTS = new String[] {
        "wlsdeploy/domainLibraries/foo.jar"
    };

    static final String[] DOMAIN_LIB_CONTENT = mergeStringArrays(
        new String[] { "wlsdeploy/domainLibraries/" },
        DOMAIN_LIB_FOO_JAR_CONTENTS
    );

    static final String[] NODE_MANAGER_IDENTITY_JKS_CONTENTS = new String[] {
        "wlsdeploy/nodeManager/nmIdentity.jks"
    };

    static final String[] NODE_MANAGER_TRUST_JKS_CONTENTS = new String[] {
        "wlsdeploy/nodeManager/nmTrust.jks"
    };

    static final String[] NODE_MANAGER_CONTENT = mergeStringArrays(
        new String[] { "wlsdeploy/nodeManager/" },
        NODE_MANAGER_IDENTITY_JKS_CONTENTS,
        NODE_MANAGER_TRUST_JKS_CONTENTS
    );

    static final String[] OPSS_WALLET_CONTENT = new String[] {
        "wlsdeploy/opsswallet/",
        "wlsdeploy/opsswallet/opss-wallet.zip"
    };

    static final String[] SCRIPTS_FANCY_SCRIPT_CONTENTS = new String[] {
        "wlsdeploy/scripts/my_fancy_script.sh"
    };

    static final String[] SCRIPTS_CONTENT = mergeStringArrays(
        new String[] { "wlsdeploy/scripts/" },
        SCRIPTS_FANCY_SCRIPT_CONTENTS
    );

    static final String[] SERVERS_ADMIN_SERVER_IDENTITY_JKS_CONTENTS = new String[] {
        "wlsdeploy/servers/AdminServer/identity.jks"
    };

    static final String[] SERVERS_ADMIN_SERVER_TRUST_JKS_CONTENTS = new String[] {
        "wlsdeploy/servers/AdminServer/trust.jks"
    };

    static final String[] SERVERS_ADMIN_SERVER_CONTENTS = mergeStringArrays(
        new String[] { "wlsdeploy/servers/AdminServer/" },
        SERVERS_ADMIN_SERVER_IDENTITY_JKS_CONTENTS,
        SERVERS_ADMIN_SERVER_TRUST_JKS_CONTENTS
    );

    static final String[] SERVERS_CONTENT = mergeStringArrays(
        new String[] { "wlsdeploy/servers/" },
        SERVERS_ADMIN_SERVER_CONTENTS
    );

    static final String[] FILE_STORES_FS1_CONTENTS = new String[] {
        "wlsdeploy/stores/fs1/"
    };

    static final String[] FILE_STORES_FS2_CONTENTS = new String[] {
        "wlsdeploy/stores/fs2/"
    };

    static final String[] FILE_STORES_FS3_CONTENTS = new String[] {
        "wlsdeploy/stores/fs3/"
    };

    static final String[] FILE_STORES_CONTENT = mergeStringArrays(
        new String[] { "wlsdeploy/stores/" },
        FILE_STORES_FS1_CONTENTS,
        FILE_STORES_FS2_CONTENTS,
        FILE_STORES_FS3_CONTENTS
    );

    static final String[] STRUCTURED_APP_WEBAPP_CONTENTS = new String[] {
        "wlsdeploy/structuredApplications/webapp/",
        "wlsdeploy/structuredApplications/webapp/app/",
        "wlsdeploy/structuredApplications/webapp/app/META-INF/",
        "wlsdeploy/structuredApplications/webapp/app/META-INF/MANIFEST.MF",
        "wlsdeploy/structuredApplications/webapp/app/WEB-INF/",
        "wlsdeploy/structuredApplications/webapp/app/WEB-INF/classes/",
        "wlsdeploy/structuredApplications/webapp/app/WEB-INF/classes/com/",
        "wlsdeploy/structuredApplications/webapp/app/WEB-INF/classes/com/oracle/",
        "wlsdeploy/structuredApplications/webapp/app/WEB-INF/classes/com/oracle/weblogic/",
        "wlsdeploy/structuredApplications/webapp/app/WEB-INF/classes/com/oracle/weblogic/example/",
        "wlsdeploy/structuredApplications/webapp/app/WEB-INF/classes/com/oracle/weblogic/example/HelloServlet.class",
        "wlsdeploy/structuredApplications/webapp/app/WEB-INF/classes/hello.properties",
        "wlsdeploy/structuredApplications/webapp/app/WEB-INF/web.xml",
        "wlsdeploy/structuredApplications/webapp/plan/",
        "wlsdeploy/structuredApplications/webapp/plan/AppFileOverrides/",
        "wlsdeploy/structuredApplications/webapp/plan/AppFileOverrides/hello.properties",
        "wlsdeploy/structuredApplications/webapp/plan/WEB-INF/",
        "wlsdeploy/structuredApplications/webapp/plan/WEB-INF/weblogic.xml",
        "wlsdeploy/structuredApplications/webapp/plan/plan.xml"
    };

    static final String[] STRUCTURED_APP_WEBAPP1_CONTENTS = new String[] {
        "wlsdeploy/structuredApplications/webapp1/",
        "wlsdeploy/structuredApplications/webapp1/app/",
        "wlsdeploy/structuredApplications/webapp1/app/webapp.war",
        "wlsdeploy/structuredApplications/webapp1/plan1/",
        "wlsdeploy/structuredApplications/webapp1/plan1/AppFileOverrides/",
        "wlsdeploy/structuredApplications/webapp1/plan1/AppFileOverrides/hello.properties",
        "wlsdeploy/structuredApplications/webapp1/plan1/WEB-INF/",
        "wlsdeploy/structuredApplications/webapp1/plan1/WEB-INF/weblogic.xml",
        "wlsdeploy/structuredApplications/webapp1/plan1/plan.xml",
        "wlsdeploy/structuredApplications/webapp1/plan2/",
        "wlsdeploy/structuredApplications/webapp1/plan2/AppFileOverrides/",
        "wlsdeploy/structuredApplications/webapp1/plan2/AppFileOverrides/hello.properties",
        "wlsdeploy/structuredApplications/webapp1/plan2/WEB-INF/",
        "wlsdeploy/structuredApplications/webapp1/plan2/WEB-INF/weblogic.xml",
        "wlsdeploy/structuredApplications/webapp1/plan2/plan.xml"
    };

    static final String[] STRUCTURED_APPS_CONTENT = mergeStringArrays(
        new String[] { "wlsdeploy/structuredApplications/" },
        STRUCTURED_APP_WEBAPP_CONTENTS,
        STRUCTURED_APP_WEBAPP1_CONTENTS
    );

    static String[] mergeStringArrays(String[]... arrays) {
        int totalSize = 0;
        for (String[] array : arrays) {
            totalSize += array.length;
        }

        String[] result = new String[totalSize];
        int nextPos = 0;
        for (String[] array : arrays) {
            System.arraycopy(array, 0, result, nextPos, array.length);
            nextPos += array.length;
        }
        return result;
    }
}
