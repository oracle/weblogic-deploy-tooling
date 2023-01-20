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
import java.util.Collections;
import java.util.List;
import java.util.logging.Level;

import oracle.weblogic.deploy.logging.PlatformLogger;
import oracle.weblogic.deploy.logging.WLSDeployLogFactory;
import oracle.weblogic.deploy.util.ExitCode;
import oracle.weblogic.deploy.util.StringUtils;
import oracle.weblogic.deploy.util.WLSDeployZipFileTest;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import static oracle.weblogic.deploy.tool.ArchiveHelper.LOGGER_NAME;
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

    @Test
    void testRemoveNoArchive_Fails() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "remove",
            "application",
            "-name",
            "my-app.war"
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
    void testRemoveNoApp_Fails() {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();
        String[] args = new String[] {
            "remove",
            "application",
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

    // @Test
    void testRemoveExistingAppFile_ReturnsExpectedResults() {
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

        List<String> remainingEntries = getRemainingEntries("list", "application", "-archive_file", ARCHIVE_HELPER_VALUE);
    }

    List<String> getRemainingEntries(String... args) {
        StringWriter outStringWriter = new StringWriter();
        StringWriter errStringWriter = new StringWriter();

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        String[] outputLines = outStringWriter.getBuffer().toString().trim().split(System.lineSeparator());
        if (outputLines.length == 0 || (outputLines.length == 1 && StringUtils.isEmpty(outputLines[0]))) {
            return new ArrayList<>();
        } else {
            return Arrays.asList(outputLines);
        }
    }
}
