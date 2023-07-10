/*
 * Copyright (c) 2017, 2023, Oracle Corporation and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.util;

import java.io.File;
import java.nio.file.attribute.PosixFilePermission;
import java.text.MessageFormat;
import java.util.Set;

import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

public class FileUtilsTest {
    private static final String FILE_ERR_FORMAT = "Unexpected {0}: got {1}, expected {2}";

    private static final String FILE1 = "../../foo/bar/somefile.zip";
    private static final String FILE1_EXPECTED_NAME = "somefile";
    private static final String FILE1_EXPECTED_EXT = "zip";

    private static final String FILE2 = "/foo/bar/somefile.zip";
    private static final String FILE2_EXPECTED_NAME = "somefile";
    private static final String FILE2_EXPECTED_EXT = "zip";

    private static final String FILE3 = "/somefile.zip";
    private static final String FILE3_EXPECTED_NAME = "somefile";
    private static final String FILE3_EXPECTED_EXT = "zip";

    private static final String FILE4 = "somefile.zip";
    private static final String FILE4_EXPECTED_NAME = "somefile";
    private static final String FILE4_EXPECTED_EXT = "zip";

    private static final String FILE5 = "somefile.z";
    private static final String FILE5_EXPECTED_NAME = "somefile";
    private static final String FILE5_EXPECTED_EXT = "z";

    private static final String FILE6 = ".somefile";
    private static final String FILE6_EXPECTED_NAME = "";
    private static final String FILE6_EXPECTED_EXT = "somefile";

    private static final String FILE7 = ".";
    private static final String FILE7_EXPECTED_NAME = ".";
    private static final String FILE7_EXPECTED_EXT = "";

    private static final String FILE8 = "somefile.";
    private static final String FILE8_EXPECTED_NAME = "somefile";
    private static final String FILE8_EXPECTED_EXT = "";

    private static final String ARCHIVE_FILE_NAME = "src/test/resources/DemoDomain.zip";
    private static final String APP_PATH = "wlsdeploy/applications/simpleear.ear";
    private static final String APP_FILE_NAME = "src/test/resources/simpleear.ear";

    private static final File UNIT_TEST_TARGET_DIR = new File(WLSDeployZipFileTest.UNIT_TEST_TARGET_DIR, "fileutils");
    private static final String WALLET_PATH = "wlsdeploy/wallet.zip";

    @BeforeAll
    static void initialize() throws Exception {
        if(!UNIT_TEST_TARGET_DIR.exists() && !UNIT_TEST_TARGET_DIR.mkdirs()) {
            throw new Exception("Unable to create unit test directory: " + UNIT_TEST_TARGET_DIR);
        }
    }

    @Test
    void testNormalFile_parseFileName() {
        File f = new File(FILE1);
        String[] nameComponents = FileUtils.parseFileName(f);
        assertMatch("filename", nameComponents[0], FILE1_EXPECTED_NAME);
        assertMatch("file extension", nameComponents[1], FILE1_EXPECTED_EXT);

        f = new File(FILE2);
        nameComponents = FileUtils.parseFileName(f);
        assertMatch("filename", nameComponents[0], FILE2_EXPECTED_NAME);
        assertMatch("file extension", nameComponents[1], FILE2_EXPECTED_EXT);

        f = new File(FILE3);
        nameComponents = FileUtils.parseFileName(f);
        assertMatch("filename", nameComponents[0], FILE3_EXPECTED_NAME);
        assertMatch("file extension", nameComponents[1], FILE3_EXPECTED_EXT);

        f = new File(FILE4);
        nameComponents = FileUtils.parseFileName(f);
        assertMatch("filename", nameComponents[0], FILE4_EXPECTED_NAME);
        assertMatch("file extension", nameComponents[1], FILE4_EXPECTED_EXT);

        f = new File(FILE5);
        nameComponents = FileUtils.parseFileName(f);
        assertMatch("filename", nameComponents[0], FILE5_EXPECTED_NAME);
        assertMatch("file extension", nameComponents[1], FILE5_EXPECTED_EXT);

        f = new File(FILE6);
        nameComponents = FileUtils.parseFileName(f);
        assertMatch("filename", nameComponents[0], FILE6_EXPECTED_NAME);
        assertMatch("file extension", nameComponents[1], FILE6_EXPECTED_EXT);

        f = new File(FILE7);
        nameComponents = FileUtils.parseFileName(f);
        assertMatch("filename", nameComponents[0], FILE7_EXPECTED_NAME);
        assertMatch("file extension", nameComponents[1], FILE7_EXPECTED_EXT);

        f = new File(FILE8);
        nameComponents = FileUtils.parseFileName(f);
        assertMatch("filename", nameComponents[0], FILE8_EXPECTED_NAME);
        assertMatch("file extension", nameComponents[1], FILE8_EXPECTED_EXT);
    }

    @Test
    void testHashing() throws Exception {
        File archiveFile = FileUtils.getCanonicalFile(new File(ARCHIVE_FILE_NAME));
        WLSDeployArchive archive = new WLSDeployArchive(archiveFile.getAbsolutePath());
        String archiveHash = archive.getFileHash(APP_PATH);

        File appFile = FileUtils.getCanonicalFile(new File(APP_FILE_NAME));
        String appHash = FileUtils.computeHash(appFile.getAbsolutePath());

        assertEquals(appHash, archiveHash);
    }

    private void assertMatch(String name, String got, String expected) {
        assertEquals(expected, got, MessageFormat.format(FILE_ERR_FORMAT, name, got, expected));
    }

    @Test
    void posixPermissions() {
        Set<PosixFilePermission> perms = FileUtils.getPermissions(0700);
        assertTrue(perms.contains(PosixFilePermission.OWNER_READ));
        assertTrue(perms.contains(PosixFilePermission.OWNER_WRITE));
        assertTrue(perms.contains(PosixFilePermission.OWNER_EXECUTE));

        Set<PosixFilePermission> perms2 = FileUtils.getPermissions(0006);
        assertTrue(perms2.contains(PosixFilePermission.OTHERS_READ));
        assertTrue(perms2.contains(PosixFilePermission.OTHERS_WRITE));
    }

    @Test
    void testIsRemotePathAbsolute_UnixAbsolutePath_ToBeTrue() {
        String path = "/foo/bar";
        boolean actual = FileUtils.isRemotePathAbsolute(path);
        assertTrue(actual, "Excepted " + path + " to be absolute");
    }

    @Test
    void testIsRemotePathAbsolute_UnixRelativePath_ToBeFalse() {
        String path = "foo/bar";
        boolean actual = FileUtils.isRemotePathAbsolute(path);
        assertFalse(actual, "Excepted " + path + " to not be absolute");
    }

    @Test
    void testIsRemotePathAbsolute_WindowsDriveAbsolutePath_ToBeTrue() {
        String path = "c:\\foo\\bar";
        boolean actual = FileUtils.isRemotePathAbsolute(path);
        assertTrue(actual, "Excepted " + path + " to be absolute");
    }

    @Test
    void testIsRemotePathAbsolute_WindowsUNCAbsolutePath_ToBeTrue() {
        String path = "\\\\foo\\bar";
        boolean actual = FileUtils.isRemotePathAbsolute(path);
        assertTrue(actual, "Excepted " + path + " to be absolute");
    }

    @Test
    void testIsRemotePathAbsolute_WindowsRelativePath_ToBeFalse() {
        String path = "\\foo\\bar";
        boolean actual = FileUtils.isRemotePathAbsolute(path);
        assertFalse(actual, "Excepted " + path + " to not be absolute");
    }
}
