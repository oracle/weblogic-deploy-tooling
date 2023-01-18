/*
 * Copyright (c) 2017, 2022, Oracle Corporation and/or its affiliates.  All rights reserved.
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

import oracle.weblogic.deploy.util.WLSDeployZipFileTest;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;

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

    private static final String[] LIST_APP_FILE_EXPECTED = new String[] {"wlsdeploy/applications/my-app.war"};

    private static final String[] LIST_APP_DIR_EXPECTED = new String[] {
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

    private static final String[] LIST_APPS_EXPECTED = new String[LIST_APP_DIR_EXPECTED.length + 3];

    static {
        String[] files = new String[] {
            "wlsdeploy/applications/my-app.war",
            "wlsdeploy/applications/my-app.xml",
            "wlsdeploy/applications/my-other-app.war"
        };
        System.arraycopy(files, 0, LIST_APPS_EXPECTED, 0, 3);
        System.arraycopy(LIST_APP_DIR_EXPECTED, 0, LIST_APPS_EXPECTED, 3, LIST_APP_DIR_EXPECTED.length);
    }

    @BeforeAll
    static void initialize() throws Exception {
        if(!UNIT_TEST_TARGET_DIR.exists() && !UNIT_TEST_TARGET_DIR.mkdirs()) {
            throw new Exception("Unable to create unit test directory: " + UNIT_TEST_TARGET_DIR);
        }
        Files.copy(ARCHIVE_HELPER_SOURCE_ZIP, ARCHIVE_HELPER_TARGET_ZIP, StandardCopyOption.REPLACE_EXISTING);
    }

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
        String expectedPath = LIST_APP_FILE_EXPECTED[0];

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        String[] outputLines = outStringWriter.getBuffer().toString().trim().split(System.lineSeparator());

        assertEquals(0, actual, "expected command to exit with exit code 0");
        assertEquals(1, outputLines.length, "expected list applications my-app.war to return 1 entry");
        assertEquals(expectedPath, outputLines[0],"expected " + expectedPath);
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
        assertEquals(expectedPaths.size(), outputLines.length,
            "expected list applications my-other-app to return " + expectedPaths.size() + " entries");
        for (String actualLine : outputLines) {
            assertTrue(expectedPaths.contains(actualLine), actualLine + " not in expected output");
        }
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
        List<String> expectedPaths = Arrays.asList(LIST_APP_DIR_EXPECTED);

        int actual = -1;
        try (PrintWriter out = new PrintWriter(outStringWriter);
             PrintWriter err = new PrintWriter(errStringWriter)) {
            actual = ArchiveHelper.executeCommand(out, err, args);
        }
        String[] outputLines = outStringWriter.getBuffer().toString().trim().split(System.lineSeparator());

    }
}
