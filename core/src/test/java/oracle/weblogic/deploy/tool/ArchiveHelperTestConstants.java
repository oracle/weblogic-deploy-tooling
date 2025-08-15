/*
 * Copyright (c) 2023, 2025, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.tool;

import oracle.weblogic.deploy.util.WLSDeployArchive;

// When creating the archive-helper-test.zip, use the following command
// once the config and wlsdeploy subdirectories are populated with the
// necessary content.
//
// zip archive-helper-test.zip wlsdeploy/**/* config/wlsdeploy/**/*


public class ArchiveHelperTestConstants {
    static final String[] MY_APP_WAR_CONTENTS = new String[] {
        "wlsdeploy/applications/my-app.war"
    };

    static final String[] MY_APP_WAR_DUP_CONTENTS = new String[] {
        "wlsdeploy/applications/my-app(1).war"
    };

    static final String[] MY_APP_DEPLOYMENT_PLAN_CONTENTS = new String[] {
        "wlsdeploy/applications/my-app.xml"
    };

    static final String[] MY_APP_DEPLOYMENT_PLAN_DUP_CONTENTS = new String[] {
        "wlsdeploy/applications/my-app(1).xml"
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

    static final String[] MY_OTHER_APP_DIR_DUP_CONTENTS = new String[] {
        "wlsdeploy/applications/my-other-app(1)/",
        "wlsdeploy/applications/my-other-app(1)/META-INF/",
        "wlsdeploy/applications/my-other-app(1)/META-INF/maven/",
        "wlsdeploy/applications/my-other-app(1)/META-INF/maven/oracle.jcs.lifecycle/",
        "wlsdeploy/applications/my-other-app(1)/META-INF/maven/oracle.jcs.lifecycle/get-listen-address-app/",
        "wlsdeploy/applications/my-other-app(1)/META-INF/maven/oracle.jcs.lifecycle/get-listen-address-app/pom.properties",
        "wlsdeploy/applications/my-other-app(1)/META-INF/maven/oracle.jcs.lifecycle/get-listen-address-app/pom.xml",
        "wlsdeploy/applications/my-other-app(1)/META-INF/MANIFEST.MF",
        "wlsdeploy/applications/my-other-app(1)/WEB-INF/",
        "wlsdeploy/applications/my-other-app(1)/WEB-INF/classes/",
        "wlsdeploy/applications/my-other-app(1)/WEB-INF/classes/com/",
        "wlsdeploy/applications/my-other-app(1)/WEB-INF/classes/com/oracle/",
        "wlsdeploy/applications/my-other-app(1)/WEB-INF/classes/com/oracle/platform/",
        "wlsdeploy/applications/my-other-app(1)/WEB-INF/classes/com/oracle/platform/GetListenAddressServlet.class",
        "wlsdeploy/applications/my-other-app(1)/WEB-INF/classes/com/oracle/platform/ListenAddressAndPort.class",
        "wlsdeploy/applications/my-other-app(1)/WEB-INF/web.xml",
        "wlsdeploy/applications/my-other-app(1)/WEB-INF/weblogic.xml"
    };

    static final String[] APPLICATIONS_CONTENT = mergeStringArrays(
        new String[] { "wlsdeploy/applications/" },
        MY_OTHER_APP_DIR_CONTENTS,
        MY_APP_WAR_CONTENTS,
        MY_APP_DEPLOYMENT_PLAN_CONTENTS,
        MY_OTHER_APP_WAR_CONTENTS
    );

    static final String[] CLASSPATH_LIB_BAR_DIR_CONTENTS = new String[] {
        "wlsdeploy/classpathLibraries/bar/",
        "wlsdeploy/classpathLibraries/bar/Foo.class"
    };

    static final String[] CLASSPATH_LIB_BAR_DIR_DUP_CONTENTS = new String[] {
        "wlsdeploy/classpathLibraries/bar(1)/",
        "wlsdeploy/classpathLibraries/bar(1)/Foo.class"
    };

    static final String[] CLASSPATH_LIB_BAR_JAR_CONTENTS = new String[] {
        "wlsdeploy/classpathLibraries/bar.jar"
    };

    static final String[] CLASSPATH_LIB_BAR_JAR_DUP_CONTENTS = new String[] {
        "wlsdeploy/classpathLibraries/bar(1).jar"
    };

    static final String[] CLASSPATH_LIBS_CONTENT = mergeStringArrays(
        new String[] { "wlsdeploy/classpathLibraries/" },
        CLASSPATH_LIB_BAR_DIR_CONTENTS,
        CLASSPATH_LIB_BAR_JAR_CONTENTS
    );

    static final String[] COHERENCE_MYCLUSTER_CONFIG_FILE_CONTENTS = new String[] {
        WLSDeployArchive.ARCHIVE_COHERENCE_TARGET_DIR + "/mycluster/cache-config.xml"
    };

    static final String[] COHERENCE_MYCLUSTER_CONFIG_FILE_DUP_CONTENTS = new String[] {
        WLSDeployArchive.ARCHIVE_COHERENCE_TARGET_DIR + "/mycluster/cache-config(1).xml"
    };

    static final String[] COHERENCE_MYCLUSTER_PERSISTENT_DIR_ACTIVE_CONTENTS = new String[] {
        WLSDeployArchive.ARCHIVE_COHERENCE_TARGET_DIR + "/mycluster/active/"
    };

    static final String[] COHERENCE_MYCLUSTER_PERSISTENT_DIR_ACTIVE_DUP_CONTENTS = new String[] {
        WLSDeployArchive.ARCHIVE_COHERENCE_TARGET_DIR + "/mycluster/active(1)/"
    };

    static final String[] COHERENCE_MYCLUSTER_PERSISTENT_DIR_SNAPSHOT_CONTENTS = new String[] {
        WLSDeployArchive.ARCHIVE_COHERENCE_TARGET_DIR + "/mycluster/snapshot/"
    };

    static final String[] COHERENCE_MYCLUSTER_PERSISTENT_DIR_TRASH_CONTENTS = new String[] {
        WLSDeployArchive.ARCHIVE_COHERENCE_TARGET_DIR + "/mycluster/trash/"
    };

    static final String[] COHERENCE_MYCLUSTER_PERSISTENT_DIR_CONTENTS = mergeStringArrays(
        COHERENCE_MYCLUSTER_PERSISTENT_DIR_ACTIVE_CONTENTS,
        COHERENCE_MYCLUSTER_PERSISTENT_DIR_SNAPSHOT_CONTENTS,
        COHERENCE_MYCLUSTER_PERSISTENT_DIR_TRASH_CONTENTS
    );

    static final String[] COHERENCE_MYCLUSTER_CONTENTS = mergeStringArrays(
        new String[] { WLSDeployArchive.ARCHIVE_COHERENCE_TARGET_DIR + "/mycluster/" },
        COHERENCE_MYCLUSTER_PERSISTENT_DIR_CONTENTS,
        COHERENCE_MYCLUSTER_CONFIG_FILE_CONTENTS
    );

    static final String[] COHERENCE_MYCLUSTER2_CONFIG_FILE_CONTENTS = new String[] {
        WLSDeployArchive.ARCHIVE_COHERENCE_TARGET_DIR + "/mycluster2/cache-config.xml"
    };

    static final String[] COHERENCE_MYCLUSTER2_PERSISTENT_DIR_CONTENTS = new String[] {
        WLSDeployArchive.ARCHIVE_COHERENCE_TARGET_DIR + "/mycluster2/snapshot/"
    };

    static final String[] COHERENCE_MYCLUSTER2_CONTENTS = mergeStringArrays(
        new String[] { WLSDeployArchive.ARCHIVE_COHERENCE_TARGET_DIR + "/mycluster2/" },
        COHERENCE_MYCLUSTER2_PERSISTENT_DIR_CONTENTS,
        COHERENCE_MYCLUSTER2_CONFIG_FILE_CONTENTS
    );

    static final String[] COHERENCE_CONTENT = mergeStringArrays(
        new String[] { WLSDeployArchive.ARCHIVE_COHERENCE_TARGET_DIR + "/" },
        COHERENCE_MYCLUSTER_CONTENTS,
        COHERENCE_MYCLUSTER2_CONTENTS
    );

    static final String[] MIME_MAPPING_PROPERTIES_CONTENTS = new String[] {
        WLSDeployArchive.ARCHIVE_CONFIG_TARGET_DIR + "/mimemappings.properties"
    };

    static final String[] MIME_MAPPING_PROPERTIES_DUP_CONTENTS = new String[] {
        WLSDeployArchive.ARCHIVE_CONFIG_TARGET_DIR + "/mimemappings(1).properties"
    };

    static final String[] MIME_MAPPINGS_CONTENT = new String[] {
        WLSDeployArchive.ARCHIVE_CONFIG_TARGET_DIR + "/",
        WLSDeployArchive.ARCHIVE_CONFIG_TARGET_DIR + "/mimemappings.properties"
    };

    static final String[] CUSTOM_MYDIR_BAR_PROPERTIES_CONTENTS = new String[] {
        WLSDeployArchive.ARCHIVE_CUSTOM_TARGET_DIR + "/mydir/bar.properties"
    };

    static final String[] CUSTOM_MYDIR_CONTENTS = mergeStringArrays(
        new String[] { WLSDeployArchive.ARCHIVE_CUSTOM_TARGET_DIR + "/mydir/" },
        CUSTOM_MYDIR_BAR_PROPERTIES_CONTENTS
    );

    static final String[] CUSTOM_MYDIR_DUP_CONTENTS = new String[] {
        WLSDeployArchive.ARCHIVE_CUSTOM_TARGET_DIR + "/mydir(1)/",
        WLSDeployArchive.ARCHIVE_CUSTOM_TARGET_DIR + "/mydir(1)/bar.properties"
    };

    static final String[] CUSTOM_FOO_PROPERTIES_CONTENTS = {
        WLSDeployArchive.ARCHIVE_CUSTOM_TARGET_DIR + "/foo.properties"
    };

    static final String[] CUSTOM_FOO_PROPERTIES_DUP_CONTENTS = {
        WLSDeployArchive.ARCHIVE_CUSTOM_TARGET_DIR + "/foo(1).properties"
    };

    static final String[] CUSTOM_CONTENT = mergeStringArrays(
        new String[] { WLSDeployArchive.ARCHIVE_CUSTOM_TARGET_DIR + "/" },
        CUSTOM_MYDIR_CONTENTS,
        CUSTOM_FOO_PROPERTIES_CONTENTS
    );

    static final String[] DATABASE_WALLET_RCU_CONTENTS = new String[] {
        WLSDeployArchive.ARCHIVE_DB_WALLETS_DIR + "/rcu/",
        WLSDeployArchive.ARCHIVE_DB_WALLETS_DIR + "/rcu/cwallet.sso",
        WLSDeployArchive.ARCHIVE_DB_WALLETS_DIR + "/rcu/ewallet.p12",
        WLSDeployArchive.ARCHIVE_DB_WALLETS_DIR + "/rcu/ewallet.pem",
        WLSDeployArchive.ARCHIVE_DB_WALLETS_DIR + "/rcu/keystore.jks",
        WLSDeployArchive.ARCHIVE_DB_WALLETS_DIR + "/rcu/ojdbc.properties",
        WLSDeployArchive.ARCHIVE_DB_WALLETS_DIR + "/rcu/README",
        WLSDeployArchive.ARCHIVE_DB_WALLETS_DIR + "/rcu/sqlnet.ora",
        WLSDeployArchive.ARCHIVE_DB_WALLETS_DIR + "/rcu/tnsnames.ora",
        WLSDeployArchive.ARCHIVE_DB_WALLETS_DIR + "/rcu/truststore.jks"
    };

    static final String[] DATABASE_WALLET_WALLET1_CONTENTS = new String[] {
        WLSDeployArchive.ARCHIVE_DB_WALLETS_DIR + "/wallet1/",
        WLSDeployArchive.ARCHIVE_DB_WALLETS_DIR + "/wallet1/atpwallet.zip"
    };

    static final String[] DATABASE_WALLET_WALLET1_DUP_CONTENTS = new String[] {
        WLSDeployArchive.ARCHIVE_DB_WALLETS_DIR + "/wallet1(1)/",
        WLSDeployArchive.ARCHIVE_DB_WALLETS_DIR + "/wallet1(1)/atpwallet.zip"
    };

    static final String[] DATABASE_WALLETS_CONTENT = mergeStringArrays(
        new String[] { WLSDeployArchive.ARCHIVE_DB_WALLETS_DIR + "/" },
        DATABASE_WALLET_RCU_CONTENTS,
        DATABASE_WALLET_WALLET1_CONTENTS
    );

    static final String[] DOMAIN_BIN_SET_USER_OVERRIDES_SH_CONTENTS = new String[] {
        "wlsdeploy/domainBin/setUserOverrides.sh"
    };

    static final String[] DOMAIN_BIN_SET_USER_OVERRIDES_SH_DUP_CONTENTS = new String[] {
        "wlsdeploy/domainBin/setUserOverrides(1).sh"
    };

    static final String[] DOMAIN_BIN_CONTENT = mergeStringArrays(
        new String[] { "wlsdeploy/domainBin/" },
        DOMAIN_BIN_SET_USER_OVERRIDES_SH_CONTENTS
    );

    static final String[] DOMAIN_LIB_FOO_JAR_CONTENTS = new String[] {
        "wlsdeploy/domainLibraries/foo.jar"
    };

    static final String[] DOMAIN_LIB_FOO_JAR_DUP_CONTENTS = new String[] {
        "wlsdeploy/domainLibraries/foo(1).jar"
    };

    static final String[] DOMAIN_LIB_CONTENT = mergeStringArrays(
        new String[] { "wlsdeploy/domainLibraries/" },
        DOMAIN_LIB_FOO_JAR_CONTENTS
    );

    static final String[] FILE_STORES_FS1_CONTENTS = new String[] {
        "wlsdeploy/stores/fs1/"
    };

    static final String[] FILE_STORES_FS1_DUP_CONTENTS = new String[] {
        "wlsdeploy/stores/fs1(1)/"
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

    static final String[] FOREIGN_SERVERS_FS1_JNDI_PROPERTIES_CONTENTS = new String[] {
        WLSDeployArchive.ARCHIVE_JMS_FOREIGN_SERVER_DIR + "/fs1/jndi.properties"
    };

    static final String[] FOREIGN_SERVERS_FS1_JNDI_PROPERTIES_DUP_CONTENTS = new String[] {
        WLSDeployArchive.ARCHIVE_JMS_FOREIGN_SERVER_DIR + "/fs1/jndi(1).properties"
    };

    static final String[] FOREIGN_SERVERS_FS1_CONTENTS = mergeStringArrays(
        new String[] { WLSDeployArchive.ARCHIVE_JMS_FOREIGN_SERVER_DIR + "/fs1/" },
        FOREIGN_SERVERS_FS1_JNDI_PROPERTIES_CONTENTS
    );

    static final String[] FOREIGN_SERVERS_FS2_JNDI_PROPERTIES_CONTENTS = new String[] {
        WLSDeployArchive.ARCHIVE_JMS_FOREIGN_SERVER_DIR + "/fs2/jndi.properties"
    };

    static final String[] FOREIGN_SERVERS_FS2_CONTENTS = mergeStringArrays(
        new String[] { WLSDeployArchive.ARCHIVE_JMS_FOREIGN_SERVER_DIR + "/fs2/" },
        FOREIGN_SERVERS_FS2_JNDI_PROPERTIES_CONTENTS
    );

    static final String[] FOREIGN_SERVERS_CONTENT = mergeStringArrays(
        new String[] {
            WLSDeployArchive.ARCHIVE_JMS_DIR + "/",
            WLSDeployArchive.ARCHIVE_JMS_FOREIGN_SERVER_DIR + "/"
        },
        FOREIGN_SERVERS_FS1_CONTENTS,
        FOREIGN_SERVERS_FS2_CONTENTS
    );

    static final String[] NODE_MANAGER_IDENTITY_JKS_CONTENTS = new String[] {
        WLSDeployArchive.ARCHIVE_NODE_MANAGER_TARGET_DIR + "/nmIdentity.jks"
    };

    static final String[] NODE_MANAGER_IDENTITY_JKS_DUP_CONTENTS = new String[] {
        WLSDeployArchive.ARCHIVE_NODE_MANAGER_TARGET_DIR + "/nmIdentity(1).jks"
    };

    static final String[] NODE_MANAGER_TRUST_JKS_CONTENTS = new String[] {
        WLSDeployArchive.ARCHIVE_NODE_MANAGER_TARGET_DIR + "/nmTrust.jks"
    };

    static final String[] NODE_MANAGER_CONTENT = mergeStringArrays(
        new String[] { WLSDeployArchive.ARCHIVE_NODE_MANAGER_TARGET_DIR + "/" },
        NODE_MANAGER_IDENTITY_JKS_CONTENTS,
        NODE_MANAGER_TRUST_JKS_CONTENTS
    );

    static final String[] OPSS_WALLET_CONTENT = new String[] {
        "wlsdeploy/opsswallet/",
        "wlsdeploy/opsswallet/opss-wallet.zip"
    };

    static final String[] PLUGIN_DEPS_TEST_EXP_PLUGIN_CONTENTS = new String[] {
            "wlsdeploy/pluginDeployments/test-exp-plugin/",
            "wlsdeploy/pluginDeployments/test-exp-plugin/META-INF/",
            "wlsdeploy/pluginDeployments/test-exp-plugin/META-INF/MANIFEST.MF",
            "wlsdeploy/pluginDeployments/test-exp-plugin/META-INF/maven/",
            "wlsdeploy/pluginDeployments/test-exp-plugin/META-INF/maven/com.oracle.weblogic.lifecycle/",
            "wlsdeploy/pluginDeployments/test-exp-plugin/META-INF/maven/com.oracle.weblogic.lifecycle/test-plugin/",
            "wlsdeploy/pluginDeployments/test-exp-plugin/META-INF/maven/com.oracle.weblogic.lifecycle/test-plugin/pom.properties",
            "wlsdeploy/pluginDeployments/test-exp-plugin/META-INF/maven/com.oracle.weblogic.lifecycle/test-plugin/pom.xml",
            "wlsdeploy/pluginDeployments/test-exp-plugin/oracle/",
            "wlsdeploy/pluginDeployments/test-exp-plugin/oracle/weblogic/",
            "wlsdeploy/pluginDeployments/test-exp-plugin/oracle/weblogic/deploy/",
            "wlsdeploy/pluginDeployments/test-exp-plugin/oracle/weblogic/deploy/testplugin/",
            "wlsdeploy/pluginDeployments/test-exp-plugin/oracle/weblogic/deploy/testplugin/TestPlugin.class"
    };

    static final String[] PLUGIN_DEPS_TEST_EXP_PLUGIN_DUP_CONTENTS = new String[] {
            "wlsdeploy/pluginDeployments/test-exp-plugin(1)/",
            "wlsdeploy/pluginDeployments/test-exp-plugin(1)/META-INF/",
            "wlsdeploy/pluginDeployments/test-exp-plugin(1)/META-INF/MANIFEST.MF",
            "wlsdeploy/pluginDeployments/test-exp-plugin(1)/META-INF/maven/",
            "wlsdeploy/pluginDeployments/test-exp-plugin(1)/META-INF/maven/com.oracle.weblogic.lifecycle/",
            "wlsdeploy/pluginDeployments/test-exp-plugin(1)/META-INF/maven/com.oracle.weblogic.lifecycle/test-plugin/",
            "wlsdeploy/pluginDeployments/test-exp-plugin(1)/META-INF/maven/com.oracle.weblogic.lifecycle/test-plugin/pom.properties",
            "wlsdeploy/pluginDeployments/test-exp-plugin(1)/META-INF/maven/com.oracle.weblogic.lifecycle/test-plugin/pom.xml",
            "wlsdeploy/pluginDeployments/test-exp-plugin(1)/oracle/",
            "wlsdeploy/pluginDeployments/test-exp-plugin(1)/oracle/weblogic/",
            "wlsdeploy/pluginDeployments/test-exp-plugin(1)/oracle/weblogic/deploy/",
            "wlsdeploy/pluginDeployments/test-exp-plugin(1)/oracle/weblogic/deploy/testplugin/",
            "wlsdeploy/pluginDeployments/test-exp-plugin(1)/oracle/weblogic/deploy/testplugin/TestPlugin.class"
    };

    static final String[] PLUGIN_DEPS_TEST_PLUGIN_JAR_CONTENTS = new String[] {
            "wlsdeploy/pluginDeployments/test-plugin.jar"
    };

    static final String[] PLUGIN_DEPS_TEST_PLUGIN_JAR_DUP_CONTENTS = new String[] {
            "wlsdeploy/pluginDeployments/test-plugin(1).jar"
    };

    static final String[] PLUGIN_DEPS_CONTENT = mergeStringArrays(
            new String[] { "wlsdeploy/pluginDeployments/" },
            PLUGIN_DEPS_TEST_EXP_PLUGIN_CONTENTS,
            PLUGIN_DEPS_TEST_PLUGIN_JAR_CONTENTS
    );

    static final String[] SAML2_SP_PROPERTIES_CONTENT = new String[] {
        "wlsdeploy/security/saml2/saml2sppartner.properties"
    };

    static final String[] SAML2_DATA_CONTENTS = new String[] {
        "wlsdeploy/security/saml2/",
        "wlsdeploy/security/saml2/company1idp_metadata.xml",
        "wlsdeploy/security/saml2/company2idp_metadata.xml",
        "wlsdeploy/security/saml2/hmosp_metadata.xml",
        "wlsdeploy/security/saml2/saml2idppartner.properties",
        "wlsdeploy/security/saml2/saml2sppartner.properties"
    };

    static final String[] SAML2_DATA_LIST_ALL_CONTENTS = mergeStringArrays(
        new String[] { "wlsdeploy/security/" },
        SAML2_DATA_CONTENTS
    );

    static final String[] SCRIPTS_FANCY_SCRIPT_CONTENTS = new String[] {
        WLSDeployArchive.ARCHIVE_SCRIPTS_DIR + "/my_fancy_script.sh"
    };

    static final String[] SCRIPTS_FANCY_SCRIPT_DUP_CONTENTS = new String[] {
        WLSDeployArchive.ARCHIVE_SCRIPTS_DIR + "/my_fancy_script(1).sh"
    };

    static final String[] SCRIPTS_CONTENT = mergeStringArrays(
        new String[] { WLSDeployArchive.ARCHIVE_SCRIPTS_DIR + "/" },
        SCRIPTS_FANCY_SCRIPT_CONTENTS
    );

    static final String[] SERVERS_ADMIN_SERVER_IDENTITY_JKS_CONTENTS = new String[] {
        WLSDeployArchive.ARCHIVE_SERVER_TARGET_DIR + "/AdminServer/identity.jks"
    };

    static final String[] SERVERS_ADMIN_SERVER_IDENTITY_JKS_DUP_CONTENTS = new String[] {
        WLSDeployArchive.ARCHIVE_SERVER_TARGET_DIR + "/AdminServer/identity(1).jks"
    };

    static final String[] SERVERS_ADMIN_SERVER_TRUST_JKS_CONTENTS = new String[] {
        WLSDeployArchive.ARCHIVE_SERVER_TARGET_DIR + "/AdminServer/trust.jks"
    };

    static final String[] SERVERS_ADMIN_SERVER_CONTENTS = mergeStringArrays(
        new String[] { WLSDeployArchive.ARCHIVE_SERVER_TARGET_DIR + "/AdminServer/" },
        SERVERS_ADMIN_SERVER_IDENTITY_JKS_CONTENTS,
        SERVERS_ADMIN_SERVER_TRUST_JKS_CONTENTS
    );

    static final String[] SERVERS_CONTENT = mergeStringArrays(
        new String[] { WLSDeployArchive.ARCHIVE_SERVER_TARGET_DIR + "/" },
        SERVERS_ADMIN_SERVER_CONTENTS
    );

    static final String[] SERVER_TEMPLATE_IDENTITY_JKS_CONTENTS = new String[] {
            WLSDeployArchive.ARCHIVE_SERVER_TEMPLATE_TARGET_DIR + "/myServerTemplate/identity.jks"
    };

    static final String[] SERVER_TEMPLATE_IDENTITY_JKS_DUP_CONTENTS = new String[] {
            WLSDeployArchive.ARCHIVE_SERVER_TEMPLATE_TARGET_DIR + "/myServerTemplate/identity(1).jks"
    };

    static final String[] SERVER_TEMPLATE_TRUST_JKS_CONTENTS = new String[] {
            WLSDeployArchive.ARCHIVE_SERVER_TEMPLATE_TARGET_DIR + "/myServerTemplate/trust.jks"
    };

    static final String[] SERVER_TEMPLATE_CONTENTS = mergeStringArrays(
            new String[] { WLSDeployArchive.ARCHIVE_SERVER_TEMPLATE_TARGET_DIR + "/myServerTemplate/" },
            SERVER_TEMPLATE_IDENTITY_JKS_CONTENTS,
            SERVER_TEMPLATE_TRUST_JKS_CONTENTS
    );

    static final String[] SERVER_TEMPLATES_CONTENT = mergeStringArrays(
            new String[] { WLSDeployArchive.ARCHIVE_SERVER_TEMPLATE_TARGET_DIR + "/" },
            SERVER_TEMPLATE_CONTENTS
    );

    static final String[] SHARED_LIBS_MY_OTHER_LIB_CONTENTS = new String[] {
        "wlsdeploy/sharedLibraries/my-other-lib/",
        "wlsdeploy/sharedLibraries/my-other-lib/META-INF/",
        "wlsdeploy/sharedLibraries/my-other-lib/META-INF/maven/",
        "wlsdeploy/sharedLibraries/my-other-lib/META-INF/maven/oracle.jcs.lifecycle/",
        "wlsdeploy/sharedLibraries/my-other-lib/META-INF/maven/oracle.jcs.lifecycle/get-listen-address-app/",
        "wlsdeploy/sharedLibraries/my-other-lib/META-INF/maven/oracle.jcs.lifecycle/get-listen-address-app/pom.properties",
        "wlsdeploy/sharedLibraries/my-other-lib/META-INF/maven/oracle.jcs.lifecycle/get-listen-address-app/pom.xml",
        "wlsdeploy/sharedLibraries/my-other-lib/META-INF/MANIFEST.MF",
        "wlsdeploy/sharedLibraries/my-other-lib/WEB-INF/",
        "wlsdeploy/sharedLibraries/my-other-lib/WEB-INF/classes/",
        "wlsdeploy/sharedLibraries/my-other-lib/WEB-INF/classes/com/",
        "wlsdeploy/sharedLibraries/my-other-lib/WEB-INF/classes/com/oracle/",
        "wlsdeploy/sharedLibraries/my-other-lib/WEB-INF/classes/com/oracle/platform/",
        "wlsdeploy/sharedLibraries/my-other-lib/WEB-INF/classes/com/oracle/platform/GetListenAddressServlet.class",
        "wlsdeploy/sharedLibraries/my-other-lib/WEB-INF/classes/com/oracle/platform/ListenAddressAndPort.class",
        "wlsdeploy/sharedLibraries/my-other-lib/WEB-INF/web.xml",
        "wlsdeploy/sharedLibraries/my-other-lib/WEB-INF/weblogic.xml"
    };

    static final String[] SHARED_LIBS_MY_OTHER_LIB_DUP_CONTENTS = new String[] {
        "wlsdeploy/sharedLibraries/my-other-lib(1)/",
        "wlsdeploy/sharedLibraries/my-other-lib(1)/META-INF/",
        "wlsdeploy/sharedLibraries/my-other-lib(1)/META-INF/maven/",
        "wlsdeploy/sharedLibraries/my-other-lib(1)/META-INF/maven/oracle.jcs.lifecycle/",
        "wlsdeploy/sharedLibraries/my-other-lib(1)/META-INF/maven/oracle.jcs.lifecycle/get-listen-address-app/",
        "wlsdeploy/sharedLibraries/my-other-lib(1)/META-INF/maven/oracle.jcs.lifecycle/get-listen-address-app/pom.properties",
        "wlsdeploy/sharedLibraries/my-other-lib(1)/META-INF/maven/oracle.jcs.lifecycle/get-listen-address-app/pom.xml",
        "wlsdeploy/sharedLibraries/my-other-lib(1)/META-INF/MANIFEST.MF",
        "wlsdeploy/sharedLibraries/my-other-lib(1)/WEB-INF/",
        "wlsdeploy/sharedLibraries/my-other-lib(1)/WEB-INF/classes/",
        "wlsdeploy/sharedLibraries/my-other-lib(1)/WEB-INF/classes/com/",
        "wlsdeploy/sharedLibraries/my-other-lib(1)/WEB-INF/classes/com/oracle/",
        "wlsdeploy/sharedLibraries/my-other-lib(1)/WEB-INF/classes/com/oracle/platform/",
        "wlsdeploy/sharedLibraries/my-other-lib(1)/WEB-INF/classes/com/oracle/platform/GetListenAddressServlet.class",
        "wlsdeploy/sharedLibraries/my-other-lib(1)/WEB-INF/classes/com/oracle/platform/ListenAddressAndPort.class",
        "wlsdeploy/sharedLibraries/my-other-lib(1)/WEB-INF/web.xml",
        "wlsdeploy/sharedLibraries/my-other-lib(1)/WEB-INF/weblogic.xml"
    };

    static final String[] SHARED_LIBS_MY_LIB_WAR_CONTENTS = new String[] {
        "wlsdeploy/sharedLibraries/my-lib.war"
    };

    static final String[] SHARED_LIBS_MY_LIB_WAR_DUP_CONTENTS = new String[] {
        "wlsdeploy/sharedLibraries/my-lib(1).war"
    };

    static final String[] SHARED_LIBS_MY_LIB_XML_CONTENTS = new String[] {
        "wlsdeploy/sharedLibraries/my-lib.xml"
    };

    static final String[] SHARED_LIBS_MY_LIB_XML_DUP_CONTENTS = new String[] {
        "wlsdeploy/sharedLibraries/my-lib(1).xml"
    };

    static final String[] SHARED_LIBS_CONTENT = mergeStringArrays(
        new String[] { "wlsdeploy/sharedLibraries/" },
        SHARED_LIBS_MY_OTHER_LIB_CONTENTS,
        SHARED_LIBS_MY_LIB_WAR_CONTENTS,
        SHARED_LIBS_MY_LIB_XML_CONTENTS
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

    static final String[] STRUCTURED_APP_WEBAPP_DUP_CONTENTS = new String[] {
        "wlsdeploy/structuredApplications/webapp(1)/",
        "wlsdeploy/structuredApplications/webapp(1)/app/",
        "wlsdeploy/structuredApplications/webapp(1)/app/META-INF/",
        "wlsdeploy/structuredApplications/webapp(1)/app/META-INF/MANIFEST.MF",
        "wlsdeploy/structuredApplications/webapp(1)/app/WEB-INF/",
        "wlsdeploy/structuredApplications/webapp(1)/app/WEB-INF/classes/",
        "wlsdeploy/structuredApplications/webapp(1)/app/WEB-INF/classes/com/",
        "wlsdeploy/structuredApplications/webapp(1)/app/WEB-INF/classes/com/oracle/",
        "wlsdeploy/structuredApplications/webapp(1)/app/WEB-INF/classes/com/oracle/weblogic/",
        "wlsdeploy/structuredApplications/webapp(1)/app/WEB-INF/classes/com/oracle/weblogic/example/",
        "wlsdeploy/structuredApplications/webapp(1)/app/WEB-INF/classes/com/oracle/weblogic/example/HelloServlet.class",
        "wlsdeploy/structuredApplications/webapp(1)/app/WEB-INF/classes/hello.properties",
        "wlsdeploy/structuredApplications/webapp(1)/app/WEB-INF/web.xml",
        "wlsdeploy/structuredApplications/webapp(1)/plan/",
        "wlsdeploy/structuredApplications/webapp(1)/plan/AppFileOverrides/",
        "wlsdeploy/structuredApplications/webapp(1)/plan/AppFileOverrides/hello.properties",
        "wlsdeploy/structuredApplications/webapp(1)/plan/WEB-INF/",
        "wlsdeploy/structuredApplications/webapp(1)/plan/WEB-INF/weblogic.xml",
        "wlsdeploy/structuredApplications/webapp(1)/plan/plan.xml"
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

    static final String[] WRC_EXTENSION_FILE_CONTENT = new String[] {
        "wlsdeploy/wrcExtension/console-rest-ext-6.0.war"
    };

    static final String[] WRC_EXTENSION_CONTENTS = mergeStringArrays(
        new String[] { "wlsdeploy/wrcExtension/" },
        WRC_EXTENSION_FILE_CONTENT
    );

    static final String[] WRC_EXTENSION_LIST_ALL_CONTENTS = WRC_EXTENSION_CONTENTS;

    static final String[] ALL_CONTENT = mergeStringArrays(
        APPLICATIONS_CONTENT,
        CLASSPATH_LIBS_CONTENT,
        COHERENCE_CONTENT,
        CUSTOM_CONTENT,
        DATABASE_WALLETS_CONTENT,
        DOMAIN_BIN_CONTENT,
        DOMAIN_LIB_CONTENT,
        FILE_STORES_CONTENT,
        FOREIGN_SERVERS_CONTENT,
        MIME_MAPPINGS_CONTENT,
        NODE_MANAGER_CONTENT,
        OPSS_WALLET_CONTENT,
        PLUGIN_DEPS_CONTENT,
        SAML2_DATA_LIST_ALL_CONTENTS,
        SCRIPTS_CONTENT,
        SERVERS_CONTENT,
        SERVER_TEMPLATES_CONTENT,
        SHARED_LIBS_CONTENT,
        STRUCTURED_APPS_CONTENT,
        WRC_EXTENSION_LIST_ALL_CONTENTS
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
