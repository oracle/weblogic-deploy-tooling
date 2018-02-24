/*
 * Copyright (c) 2017, 2018, Oracle and/or its affiliates. All rights reserved.
 * The Universal Permissive License (UPL), Version 1.0
 */
package oracle.weblogic.deploy.util;

import java.io.File;
import java.text.MessageFormat;

import org.junit.Assert;
import org.junit.Test;

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

    @Test
    public void testNormalFile_parseFileName() throws Exception {
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
    public void testHashing() throws Exception {
        File archiveFile = FileUtils.getCanonicalFile(new File(ARCHIVE_FILE_NAME));
        WLSDeployArchive archive = new WLSDeployArchive(archiveFile.getAbsolutePath());
        String archiveHash = archive.getFileHash(APP_PATH);

        File appFile = FileUtils.getCanonicalFile(new File(APP_FILE_NAME));
        String appHash = FileUtils.computeHash(appFile.getAbsolutePath());

        Assert.assertEquals(appHash, archiveHash);
    }


    private void assertMatch(String name, String got, String expected) {
        Assert.assertTrue(MessageFormat.format(FILE_ERR_FORMAT, name, got, expected),
            got.equals(expected));
    }
}
