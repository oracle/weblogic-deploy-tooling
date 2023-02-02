/*
 * Copyright (c) 2023, Oracle Corporation and/or its affiliates.  All rights reserved.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.tool;

import java.io.File;
import java.io.PrintWriter;
import java.io.StringWriter;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;
import java.util.ListIterator;
import java.util.logging.Level;
import java.util.stream.Collectors;

import oracle.weblogic.deploy.logging.PlatformLogger;
import oracle.weblogic.deploy.logging.WLSDeployLogFactory;
import oracle.weblogic.deploy.tool.archive_helper.ArchiveHelperException;
import oracle.weblogic.deploy.util.ExitCode;
import oracle.weblogic.deploy.util.FileUtils;
import oracle.weblogic.deploy.util.StringUtils;
import oracle.weblogic.deploy.util.WLSDeployArchive;
import oracle.weblogic.deploy.util.WLSDeployArchive.ArchiveEntryType;
import oracle.weblogic.deploy.util.WLSDeployZipFileTest;

import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.CsvSource;
import org.junit.jupiter.params.provider.ValueSource;

import static oracle.weblogic.deploy.tool.ArchiveHelper.LOGGER_NAME;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.CLASSPATH_LIB_BAR_DIR_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.CLASSPATH_LIB_BAR_DIR_DUP_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.CLASSPATH_LIB_BAR_JAR_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.CLASSPATH_LIB_BAR_JAR_DUP_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.COHERENCE_MYCLUSTER_CONFIG_FILE_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.COHERENCE_MYCLUSTER_CONFIG_FILE_DUP_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.COHERENCE_MYCLUSTER_PERSISTENT_DIR_ACTIVE_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.COHERENCE_MYCLUSTER_PERSISTENT_DIR_ACTIVE_DUP_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.CUSTOM_FOO_PROPERTIES_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.CUSTOM_FOO_PROPERTIES_DUP_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.CUSTOM_MYDIR_BAR_PROPERTIES_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.CUSTOM_MYDIR_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.CUSTOM_MYDIR_DUP_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.DATABASE_WALLET_RCU_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.DATABASE_WALLET_WALLET1_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.DATABASE_WALLET_WALLET1_DUP_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.DOMAIN_BIN_SET_USER_OVERRIDES_SH_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.DOMAIN_BIN_SET_USER_OVERRIDES_SH_DUP_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.DOMAIN_LIB_FOO_JAR_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.DOMAIN_LIB_FOO_JAR_DUP_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.FILE_STORES_FS1_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.FILE_STORES_FS1_DUP_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.FOREIGN_SERVERS_FS1_JNDI_PROPERTIES_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.FOREIGN_SERVERS_FS1_JNDI_PROPERTIES_DUP_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.MIME_MAPPING_PROPERTIES_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.MIME_MAPPING_PROPERTIES_DUP_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.MY_APP_DEPLOYMENT_PLAN_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.MY_APP_DEPLOYMENT_PLAN_DUP_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.MY_APP_WAR_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.MY_APP_WAR_DUP_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.MY_OTHER_APP_DIR_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.MY_OTHER_APP_DIR_DUP_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.NODE_MANAGER_IDENTITY_JKS_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.NODE_MANAGER_IDENTITY_JKS_DUP_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.OPSS_WALLET_CONTENT;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.SCRIPTS_FANCY_SCRIPT_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.SCRIPTS_FANCY_SCRIPT_DUP_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.SERVERS_ADMIN_SERVER_IDENTITY_JKS_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.SERVERS_ADMIN_SERVER_IDENTITY_JKS_DUP_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.SHARED_LIBS_MY_LIB_WAR_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.SHARED_LIBS_MY_LIB_WAR_DUP_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.SHARED_LIBS_MY_LIB_XML_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.SHARED_LIBS_MY_LIB_XML_DUP_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.SHARED_LIBS_MY_OTHER_LIB_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.SHARED_LIBS_MY_OTHER_LIB_DUP_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.STRUCTURED_APP_WEBAPP_CONTENTS;
import static oracle.weblogic.deploy.tool.ArchiveHelperTestConstants.STRUCTURED_APP_WEBAPP_DUP_CONTENTS;
import static oracle.weblogic.deploy.util.WLSDeployArchive.ZIP_SEP;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

public class ArchiveHelperAddTest {
    public static final File UNIT_TEST_SOURCE_DIR = new File(WLSDeployZipFileTest.UNIT_TEST_SOURCE_DIR);
    private static final File UNIT_TEST_TARGET_DIR =
        new File(new File(WLSDeployZipFileTest.UNIT_TEST_TARGET_DIR, "archiveHelper"), "add");
    private static final File SOURCE_ROOT_VALUE = FileUtils.getCanonicalFile(UNIT_TEST_TARGET_DIR);

    private static final Path ARCHIVE_HELPER_SOURCE_ZIP =
        new File(UNIT_TEST_SOURCE_DIR, "archive-helper-test.zip").toPath();
    private static final Path NEW_ARCHIVE_TARGET_ZIP =
        new File(UNIT_TEST_TARGET_DIR, "new-archive.zip").toPath();
    private static final String NEW_ARCHIVE_VALUE = NEW_ARCHIVE_TARGET_ZIP.toFile().getAbsolutePath();

    private static final String[] EMPTY_ARRAY = new String[0];
    private static final String[] LIST_APPLICATIONS = new String[] { "application" };
    private static final String[] LIST_APPLICATION_PLANS = LIST_APPLICATIONS;
    private static final String[] LIST_CLASSPATH_LIBRARIES = new String[] { "classpathLibrary" };
    private static final String[] LIST_COHERENCE_CONFIGS = new String[] { "coherence" };
    private static final String[] LIST_COHERENCE_PERSISTENCE_DIRS = LIST_COHERENCE_CONFIGS;
    private static final String[] LIST_CUSTOM = new String[] { "custom" };
    private static final String[] LIST_DATABASE_WALLETS = new String[] { "databaseWallet" };
    private static final String[] LIST_DOMAIN_BIN_SCRIPTS = new String[] { "domainBinScript" };
    private static final String[] LIST_DOMAIN_LIBRARIES = new String[] { "domainLibrary" };
    private static final String[] LIST_FILE_STORES = new String[] { "fileStore" };
    private static final String[] LIST_FOREIGN_SERVERS = new String[] {
        "jmsForeignServer",
        "-foreign_server_name",
        "fs1"
    };
    private static final String[] LIST_MIME_MAPPINGS = new String[] { "mimeMapping" };
    private static final String[] LIST_NODE_MANAGER_KEYSTORES = new String[] { "nodeManagerKeystore" };
    private static final String[] LIST_OPSS_WALLET = new String[] { "opssWallet" };
    private static final String[] LIST_RCU_WALLET = new String[] { "rcuWallet" };
    private static final String[] LIST_SCRIPTS = new String[] { "script" };
    private static final String[] LIST_SERVER_KEYSTORES = new String[] {
        "serverKeystore",
        "-server_name",
        "AdminServer"
    };
    private static final String[] LIST_SHARED_LIBRARIES = new String[] { "sharedLibrary" };
    private static final String[] LIST_SHARED_LIBRARIES_PLANS = LIST_SHARED_LIBRARIES;
    private static final String[] LIST_STRUCTURED_APPLICATIONS = new String[] { "structuredApplication" };

    @BeforeAll
    static void initialize() throws Exception {
        PlatformLogger logger = WLSDeployLogFactory.getLogger(LOGGER_NAME);
        logger.setLevel(Level.OFF);

        if(!UNIT_TEST_TARGET_DIR.exists() && !UNIT_TEST_TARGET_DIR.mkdirs()) {
            throw new Exception("Unable to create unit test directory: " + UNIT_TEST_TARGET_DIR);
        }

        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "extract",
            "all",
            "-archive_file",
            ARCHIVE_HELPER_SOURCE_ZIP.toFile().getAbsolutePath(),
            "-target",
            FileUtils.getCanonicalPath(UNIT_TEST_TARGET_DIR)
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        assertEquals(ExitCode.OK, actual, "ArchiveHelperAddTest initialization failed.");
    }

    @BeforeEach
    void setup() throws Exception {
        File targetArchiveFile = NEW_ARCHIVE_TARGET_ZIP.toFile();
        if (targetArchiveFile.exists() && !targetArchiveFile.delete()) {
            throw new Exception("setup() failed to delete file " + targetArchiveFile.getPath());
        }
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                                   parameterized                                           //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    @ParameterizedTest
    @CsvSource({
        "application, missing.war",
        "applicationPlan, missing.xml",
        "classpathLibrary, missing.jar",
        "coherenceConfig, missing.xml",
        "custom, missing",
        "databaseWallet, missing",
        "domainBinScript, missing.sh",
        "domainLibrary, missing.jar",
        "jmsForeignServer, missing.properties",
        "mimeMapping, missing.properties",
        "nodeManagerKeystore, missing.jks",
        "opssWallet, missing.zip",
        "rcuWallet, missing",
        "script, missing.sh",
        "serverKeystore, missing.jks",
        "sharedLibrary, missing.war",
        "sharedLibraryPlan, missing.xml",
        "structuredApplication, missing"
    })
    void testAddNoArchive_Fails(String subcommand, String source) {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "add",
            subcommand,
            "-source",
            source
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
        "custom",
        "databaseWallet",
        "domainBinScript",
        "domainLibrary",
        "jmsForeignServer",
        "mimeMapping",
        "nodeManagerKeystore",
        "opssWallet",
        "rcuWallet",
        "script",
        "serverKeystore",
        "sharedLibrary",
        "sharedLibraryPlan",
        "structuredApplication"
    })
    void testAddNoSource_Fails(String subcommand) {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "add",
            subcommand,
            "-archive_file",
            NEW_ARCHIVE_VALUE
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
        "domainBinScript, missing.sh",
        "domainLibrary, missing.jar",
        "mimeMapping, missing.properties",
        "nodeManagerKeystore, missing.jks",
        "opssWallet, missing.zip",
        "rcuWallet, missing",
        "script, missing.sh",
        "sharedLibrary, missing.war",
        "sharedLibraryPlan, missing.xml",
        "structuredApplication, missing"
    })
    void testAddBadSource_Fails(String subcommand, String source) {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "add",
            subcommand,
            "-archive_file",
            NEW_ARCHIVE_VALUE,
            "-source",
            source
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.ARG_VALIDATION_ERROR, actual,
            "expected command to exit with exit code " + ExitCode.ARG_VALIDATION_ERROR);
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                                    application                                            //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    @Test
    void testAddNewApplicationFile_ReturnsExceptedResult() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "add",
            "application",
            "-archive_file",
            NEW_ARCHIVE_VALUE,
            "-source",
            getSourcePath(ArchiveEntryType.APPLICATION, "my-app.war")
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to return " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_APPLICATIONS, EMPTY_ARRAY, MY_APP_WAR_CONTENTS);
    }

    @Test
    void testAddApplicationFileOverwrite_ReturnsExceptedResult() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "add",
            "application",
            "-archive_file",
            NEW_ARCHIVE_VALUE,
            "-source",
            getSourcePath(ArchiveEntryType.APPLICATION, "my-app.war")
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to return " + ExitCode.OK);

        String[] overwriteArgs = getOverwriteArgs(args);
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, overwriteArgs);
        }

        assertEquals(ExitCode.OK, actual, "expected command to return " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_APPLICATIONS, EMPTY_ARRAY, MY_APP_WAR_CONTENTS);
    }

    @Test
    void testAddApplicationFileTwice_ReturnsExceptedResult() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "add",
            "application",
            "-archive_file",
            NEW_ARCHIVE_VALUE,
            "-source",
            getSourcePath(ArchiveEntryType.APPLICATION, "my-app.war")
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to return " + ExitCode.OK);

        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to return " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_APPLICATIONS, EMPTY_ARRAY, MY_APP_WAR_CONTENTS, MY_APP_WAR_DUP_CONTENTS);
    }

    @Test
    void testAddNewApplicationDir_ReturnsExceptedResult() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "add",
            "application",
            "-archive_file",
            NEW_ARCHIVE_VALUE,
            "-source",
            getSourcePath(ArchiveEntryType.APPLICATION, "my-other-app")
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to exit with exit code " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_APPLICATIONS, EMPTY_ARRAY, MY_OTHER_APP_DIR_CONTENTS);
    }

    @Test
    void testAddApplicationDirOverwrite_ReturnsExceptedResult() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "add",
            "application",
            "-archive_file",
            NEW_ARCHIVE_VALUE,
            "-source",
            getSourcePath(ArchiveEntryType.APPLICATION, "my-other-app")
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to exit with exit code " + ExitCode.OK);

        String[] overwriteArgs = getOverwriteArgs(args);
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, overwriteArgs);
        }

        assertEquals(ExitCode.OK, actual, "expected command to exit with exit code " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_APPLICATIONS, EMPTY_ARRAY, MY_OTHER_APP_DIR_CONTENTS);
    }

    @Test
    void testAddApplicationDirTwice_ReturnsExceptedResult() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "add",
            "application",
            "-archive_file",
            NEW_ARCHIVE_VALUE,
            "-source",
            getSourcePath(ArchiveEntryType.APPLICATION, "my-other-app")
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to exit with exit code " + ExitCode.OK);

        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to exit with exit code " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_APPLICATIONS, EMPTY_ARRAY, MY_OTHER_APP_DIR_CONTENTS,
            MY_OTHER_APP_DIR_DUP_CONTENTS);
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                                 application plan                                          //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    @Test
    void testAddNewApplicationPlanFile_ReturnsExceptedResult() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "add",
            "applicationPlan",
            "-archive_file",
            NEW_ARCHIVE_VALUE,
            "-source",
            getSourcePath(ArchiveEntryType.APPLICATION_PLAN, "my-app.xml")
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to return " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_APPLICATION_PLANS, EMPTY_ARRAY, MY_APP_DEPLOYMENT_PLAN_CONTENTS);
    }

    @Test
    void testAddApplicationPlanFileOverwrite_ReturnsExceptedResult() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "add",
            "applicationPlan",
            "-archive_file",
            NEW_ARCHIVE_VALUE,
            "-source",
            getSourcePath(ArchiveEntryType.APPLICATION_PLAN, "my-app.xml")
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to return " + ExitCode.OK);

        String[] overwriteArgs = getOverwriteArgs(args);
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, overwriteArgs);
        }

        assertEquals(ExitCode.OK, actual, "expected command to return " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_APPLICATION_PLANS, EMPTY_ARRAY, MY_APP_DEPLOYMENT_PLAN_CONTENTS);
    }

    @Test
    void testAddApplicationPlanFileTwice_ReturnsExceptedResult() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "add",
            "applicationPlan",
            "-archive_file",
            NEW_ARCHIVE_VALUE,
            "-source",
            getSourcePath(ArchiveEntryType.APPLICATION_PLAN, "my-app.xml")
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to return " + ExitCode.OK);

        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to return " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_APPLICATION_PLANS, EMPTY_ARRAY, MY_APP_DEPLOYMENT_PLAN_CONTENTS,
            MY_APP_DEPLOYMENT_PLAN_DUP_CONTENTS);
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                                 classpath library                                         //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    @Test
    void testAddNewClasspathLibraryFile_ReturnsExceptedResult() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "add",
            "classpathLibrary",
            "-archive_file",
            NEW_ARCHIVE_VALUE,
            "-source",
            getSourcePath(ArchiveEntryType.CLASSPATH_LIB, "bar.jar")
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to return " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_CLASSPATH_LIBRARIES, EMPTY_ARRAY, CLASSPATH_LIB_BAR_JAR_CONTENTS);
    }

    @Test
    void testAddClasspathLibraryFileOverwrite_ReturnsExceptedResult() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "add",
            "classpathLibrary",
            "-archive_file",
            NEW_ARCHIVE_VALUE,
            "-source",
            getSourcePath(ArchiveEntryType.CLASSPATH_LIB, "bar.jar")
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to return " + ExitCode.OK);

        String[] overwriteArgs = getOverwriteArgs(args);
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, overwriteArgs);
        }

        assertEquals(ExitCode.OK, actual, "expected command to return " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_CLASSPATH_LIBRARIES, EMPTY_ARRAY, CLASSPATH_LIB_BAR_JAR_CONTENTS);
    }

    @Test
    void testAddClasspathLibraryFileTwice_ReturnsExceptedResult() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "add",
            "classpathLibrary",
            "-archive_file",
            NEW_ARCHIVE_VALUE,
            "-source",
            getSourcePath(ArchiveEntryType.CLASSPATH_LIB, "bar.jar")
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to return " + ExitCode.OK);

        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to return " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_CLASSPATH_LIBRARIES, EMPTY_ARRAY, CLASSPATH_LIB_BAR_JAR_CONTENTS,
            CLASSPATH_LIB_BAR_JAR_DUP_CONTENTS);
    }

    @Test
    void testAddNewClasspathLibraryDir_ReturnsExceptedResult() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "add",
            "classpathLibrary",
            "-archive_file",
            NEW_ARCHIVE_VALUE,
            "-source",
            getSourcePath(ArchiveEntryType.CLASSPATH_LIB, "bar")
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to exit with exit code " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_CLASSPATH_LIBRARIES, EMPTY_ARRAY, CLASSPATH_LIB_BAR_DIR_CONTENTS);
    }

    @Test
    void testAddClasspathLibraryDirOverwrite_ReturnsExceptedResult() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "add",
            "classpathLibrary",
            "-archive_file",
            NEW_ARCHIVE_VALUE,
            "-source",
            getSourcePath(ArchiveEntryType.CLASSPATH_LIB, "bar")
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to exit with exit code " + ExitCode.OK);

        String[] overwriteArgs = getOverwriteArgs(args);
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, overwriteArgs);
        }

        assertEquals(ExitCode.OK, actual, "expected command to exit with exit code " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_CLASSPATH_LIBRARIES, EMPTY_ARRAY, CLASSPATH_LIB_BAR_DIR_CONTENTS);
    }

    @Test
    void testAddClasspathLibraryDirTwice_ReturnsExceptedResult() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "add",
            "classpathLibrary",
            "-archive_file",
            NEW_ARCHIVE_VALUE,
            "-source",
            getSourcePath(ArchiveEntryType.CLASSPATH_LIB, "bar")
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to exit with exit code " + ExitCode.OK);

        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to exit with exit code " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_CLASSPATH_LIBRARIES, EMPTY_ARRAY, CLASSPATH_LIB_BAR_DIR_CONTENTS,
            CLASSPATH_LIB_BAR_DIR_DUP_CONTENTS);
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                                 Coherence config                                          //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    @Test
    void testAddCoherenceConfigBadSource_Fails() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "add",
            "coherenceConfig",
            "-archive_file",
            NEW_ARCHIVE_VALUE,
            "-cluster_name",
            "mycluster",
            "-source",
            "missing.xml"
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.ARG_VALIDATION_ERROR, actual,
            "expected command to exit with exit code " + ExitCode.ARG_VALIDATION_ERROR);
    }

    @Test
    void testAddCoherenceConfigNoCluster_Fails() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "add",
            "coherenceConfig",
            "-archive_file",
            NEW_ARCHIVE_VALUE,
            "-source",
            "missing.xml"
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
    void testAddNewCoherenceConfigFile_ReturnsExceptedResult() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "add",
            "coherenceConfig",
            "-archive_file",
            NEW_ARCHIVE_VALUE,
            "-cluster_name",
            "mycluster",
            "-source",
            getSegregatedSourcePath(ArchiveEntryType.COHERENCE_CONFIG, "mycluster", "cache-config.xml")
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to return " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_COHERENCE_CONFIGS, EMPTY_ARRAY, COHERENCE_MYCLUSTER_CONFIG_FILE_CONTENTS);
    }

    @Test
    void testAddCoherenceConfigFileOverwrite_ReturnsExceptedResult() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "add",
            "coherenceConfig",
            "-archive_file",
            NEW_ARCHIVE_VALUE,
            "-cluster_name",
            "mycluster",
            "-source",
            getSegregatedSourcePath(ArchiveEntryType.COHERENCE_CONFIG, "mycluster", "cache-config.xml")
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to return " + ExitCode.OK);

        String[] overwriteArgs = getOverwriteArgs(args);
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, overwriteArgs);
        }

        assertEquals(ExitCode.OK, actual, "expected command to return " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_COHERENCE_CONFIGS, EMPTY_ARRAY, COHERENCE_MYCLUSTER_CONFIG_FILE_CONTENTS);
    }

    @Test
    void testAddCoherenceConfigFileTwice_ReturnsExceptedResult() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "add",
            "coherenceConfig",
            "-archive_file",
            NEW_ARCHIVE_VALUE,
            "-cluster_name",
            "mycluster",
            "-source",
            getSegregatedSourcePath(ArchiveEntryType.COHERENCE_CONFIG, "mycluster", "cache-config.xml")
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to return " + ExitCode.OK);

        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to return " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_COHERENCE_CONFIGS, EMPTY_ARRAY, COHERENCE_MYCLUSTER_CONFIG_FILE_CONTENTS,
            COHERENCE_MYCLUSTER_CONFIG_FILE_DUP_CONTENTS);
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                              Coherence persistence dir                                    //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    @Test
    void testAddCoherencePersistenceDirNoType_Fails() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "add",
            "coherencePersistenceDir",
            "-archive_file",
            NEW_ARCHIVE_VALUE,
            "-cluster_name",
            "mycluster"
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
    void testAddCoherencePersistenceDirNoCluster_Fails() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "add",
            "coherencePersistenceDir",
            "-archive_file",
            NEW_ARCHIVE_VALUE,
            "-source",
            "missing.xml"
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
    void testAddNewCoherencePersistenceDir_ReturnsExceptedResult() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "add",
            "coherencePersistenceDir",
            "-archive_file",
            NEW_ARCHIVE_VALUE,
            "-cluster_name",
            "mycluster",
            "-type",
            "active"
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to return " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_COHERENCE_PERSISTENCE_DIRS, EMPTY_ARRAY,
            COHERENCE_MYCLUSTER_PERSISTENT_DIR_ACTIVE_CONTENTS);
    }

    @Test
    void testAddCoherencePersistenceDirOverwrite_ReturnsExceptedResult() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "add",
            "coherencePersistenceDir",
            "-archive_file",
            NEW_ARCHIVE_VALUE,
            "-cluster_name",
            "mycluster",
            "-type",
            "active"
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to return " + ExitCode.OK);

        String[] overwriteArgs = getOverwriteArgs(args);
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, overwriteArgs);
        }

        assertEquals(ExitCode.OK, actual, "expected command to return " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_COHERENCE_PERSISTENCE_DIRS, EMPTY_ARRAY,
            COHERENCE_MYCLUSTER_PERSISTENT_DIR_ACTIVE_CONTENTS);
    }

    @Test
    void testAddCoherencePersistenceDirTwice_ReturnsExceptedResult() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "add",
            "coherencePersistenceDir",
            "-archive_file",
            NEW_ARCHIVE_VALUE,
            "-cluster_name",
            "mycluster",
            "-type",
            "active"
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to return " + ExitCode.OK);

        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to return " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_COHERENCE_PERSISTENCE_DIRS, EMPTY_ARRAY,
            COHERENCE_MYCLUSTER_PERSISTENT_DIR_ACTIVE_CONTENTS,
            COHERENCE_MYCLUSTER_PERSISTENT_DIR_ACTIVE_DUP_CONTENTS);
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                                      custom                                               //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    @Test
    void testAddNewCustomFile_ReturnsExceptedResult() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "add",
            "custom",
            "-archive_file",
            NEW_ARCHIVE_VALUE,
            "-source",
            getSourcePath(ArchiveEntryType.CUSTOM, "foo.properties")
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to return " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_CUSTOM, EMPTY_ARRAY, CUSTOM_FOO_PROPERTIES_CONTENTS);
    }

    @Test
    void testAddNewCustomNestedFile_ReturnsExceptedResult() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "add",
            "custom",
            "-archive_file",
            NEW_ARCHIVE_VALUE,
            "-path",
            "mydir",
            "-source",
            getSourcePath(ArchiveEntryType.CUSTOM, "mydir/bar.properties")
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to return " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_CUSTOM, EMPTY_ARRAY, CUSTOM_MYDIR_BAR_PROPERTIES_CONTENTS);
    }

    @Test
    void testAddCustomFileOverwrite_ReturnsExceptedResult() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "add",
            "custom",
            "-archive_file",
            NEW_ARCHIVE_VALUE,
            "-source",
            getSourcePath(ArchiveEntryType.CUSTOM, "foo.properties")
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to return " + ExitCode.OK);

        String[] overwriteArgs = getOverwriteArgs(args);
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, overwriteArgs);
        }

        assertEquals(ExitCode.OK, actual, "expected command to return " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_CUSTOM, EMPTY_ARRAY, CUSTOM_FOO_PROPERTIES_CONTENTS);
    }

    @Test
    void testAddCustomFileTwice_ReturnsExceptedResult() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "add",
            "custom",
            "-archive_file",
            NEW_ARCHIVE_VALUE,
            "-source",
            getSourcePath(ArchiveEntryType.CUSTOM, "foo.properties")
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to return " + ExitCode.OK);

        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to return " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_CUSTOM, EMPTY_ARRAY, CUSTOM_FOO_PROPERTIES_CONTENTS,
            CUSTOM_FOO_PROPERTIES_DUP_CONTENTS);
    }

    @Test
    void testAddNewCustomDir_ReturnsExceptedResult() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "add",
            "custom",
            "-archive_file",
            NEW_ARCHIVE_VALUE,
            "-source",
            getSourcePath(ArchiveEntryType.CUSTOM, "mydir")
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to exit with exit code " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_CUSTOM, EMPTY_ARRAY, CUSTOM_MYDIR_CONTENTS);
    }

    @Test
    void testAddCustomDirOverwrite_ReturnsExceptedResult() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "add",
            "custom",
            "-archive_file",
            NEW_ARCHIVE_VALUE,
            "-source",
            getSourcePath(ArchiveEntryType.CUSTOM, "mydir")
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to exit with exit code " + ExitCode.OK);

        String[] overwriteArgs = getOverwriteArgs(args);
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, overwriteArgs);
        }

        assertEquals(ExitCode.OK, actual, "expected command to exit with exit code " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_CUSTOM, EMPTY_ARRAY, CUSTOM_MYDIR_CONTENTS);
    }

    @Test
    void testAddCustomDirTwice_ReturnsExceptedResult() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "add",
            "custom",
            "-archive_file",
            NEW_ARCHIVE_VALUE,
            "-source",
            getSourcePath(ArchiveEntryType.CUSTOM, "mydir")
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to exit with exit code " + ExitCode.OK);

        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to exit with exit code " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_CUSTOM, EMPTY_ARRAY, CUSTOM_MYDIR_CONTENTS, CUSTOM_MYDIR_DUP_CONTENTS);
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                                  database wallet                                          //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    @Test
    void testAddDatabaseWalletNoWalletName_Fails() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "add",
            "databaseWallet",
            "-archive_file",
            NEW_ARCHIVE_VALUE,
            "-source",
            "missing"
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
    void testAddDatabaseWalletBadSource_Fails() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "add",
            "databaseWallet",
            "-archive_file",
            NEW_ARCHIVE_VALUE,
            "-wallet_name",
            "wallet1",
            "-source",
            "missing"
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.ARG_VALIDATION_ERROR, actual,
            "expected command to exit with exit code " + ExitCode.ARG_VALIDATION_ERROR);
    }


    @Test
    void testAddNewDatabaseWalletDir_ReturnsExceptedResult() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "add",
            "databaseWallet",
            "-archive_file",
            NEW_ARCHIVE_VALUE,
            "-wallet_name",
            "wallet1",
            "-source",
            getSourcePath(ArchiveEntryType.DB_WALLET, "wallet1")
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to exit with exit code " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_DATABASE_WALLETS, EMPTY_ARRAY, DATABASE_WALLET_WALLET1_CONTENTS);
    }

    @Test
    void testAddNewDatabaseWalletFile_ReturnsExpectedResult() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[]{
            "add",
            "databaseWallet",
            "-archive_file",
            NEW_ARCHIVE_VALUE,
            "-wallet_name",
            "wallet1",
            "-source",
            getSourcePath(ArchiveEntryType.DB_WALLET, "wallet1/atpwallet.zip")
        };
        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to exit with exit code " + ExitCode.OK);
        assertEquals("wlsdeploy/dbWallets/wallet1/atpwallet.zip", outStringWriter.toString().trim());
    }

    @Test
    void testAddDatabaseWalletDirOverwrite_ReturnsExceptedResult() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "add",
            "databaseWallet",
            "-archive_file",
            NEW_ARCHIVE_VALUE,
            "-wallet_name",
            "wallet1",
            "-source",
            getSourcePath(ArchiveEntryType.DB_WALLET, "wallet1")
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to exit with exit code " + ExitCode.OK);

        String[] overwriteArgs = getOverwriteArgs(args);
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, overwriteArgs);
        }

        assertEquals(ExitCode.OK, actual, "expected command to exit with exit code " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_DATABASE_WALLETS, EMPTY_ARRAY, DATABASE_WALLET_WALLET1_CONTENTS);
    }

    @Test
    void testAddNewDatabaseWalletFileOverwrite_ReturnsExpectedResult() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[]{
            "add",
            "databaseWallet",
            "-archive_file",
            NEW_ARCHIVE_VALUE,
            "-wallet_name",
            "wallet1",
            "-source",
            getSourcePath(ArchiveEntryType.DB_WALLET, "wallet1/atpwallet.zip")
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to exit with exit code " + ExitCode.OK);

        outStringWriter = new StringWriter();
        errStringWriter = new StringWriter();
        String[] overwriteArgs = getOverwriteArgs(args);
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, overwriteArgs);
        }

        assertEquals(ExitCode.OK, actual, "expected command to exit with exit code " + ExitCode.OK);
        assertEquals("wlsdeploy/dbWallets/wallet1/atpwallet.zip", outStringWriter.toString().trim());
    }

    @Test
    void testAddDatabaseWalletDirTwice_ReturnsExceptedResult() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "add",
            "databaseWallet",
            "-archive_file",
            NEW_ARCHIVE_VALUE,
            "-wallet_name",
            "wallet1",
            "-source",
            getSourcePath(ArchiveEntryType.DB_WALLET, "wallet1")
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to exit with exit code " + ExitCode.OK);

        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to exit with exit code " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_DATABASE_WALLETS, EMPTY_ARRAY, DATABASE_WALLET_WALLET1_CONTENTS,
            DATABASE_WALLET_WALLET1_DUP_CONTENTS);
    }

    @Test
    void testAddDatabaseWalletFileTwice_ReturnsExceptedResult() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "add",
            "databaseWallet",
            "-archive_file",
            NEW_ARCHIVE_VALUE,
            "-wallet_name",
            "wallet1",
            "-source",
            getSourcePath(ArchiveEntryType.DB_WALLET, "wallet1/atpwallet.zip")
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to exit with exit code " + ExitCode.OK);

        outStringWriter = new StringWriter();
        errStringWriter = new StringWriter();
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to exit with exit code " + ExitCode.OK);
        assertEquals("wlsdeploy/dbWallets/wallet1/atpwallet(1).zip", outStringWriter.toString().trim());
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                              $DOMAIN_HOME/bin script                                      //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    @Test
    void testAddNewDomainBinFile_ReturnsExceptedResult() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "add",
            "domainBinScript",
            "-archive_file",
            NEW_ARCHIVE_VALUE,
            "-source",
            getSourcePath(ArchiveEntryType.DOMAIN_BIN, "setUserOverrides.sh")
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to return " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_DOMAIN_BIN_SCRIPTS, EMPTY_ARRAY, DOMAIN_BIN_SET_USER_OVERRIDES_SH_CONTENTS);
    }

    @Test
    void testAddDomainBinFileOverwrite_ReturnsExceptedResult() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "add",
            "domainBinScript",
            "-archive_file",
            NEW_ARCHIVE_VALUE,
            "-source",
            getSourcePath(ArchiveEntryType.DOMAIN_BIN, "setUserOverrides.sh")
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to return " + ExitCode.OK);

        String[] overwriteArgs = getOverwriteArgs(args);
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, overwriteArgs);
        }

        assertEquals(ExitCode.OK, actual, "expected command to return " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_DOMAIN_BIN_SCRIPTS, EMPTY_ARRAY, DOMAIN_BIN_SET_USER_OVERRIDES_SH_CONTENTS);
    }

    @Test
    void testAddDomainBinFileTwice_ReturnsExceptedResult() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "add",
            "domainBinScript",
            "-archive_file",
            NEW_ARCHIVE_VALUE,
            "-source",
            getSourcePath(ArchiveEntryType.DOMAIN_BIN, "setUserOverrides.sh")
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to return " + ExitCode.OK);

        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to return " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_DOMAIN_BIN_SCRIPTS, EMPTY_ARRAY, DOMAIN_BIN_SET_USER_OVERRIDES_SH_CONTENTS,
            DOMAIN_BIN_SET_USER_OVERRIDES_SH_DUP_CONTENTS);
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                              $DOMAIN_HOME/lib library                                     //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    @Test
    void testAddNewDomainLibFile_ReturnsExceptedResult() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "add",
            "domainLibrary",
            "-archive_file",
            NEW_ARCHIVE_VALUE,
            "-source",
            getSourcePath(ArchiveEntryType.DOMAIN_LIB, "foo.jar")
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to return " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_DOMAIN_LIBRARIES, EMPTY_ARRAY, DOMAIN_LIB_FOO_JAR_CONTENTS);
    }

    @Test
    void testAddDomainLibFileOverwrite_ReturnsExceptedResult() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "add",
            "domainLibrary",
            "-archive_file",
            NEW_ARCHIVE_VALUE,
            "-source",
            getSourcePath(ArchiveEntryType.DOMAIN_LIB, "foo.jar")
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to return " + ExitCode.OK);

        String[] overwriteArgs = getOverwriteArgs(args);
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, overwriteArgs);
        }

        assertEquals(ExitCode.OK, actual, "expected command to return " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_DOMAIN_LIBRARIES, EMPTY_ARRAY, DOMAIN_LIB_FOO_JAR_CONTENTS);
    }

    @Test
    void testAddDomainLibFileTwice_ReturnsExceptedResult() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "add",
            "domainLibrary",
            "-archive_file",
            NEW_ARCHIVE_VALUE,
            "-source",
            getSourcePath(ArchiveEntryType.DOMAIN_LIB, "foo.jar")
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to return " + ExitCode.OK);

        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to return " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_DOMAIN_LIBRARIES, EMPTY_ARRAY, DOMAIN_LIB_FOO_JAR_CONTENTS,
            DOMAIN_LIB_FOO_JAR_DUP_CONTENTS);
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                                    file store                                             //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    @Test
    void testAddFileStoreNoArchive_Fails() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "add",
            "fileStore",
            "-name",
            "fs1"
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
    void testAddFileStoreNoName_Fails() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "add",
            "fileStore",
            "-archive_file",
            NEW_ARCHIVE_VALUE
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
    void testAddNewFileStoreDir_ReturnsExceptedResult() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "add",
            "fileStore",
            "-archive_file",
            NEW_ARCHIVE_VALUE,
            "-name",
            "fs1"
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to return " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_FILE_STORES, EMPTY_ARRAY, FILE_STORES_FS1_CONTENTS);
    }

    @Test
    void testAddFileStoreDirOverwrite_ReturnsExceptedResult() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "add",
            "fileStore",
            "-archive_file",
            NEW_ARCHIVE_VALUE,
            "-name",
            "fs1"
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to return " + ExitCode.OK);

        String[] overwriteArgs = getOverwriteArgs(args);
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, overwriteArgs);
        }

        assertEquals(ExitCode.OK, actual, "expected command to return " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_FILE_STORES, EMPTY_ARRAY, FILE_STORES_FS1_CONTENTS);
    }

    @Test
    void testAddFileStoreDirTwice_ReturnsExceptedResult() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "add",
            "fileStore",
            "-archive_file",
            NEW_ARCHIVE_VALUE,
            "-name",
            "fs1"
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to return " + ExitCode.OK);

        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to return " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_FILE_STORES, EMPTY_ARRAY, FILE_STORES_FS1_CONTENTS,
            FILE_STORES_FS1_DUP_CONTENTS);
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                              JMS Foreign Server binding                                   //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    @Test
    void testAddForeignServerBindingNoForeignServerName_Fails() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "add",
            "jmsForeignServer",
            "-archive_file",
            NEW_ARCHIVE_VALUE,
            "-source",
            "missing"
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
    void testAddForeignServerBindingBadSource_Fails() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "add",
            "jmsForeignServer",
            "-archive_file",
            NEW_ARCHIVE_VALUE,
            "-foreign_server_name",
            "fs1",
            "-source",
            "missing"
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.ARG_VALIDATION_ERROR, actual,
            "expected command to exit with exit code " + ExitCode.ARG_VALIDATION_ERROR);
    }

    @Test
    void testAddNewForeignServerBinding_ReturnsExceptedResult() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "add",
            "jmsForeignServer",
            "-archive_file",
            NEW_ARCHIVE_VALUE,
            "-foreign_server_name",
            "fs1",
            "-source",
            getSegregatedSourcePath(ArchiveEntryType.JMS_FOREIGN_SERVER, "fs1", "jndi.properties")
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to return " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_FOREIGN_SERVERS, EMPTY_ARRAY, FOREIGN_SERVERS_FS1_JNDI_PROPERTIES_CONTENTS);
    }

    @Test
    void testAddForeignServerBindingOverwrite_ReturnsExceptedResult() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "add",
            "jmsForeignServer",
            "-archive_file",
            NEW_ARCHIVE_VALUE,
            "-foreign_server_name",
            "fs1",
            "-source",
            getSegregatedSourcePath(ArchiveEntryType.JMS_FOREIGN_SERVER, "fs1", "jndi.properties")
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to return " + ExitCode.OK);

        String[] overwriteArgs = getOverwriteArgs(args);
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, overwriteArgs);
        }

        assertEquals(ExitCode.OK, actual, "expected command to return " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_FOREIGN_SERVERS, EMPTY_ARRAY, FOREIGN_SERVERS_FS1_JNDI_PROPERTIES_CONTENTS);
    }

    @Test
    void testAddForeignServerBindingTwice_ReturnsExceptedResult() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "add",
            "jmsForeignServer",
            "-archive_file",
            NEW_ARCHIVE_VALUE,
            "-foreign_server_name",
            "fs1",
            "-source",
            getSegregatedSourcePath(ArchiveEntryType.JMS_FOREIGN_SERVER, "fs1", "jndi.properties")
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to return " + ExitCode.OK);

        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to return " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_FOREIGN_SERVERS, EMPTY_ARRAY, FOREIGN_SERVERS_FS1_JNDI_PROPERTIES_CONTENTS,
            FOREIGN_SERVERS_FS1_JNDI_PROPERTIES_DUP_CONTENTS);
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                                    MIME mapping                                           //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    @Test
    void testAddNewMIMEMappingFile_ReturnsExceptedResult() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "add",
            "mimeMapping",
            "-archive_file",
            NEW_ARCHIVE_VALUE,
            "-source",
            getSourcePath(ArchiveEntryType.MIME_MAPPING, "mimemappings.properties")
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to return " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_MIME_MAPPINGS, EMPTY_ARRAY, MIME_MAPPING_PROPERTIES_CONTENTS);
    }

    @Test
    void testAddMIMEMappingFileOverwrite_ReturnsExceptedResult() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "add",
            "mimeMapping",
            "-archive_file",
            NEW_ARCHIVE_VALUE,
            "-source",
            getSourcePath(ArchiveEntryType.MIME_MAPPING, "mimemappings.properties")
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to return " + ExitCode.OK);

        String[] overwriteArgs = getOverwriteArgs(args);
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, overwriteArgs);
        }

        assertEquals(ExitCode.OK, actual, "expected command to return " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_MIME_MAPPINGS, EMPTY_ARRAY, MIME_MAPPING_PROPERTIES_CONTENTS);
    }

    @Test
    void testAddMIMEMappingFileTwice_ReturnsExceptedResult() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "add",
            "mimeMapping",
            "-archive_file",
            NEW_ARCHIVE_VALUE,
            "-source",
            getSourcePath(ArchiveEntryType.MIME_MAPPING, "mimemappings.properties")
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to return " + ExitCode.OK);

        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to return " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_MIME_MAPPINGS, EMPTY_ARRAY, MIME_MAPPING_PROPERTIES_CONTENTS,
            MIME_MAPPING_PROPERTIES_DUP_CONTENTS);
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                                node manager keystore                                      //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    @Test
    void testAddNewNodeManagerKeystore_ReturnsExceptedResult() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "add",
            "nodeManagerKeystore",
            "-archive_file",
            NEW_ARCHIVE_VALUE,
            "-source",
            getSourcePath(ArchiveEntryType.NODE_MANAGER_KEY_STORE, "nmIdentity.jks")
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to return " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_NODE_MANAGER_KEYSTORES, EMPTY_ARRAY, NODE_MANAGER_IDENTITY_JKS_CONTENTS);
    }

    @Test
    void testAddNodeManagerKeystoreOverwrite_ReturnsExceptedResult() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "add",
            "nodeManagerKeystore",
            "-archive_file",
            NEW_ARCHIVE_VALUE,
            "-source",
            getSourcePath(ArchiveEntryType.NODE_MANAGER_KEY_STORE, "nmIdentity.jks")
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to return " + ExitCode.OK);

        String[] overwriteArgs = getOverwriteArgs(args);
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, overwriteArgs);
        }

        assertEquals(ExitCode.OK, actual, "expected command to return " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_NODE_MANAGER_KEYSTORES, EMPTY_ARRAY, NODE_MANAGER_IDENTITY_JKS_CONTENTS);
    }

    @Test
    void testAddNodeManagerKeystoreTwice_ReturnsExceptedResult() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "add",
            "nodeManagerKeystore",
            "-archive_file",
            NEW_ARCHIVE_VALUE,
            "-source",
            getSourcePath(ArchiveEntryType.NODE_MANAGER_KEY_STORE, "nmIdentity.jks")
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to return " + ExitCode.OK);

        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to return " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_NODE_MANAGER_KEYSTORES, EMPTY_ARRAY, NODE_MANAGER_IDENTITY_JKS_CONTENTS,
            NODE_MANAGER_IDENTITY_JKS_DUP_CONTENTS);
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                                     OPSS wallet                                           //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    @Test
    void testAddNewOPSSWallet_ReturnsExceptedResult() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "add",
            "opssWallet",
            "-archive_file",
            NEW_ARCHIVE_VALUE,
            "-source",
            getSourcePath(ArchiveEntryType.OPSS_WALLET, "opss-wallet.zip")
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to return " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_OPSS_WALLET, EMPTY_ARRAY, OPSS_WALLET_CONTENT);
    }

    @Test
    void testAddOPSSWalletOverwrite_ReturnsExceptedResult() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "add",
            "opssWallet",
            "-archive_file",
            NEW_ARCHIVE_VALUE,
            "-source",
            getSourcePath(ArchiveEntryType.OPSS_WALLET, "opss-wallet.zip")
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to return " + ExitCode.OK);

        String[] overwriteArgs = getOverwriteArgs(args);
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, overwriteArgs);
        }

        assertEquals(ExitCode.OK, actual, "expected command to return " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_OPSS_WALLET, EMPTY_ARRAY, OPSS_WALLET_CONTENT);
    }

    @Test
    void testAddOPSSWalletTwice_Fails() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "add",
            "opssWallet",
            "-archive_file",
            NEW_ARCHIVE_VALUE,
            "-source",
            getSourcePath(ArchiveEntryType.OPSS_WALLET, "opss-wallet.zip")
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to return " + ExitCode.OK);

        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.ERROR, actual, "expected command to return " + ExitCode.ERROR);
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                                      RCU wallet                                           //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    @Test
    void testAddNewRCUWallet_ReturnsExceptedResult() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "add",
            "rcuWallet",
            "-archive_file",
            NEW_ARCHIVE_VALUE,
            "-source",
            getSourcePath(ArchiveEntryType.RCU_WALLET, "")
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to return " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_RCU_WALLET, EMPTY_ARRAY, DATABASE_WALLET_RCU_CONTENTS);
    }

    @Test
    void testAddRCUWalletOverwrite_ReturnsExceptedResult() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "add",
            "rcuWallet",
            "-archive_file",
            NEW_ARCHIVE_VALUE,
            "-source",
            getSourcePath(ArchiveEntryType.RCU_WALLET, "")
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to return " + ExitCode.OK);

        String[] overwriteArgs = getOverwriteArgs(args);
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, overwriteArgs);
        }

        assertEquals(ExitCode.OK, actual, "expected command to return " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_RCU_WALLET, EMPTY_ARRAY, DATABASE_WALLET_RCU_CONTENTS);
    }

    @Test
    void testAddRCUWalletTwice_Fails() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "add",
            "rcuWallet",
            "-archive_file",
            NEW_ARCHIVE_VALUE,
            "-source",
            getSourcePath(ArchiveEntryType.RCU_WALLET, "")
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to return " + ExitCode.OK);

        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.ERROR, actual, "expected command to return " + ExitCode.ERROR);
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                                        script                                             //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    @Test
    void testAddNewScript_ReturnsExceptedResult() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "add",
            "script",
            "-archive_file",
            NEW_ARCHIVE_VALUE,
            "-source",
            getSourcePath(ArchiveEntryType.SCRIPT, "my_fancy_script.sh")
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to return " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_SCRIPTS, EMPTY_ARRAY, SCRIPTS_FANCY_SCRIPT_CONTENTS);
    }

    @Test
    void testAddScriptOverwrite_ReturnsExceptedResult() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "add",
            "script",
            "-archive_file",
            NEW_ARCHIVE_VALUE,
            "-source",
            getSourcePath(ArchiveEntryType.SCRIPT, "my_fancy_script.sh")
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to return " + ExitCode.OK);

        String[] overwriteArgs = getOverwriteArgs(args);
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, overwriteArgs);
        }

        assertEquals(ExitCode.OK, actual, "expected command to return " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_SCRIPTS, EMPTY_ARRAY, SCRIPTS_FANCY_SCRIPT_CONTENTS);
    }

    @Test
    void testAddScriptTwice_ReturnsExceptedResult() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "add",
            "script",
            "-archive_file",
            NEW_ARCHIVE_VALUE,
            "-source",
            getSourcePath(ArchiveEntryType.SCRIPT, "my_fancy_script.sh")
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to return " + ExitCode.OK);

        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to return " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_SCRIPTS, EMPTY_ARRAY, SCRIPTS_FANCY_SCRIPT_CONTENTS,
            SCRIPTS_FANCY_SCRIPT_DUP_CONTENTS);
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                                     server keystore                                       //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    @Test
    void testAddServerKeystoreNoServerName_Fails() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "add",
            "serverKeystore",
            "-archive_file",
            NEW_ARCHIVE_VALUE,
            "-source",
            "missing"
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
    void testAddServerKeystoreBadSource_Fails() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "add",
            "serverKeystore",
            "-archive_file",
            NEW_ARCHIVE_VALUE,
            "-server_name",
            "AdminServer",
            "-source",
            "missing"
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.ARG_VALIDATION_ERROR, actual,
            "expected command to exit with exit code " + ExitCode.ARG_VALIDATION_ERROR);
    }

    @Test
    void testAddNewServerKeystore_ReturnsExceptedResult() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "add",
            "serverKeystore",
            "-archive_file",
            NEW_ARCHIVE_VALUE,
            "-server_name",
            "AdminServer",
            "-source",
            getSegregatedSourcePath(ArchiveEntryType.SERVER_KEYSTORE, "AdminServer", "identity.jks")
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to return " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_SERVER_KEYSTORES, EMPTY_ARRAY, SERVERS_ADMIN_SERVER_IDENTITY_JKS_CONTENTS);
    }

    @Test
    void testAddServerKeystoreOverwrite_ReturnsExceptedResult() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "add",
            "serverKeystore",
            "-archive_file",
            NEW_ARCHIVE_VALUE,
            "-server_name",
            "AdminServer",
            "-source",
            getSegregatedSourcePath(ArchiveEntryType.SERVER_KEYSTORE, "AdminServer", "identity.jks")
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to return " + ExitCode.OK);

        String[] overwriteArgs = getOverwriteArgs(args);
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, overwriteArgs);
        }

        assertEquals(ExitCode.OK, actual, "expected command to return " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_SERVER_KEYSTORES, EMPTY_ARRAY, SERVERS_ADMIN_SERVER_IDENTITY_JKS_CONTENTS);
    }

    @Test
    void testAddServerKeystoreTwice_ReturnsExceptedResult() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "add",
            "serverKeystore",
            "-archive_file",
            NEW_ARCHIVE_VALUE,
            "-server_name",
            "AdminServer",
            "-source",
            getSegregatedSourcePath(ArchiveEntryType.SERVER_KEYSTORE, "AdminServer", "identity.jks")
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to return " + ExitCode.OK);

        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to return " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_SERVER_KEYSTORES, EMPTY_ARRAY, SERVERS_ADMIN_SERVER_IDENTITY_JKS_CONTENTS,
            SERVERS_ADMIN_SERVER_IDENTITY_JKS_DUP_CONTENTS);
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                                  shared library                                           //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    @Test
    void testAddNewSharedLibraryFile_ReturnsExceptedResult() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "add",
            "sharedLibrary",
            "-archive_file",
            NEW_ARCHIVE_VALUE,
            "-source",
            getSourcePath(ArchiveEntryType.SHARED_LIBRARY, "my-lib.war")
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to return " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_SHARED_LIBRARIES, EMPTY_ARRAY, SHARED_LIBS_MY_LIB_WAR_CONTENTS);
    }

    @Test
    void testAddSharedLibraryFileOverwrite_ReturnsExceptedResult() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "add",
            "sharedLibrary",
            "-archive_file",
            NEW_ARCHIVE_VALUE,
            "-source",
            getSourcePath(ArchiveEntryType.SHARED_LIBRARY, "my-lib.war")
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to return " + ExitCode.OK);

        String[] overwriteArgs = getOverwriteArgs(args);
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, overwriteArgs);
        }

        assertEquals(ExitCode.OK, actual, "expected command to return " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_SHARED_LIBRARIES, EMPTY_ARRAY, SHARED_LIBS_MY_LIB_WAR_CONTENTS);
    }

    @Test
    void testAddSharedLibraryFileTwice_ReturnsExceptedResult() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "add",
            "sharedLibrary",
            "-archive_file",
            NEW_ARCHIVE_VALUE,
            "-source",
            getSourcePath(ArchiveEntryType.SHARED_LIBRARY, "my-lib.war")
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to return " + ExitCode.OK);

        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to return " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_SHARED_LIBRARIES, EMPTY_ARRAY, SHARED_LIBS_MY_LIB_WAR_CONTENTS,
            SHARED_LIBS_MY_LIB_WAR_DUP_CONTENTS);
    }

    @Test
    void testAddNewSharedLibraryDir_ReturnsExceptedResult() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "add",
            "sharedLibrary",
            "-archive_file",
            NEW_ARCHIVE_VALUE,
            "-source",
            getSourcePath(ArchiveEntryType.SHARED_LIBRARY, "my-other-lib")
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to exit with exit code " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_SHARED_LIBRARIES, EMPTY_ARRAY, SHARED_LIBS_MY_OTHER_LIB_CONTENTS);
    }

    @Test
    void testAddSharedLibraryDirOverwrite_ReturnsExceptedResult() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "add",
            "sharedLibrary",
            "-archive_file",
            NEW_ARCHIVE_VALUE,
            "-source",
            getSourcePath(ArchiveEntryType.SHARED_LIBRARY, "my-other-lib")
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to exit with exit code " + ExitCode.OK);

        String[] overwriteArgs = getOverwriteArgs(args);
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, overwriteArgs);
        }

        assertEquals(ExitCode.OK, actual, "expected command to exit with exit code " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_SHARED_LIBRARIES, EMPTY_ARRAY, SHARED_LIBS_MY_OTHER_LIB_CONTENTS);
    }

    @Test
    void testAddSharedLibraryDirTwice_ReturnsExceptedResult() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "add",
            "sharedLibrary",
            "-archive_file",
            NEW_ARCHIVE_VALUE,
            "-source",
            getSourcePath(ArchiveEntryType.SHARED_LIBRARY, "my-other-lib")
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to exit with exit code " + ExitCode.OK);

        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to exit with exit code " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_SHARED_LIBRARIES, EMPTY_ARRAY, SHARED_LIBS_MY_OTHER_LIB_CONTENTS,
            SHARED_LIBS_MY_OTHER_LIB_DUP_CONTENTS);
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                                shared library plan                                        //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    @Test
    void testAddNewSharedLibraryPlanFile_ReturnsExceptedResult() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "add",
            "sharedLibraryPlan",
            "-archive_file",
            NEW_ARCHIVE_VALUE,
            "-source",
            getSourcePath(ArchiveEntryType.SHLIB_PLAN, "my-lib.xml")
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to return " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_SHARED_LIBRARIES_PLANS, EMPTY_ARRAY, SHARED_LIBS_MY_LIB_XML_CONTENTS);
    }

    @Test
    void testAddSharedLibraryPlanFileOverwrite_ReturnsExceptedResult() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "add",
            "sharedLibraryPlan",
            "-archive_file",
            NEW_ARCHIVE_VALUE,
            "-source",
            getSourcePath(ArchiveEntryType.SHLIB_PLAN, "my-lib.xml")
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to return " + ExitCode.OK);

        String[] overwriteArgs = getOverwriteArgs(args);
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, overwriteArgs);
        }

        assertEquals(ExitCode.OK, actual, "expected command to return " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_SHARED_LIBRARIES_PLANS, EMPTY_ARRAY, SHARED_LIBS_MY_LIB_XML_CONTENTS);
    }

    @Test
    void testAddSharedLibraryPlanFileTwice_ReturnsExceptedResult() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "add",
            "sharedLibraryPlan",
            "-archive_file",
            NEW_ARCHIVE_VALUE,
            "-source",
            getSourcePath(ArchiveEntryType.SHLIB_PLAN, "my-lib.xml")
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to return " + ExitCode.OK);

        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to return " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_SHARED_LIBRARIES_PLANS, EMPTY_ARRAY, SHARED_LIBS_MY_LIB_XML_CONTENTS,
            SHARED_LIBS_MY_LIB_XML_DUP_CONTENTS);
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                               structured application                                      //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    @Test
    void testAddNewStructuredApplication_ReturnsExceptedResult() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "add",
            "structuredApplication",
            "-archive_file",
            NEW_ARCHIVE_VALUE,
            "-source",
            getSourcePath(ArchiveEntryType.STRUCTURED_APPLICATION, "webapp")
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to return " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_STRUCTURED_APPLICATIONS, EMPTY_ARRAY, STRUCTURED_APP_WEBAPP_CONTENTS);
    }

    @Test
    void testAddStructuredApplicationOverwrite_ReturnsExceptedResult() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "add",
            "structuredApplication",
            "-archive_file",
            NEW_ARCHIVE_VALUE,
            "-source",
            getSourcePath(ArchiveEntryType.STRUCTURED_APPLICATION, "webapp")
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to return " + ExitCode.OK);

        String[] overwriteArgs = getOverwriteArgs(args);
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, overwriteArgs);
        }

        assertEquals(ExitCode.OK, actual, "expected command to return " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_STRUCTURED_APPLICATIONS, EMPTY_ARRAY, STRUCTURED_APP_WEBAPP_CONTENTS);
    }

    @Test
    void testAddStructuredApplicationTwice_ReturnsExceptedResult() throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "add",
            "structuredApplication",
            "-archive_file",
            NEW_ARCHIVE_VALUE,
            "-source",
            getSourcePath(ArchiveEntryType.STRUCTURED_APPLICATION, "webapp")
        };

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to return " + ExitCode.OK);

        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }

        assertEquals(ExitCode.OK, actual, "expected command to return " + ExitCode.OK);
        assertArchiveInExpectedState(LIST_STRUCTURED_APPLICATIONS, EMPTY_ARRAY, STRUCTURED_APP_WEBAPP_CONTENTS,
            STRUCTURED_APP_WEBAPP_DUP_CONTENTS);
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                               private helper methods                                      //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    private String getSourcePath(ArchiveEntryType type, String sourceName) {
        String relativePath = WLSDeployArchive.getPathForType(type) + sourceName;
        File result = new File(SOURCE_ROOT_VALUE, relativePath);
        return FileUtils.getCanonicalPath(result);
    }

    private String getSegregatedSourcePath(ArchiveEntryType type, String segregationName, String sourceName) {
        String relativePath = WLSDeployArchive.getPathForSegregationType(type, segregationName) + sourceName;
        File result = new File(SOURCE_ROOT_VALUE, relativePath);
        return FileUtils.getCanonicalPath(result);
    }

    private void assertArchiveInExpectedState(String[] actualArgs, String[] originalContent,
                                              String[]... addedContent) throws Exception {
        String[] args = new String[actualArgs.length + 3];
        args[0] = "list";
        System.arraycopy(actualArgs, 0, args, 1, actualArgs.length);
        args[actualArgs.length + 1] = "-archive_file";
        args[actualArgs.length + 2] = NEW_ARCHIVE_VALUE;

        List<String> actualEntries = getActualEntries(args);
        List<String> expectedEntries = getExpectedEntries(originalContent, addedContent);
        assertEquals(expectedEntries.size(), actualEntries.size(), "expected zip file to contain " +
            expectedEntries.size());
        for (String actualLine : actualEntries) {
            assertTrue(expectedEntries.contains(actualLine), actualLine + " not in expected output");
        }
    }

    private List<String> getActualEntries(String... args) throws Exception {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
            if (actual != ExitCode.OK) {
                throw new ArchiveHelperException(actual,
                    "Failed to get actual entries for args = {0}", Arrays.toString(args));
            }
        }

        String[] outputLines = outStringWriter.getBuffer().toString().trim().split(System.lineSeparator());
        if (outputLines.length == 0 || (outputLines.length == 1 && StringUtils.isEmpty(outputLines[0]))) {
            return new ArrayList<>();
        } else {
            return Arrays.asList(outputLines);
        }
    }

    private List<String> getExpectedEntries(String[] expected, String[]... addLists) {
        List<String> expectedPaths = new ArrayList<>(Arrays.asList(expected));

        for (String[] addList : addLists) {
            Collections.addAll(expectedPaths, addList);
        }
        return removeEmptyIntermediateDirectories(expectedPaths);
    }

    private List<String> removeEmptyIntermediateDirectories(List<String> entries) {
        List<String> directoryList = entries.stream().filter(s -> s.endsWith(ZIP_SEP)).collect(Collectors.toList());

        ListIterator<String> directoryIterator = directoryList.listIterator();
        while (directoryIterator.hasNext()) {
            String directory = directoryIterator.next();

            boolean removeFromList = true;
            for (String entry : entries) {
                if (!entry.equals(directory) && entry.startsWith(directory)) {
                    removeFromList = false;
                    break;
                }
            }
            if (removeFromList) {
                directoryIterator.remove();
            }
        }

        List<String> results = new ArrayList<>(entries);
        results.removeAll(directoryList);
        return results;
    }

    private String[] getOverwriteArgs(String[] args) {
        String[] result = new String[args.length + 1];
        System.arraycopy(args, 0, result, 0, args.length);
        result[args.length] = "-overwrite";
        return result;
    }
}
