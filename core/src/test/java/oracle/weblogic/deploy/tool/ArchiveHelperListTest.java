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
import java.util.Arrays;
import java.util.List;
import java.util.logging.Level;

import oracle.weblogic.deploy.logging.PlatformLogger;
import oracle.weblogic.deploy.logging.WLSDeployLogFactory;
import oracle.weblogic.deploy.util.ExitCode;
import oracle.weblogic.deploy.util.WLSDeployZipFileTest;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;

import static oracle.weblogic.deploy.tool.ArchiveHelper.LOGGER_NAME;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.ALL_CONTENT;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.APPLICATIONS_CONTENT;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.CLASSPATH_LIBS_CONTENT;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.CLASSPATH_LIB_BAR_JAR_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.COHERENCE_CONTENT;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.COHERENCE_MYCLUSTER2_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.COHERENCE_MYCLUSTER_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.CUSTOM_CONTENT;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.CUSTOM_FOO_PROPERTIES_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.CUSTOM_MYDIR_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.DATABASE_WALLET_RCU_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.DATABASE_WALLET_WALLET1_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.DOMAIN_BIN_CONTENT;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.DOMAIN_BIN_SET_USER_OVERRIDES_SH_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.DOMAIN_LIB_CONTENT;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.DOMAIN_LIB_FOO_JAR_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.FILE_STORES_CONTENT;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.FILE_STORES_FS2_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.MIME_MAPPINGS_CONTENT;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.MIME_MAPPING_PROPERTIES_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.MY_APP_WAR_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.MY_OTHER_APP_DIR_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.NODE_MANAGER_CONTENT;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.NODE_MANAGER_TRUST_JKS_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.OPSS_WALLET_CONTENT;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.SAML2_DATA_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.SAML2_SP_PROPERTIES_CONTENT;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.SCRIPTS_CONTENT;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.SCRIPTS_FANCY_SCRIPT_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.SERVERS_ADMIN_SERVER_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.SERVERS_ADMIN_SERVER_TRUST_JKS_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.SHARED_LIBS_CONTENT;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.SHARED_LIBS_MY_LIB_WAR_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.SHARED_LIBS_MY_OTHER_LIB_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.STRUCTURED_APPS_CONTENT;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.STRUCTURED_APP_WEBAPP_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.STRUCTURED_APP_WEBAPP1_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.WRC_EXTENSION_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.WRC_EXTENSION_FILE_CONTENT;
import static oracle.weblogic.deploy.util.WLSDeployArchive.DEFAULT_RCU_WALLET_NAME;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

public class ArchiveHelperListTest {
    public static final File UNIT_TEST_SOURCE_DIR = new File(WLSDeployZipFileTest.UNIT_TEST_SOURCE_DIR);
    private static final File UNIT_TEST_TARGET_DIR =
        new File(new File(WLSDeployZipFileTest.UNIT_TEST_TARGET_DIR, "archiveHelper"), "list");

    private static final Path ARCHIVE_HELPER_SOURCE_ZIP =
        new File(UNIT_TEST_SOURCE_DIR, "archive-helper-test.zip").toPath();
    private static final Path ARCHIVE_HELPER_TARGET_ZIP =
        new File(UNIT_TEST_TARGET_DIR, "archive-helper-test.zip").toPath();
    private static final String ARCHIVE_HELPER_VALUE = ARCHIVE_HELPER_TARGET_ZIP.toFile().getAbsolutePath();

    private static final String[] LIST_ALL_EXPECTED = ALL_CONTENT;

    private static final String[] LIST_APP_FILE_EXPECTED = MY_APP_WAR_CONTENTS;
    private static final String[] LIST_APP_DIR_EXPECTED = MY_OTHER_APP_DIR_CONTENTS;
    private static final String[] LIST_APPS_EXPECTED = APPLICATIONS_CONTENT;

    private static final String[] LIST_CP_LIBS_EXPECTED = CLASSPATH_LIBS_CONTENT;

    private static final String[] LIST_COH_MYCLUSTER_EXPECTED = COHERENCE_MYCLUSTER_CONTENTS;
    private static final String[] LIST_COH_MYCLUSTER2_EXPECTED = COHERENCE_MYCLUSTER2_CONTENTS;
    private static final String[] LIST_COH_EXPECTED = COHERENCE_CONTENT;

    private static final String[] LIST_MIME_MAPPINGS_EXPECTED = MIME_MAPPINGS_CONTENT;
    private static final String[] LIST_MIME_MAPPINGS_PROPERTIES_EXPECTED = MIME_MAPPING_PROPERTIES_CONTENTS;

    private static final String[] LIST_CUSTOM_MYDIR_EXPECTED = CUSTOM_MYDIR_CONTENTS;
    private static final String[] LIST_CUSTOM_EXPECTED = CUSTOM_CONTENT;

    private static final String[] LIST_RCU_WALLET_EXPECTED = DATABASE_WALLET_RCU_CONTENTS;
    private static final String[] LIST_WALLET1_EXPECTED = DATABASE_WALLET_WALLET1_CONTENTS;

    private static final String[] LIST_SAML2_DATA_EXPECTED = SAML2_DATA_CONTENTS;

    private static final String[] LIST_SHLIB_FILE_EXPECTED = SHARED_LIBS_MY_LIB_WAR_CONTENTS;
    private static final String[] LIST_SHLIB_DIR_EXPECTED = SHARED_LIBS_MY_OTHER_LIB_CONTENTS;
    private static final String[] LIST_SHLIB_EXPECTED = SHARED_LIBS_CONTENT;


    private static final String[] LIST_STRUCTURED_APP_WEBAPP_EXPECTED = STRUCTURED_APP_WEBAPP_CONTENTS;
    private static final String[] LIST_STRUCTURED_APP_WEBAPP1_EXPECTED = STRUCTURED_APP_WEBAPP1_CONTENTS;
    private static final String[] LIST_STRUCTURED_APPS_EXPECTED = STRUCTURED_APPS_CONTENT;


    @BeforeAll
    static void initialize() throws Exception {
        if(!UNIT_TEST_TARGET_DIR.exists() && !UNIT_TEST_TARGET_DIR.mkdirs()) {
            throw new Exception("Unable to create unit test directory: " + UNIT_TEST_TARGET_DIR);
        }
        Files.copy(ARCHIVE_HELPER_SOURCE_ZIP, ARCHIVE_HELPER_TARGET_ZIP, StandardCopyOption.REPLACE_EXISTING);

        PlatformLogger logger = WLSDeployLogFactory.getLogger(LOGGER_NAME);
        logger.setLevel(Level.OFF);
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                                     parameterized                                         //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    @ParameterizedTest
    @ValueSource(strings = {
        "all",
        "application",
        "classpathLibrary",
        "coherence",
        "custom",
        "databaseWallet",
        "domainBinScript",
        "domainLibrary",
        "fileStore",
        "jmsForeignServer",
        "mimMapping",
        "nodeManagerKeystore",
        "opssWallet",
        "rcuWallet",
        "saml2InitializationData",
        "script",
        "serverKeystore",
        "sharedLibrary",
        "structuredApplication",
        "weblogicRemoteConsoleExtension"
    })
    void testListNoArchive_Fails(String subcommand) {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "list",
            subcommand
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
        "all",
        "application",
        "classpathLibrary",
        "coherence",
        "custom",
        "databaseWallet",
        "domainBinScript",
        "domainLibrary",
        "fileStore",
        "jmsForeignServer",
        "mimeMapping",
        "nodeManagerKeystore",
        "opssWallet",
        "rcuWallet",
        "saml2InitializationData",
        "script",
        "serverKeystore",
        "sharedLibrary",
        "structuredApplication",
        "weblogicRemoteConsoleExtension"
    })
    void testListBadArchive_Fails(String subcommand) {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args;
        switch(subcommand) {
            case "jmsForeignServer":
                args = new String[] {
                    "list",
                    subcommand,
                    "-foreign_server_name",
                    "foo",
                    "-archive_file",
                    "foo.zip"
                };
                break;

            case "serverKeystore":
                args = new String[] {
                    "list",
                    subcommand,
                    "-server_name",
                    "foo",
                    "-archive_file",
                    "foo.zip"
                };
                break;

            default:
                args = new String[] {
                    "list",
                    subcommand,
                    "-archive_file",
                    "foo.zip"
                };
        }

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.ARG_VALIDATION_ERROR, actual,
            "expected command to exit with exit code " + ExitCode.ARG_VALIDATION_ERROR);
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                                         all                                               //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    @Test
    void testListAll_ReturnedExceptedNames() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "list",
            "all",
            "-archive_file",
            ARCHIVE_HELPER_VALUE
        };
        List<String> expectedPaths = Arrays.asList(LIST_ALL_EXPECTED);

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        String[] outputLines = outStringWriter.getBuffer().toString().trim().split(System.lineSeparator());

        assertEquals(0, actual, "expected command to exit with exit code 0");
        assertListsHaveSameElements(expectedPaths, outputLines, "all");
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                                     application                                           //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    @Test
    void testListAppFile_ReturnsExpectedName() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "list",
            "application",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-name",
            "my-app.war"
        };
        List<String> expectedPaths = Arrays.asList(LIST_APP_FILE_EXPECTED);

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        String[] outputLines = outStringWriter.getBuffer().toString().trim().split(System.lineSeparator());

        assertEquals(0, actual, "expected command to exit with exit code 0");
        assertListsHaveSameElements(expectedPaths, outputLines, "application -name my-app.war");
    }

    @Test
    void testListAppDirectory_ReturnsExpectedNames() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "list",
            "application",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-name",
            "my-other-app"
        };
        List<String> expectedPaths = Arrays.asList(LIST_APP_DIR_EXPECTED);

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        String[] outputLines = outStringWriter.getBuffer().toString().trim().split(System.lineSeparator());

        assertEquals(0, actual, "expected command to exit with exit code 0");
        assertListsHaveSameElements(expectedPaths, outputLines, "application -name my-other-app");
    }

    @Test
    void testListApps_ReturnsExceptedNames() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "list",
            "application",
            "-archive_file",
            ARCHIVE_HELPER_VALUE
        };
        List<String> expectedPaths = Arrays.asList(LIST_APPS_EXPECTED);

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        String[] outputLines = outStringWriter.getBuffer().toString().trim().split(System.lineSeparator());

        assertEquals(0, actual, "expected command to exit with exit code 0");
        assertListsHaveSameElements(expectedPaths, outputLines, "application");
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                                   classpath library                                       //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    @Test
    void testListClasspathLibs_ReturnsExceptedNames() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[]{
            "list",
            "classpathLibrary",
            "-archive_file",
            ARCHIVE_HELPER_VALUE
        };
        List<String> expectedPaths = Arrays.asList(LIST_CP_LIBS_EXPECTED);

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        String[] outputLines = outStringWriter.getBuffer().toString().trim().split(System.lineSeparator());

        assertEquals(0, actual, "expected command to exit with exit code 0");
        assertListsHaveSameElements(expectedPaths, outputLines, "classpathLibrary");
    }

    @Test
    void testListClasspathLibFile_ReturnsExceptedNames() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[]{
            "list",
            "classpathLibrary",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-name",
            "bar.jar"
        };
        List<String> expectedPaths = Arrays.asList(CLASSPATH_LIB_BAR_JAR_CONTENTS);

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        String[] outputLines = outStringWriter.getBuffer().toString().trim().split(System.lineSeparator());

        assertEquals(0, actual, "expected command to exit with exit code 0");
        assertListsHaveSameElements(expectedPaths, outputLines, "classpathLibrary -name bar.jar");
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                                       Coherence                                           //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    @Test
    void testListCohMyCluster_ReturnedExpectedNames() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[]{
            "list",
            "coherence",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-cluster_name",
            "mycluster"
        };
        List<String> expectedPaths = Arrays.asList(LIST_COH_MYCLUSTER_EXPECTED);

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        String[] outputLines = outStringWriter.getBuffer().toString().trim().split(System.lineSeparator());

        assertEquals(0, actual, "expected command to exit with exit code 0");
        assertListsHaveSameElements(expectedPaths, outputLines, "coherence -cluster_name mycluster");
    }

    @Test
    void testListCohMyCluster2_ReturnedExpectedNames() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[]{
            "list",
            "coherence",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-cluster_name",
            "mycluster2"
        };
        List<String> expectedPaths = Arrays.asList(LIST_COH_MYCLUSTER2_EXPECTED);

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        String[] outputLines = outStringWriter.getBuffer().toString().trim().split(System.lineSeparator());

        assertEquals(0, actual, "expected command to exit with exit code 0");
        assertListsHaveSameElements(expectedPaths, outputLines, "coherence -cluster_name mycluster2");
    }

    @Test
    void testListCoh_ReturnedExpectedNames() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[]{
            "list",
            "coherence",
            "-archive_file",
            ARCHIVE_HELPER_VALUE
        };
        List<String> expectedPaths = Arrays.asList(LIST_COH_EXPECTED);

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        String[] outputLines = outStringWriter.getBuffer().toString().trim().split(System.lineSeparator());

        assertEquals(0, actual, "expected command to exit with exit code 0");
        assertListsHaveSameElements(expectedPaths, outputLines, "coherence");
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                                         custom                                            //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    @Test
    void testListCustom_ReturnsExceptedNames() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[]{
            "list",
            "custom",
            "-archive_file",
            ARCHIVE_HELPER_VALUE
        };
        List<String> expectedPaths = Arrays.asList(LIST_CUSTOM_EXPECTED);

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        String[] outputLines = outStringWriter.getBuffer().toString().trim().split(System.lineSeparator());

        assertEquals(0, actual, "expected command to exit with exit code 0");
        assertListsHaveSameElements(expectedPaths, outputLines, "custom");
    }

    @Test
    void testListCustomDir_ReturnsExceptedNames() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[]{
            "list",
            "custom",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-name",
            "mydir"
        };
        List<String> expectedPaths = Arrays.asList(LIST_CUSTOM_MYDIR_EXPECTED);

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        String[] outputLines = outStringWriter.getBuffer().toString().trim().split(System.lineSeparator());

        assertEquals(0, actual, "expected command to exit with exit code 0");
        assertListsHaveSameElements(expectedPaths, outputLines, "custom -name mydir");
    }

    @Test
    void testListCustomFile_ReturnsExceptedNames() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[]{
            "list",
            "custom",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-name",
            "foo.properties"
        };
        List<String> expectedPaths = Arrays.asList(CUSTOM_FOO_PROPERTIES_CONTENTS);

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        String[] outputLines = outStringWriter.getBuffer().toString().trim().split(System.lineSeparator());

        assertEquals(0, actual, "expected command to exit with exit code 0");
        assertListsHaveSameElements(expectedPaths, outputLines, "custom -name foo.properties");
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                                     database wallet                                       //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    @Test
    void testListDbWalletRCU_ReturnsExceptedNames() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[]{
            "list",
            "databaseWallet",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-name",
            DEFAULT_RCU_WALLET_NAME
        };
        List<String> expectedPaths = Arrays.asList(LIST_RCU_WALLET_EXPECTED);

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        String[] outputLines = outStringWriter.getBuffer().toString().trim().split(System.lineSeparator());

        assertEquals(0, actual, "expected command to exit with exit code 0");
        assertListsHaveSameElements(expectedPaths, outputLines, "databaseWallet -name " + DEFAULT_RCU_WALLET_NAME);
    }

    @Test
    void testListWallet1Dir_ReturnsExceptedNames() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[]{
            "list",
            "databaseWallet",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-name",
            "wallet1"
        };
        List<String> expectedPaths = Arrays.asList(LIST_WALLET1_EXPECTED);

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        String[] outputLines = outStringWriter.getBuffer().toString().trim().split(System.lineSeparator());

        assertEquals(0, actual, "expected command to exit with exit code 0");
        assertListsHaveSameElements(expectedPaths, outputLines, "databaseWallet -name wallet1");
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                                $DOMAIN_HOME/bin script                                    //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    @Test
    void testListDomainBin_ReturnsExceptedNames() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[]{
            "list",
            "domainBinScript",
            "-archive_file",
            ARCHIVE_HELPER_VALUE
        };
        List<String> expectedPaths = Arrays.asList(DOMAIN_BIN_CONTENT);

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        String[] outputLines = outStringWriter.getBuffer().toString().trim().split(System.lineSeparator());

        assertEquals(0, actual, "expected command to exit with exit code 0");
        assertListsHaveSameElements(expectedPaths, outputLines, "domainBinScript");
    }

    @Test
    void testListDomainBinFile_ReturnsExceptedNames() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[]{
            "list",
            "domainBinScript",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-name",
            "setUserOverrides.sh"
        };
        List<String> expectedPaths = Arrays.asList(DOMAIN_BIN_SET_USER_OVERRIDES_SH_CONTENTS);

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        String[] outputLines = outStringWriter.getBuffer().toString().trim().split(System.lineSeparator());

        assertEquals(0, actual, "expected command to exit with exit code 0");
        assertListsHaveSameElements(expectedPaths, outputLines, "domainBinScript -name setUserOverrides.sh");
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                                $DOMAIN_HOME/lib library                                   //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    @Test
    void testListDomainLib_ReturnsExceptedNames() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[]{
            "list",
            "domainLibrary",
            "-archive_file",
            ARCHIVE_HELPER_VALUE
        };
        List<String> expectedPaths = Arrays.asList(DOMAIN_LIB_CONTENT);

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        String[] outputLines = outStringWriter.getBuffer().toString().trim().split(System.lineSeparator());

        assertEquals(0, actual, "expected command to exit with exit code 0");
        assertListsHaveSameElements(expectedPaths, outputLines, "domainLibrary");
    }

    @Test
    void testListDomainLibFile_ReturnsExceptedNames() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[]{
            "list",
            "domainLibrary",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-name",
            "foo.jar"
        };
        List<String> expectedPaths = Arrays.asList(DOMAIN_LIB_FOO_JAR_CONTENTS);

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        String[] outputLines = outStringWriter.getBuffer().toString().trim().split(System.lineSeparator());

        assertEquals(0, actual, "expected command to exit with exit code 0");
        assertListsHaveSameElements(expectedPaths, outputLines, "domainLibrary -name foo.jar");
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                                       file store                                          //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    @Test
    void testListFileStore_ReturnsExceptedNames() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[]{
            "list",
            "fileStore",
            "-archive_file",
            ARCHIVE_HELPER_VALUE
        };
        List<String> expectedPaths = Arrays.asList(FILE_STORES_CONTENT);

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        String[] outputLines = outStringWriter.getBuffer().toString().trim().split(System.lineSeparator());

        assertEquals(0, actual, "expected command to exit with exit code 0");
        assertListsHaveSameElements(expectedPaths, outputLines, "fileStore");
    }

    @Test
    void testListFileStoreDir_ReturnsExceptedNames() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[]{
            "list",
            "fileStore",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-name",
            "fs2"
        };
        List<String> expectedPaths = Arrays.asList(FILE_STORES_FS2_CONTENTS);

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        String[] outputLines = outStringWriter.getBuffer().toString().trim().split(System.lineSeparator());

        assertEquals(0, actual, "expected command to exit with exit code 0");
        assertListsHaveSameElements(expectedPaths, outputLines, "fileStore -name fs2");
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                                     MIME mappings                                         //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    @Test
    void testListMime_ReturnedExceptedNames() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[]{
            "list",
            "mimeMapping",
            "-archive_file",
            ARCHIVE_HELPER_VALUE
        };
        List<String> expectedPaths = Arrays.asList(LIST_MIME_MAPPINGS_EXPECTED);

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        String[] outputLines = outStringWriter.getBuffer().toString().trim().split(System.lineSeparator());

        assertEquals(0, actual, "expected command to exit with exit code 0");
        assertListsHaveSameElements(expectedPaths, outputLines, "mimeMapping");
    }

    @Test
    void testListMimeMappingProperties_ReturnedExceptedNames() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[]{
            "list",
            "mimeMapping",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-name",
            "mimemappings.properties"
        };
        List<String> expectedPaths = Arrays.asList(LIST_MIME_MAPPINGS_PROPERTIES_EXPECTED);

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        String[] outputLines = outStringWriter.getBuffer().toString().trim().split(System.lineSeparator());

        assertEquals(0, actual, "expected command to exit with exit code 0");
        assertListsHaveSameElements(expectedPaths, outputLines, "mimeMapping -name mimemappings.properties");
    }


    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                                 node manager keystore                                     //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    @Test
    void testListNodeManager_ReturnsExceptedNames() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[]{
            "list",
            "nodeManagerKeystore",
            "-archive_file",
            ARCHIVE_HELPER_VALUE
        };
        List<String> expectedPaths = Arrays.asList(NODE_MANAGER_CONTENT);

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        String[] outputLines = outStringWriter.getBuffer().toString().trim().split(System.lineSeparator());

        assertEquals(0, actual, "expected command to exit with exit code 0");
        assertListsHaveSameElements(expectedPaths, outputLines, "nodeManagerKeystore");
    }

    @Test
    void testListNodeManagerFile_ReturnsExceptedNames() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[]{
            "list",
            "nodeManagerKeystore",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-name",
            "nmTrust.jks"
        };
        List<String> expectedPaths = Arrays.asList(NODE_MANAGER_TRUST_JKS_CONTENTS);

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        String[] outputLines = outStringWriter.getBuffer().toString().trim().split(System.lineSeparator());

        assertEquals(0, actual, "expected command to exit with exit code 0");
        assertListsHaveSameElements(expectedPaths, outputLines, "nodeManagerKeystore -name nmTrust.jks");
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                                      OPSS wallet                                          //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    @Test
    void testListOPSSWallet_ReturnsExceptedNames() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[]{
            "list",
            "opssWallet",
            "-archive_file",
            ARCHIVE_HELPER_VALUE
        };
        List<String> expectedPaths = Arrays.asList(OPSS_WALLET_CONTENT);

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        String[] outputLines = outStringWriter.getBuffer().toString().trim().split(System.lineSeparator());

        assertEquals(0, actual, "expected command to exit with exit code 0");
        assertListsHaveSameElements(expectedPaths, outputLines, "opssWallet");
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                                        RCU wallet                                         //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    @Test
    void testListRCUWallet_ReturnsExceptedNames() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[]{
            "list",
            "rcuWallet",
            "-archive_file",
            ARCHIVE_HELPER_VALUE
        };
        List<String> expectedPaths = Arrays.asList(LIST_RCU_WALLET_EXPECTED);

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        String[] outputLines = outStringWriter.getBuffer().toString().trim().split(System.lineSeparator());

        assertEquals(0, actual, "expected command to exit with exit code 0");
        assertListsHaveSameElements(expectedPaths, outputLines, "rcuWallet");
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                                 SAML2 Initialization Data                                 //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    @Test
    void testListSaml2InitializationData_ReturnsExceptedNames() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[]{
            "list",
            "saml2InitializationData",
            "-archive_file",
            ARCHIVE_HELPER_VALUE
        };
        List<String> expectedPaths = Arrays.asList(SAML2_DATA_CONTENTS);

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        String[] outputLines = outStringWriter.getBuffer().toString().trim().split(System.lineSeparator());

        assertEquals(0, actual, "expected command to exit with exit code 0");
        assertListsHaveSameElements(expectedPaths, outputLines, "saml2InitializationData");
    }

    @Test
    void testListSaml2InitializationDataFile_ReturnsExceptedNames() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[]{
            "list",
            "saml2InitializationData",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-name",
            "saml2sppartner.properties"
        };
        List<String> expectedPaths = Arrays.asList(SAML2_SP_PROPERTIES_CONTENT);

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        String[] outputLines = outStringWriter.getBuffer().toString().trim().split(System.lineSeparator());

        assertEquals(0, actual, "expected command to exit with exit code 0");
        assertListsHaveSameElements(expectedPaths, outputLines,
            "saml2InitializationData -name saml2sppartner.properties");
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                                         script                                            //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    @Test
    void testListScripts_ReturnsExceptedNames() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[]{
            "list",
            "script",
            "-archive_file",
            ARCHIVE_HELPER_VALUE
        };
        List<String> expectedPaths = Arrays.asList(SCRIPTS_CONTENT);

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        String[] outputLines = outStringWriter.getBuffer().toString().trim().split(System.lineSeparator());

        assertEquals(0, actual, "expected command to exit with exit code 0");
        assertListsHaveSameElements(expectedPaths, outputLines, "script");
    }

    @Test
    void testListScriptsFile_ReturnsExceptedNames() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[]{
            "list",
            "script",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-name",
            "my_fancy_script.sh"
        };
        List<String> expectedPaths = Arrays.asList(SCRIPTS_FANCY_SCRIPT_CONTENTS);

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        String[] outputLines = outStringWriter.getBuffer().toString().trim().split(System.lineSeparator());

        assertEquals(0, actual, "expected command to exit with exit code 0");
        assertListsHaveSameElements(expectedPaths, outputLines, "script -name my_fancy_script.sh");
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                                    server keystore                                        //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    @Test
    void testListServerKeystore_ReturnsExceptedNames() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[]{
            "list",
            "serverKeystore",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-server_name",
            "AdminServer"
        };
        List<String> expectedPaths = Arrays.asList(SERVERS_ADMIN_SERVER_CONTENTS);

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        String[] outputLines = outStringWriter.getBuffer().toString().trim().split(System.lineSeparator());

        assertEquals(0, actual, "expected command to exit with exit code 0");
        assertListsHaveSameElements(expectedPaths, outputLines, "serverKeystore");
    }

    @Test
    void testListServerKeystoreFile_ReturnsExceptedNames() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[]{
            "list",
            "serverKeystore",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-server_name",
            "AdminServer",
            "-name",
            "trust.jks"
        };
        List<String> expectedPaths = Arrays.asList(SERVERS_ADMIN_SERVER_TRUST_JKS_CONTENTS);

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        String[] outputLines = outStringWriter.getBuffer().toString().trim().split(System.lineSeparator());

        assertEquals(0, actual, "expected command to exit with exit code 0");
        assertListsHaveSameElements(expectedPaths, outputLines, "serverKeystore -name trust.jks");
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                                     shared library                                         //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    @Test
    void testListSharedLibraries_ReturnsExpectedNames() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "list",
            "sharedLibrary",
            "-archive_file",
            ARCHIVE_HELPER_VALUE
        };
        List<String> expectedPaths = Arrays.asList(LIST_SHLIB_EXPECTED);

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        String[] outputLines = outStringWriter.getBuffer().toString().trim().split(System.lineSeparator());

        assertEquals(0, actual, "expected command to exit with exit code 0");
        assertListsHaveSameElements(expectedPaths, outputLines, "sharedLibrary");
    }

    @Test
    void testListSharedLibraryFile_ReturnsExpectedNames() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "list",
            "sharedLibrary",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-name",
            "my-lib.war"
        };
        List<String> expectedPaths = Arrays.asList(LIST_SHLIB_FILE_EXPECTED);

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        String[] outputLines = outStringWriter.getBuffer().toString().trim().split(System.lineSeparator());

        assertEquals(0, actual, "expected command to exit with exit code 0");
        assertListsHaveSameElements(expectedPaths, outputLines, "sharedLibrary -name my-lib.war");
    }

    @Test
    void testListSharedLibraryDir_ReturnsExpectedNames() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "list",
            "sharedLibrary",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-name",
            "my-other-lib"
        };
        List<String> expectedPaths = Arrays.asList(LIST_SHLIB_DIR_EXPECTED);

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        String[] outputLines = outStringWriter.getBuffer().toString().trim().split(System.lineSeparator());

        assertEquals(0, actual, "expected command to exit with exit code 0");
        assertListsHaveSameElements(expectedPaths, outputLines, "sharedLibrary -name my-other-lib");
    }

    @Test
    void testListSharedLibraryUnknownFile_ReturnsNoNames() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "list",
            "sharedLibrary",
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
        String outputLines = outStringWriter.getBuffer().toString().trim();

        assertEquals(0, actual, "expected command to exit with exit code 0");
        assertEquals("", outputLines, "expected list sharedLibrary -name foo.jar to return nothing");
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                                structured application                                     //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    @Test
    void testListStructuredAppWebapp_ReturnedExpectedNames() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[]{
            "list",
            "structuredApplication",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-name",
            "webapp"
        };
        List<String> expectedPaths = Arrays.asList(LIST_STRUCTURED_APP_WEBAPP_EXPECTED);

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        String[] outputLines = outStringWriter.getBuffer().toString().trim().split(System.lineSeparator());

        assertEquals(0, actual, "expected command to exit with exit code 0");
        assertListsHaveSameElements(expectedPaths, outputLines, "structuredApplication -name webapp");
    }

    @Test
    void testListStructuredAppWebapp1_ReturnedExpectedNames() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[]{
            "list",
            "structuredApplication",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-name",
            "webapp1"
        };
        List<String> expectedPaths = Arrays.asList(LIST_STRUCTURED_APP_WEBAPP1_EXPECTED);

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        String[] outputLines = outStringWriter.getBuffer().toString().trim().split(System.lineSeparator());

        assertEquals(0, actual, "expected command to exit with exit code 0");
        assertListsHaveSameElements(expectedPaths, outputLines, "structuredApplication -name webapp1");
    }

    @Test
    void testListStructuredApp_ReturnedExpectedNames() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[]{
            "list",
            "structuredApplication",
            "-archive_file",
            ARCHIVE_HELPER_VALUE
        };
        List<String> expectedPaths = Arrays.asList(LIST_STRUCTURED_APPS_EXPECTED);

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        String[] outputLines = outStringWriter.getBuffer().toString().trim().split(System.lineSeparator());

        assertEquals(0, actual, "expected command to exit with exit code 0");
        assertListsHaveSameElements(expectedPaths, outputLines, "structuredApplication");
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                           WebLogic Remote Console Extension                               //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    @Test
    void testListWrcExtension_ReturnsExceptedNames() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[]{
            "list",
            "weblogicRemoteConsoleExtension",
            "-archive_file",
            ARCHIVE_HELPER_VALUE
        };
        List<String> expectedPaths = Arrays.asList(WRC_EXTENSION_CONTENTS);

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        String[] outputLines = outStringWriter.getBuffer().toString().trim().split(System.lineSeparator());

        assertEquals(0, actual, "expected command to exit with exit code 0");
        assertListsHaveSameElements(expectedPaths, outputLines, "weblogicRemoteConsoleExtension");
    }

    @Test
    void testListWrcExtensionFile_ReturnsExceptedNames() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[]{
            "list",
            "weblogicRemoteConsoleExtension",
            "-archive_file",
            ARCHIVE_HELPER_VALUE,
            "-name",
            "console-rest-ext-6.0.war"
        };
        List<String> expectedPaths = Arrays.asList(WRC_EXTENSION_FILE_CONTENT);

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        String[] outputLines = outStringWriter.getBuffer().toString().trim().split(System.lineSeparator());

        assertEquals(0, actual, "expected command to exit with exit code 0");
        assertListsHaveSameElements(expectedPaths, outputLines,
            "weblogicRemoteConsoleExtension -name console-rest-ext-6.0.war");
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                                private helper methods                                     //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    private static void assertListsHaveSameElements(List<String> expectedEntries, String[] actualLines, String command) {
        assertEquals(expectedEntries.size(), actualLines.length, "expected list " + command + " to return " +
            expectedEntries.size() + " entries");
        for (String actualLine : actualLines) {
            assertTrue(expectedEntries.contains(actualLine), actualLine + " not in expected output");
        }
    }
}
