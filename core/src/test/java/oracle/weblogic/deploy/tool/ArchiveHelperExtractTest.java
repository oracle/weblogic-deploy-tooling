/*
 * Copyright (c) 2023, 2025, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.tool;

import java.io.File;
import java.io.PrintWriter;
import java.io.StringWriter;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.util.Arrays;
import java.util.List;
import java.util.logging.Level;

import oracle.weblogic.deploy.logging.PlatformLogger;
import oracle.weblogic.deploy.logging.WLSDeployLogFactory;
import oracle.weblogic.deploy.util.ExitCode;
import oracle.weblogic.deploy.util.FileUtils;
import oracle.weblogic.deploy.util.WLSDeployZipFileTest;

import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.CsvSource;
import org.junit.jupiter.params.provider.ValueSource;

import static oracle.weblogic.deploy.tool.ArchiveHelper.LOGGER_NAME;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.ALL_CONTENT;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.CLASSPATH_LIB_BAR_DIR_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.CLASSPATH_LIB_BAR_JAR_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.COHERENCE_MYCLUSTER_CONFIG_FILE_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.COHERENCE_MYCLUSTER_PERSISTENT_DIR_ACTIVE_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.CUSTOM_FOO_PROPERTIES_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.CUSTOM_MYDIR_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.DATABASE_WALLET_RCU_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.DATABASE_WALLET_WALLET1_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.DOMAIN_BIN_SET_USER_OVERRIDES_SH_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.DOMAIN_LIB_FOO_JAR_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.FOREIGN_SERVERS_FS1_JNDI_PROPERTIES_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.MIME_MAPPING_PROPERTIES_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.MY_APP_DEPLOYMENT_PLAN_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.MY_OTHER_APP_DIR_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.MY_OTHER_APP_WAR_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.NODE_MANAGER_IDENTITY_JKS_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.OPSS_WALLET_CONTENT;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.SAML2_SP_PROPERTIES_CONTENT;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.SCRIPTS_FANCY_SCRIPT_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.SERVERS_ADMIN_SERVER_IDENTITY_JKS_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.SERVER_TEMPLATE_IDENTITY_JKS_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.SHARED_LIBS_MY_LIB_WAR_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.SHARED_LIBS_MY_LIB_XML_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.SHARED_LIBS_MY_OTHER_LIB_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.STRUCTURED_APP_WEBAPP_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.WRC_EXTENSION_FILE_CONTENT;
import static oracle.weblogic.deploy.util.WLSDeployArchive.DEFAULT_RCU_WALLET_NAME;
import static oracle.weblogic.deploy.util.WLSDeployArchive.ZIP_SEP;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

public class ArchiveHelperExtractTest {
    public static final File UNIT_TEST_SOURCE_DIR = new File(WLSDeployZipFileTest.UNIT_TEST_SOURCE_DIR);
    private static final File UNIT_TEST_TARGET_DIR =
        new File(new File(WLSDeployZipFileTest.UNIT_TEST_TARGET_DIR, "archiveHelper"), "extract");
    private static final String TARGET_VALUE = FileUtils.getCanonicalPath(UNIT_TEST_TARGET_DIR);
    private static final File WLSDEPLOY_TARGET_DIR = new File(UNIT_TEST_TARGET_DIR, "wlsdeploy");

    private static final Path ARCHIVE_HELPER_SOURCE_ZIP =
        new File(UNIT_TEST_SOURCE_DIR, "archive-helper-test.zip").toPath();
    private static final Path ARCHIVE_HELPER_TARGET_ZIP =
        new File(UNIT_TEST_TARGET_DIR, "archive-helper-test.zip").toPath();
    private static final String ARCHIVE_HELPER_VALUE = ARCHIVE_HELPER_TARGET_ZIP.toFile().getAbsolutePath();

    @BeforeAll
    static void initialize() throws Exception {
        if(!UNIT_TEST_TARGET_DIR.exists() && !UNIT_TEST_TARGET_DIR.mkdirs()) {
            throw new Exception("Unable to create unit test directory: " + UNIT_TEST_TARGET_DIR);
        }
        Files.copy(ARCHIVE_HELPER_SOURCE_ZIP, ARCHIVE_HELPER_TARGET_ZIP, StandardCopyOption.REPLACE_EXISTING);

        PlatformLogger logger = WLSDeployLogFactory.getLogger(LOGGER_NAME);
        logger.setLevel(Level.OFF);
    }

    @BeforeEach
    void setup() {
        if (WLSDEPLOY_TARGET_DIR.exists()) {
            FileUtils.deleteDirectory(WLSDEPLOY_TARGET_DIR);
        }
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
        "coherencePersistenceDir, missing",
        "custom, missing",
        "databaseWallet, missing",
        "domainBinScript, missing.sh",
        "domainLibrary, missing.jar",
        "fileStore, missing",
        "jmsForeignServer, missing.properties",
        "mimeMapping, missing.properties",
        "nodeManagerKeystore, missing.jks",
        "saml2InitializationData, missing.xml",
        "script, missing.sh",
        "serverKeystore, missing.jks",
        "serverTemplateKeystore, missing.jks",
        "sharedLibrary, missing.war",
        "sharedLibraryPlan, missing.xml",
        "structuredApplication, missing",
        "weblogicRemoteConsoleExtension, missing.war"
    })
    void testExtractNoArchive_Fails(String subcommand, String name) {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "extract",
            subcommand,
            "-target",
            TARGET_VALUE,
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
    @CsvSource({
        "application, missing.war",
        "applicationPlan, missing.xml",
        "classpathLibrary, missing.jar",
        "coherenceConfig, missing.xml",
        "coherencePersistenceDir, missing",
        "custom, missing",
        "databaseWallet, missing",
        "domainBinScript, missing.sh",
        "domainLibrary, missing.jar",
        "fileStore, missing",
        "jmsForeignServer, missing.properties",
        "mimeMapping, missing.properties",
        "nodeManagerKeystore, missing.jks",
        "saml2InitializationData, missing.xml",
        "script, missing.sh",
        "serverKeystore, missing.jks",
        "serverTemplateKeystore, missing.jks",
        "sharedLibrary, missing.war",
        "sharedLibraryPlan, missing.xml",
        "structuredApplication, missing",
        "weblogicRemoteConsoleExtension, missing.war"
    })
    void testExtractNoTarget_Fails(String subcommand, String name) {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "extract",
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
        "saml2InitializationData",
        "script",
        "serverKeystore",
        "serverTemplateKeystore",
        "sharedLibrary",
        "sharedLibraryPlan",
        "structuredApplication",
        "weblogicRemoteConsoleExtension"
    })
    void testExtractNoName_Fails(String subcommand) {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "extract",
            subcommand,
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-target",
            TARGET_VALUE
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
        "custom, missing",
        "databaseWallet, missing",
        "domainBinScript, missing.sh",
        "domainLibrary, missing.jar",
        "fileStore, missing",
        "mimeMapping, missing.properties",
        "nodeManagerKeystore, missing.jks",
        "saml2InitializationData, missing.xml",
        "script, missing.sh",
        "sharedLibrary, missing.war",
        "sharedLibraryPlan, missing.xml",
        "structuredApplication, missing",
        "weblogicRemoteConsoleExtension, missing.war"
    })
    void testExtractBadName_Fails(String subcommand, String name) {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "extract",
            subcommand,
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-target",
            TARGET_VALUE,
            "-name",
            name
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        assertEquals(ExitCode.ERROR, actual,
            "expected command to exit with exit code " + ExitCode.ERROR);
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                                        all                                                //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    @Test
    void testExtractAllNoArchive_Fails() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "extract",
            "all",
            "-target",
            TARGET_VALUE
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
    void testExtractAllNoTarget_Fails() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "extract",
            "all",
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

    @Test
    void testExtractAll_ProducesExpectedResults() {
        assertExtractDirectoryIsClean();
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "extract",
            "all",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-target",
            TARGET_VALUE
        };
        List<String> expectedPaths = Arrays.asList(ALL_CONTENT);

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(0, actual, "expected command to exit with exit code 0");
        assertExtractedFilesMatch(expectedPaths);
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                                    application                                            //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    @Test
    void testExtractExistingApplicationFile_ProducesExpectedResults() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "extract",
            "application",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-target",
            TARGET_VALUE,
            "-name",
            "my-other-app.war"
        };
        List<String> expectedPaths = Arrays.asList(MY_OTHER_APP_WAR_CONTENTS);

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(0, actual, "expected command to exit with exit code 0");
        assertExtractedFilesMatch(expectedPaths);
    }

    @Test
    void testExtractExistingApplicationDir_ProducesExpectedResults() {
        assertExtractDirectoryIsClean();
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "extract",
            "application",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-target",
            TARGET_VALUE,
            "-name",
            "my-other-app"
        };
        List<String> expectedPaths = Arrays.asList(MY_OTHER_APP_DIR_CONTENTS);

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(0, actual, "expected command to exit with exit code 0");
        assertExtractedFilesMatch(expectedPaths);
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                                 application plan                                          //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    @Test
    void testExtractExistingApplicationPlanFile_ProducesExpectedResults() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "extract",
            "applicationPlan",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-target",
            TARGET_VALUE,
            "-name",
            "my-app.xml"
        };
        List<String> expectedPaths = Arrays.asList(MY_APP_DEPLOYMENT_PLAN_CONTENTS);

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(0, actual, "expected command to exit with exit code 0");
        assertExtractedFilesMatch(expectedPaths);
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                                classpath library                                          //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    @Test
    void testExtractExistingClasspathLibraryFile_ProducesExpectedResults() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "extract",
            "classpathLibrary",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-target",
            TARGET_VALUE,
            "-name",
            "bar.jar"
        };
        List<String> expectedPaths = Arrays.asList(CLASSPATH_LIB_BAR_JAR_CONTENTS);

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(0, actual, "expected command to exit with exit code 0");
        assertExtractedFilesMatch(expectedPaths);
    }

    @Test
    void testExtractExistingClasspathLibraryDir_ProducesExpectedResults() {
        assertExtractDirectoryIsClean();
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "extract",
            "classpathLibrary",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-target",
            TARGET_VALUE,
            "-name",
            "bar"
        };
        List<String> expectedPaths = Arrays.asList(CLASSPATH_LIB_BAR_DIR_CONTENTS);

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(0, actual, "expected command to exit with exit code 0");
        assertExtractedFilesMatch(expectedPaths);
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                                  Coherence config                                         //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    @Test
    void testExtractCoherenceConfigBadClusterName_Fails() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "extract",
            "coherenceConfig",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-target",
            TARGET_VALUE,
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
        assertEquals(ExitCode.ERROR, actual,
            "expected command to exit with exit code " + ExitCode.ERROR);
    }

    @Test
    void testExtractCoherenceConfigBadName_Fails() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "extract",
            "coherenceConfig",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-target",
            TARGET_VALUE,
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
        assertEquals(ExitCode.ERROR, actual,
            "expected command to exit with exit code " + ExitCode.ERROR);
    }

    @Test
    void testExtractExistingCoherenceConfigFile_ProducesExpectedResults() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "extract",
            "coherenceConfig",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-target",
            TARGET_VALUE,
            "-cluster_name",
            "mycluster",
            "-name",
            "cache-config.xml"
        };
        List<String> expectedPaths = Arrays.asList(COHERENCE_MYCLUSTER_CONFIG_FILE_CONTENTS);

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(0, actual, "expected command to exit with exit code 0");
        assertExtractedFilesMatch(expectedPaths);
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                           Coherence persistence directory                                 //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    @Test
    void testExtractCoherencePersistenceDirBadClusterName_Fails() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "extract",
            "coherencePersistenceDir",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-target",
            TARGET_VALUE,
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
        assertEquals(ExitCode.ERROR, actual,
            "expected command to exit with exit code " + ExitCode.ERROR);
    }

    @Test
    void testExtractCoherencePersistenceDirBadName_Fails() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "extract",
            "coherencePersistenceDir",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-target",
            TARGET_VALUE,
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
        assertEquals(ExitCode.ERROR, actual,
            "expected command to exit with exit code " + ExitCode.ERROR);
    }

    @Test
    void testExtractExistingCoherencePersistenceDir_ProducesExpectedResults() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "extract",
            "coherencePersistenceDir",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-target",
            TARGET_VALUE,
            "-cluster_name",
            "mycluster",
            "-name",
            "active"
        };
        List<String> expectedPaths = Arrays.asList(COHERENCE_MYCLUSTER_PERSISTENT_DIR_ACTIVE_CONTENTS);

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(0, actual, "expected command to exit with exit code 0");
        assertExtractedFilesMatch(expectedPaths);
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                                       custom                                              //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    @Test
    void testExtractExistingCustomFile_ProducesExpectedResults() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "extract",
            "custom",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-target",
            TARGET_VALUE,
            "-name",
            "foo.properties"
        };
        List<String> expectedPaths = Arrays.asList(CUSTOM_FOO_PROPERTIES_CONTENTS);

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(0, actual, "expected command to exit with exit code 0");
        assertExtractedFilesMatch(expectedPaths);
    }

    @Test
    void testExtractExistingCustomDir_ProducesExpectedResults() {
        assertExtractDirectoryIsClean();
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "extract",
            "custom",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-target",
            TARGET_VALUE,
            "-name",
            "mydir"
        };
        List<String> expectedPaths = Arrays.asList(CUSTOM_MYDIR_CONTENTS);

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(0, actual, "expected command to exit with exit code 0");
        assertExtractedFilesMatch(expectedPaths);
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                                 database wallet                                           //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    @Test
    void testExtractExistingDatabaseWalletFile_ProducesExpectedResults() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "extract",
            "databaseWallet",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-target",
            TARGET_VALUE,
            "-name",
            "wallet1"
        };
        List<String> expectedPaths = Arrays.asList(DATABASE_WALLET_WALLET1_CONTENTS);

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(0, actual, "expected command to exit with exit code 0");
        assertExtractedFilesMatch(expectedPaths);
    }

    @Test
    void testExtractExistingDatabaseWalletDir_ProducesExpectedResults() {
        assertExtractDirectoryIsClean();
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "extract",
            "databaseWallet",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-target",
            TARGET_VALUE,
            "-name",
            DEFAULT_RCU_WALLET_NAME
        };
        List<String> expectedPaths = Arrays.asList(DATABASE_WALLET_RCU_CONTENTS);

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(0, actual, "expected command to exit with exit code 0");
        assertExtractedFilesMatch(expectedPaths);
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                             $DOMAIN_HOME/bin script                                       //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    @Test
    void testExtractExistingDomainBinScript_ProducesExpectedResults() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "extract",
            "domainBinScript",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-target",
            TARGET_VALUE,
            "-name",
            "setUserOverrides.sh"
        };
        List<String> expectedPaths = Arrays.asList(DOMAIN_BIN_SET_USER_OVERRIDES_SH_CONTENTS);

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(0, actual, "expected command to exit with exit code 0");
        assertExtractedFilesMatch(expectedPaths);
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                              $DOMAIN_HOME/lib library                                     //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    @Test
    void testExtractExistingDomainLibraryFile_ProducesExpectedResults() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "extract",
            "domainLibrary",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-target",
            TARGET_VALUE,
            "-name",
            "foo.jar"
        };
        List<String> expectedPaths = Arrays.asList(DOMAIN_LIB_FOO_JAR_CONTENTS);

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(0, actual, "expected command to exit with exit code 0");
        assertExtractedFilesMatch(expectedPaths);
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                                JMS Foreign Server binding                                 //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    @Test
    void testExtractForeignServerBindingBadForeignServerName_Fails() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "extract",
            "jmsForeignServer",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-target",
            TARGET_VALUE,
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
        assertEquals(ExitCode.ERROR, actual,
            "expected command to exit with exit code " + ExitCode.ERROR);
    }

    @Test
    void testExtractForeignServerBindingBadName_Fails() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "extract",
            "jmsForeignServer",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-target",
            TARGET_VALUE,
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
        assertEquals(ExitCode.ERROR, actual,
            "expected command to exit with exit code " + ExitCode.ERROR);
    }

    @Test
    void testExtractExistingForeignServerBindingFile_ProducesExpectedResults() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "extract",
            "jmsForeignServer",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-target",
            TARGET_VALUE,
            "-foreign_server_name",
            "fs1",
            "-name",
            "jndi.properties"
        };
        List<String> expectedPaths = Arrays.asList(FOREIGN_SERVERS_FS1_JNDI_PROPERTIES_CONTENTS);

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(0, actual, "expected command to exit with exit code 0");
        assertExtractedFilesMatch(expectedPaths);
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                                   MIME mapping                                            //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    @Test
    void testExtractExistingMIMEMappingFile_ProducesExpectedResults() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "extract",
            "mimeMapping",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-target",
            TARGET_VALUE,
            "-name",
            "mimemappings.properties"
        };
        List<String> expectedPaths = Arrays.asList(MIME_MAPPING_PROPERTIES_CONTENTS);

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to exit with exit code 0");
        assertExtractedFilesMatch(expectedPaths);
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                               node manager keystore                                       //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    @Test
    void testExtractExistingNodeManagerKeystoreFile_ProducesExpectedResults() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "extract",
            "nodeManagerKeystore",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-target",
            TARGET_VALUE,
            "-name",
            "nmIdentity.jks"
        };
        List<String> expectedPaths = Arrays.asList(NODE_MANAGER_IDENTITY_JKS_CONTENTS);

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(0, actual, "expected command to exit with exit code 0");
        assertExtractedFilesMatch(expectedPaths);
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                                   OPSS wallet                                             //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    @Test
    void testExtractOPSSWalletNoArchive_Fails() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "extract",
            "opssWallet",
            "-target",
            TARGET_VALUE
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
    void testExtractOPSSWalletNoTarget_Fails() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "extract",
            "opssWallet",
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

    @Test
    void testExtractExistingOPSSWallet_ProducesExpectedResults() {
        assertExtractDirectoryIsClean();
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "extract",
            "opssWallet",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-target",
            TARGET_VALUE
        };
        List<String> expectedPaths = Arrays.asList(OPSS_WALLET_CONTENT);

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(0, actual, "expected command to exit with exit code 0");
        assertExtractedFilesMatch(expectedPaths);
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                                    RCU wallet                                             //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    @Test
    void testExtractRCUWalletNoArchive_Fails() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "extract",
            "rcuWallet",
            "-target",
            TARGET_VALUE
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
    void testExtractRCUWalletNoTarget_Fails() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "extract",
            "rcuWallet",
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

    @Test
    void testExtractExistingRCUWallet_ProducesExpectedResults() {
        assertExtractDirectoryIsClean();
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "extract",
            "rcuWallet",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-target",
            TARGET_VALUE
        };
        List<String> expectedPaths = Arrays.asList(DATABASE_WALLET_RCU_CONTENTS);

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(0, actual, "expected command to exit with exit code 0");
        assertExtractedFilesMatch(expectedPaths);
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                              SAML2 Initialization Data                                    //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    @Test
    void testExtractExistingSaml2InitializationDataFile_ProducesExpectedResults() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "extract",
            "saml2InitializationData",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-target",
            TARGET_VALUE,
            "-name",
            "saml2sppartner.properties"
        };
        List<String> expectedPaths = Arrays.asList(SAML2_SP_PROPERTIES_CONTENT);

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(0, actual, "expected command to exit with exit code 0");
        assertExtractedFilesMatch(expectedPaths);
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                                      script                                               //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    @Test
    void testExtractExistingScriptFile_ProducesExpectedResults() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "extract",
            "script",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-target",
            TARGET_VALUE,
            "-name",
            "my_fancy_script.sh"
        };
        List<String> expectedPaths = Arrays.asList(SCRIPTS_FANCY_SCRIPT_CONTENTS);

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(0, actual, "expected command to exit with exit code 0");
        assertExtractedFilesMatch(expectedPaths);
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                                  server keystore                                          //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    @Test
    void testExtractServerKeystoreBadServerName_Fails() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "extract",
            "serverKeystore",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-target",
            TARGET_VALUE,
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
        assertEquals(ExitCode.ERROR, actual,
            "expected command to exit with exit code " + ExitCode.ERROR);
    }

    @Test
    void testExtractServerKeystoreBadName_Fails() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "extract",
            "serverKeystore",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-target",
            TARGET_VALUE,
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
        assertEquals(ExitCode.ERROR, actual,
            "expected command to exit with exit code " + ExitCode.ERROR);
    }

    @Test
    void testExtractExistingServerKeystoreFile_ProducesExpectedResults() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "extract",
            "serverKeystore",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-target",
            TARGET_VALUE,
            "-server_name",
            "AdminServer",
            "-name",
            "identity.jks"
        };
        List<String> expectedPaths = Arrays.asList(SERVERS_ADMIN_SERVER_IDENTITY_JKS_CONTENTS);

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(0, actual, "expected command to exit with exit code 0");
        assertExtractedFilesMatch(expectedPaths);
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                              server template keystore                                     //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    @Test
    void testExtractServerTemplateKeystoreBadTemplateName_Fails() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
                "extract",
                "serverTemplateKeystore",
                "-archive_file",
                ARCHIVE_HELPER_VALUE,
                "-target",
                TARGET_VALUE,
                "-server_template_name",
                "missing",
                "-name",
                "identity.jks"
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        assertEquals(ExitCode.ERROR, actual,
                "expected command to exit with exit code " + ExitCode.ERROR);
    }

    @Test
    void testExtractServerTemplateKeystoreBadName_Fails() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
                "extract",
                "serverTemplateKeystore",
                "-archive_file",
                ARCHIVE_HELPER_VALUE,
                "-target",
                TARGET_VALUE,
                "-server_template_name",
                "myServerTemplate",
                "-name",
                "missing.jks"
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        assertEquals(ExitCode.ERROR, actual,
                "expected command to exit with exit code " + ExitCode.ERROR);
    }

    @Test
    void testExtractExistingServerTemplateKeystoreFile_ProducesExpectedResults() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
                "extract",
                "serverTemplateKeystore",
                "-archive_file",
                ARCHIVE_HELPER_VALUE,
                "-target",
                TARGET_VALUE,
                "-server_template_name",
                "myServerTemplate",
                "-name",
                "identity.jks"
        };
        List<String> expectedPaths = Arrays.asList(SERVER_TEMPLATE_IDENTITY_JKS_CONTENTS);

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(0, actual, "expected command to exit with exit code 0");
        assertExtractedFilesMatch(expectedPaths);
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                                  shared library                                           //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    @Test
    void testExtractExistingSharedLibraryFile_ProducesExpectedResults() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "extract",
            "sharedLibrary",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-target",
            TARGET_VALUE,
            "-name",
            "my-lib.war"
        };
        List<String> expectedPaths = Arrays.asList(SHARED_LIBS_MY_LIB_WAR_CONTENTS);

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(0, actual, "expected command to exit with exit code 0");
        assertExtractedFilesMatch(expectedPaths);
    }

    @Test
    void testExtractExistingSharedLibraryDir_ProducesExpectedResults() {
        assertExtractDirectoryIsClean();
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "extract",
            "sharedLibrary",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-target",
            TARGET_VALUE,
            "-name",
            "my-other-lib"
        };
        List<String> expectedPaths = Arrays.asList(SHARED_LIBS_MY_OTHER_LIB_CONTENTS);

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(0, actual, "expected command to exit with exit code 0");
        assertExtractedFilesMatch(expectedPaths);
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                               shared library plan                                         //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    @Test
    void testExtractExistingSharedLibraryPlanFile_ProducesExpectedResults() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "extract",
            "sharedLibraryPlan",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-target",
            TARGET_VALUE,
            "-name",
            "my-lib.xml"
        };
        List<String> expectedPaths = Arrays.asList(SHARED_LIBS_MY_LIB_XML_CONTENTS);

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(0, actual, "expected command to exit with exit code 0");
        assertExtractedFilesMatch(expectedPaths);
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                               structured application                                      //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    @Test
    void testExtractExistingStructuredApplicationDir_ProducesExpectedResults() {
        assertExtractDirectoryIsClean();
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "extract",
            "structuredApplication",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-target",
            TARGET_VALUE,
            "-name",
            "webapp"
        };
        List<String> expectedPaths = Arrays.asList(STRUCTURED_APP_WEBAPP_CONTENTS);

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(0, actual, "expected command to exit with exit code 0");
        assertExtractedFilesMatch(expectedPaths);
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                           WebLogic Remote Console Extension                               //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    @Test
    void testExtractExistingWrcExtensionFile_ProducesExpectedResults() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "extract",
            "weblogicRemoteConsoleExtension",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-target",
            TARGET_VALUE,
            "-name",
            "console-rest-ext-6.0.war"
        };
        List<String> expectedPaths = Arrays.asList(WRC_EXTENSION_FILE_CONTENT);

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(0, actual, "expected command to exit with exit code 0");
        assertExtractedFilesMatch(expectedPaths);
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                              private helper methods                                       //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    private void assertExtractDirectoryIsClean() {
        assertFalse(WLSDEPLOY_TARGET_DIR.exists(), "expected " + WLSDEPLOY_TARGET_DIR.getPath() +
            " have been deleted prior to the test");
    }

    private void assertExtractedFilesMatch(List<String> expectedPaths) {
        for (String expectedPath : expectedPaths) {
            File expectedFile = FileUtils.getCanonicalFile(new File(UNIT_TEST_TARGET_DIR, expectedPath));
            String expectedFilePath = FileUtils.getCanonicalPath(expectedFile);

            assertTrue(expectedFile.exists(), "expected " + expectedFilePath + " to exist");
            if (expectedPath.endsWith(ZIP_SEP)) {
                assertTrue(expectedFile.isDirectory(), "expected " + expectedFilePath + " to be a directory");
            } else {
                assertTrue(expectedFile.isFile(), "expected " + expectedFilePath + " to be a file");
            }
        }
    }
}
