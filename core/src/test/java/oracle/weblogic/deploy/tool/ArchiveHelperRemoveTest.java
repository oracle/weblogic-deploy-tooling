/*
 * Copyright (c) 2023, Oracle Corporation and/or its affiliates.  All rights reserved.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.tool;

import java.io.File;
import java.io.PrintWriter;
import java.io.StringWriter;
import java.nio.file.StandardCopyOption;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.logging.Level;

import oracle.weblogic.deploy.logging.PlatformLogger;
import oracle.weblogic.deploy.logging.WLSDeployLogFactory;
import oracle.weblogic.deploy.tool.archive_helper.ArchiveHelperException;
import oracle.weblogic.deploy.util.ExitCode;
import oracle.weblogic.deploy.util.StringUtils;
import oracle.weblogic.deploy.util.WLSDeployZipFileTest;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.CsvSource;
import org.junit.jupiter.params.provider.ValueSource;

import static oracle.weblogic.deploy.tool.ArchiveHelper.LOGGER_NAME;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.APPLICATIONS_CONTENT;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.CLASSPATH_LIBS_CONTENT;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.CLASSPATH_LIB_BAR_DIR_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.CLASSPATH_LIB_BAR_JAR_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.COHERENCE_MYCLUSTER_CONFIG_FILE_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.COHERENCE_MYCLUSTER_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.COHERENCE_MYCLUSTER_PERSISTENT_DIR_ACTIVE_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.CUSTOM_CONTENT;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.CUSTOM_FOO_PROPERTIES_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.CUSTOM_MYDIR_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.DATABASE_WALLETS_CONTENT;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.DATABASE_WALLET_RCU_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.DATABASE_WALLET_WALLET1_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.DOMAIN_BIN_CONTENT;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.DOMAIN_LIB_CONTENT;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.FILE_STORES_CONTENT;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.FILE_STORES_FS2_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.FOREIGN_SERVERS_FS1_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.MIME_MAPPINGS_CONTENT;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.MY_APP_DEPLOYMENT_PLAN_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.MY_APP_WAR_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.MY_OTHER_APP_DIR_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.NODE_MANAGER_CONTENT;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.NODE_MANAGER_IDENTITY_JKS_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.OPSS_WALLET_CONTENT;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.SCRIPTS_CONTENT;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.SERVERS_ADMIN_SERVER_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.SERVERS_ADMIN_SERVER_IDENTITY_JKS_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.SHARED_LIBS_CONTENT;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.SHARED_LIBS_MY_LIB_WAR_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.SHARED_LIBS_MY_LIB_XML_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.SHARED_LIBS_MY_OTHER_LIB_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.STRUCTURED_APPS_CONTENT;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.STRUCTURED_APP_WEBAPP_CONTENTS;
import static oracle.weblogic.deploy.util.WLSDeployArchive.DEFAULT_RCU_WALLET_NAME;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

public class ArchiveHelperRemoveTest {
    public static final File UNIT_TEST_SOURCE_DIR = new File(WLSDeployZipFileTest.UNIT_TEST_SOURCE_DIR);
    private static final File UNIT_TEST_TARGET_DIR =
        new File(new File(WLSDeployZipFileTest.UNIT_TEST_TARGET_DIR, "archiveHelper"), "remove");

    private static final Path ARCHIVE_HELPER_SOURCE_ZIP =
        new File(UNIT_TEST_SOURCE_DIR, "archive-helper-test.zip").toPath();
    private static final Path ARCHIVE_HELPER_TARGET_ZIP =
        new File(UNIT_TEST_TARGET_DIR, "archive-helper-test.zip").toPath();
    private static final String ARCHIVE_HELPER_VALUE = ARCHIVE_HELPER_TARGET_ZIP.toFile().getAbsolutePath();

    private static final String[] LIST_APPLICATIONS = new String[] { "application" };
    private static final String[] LIST_CLASSPATH_LIBRARIES = new String[] { "classpathLibrary" };
    private static final String[] LIST_COHERENCE_MY_CLUSTER = new String[] {
        "coherence",
        "-cluster_name",
        "mycluster"
    };
    private static final String[] LIST_CUSTOM_ENTRIES =  new String[] { "custom" };
    private static final String[] LIST_DATABASE_WALLETS =  new String[] { "databaseWallet" };
    private static final String[] LIST_DOMAIN_BIN_SCRIPTS = new String[] { "domainBinScript" };
    private static final String[] LIST_DOMAIN_LIBRARIES = new String[] { "domainLibrary" };
    private static final String[] LIST_FILE_STORES = new String[] { "fileStore" };
    private static final String[] LIST_FOREIGN_SERVERS_FS1 = new String[] {
        "jmsForeignServer",
        "-foreign_server_name",
        "fs1"
    };
    private static final String[] LIST_MIME_MAPPINGS = new String[] { "mimeMapping" };
    private static final String[] LIST_NODE_MANAGER_KEYSTORES = new String[] { "nodeManagerKeystore" };
    private static final String[] LIST_OPSS_WALLET = new String[] { "opssWallet" };
    private static final String[] LIST_RCU_WALLET = new String[] { "rcuWallet" };
    private static final String[] LIST_SCRIPTS = new String[] { "script" };
    private static final String[] LIST_SERVER_KEYSTORES_ADMIN_SERVER = new String[] {
        "serverKeystore",
        "-server_name",
        "AdminServer"
    };
    private static final String[] LIST_SHARED_LIBRARIES = new String[] { "sharedLibrary" };
    private static final String[] LIST_STRUCTURED_APPLICATIONS = new String[] { "structuredApplication" };

    @BeforeAll
    static void initialize() throws Exception {
        if(!UNIT_TEST_TARGET_DIR.exists() && !UNIT_TEST_TARGET_DIR.mkdirs()) {
            throw new Exception("Unable to create unit test directory: " + UNIT_TEST_TARGET_DIR);
        }

        PlatformLogger logger = WLSDeployLogFactory.getLogger(LOGGER_NAME);
        logger.setLevel(Level.OFF);
    }

    @BeforeEach
    void setup() throws Exception {
        Files.copy(ARCHIVE_HELPER_SOURCE_ZIP, ARCHIVE_HELPER_TARGET_ZIP, StandardCopyOption.REPLACE_EXISTING);
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                                     parameterized                                         //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    @ParameterizedTest
    @CsvSource({
        "application, missing.war",
        "applicationPlan, missing.xml",
        "classpathLibrary, missing.jar",
        "coherenceConfig, missing.xml",
        "coherencePersistenceDir, active",
        "custom, missing.properties",
        "databaseWallet, wallet1",
        "domainBinScript, missing.sh",
        "domainLibrary, missing.jar",
        "fileStore, missing",
        "jmsForeignServer, missing.properties",
        "mimeMapping, missing.properties",
        "nodeManagerKeystore, missing.jks",
        "script, missing.sh",
        "serverKeystore, missing.jks",
        "sharedLibrary, missing.war",
        "sharedLibraryPlan, missing.xml",
        "structuredApplication, missingApp"
    })
    void testNoArchive_Fails(String subcommand, String name) {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "remove",
            subcommand,
            "-name",
            name
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        assertEquals(ExitCode.USAGE_ERROR, actual,
            "expected command to exit with exit code " + ExitCode.USAGE_ERROR);
    }

    @ParameterizedTest
    @ValueSource(strings = {
        "application",
        "applicationPlan",
        "classpathLibrary",
        "coherenceConfig",
        "coherencePersistenceDir",
        "custom",
        "databaseWallet",
        "domainBinScript",
        "domainLibrary",
        "fileStore",
        "jmsForeignServer",
        "mimeMapping",
        "nodeManagerKeystore",
        "script",
        "serverKeystore",
        "sharedLibrary",
        "sharedLibraryPlan",
        "structuredApplication"
    })
    void testRemoveNoName_Fails(String subcommand) {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "remove",
            subcommand,
            "-archive_file",
            ARCHIVE_HELPER_VALUE
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        assertEquals(ExitCode.USAGE_ERROR, actual,
            "expected command to exit with exit code " + ExitCode.USAGE_ERROR);
    }

    @ParameterizedTest
    @CsvSource({
        "application, missing.war",
        "applicationPlan, missing.xml",
        "classpathLibrary, missing.jar",
        "custom, missing.properties",
        "databaseWallet, missing",
        "domainBinScript, missing.sh",
        "domainLibrary, missing.jar",
        "fileStore, missing",
        "mimeMapping, missing.properties",
        "nodeManagerKeystore, missing.jks",
        "script, missing.sh",
        "sharedLibrary, missing.war",
        "sharedLibraryPlan, missing.xml",
        "structuredApplication, missingApp"
    })
    void testRemoveMissingName_ReturnsExpectedResults(String subcommand, String name) {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "remove",
            subcommand,
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-name",
            name
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        assertEquals(ExitCode.ERROR, actual,"expected command to exit with exit code " + ExitCode.ERROR);
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                                      application                                          //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    @Test
    void testRemoveExistingAppFile_ReturnsExpectedResults() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "remove",
            "application",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-name",
            "my-app.war"
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        assertEquals(ExitCode.OK, actual,"expected command to exit with exit code " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_APPLICATIONS, APPLICATIONS_CONTENT, MY_APP_WAR_CONTENTS);
    }

    @Test
    void testRemoveExistingAppDir_ReturnsExpectedResults() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "remove",
            "application",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-name",
            "my-other-app"
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        assertEquals(ExitCode.OK, actual,"expected command to exit with exit code " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_APPLICATIONS, APPLICATIONS_CONTENT, MY_OTHER_APP_DIR_CONTENTS);
    }

    @Test
    void testRemoveMissingAppForce_ReturnsExpectedResults() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "remove",
            "application",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-name",
            "foo",
            "-force"
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        assertEquals(ExitCode.OK, actual,"expected command to exit with exit code " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_APPLICATIONS, APPLICATIONS_CONTENT);
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                                   application plan                                        //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    @Test
    void testRemoveExistingAppPlan_ReturnsExpectedResults() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "remove",
            "applicationPlan",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-name",
            "my-app.xml"
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        assertEquals(ExitCode.OK, actual,"expected command to exit with exit code " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_APPLICATIONS, APPLICATIONS_CONTENT, MY_APP_DEPLOYMENT_PLAN_CONTENTS);
    }

    @Test
    void testRemoveMissingAppPlanForce_ReturnsExpectedResults() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "remove",
            "applicationPlan",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-name",
            "foo.xml",
            "-force"
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        assertEquals(ExitCode.OK, actual,"expected command to exit with exit code " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_APPLICATIONS, APPLICATIONS_CONTENT);
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                                  classpath library                                        //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    @Test
    void testRemoveExistingClasspathLibFile_ReturnsExpectedResults() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "remove",
            "classpathLibrary",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-name",
            "bar.jar"
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        assertEquals(ExitCode.OK, actual,"expected command to exit with exit code " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_CLASSPATH_LIBRARIES, CLASSPATH_LIBS_CONTENT, CLASSPATH_LIB_BAR_JAR_CONTENTS);
    }

    @Test
    void testRemoveExistingClasspathLibDir_ReturnsExpectedResults() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "remove",
            "classpathLibrary",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-name",
            "bar"
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        assertEquals(ExitCode.OK, actual,"expected command to exit with exit code " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_CLASSPATH_LIBRARIES, CLASSPATH_LIBS_CONTENT, CLASSPATH_LIB_BAR_DIR_CONTENTS);
    }

    @Test
    void testRemoveMissingClasspathLibForce_ReturnsExpectedResults() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "remove",
            "classpathLibrary",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-name",
            "missing.jar",
            "-force"
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        assertEquals(ExitCode.OK, actual,"expected command to exit with exit code " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_CLASSPATH_LIBRARIES, CLASSPATH_LIBS_CONTENT);
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                                   Coherence config                                        //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    @Test
    void testRemoveCoherenceConfigNoClusterName_Fails() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "remove",
            "coherenceConfig",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-name",
            "cache-config.xml"
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        assertEquals(ExitCode.USAGE_ERROR, actual,
            "expected command to exit with exit code " + ExitCode.USAGE_ERROR);
    }

    @Test
    void testRemoveCoherenceConfigMissingClusterName_ReturnsExpectedResults() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "remove",
            "coherenceConfig",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-cluster_name",
            "missing",
            "-name",
            "cache-config.xml"
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        assertEquals(ExitCode.ERROR, actual,"expected command to exit with exit code " + ExitCode.ERROR);
    }

    @Test
    void testRemoveCoherenceConfigMissingName_ReturnsExpectedResults() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "remove",
            "coherenceConfig",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-cluster_name",
            "mycluster",
            "-name",
            "missing.xml"
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        assertEquals(ExitCode.ERROR, actual,"expected command to exit with exit code " + ExitCode.ERROR);
    }

    @Test
    void testRemoveExistingCoherenceConfig_ReturnsExpectedResults() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "remove",
            "coherenceConfig",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-cluster_name",
            "mycluster",
            "-name",
            "cache-config.xml"
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        assertEquals(ExitCode.OK, actual,"expected command to exit with exit code " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_COHERENCE_MY_CLUSTER, COHERENCE_MYCLUSTER_CONTENTS,
            COHERENCE_MYCLUSTER_CONFIG_FILE_CONTENTS);
    }

    @Test
    void testRemoveCoherenceConfigMissingNameForce_ReturnsExpectedResults() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "remove",
            "coherenceConfig",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-cluster_name",
            "mycluster",
            "-name",
            "missing.xml",
            "-force"
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        assertEquals(ExitCode.OK, actual,"expected command to exit with exit code " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_COHERENCE_MY_CLUSTER, COHERENCE_MYCLUSTER_CONTENTS);
    }

    @Test
    void testRemoveCoherenceConfigMissingClusterNameForce_ReturnsExpectedResults() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "remove",
            "coherenceConfig",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-cluster_name",
            "missing",
            "-name",
            "cache-config.xml",
            "-force"
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        assertEquals(ExitCode.OK, actual,"expected command to exit with exit code " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_COHERENCE_MY_CLUSTER, COHERENCE_MYCLUSTER_CONTENTS);
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                              Coherence persistence dir                                    //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    @Test
    void testRemoveCoherencePersistenceDirNoClusterName_Fails() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "remove",
            "coherencePersistenceDir",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-name",
            "active"
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        assertEquals(ExitCode.USAGE_ERROR, actual,
            "expected command to exit with exit code " + ExitCode.USAGE_ERROR);
    }

    @Test
    void testRemoveCoherencePersistenceDirMissingClusterName_ReturnsExpectedResults() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "remove",
            "coherencePersistenceDir",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-cluster_name",
            "missing",
            "-name",
            "active"
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        assertEquals(ExitCode.ERROR, actual,"expected command to exit with exit code " + ExitCode.ERROR);
    }

    @Test
    void testRemoveCoherencePersistenceDirMissingName_ReturnsExpectedResults() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "remove",
            "coherencePersistenceDir",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-cluster_name",
            "mycluster",
            "-name",
            "missing"
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        assertEquals(ExitCode.ERROR, actual,"expected command to exit with exit code " + ExitCode.ERROR);
    }

    @Test
    void testRemoveExistingCoherencePersistenceDir_ReturnsExpectedResults() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "remove",
            "coherencePersistenceDir",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-cluster_name",
            "mycluster",
            "-name",
            "active"
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        assertEquals(ExitCode.OK, actual,"expected command to exit with exit code " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_COHERENCE_MY_CLUSTER, COHERENCE_MYCLUSTER_CONTENTS,
            COHERENCE_MYCLUSTER_PERSISTENT_DIR_ACTIVE_CONTENTS);
    }

    @Test
    void testRemoveCoherencePersistenceDirMissingNameForce_ReturnsExpectedResults() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "remove",
            "coherencePersistenceDir",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-cluster_name",
            "mycluster",
            "-name",
            "missing.xml",
            "-force"
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        assertEquals(ExitCode.OK, actual,"expected command to exit with exit code " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_COHERENCE_MY_CLUSTER, COHERENCE_MYCLUSTER_CONTENTS);
    }

    @Test
    void testRemoveCoherencePersistenceDirMissingClusterNameForce_ReturnsExpectedResults() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "remove",
            "coherencePersistenceDir",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-cluster_name",
            "missing",
            "-name",
            "cache-config.xml",
            "-force"
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        assertEquals(ExitCode.OK, actual,"expected command to exit with exit code " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_COHERENCE_MY_CLUSTER, COHERENCE_MYCLUSTER_CONTENTS);
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                                        custom                                             //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    @Test
    void testRemoveExistingCustomFile_ReturnsExpectedResults() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "remove",
            "custom",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-name",
            "foo.properties"
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        assertEquals(ExitCode.OK, actual,"expected command to exit with exit code " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_CUSTOM_ENTRIES, CUSTOM_CONTENT, CUSTOM_FOO_PROPERTIES_CONTENTS);
    }

    @Test
    void testRemoveExistingCustomNestedFile_ReturnsExpectedResults() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "remove",
            "custom",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-name",
            "mydir/bar.properties"
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        assertEquals(ExitCode.OK, actual,"expected command to exit with exit code " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_CUSTOM_ENTRIES, CUSTOM_CONTENT, CUSTOM_MYDIR_CONTENTS);
    }

    @Test
    void testRemoveExistingCustomDir_ReturnsExpectedResults() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "remove",
            "custom",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-name",
            "mydir"
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        assertEquals(ExitCode.OK, actual,"expected command to exit with exit code " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_CUSTOM_ENTRIES, CUSTOM_CONTENT, CUSTOM_MYDIR_CONTENTS);
    }

    @Test
    void testRemoveMissingCustomForce_ReturnsExpectedResults() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "remove",
            "custom",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-name",
            "missing",
            "-force"
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        assertEquals(ExitCode.OK, actual,"expected command to exit with exit code " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_CUSTOM_ENTRIES, CUSTOM_CONTENT);
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                                   database wallet                                         //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    @Test
    void testRemoveExistingDatabaseWalletZip_ReturnsExpectedResults() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "remove",
            "databaseWallet",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-name",
            "wallet1"
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        assertEquals(ExitCode.OK, actual,"expected command to exit with exit code " + ExitCode.OK);
        // Removing the only jar so the test will also remove wlsdeploy/classpathLibraries/
        assertArchiveInExpectedState(LIST_DATABASE_WALLETS, DATABASE_WALLETS_CONTENT, DATABASE_WALLET_WALLET1_CONTENTS);
    }

    @Test
    void testRemoveExistingDatabaseWalletExploded_ReturnsExpectedResults() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "remove",
            "databaseWallet",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-name",
            DEFAULT_RCU_WALLET_NAME
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        assertEquals(ExitCode.OK, actual,"expected command to exit with exit code " + ExitCode.OK);
        // Removing the only jar so the test will also remove wlsdeploy/classpathLibraries/
        assertArchiveInExpectedState(LIST_DATABASE_WALLETS, DATABASE_WALLETS_CONTENT, DATABASE_WALLET_RCU_CONTENTS);
    }

    @Test
    void testRemoveMissingDatabaseWalletForce_ReturnsExpectedResults() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "remove",
            "databaseWallet",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-name",
            "missing",
            "-force"
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        assertEquals(ExitCode.OK, actual,"expected command to exit with exit code " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_DATABASE_WALLETS, DATABASE_WALLETS_CONTENT);
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                                $DOMAIN_HOME/bin script                                    //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    @Test
    void testRemoveExistingDomainBinFile_ReturnsExpectedResults() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "remove",
            "domainBinScript",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-name",
            "setUserOverrides.sh"
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        assertEquals(ExitCode.OK, actual,"expected command to exit with exit code " + ExitCode.OK);
        // Removing the only script so the test will also remove wlsdeploy/domainBin/
        assertArchiveInExpectedState(LIST_DOMAIN_BIN_SCRIPTS, DOMAIN_BIN_CONTENT, DOMAIN_BIN_CONTENT);
    }

    @Test
    void testRemoveMissingDomainBinForce_ReturnsExpectedResults() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "remove",
            "domainBinScript",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-name",
            "missing.sh",
            "-force"
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        assertEquals(ExitCode.OK, actual,"expected command to exit with exit code " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_DOMAIN_BIN_SCRIPTS, DOMAIN_BIN_CONTENT);
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                                $DOMAIN_HOME/lib library                                   //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    @Test
    void testRemoveExistingDomainLibFile_ReturnsExpectedResults() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "remove",
            "domainLibrary",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-name",
            "foo.jar"
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        assertEquals(ExitCode.OK, actual,"expected command to exit with exit code " + ExitCode.OK);
        // Removing the only jar so the test will also remove wlsdeploy/domainLibraries/
        assertArchiveInExpectedState(LIST_DOMAIN_LIBRARIES, DOMAIN_LIB_CONTENT, DOMAIN_LIB_CONTENT);
    }

    @Test
    void testRemoveMissingDomainLibForce_ReturnsExpectedResults() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "remove",
            "domainLibrary",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-name",
            "missing.jar",
            "-force"
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        assertEquals(ExitCode.OK, actual,"expected command to exit with exit code " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_DOMAIN_LIBRARIES, DOMAIN_LIB_CONTENT);
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                                      file store                                           //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    @Test
    void testRemoveExistingFileStore_ReturnsExpectedResults() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "remove",
            "fileStore",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-name",
            "fs2"
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        assertEquals(ExitCode.OK, actual,"expected command to exit with exit code " + ExitCode.OK);
        // Removing the only script so the test will also remove wlsdeploy/config/
        assertArchiveInExpectedState(LIST_FILE_STORES, FILE_STORES_CONTENT, FILE_STORES_FS2_CONTENTS);
    }

    @Test
    void testRemoveMissingFileStoreForce_ReturnsExpectedResults() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "remove",
            "fileStore",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-name",
            "missing",
            "-force"
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        assertEquals(ExitCode.OK, actual,"expected command to exit with exit code " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_FILE_STORES, FILE_STORES_CONTENT);
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                              JMS Foreign Server binding                                   //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    @Test
    void testRemoveForeignServerBindingNoForeignServerName_Fails() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "remove",
            "jmsForeignServer",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-name",
            "jndi.properties"
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        assertEquals(ExitCode.USAGE_ERROR, actual,
            "expected command to exit with exit code " + ExitCode.USAGE_ERROR);
    }

    @Test
    void testRemoveForeignServerBindingMissingForeignServerName_ReturnsExpectedResults() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "remove",
            "jmsForeignServer",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-foreign_server_name",
            "missing",
            "-name",
            "jndi.properties"
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        assertEquals(ExitCode.ERROR, actual,"expected command to exit with exit code " + ExitCode.ERROR);
    }

    @Test
    void testRemoveForeignServerBindingMissingName_ReturnsExpectedResults() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "remove",
            "jmsForeignServer",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-foreign_server_name",
            "fs1",
            "-name",
            "missing.properties"
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        assertEquals(ExitCode.ERROR, actual,"expected command to exit with exit code " + ExitCode.ERROR);
    }

    @Test
    void testRemoveExistingForeignServerBinding_ReturnsExpectedResults() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "remove",
            "jmsForeignServer",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-foreign_server_name",
            "fs1",
            "-name",
            "jndi.properties"
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        assertEquals(ExitCode.OK, actual,"expected command to exit with exit code " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_FOREIGN_SERVERS_FS1, FOREIGN_SERVERS_FS1_CONTENTS,
            FOREIGN_SERVERS_FS1_CONTENTS);
    }

    @Test
    void testRemoveForeignServerBindingMissingNameForce_ReturnsExpectedResults() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "remove",
            "jmsForeignServer",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-foreign_server_name",
            "fs1",
            "-name",
            "missing.properties",
            "-force"
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        assertEquals(ExitCode.OK, actual,"expected command to exit with exit code " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_FOREIGN_SERVERS_FS1, FOREIGN_SERVERS_FS1_CONTENTS);
    }

    @Test
    void testRemoveForeignServerBindingMissingForeignServerNameForce_ReturnsExpectedResults() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "remove",
            "jmsForeignServer",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-foreign_server_name",
            "missing",
            "-name",
            "jndi.properties",
            "-force"
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        assertEquals(ExitCode.OK, actual,"expected command to exit with exit code " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_FOREIGN_SERVERS_FS1, FOREIGN_SERVERS_FS1_CONTENTS);
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                                     MIME mapping                                          //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    @Test
    void testRemoveExistingMIMEMapping_ReturnsExpectedResults() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "remove",
            "mimeMapping",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-name",
            "mimemappings.properties"
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        assertEquals(ExitCode.OK, actual,"expected command to exit with exit code " + ExitCode.OK);
        // Removing the only script so the test will also remove wlsdeploy/config/
        assertArchiveInExpectedState(LIST_MIME_MAPPINGS, MIME_MAPPINGS_CONTENT, MIME_MAPPINGS_CONTENT);
    }

    @Test
    void testRemoveMissingMIMEMappingForce_ReturnsExpectedResults() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "remove",
            "mimeMapping",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-name",
            "missing.properties",
            "-force"
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        assertEquals(ExitCode.OK, actual,"expected command to exit with exit code " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_MIME_MAPPINGS, MIME_MAPPINGS_CONTENT);
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                                node manager keystore                                      //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    @Test
    void testRemoveExistingNodeManagerKeystoreFile_ReturnsExpectedResults() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "remove",
            "nodeManagerKeystore",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-name",
            "nmIdentity.jks"
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        assertEquals(ExitCode.OK, actual,"expected command to exit with exit code " + ExitCode.OK);
        // Removing the only jar so the test will also remove wlsdeploy/domainLibraries/
        assertArchiveInExpectedState(LIST_NODE_MANAGER_KEYSTORES, NODE_MANAGER_CONTENT,
            NODE_MANAGER_IDENTITY_JKS_CONTENTS);
    }

    @Test
    void testRemoveMissingNodeManagerKeystoreForce_ReturnsExpectedResults() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "remove",
            "nodeManagerKeystore",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-name",
            "missing.jks",
            "-force"
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        assertEquals(ExitCode.OK, actual,"expected command to exit with exit code " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_NODE_MANAGER_KEYSTORES, NODE_MANAGER_CONTENT);
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                                     OPSS wallet                                           //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    @Test
    void testRemoveExistingOPSSWallet_ReturnsExpectedResults() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "remove",
            "opssWallet",
            "-archive_file",
            ARCHIVE_HELPER_VALUE
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        assertEquals(ExitCode.OK, actual,"expected command to exit with exit code " + ExitCode.OK);
        // Removing the only jar so the test will also remove wlsdeploy/opsswallet/
        assertArchiveInExpectedState(LIST_OPSS_WALLET, OPSS_WALLET_CONTENT, OPSS_WALLET_CONTENT);
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                                      RCU wallet                                           //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    @Test
    void testRemoveExistingRCUWallet_ReturnsExpectedResults() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "remove",
            "rcuWallet",
            "-archive_file",
            ARCHIVE_HELPER_VALUE
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        assertEquals(ExitCode.OK, actual,"expected command to exit with exit code " + ExitCode.OK);
        // Removing the only jar so the test will also remove wlsdeploy/opsswallet/
        assertArchiveInExpectedState(LIST_DATABASE_WALLETS, DATABASE_WALLETS_CONTENT, DATABASE_WALLET_RCU_CONTENTS);
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                                        script                                             //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    @Test
    void testRemoveExistingScript_ReturnsExpectedResults() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "remove",
            "script",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-name",
            "my_fancy_script.sh"
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        assertEquals(ExitCode.OK, actual,"expected command to exit with exit code " + ExitCode.OK);
        // Removing the only script so the test will also remove wlsdeploy/scripts/
        assertArchiveInExpectedState(LIST_SCRIPTS, SCRIPTS_CONTENT, SCRIPTS_CONTENT);
    }

    @Test
    void testRemoveMissingScriptForce_ReturnsExpectedResults() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "remove",
            "script",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-name",
            "missing.sh",
            "-force"
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        assertEquals(ExitCode.OK, actual,"expected command to exit with exit code " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_SCRIPTS, SCRIPTS_CONTENT);
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                                   server keystore                                         //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    @Test
    void testRemoveServerKeystoreNoServerName_Fails() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "remove",
            "serverKeystore",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-name",
            "identity.jks"
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        assertEquals(ExitCode.USAGE_ERROR, actual,
            "expected command to exit with exit code " + ExitCode.USAGE_ERROR);
    }

    @Test
    void testRemoveServerKeystoreMissingServerName_ReturnsExpectedResults() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "remove",
            "serverKeystore",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-server_name",
            "missing",
            "-name",
            "identity.jks"
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        assertEquals(ExitCode.ERROR, actual,"expected command to exit with exit code " + ExitCode.ERROR);
    }

    @Test
    void testRemoveServerKeystoreMissingName_ReturnsExpectedResults() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "remove",
            "serverKeystore",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-server_name",
            "AdminServer",
            "-name",
            "missing.jks"
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        assertEquals(ExitCode.ERROR, actual,"expected command to exit with exit code " + ExitCode.ERROR);
    }

    @Test
    void testRemoveExistingServerKeystore_ReturnsExpectedResults() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "remove",
            "serverKeystore",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-server_name",
            "AdminServer",
            "-name",
            "identity.jks"
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        assertEquals(ExitCode.OK, actual,"expected command to exit with exit code " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_SERVER_KEYSTORES_ADMIN_SERVER, SERVERS_ADMIN_SERVER_CONTENTS,
            SERVERS_ADMIN_SERVER_IDENTITY_JKS_CONTENTS);
    }

    @Test
    void testRemoveServerKeystoreMissingNameForce_ReturnsExpectedResults() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "remove",
            "serverKeystore",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-server_name",
            "AdminServer",
            "-name",
            "missing.jks",
            "-force"
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        assertEquals(ExitCode.OK, actual,"expected command to exit with exit code " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_SERVER_KEYSTORES_ADMIN_SERVER, SERVERS_ADMIN_SERVER_CONTENTS);
    }

    @Test
    void testRemoveServerKeystoreMissingServerNameForce_ReturnsExpectedResults() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "remove",
            "serverKeystore",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-server_name",
            "missing",
            "-name",
            "identity.jks",
            "-force"
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        assertEquals(ExitCode.OK, actual,"expected command to exit with exit code " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_SERVER_KEYSTORES_ADMIN_SERVER, SERVERS_ADMIN_SERVER_CONTENTS);
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                                    shared library                                         //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    @Test
    void testRemoveExistingSharedLibFile_ReturnsExpectedResults() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "remove",
            "sharedLibrary",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-name",
            "my-lib.war"
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        assertEquals(ExitCode.OK, actual,"expected command to exit with exit code " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_SHARED_LIBRARIES, SHARED_LIBS_CONTENT, SHARED_LIBS_MY_LIB_WAR_CONTENTS);
    }

    @Test
    void testRemoveExistingSharedLibDir_ReturnsExpectedResults() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "remove",
            "sharedLibrary",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-name",
            "my-other-lib"
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        assertEquals(ExitCode.OK, actual,"expected command to exit with exit code " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_SHARED_LIBRARIES, SHARED_LIBS_CONTENT, SHARED_LIBS_MY_OTHER_LIB_CONTENTS);
    }

    @Test
    void testRemoveMissingSharedLibForce_ReturnsExpectedResults() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "remove",
            "sharedLibrary",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-name",
            "foo",
            "-force"
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        assertEquals(ExitCode.OK, actual,"expected command to exit with exit code " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_SHARED_LIBRARIES, SHARED_LIBS_CONTENT);
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                                 shared library plan                                       //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    @Test
    void testRemoveExistingSharedLibPlan_ReturnsExpectedResults() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "remove",
            "sharedLibraryPlan",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-name",
            "my-lib.xml"
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        assertEquals(ExitCode.OK, actual,"expected command to exit with exit code " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_SHARED_LIBRARIES, SHARED_LIBS_CONTENT, SHARED_LIBS_MY_LIB_XML_CONTENTS);
    }

    @Test
    void testRemoveMissingSharedLibPlanForce_ReturnsExpectedResults() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "remove",
            "sharedLibraryPlan",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-name",
            "foo.xml",
            "-force"
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        assertEquals(ExitCode.OK, actual,"expected command to exit with exit code " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_SHARED_LIBRARIES, SHARED_LIBS_CONTENT);
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                                structured application                                     //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    @Test
    void testRemoveExistingStructuredApp_ReturnsExpectedResults() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "remove",
            "structuredApplication",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-name",
            "webapp"
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        assertEquals(ExitCode.OK, actual,"expected command to exit with exit code " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_STRUCTURED_APPLICATIONS, STRUCTURED_APPS_CONTENT,
            STRUCTURED_APP_WEBAPP_CONTENTS);
    }

    @Test
    void testRemoveMissingStructuredAppForce_ReturnsExpectedResults() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "remove",
            "structuredApplication",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-name",
            "foo",
            "-force"
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        assertEquals(ExitCode.OK, actual,"expected command to exit with exit code " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_STRUCTURED_APPLICATIONS, STRUCTURED_APPS_CONTENT);
    }


    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                                Private Helper Methods                                     //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    private void assertArchiveInExpectedState(String[] remainingArgs, String[] originalContent,
                                              String[]... removedContent) throws Exception {
        String[] args = new String[remainingArgs.length + 3];
        args[0] = "list";
        System.arraycopy(remainingArgs, 0, args, 1, remainingArgs.length);
        args[remainingArgs.length + 1] = "-archive_file";
        args[remainingArgs.length + 2] = ARCHIVE_HELPER_VALUE;

        List<String> remainingEntries = getRemainingEntries(args);
        List<String> expectedEntries = getExpectedEntries(originalContent, removedContent);
        assertEquals(expectedEntries.size(), remainingEntries.size(), "expected zip file to contain " +
            expectedEntries.size());
        for (String actualLine : remainingEntries) {
            assertTrue(expectedEntries.contains(actualLine), actualLine + " not in expected output");
        }
    }

    private List<String> getRemainingEntries(String... args) throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
            if (actual != ExitCode.OK) {
                throw new ArchiveHelperException(actual,
                    "Failed to get remaining entries for args = {0}", Arrays.toString(args));
            }
        }

        String[] outputLines = outStringWriter.getBuffer().toString().trim().split(System.lineSeparator());
        if (outputLines.length == 0 || (outputLines.length == 1 && StringUtils.isEmpty(outputLines[0]))) {
            return new ArrayList<>();
        } else {
            return Arrays.asList(outputLines);
        }
    }

    private List<String> getExpectedEntries(String[] expected, String[]... removeLists) {
        List<String> expectedPaths = new ArrayList<>(Arrays.asList(expected));

        for (String[] removeList : removeLists) {
            for (String removeItem : removeList) {
                expectedPaths.remove(removeItem);
            }
        }
        return expectedPaths;
    }
}
