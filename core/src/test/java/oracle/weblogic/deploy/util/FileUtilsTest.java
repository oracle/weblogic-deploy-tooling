/*
 * Copyright (c) 2017, 2019, Oracle and/or its affiliates. All rights reserved.
 * Licensed under the Universal Permissive License v 1.0 as shown at http://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.util;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.text.MessageFormat;
import java.util.zip.ZipEntry;
import java.util.zip.ZipOutputStream;

import org.junit.Assert;
import org.junit.Before;
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

    private static final File UNIT_TEST_TARGET_DIR = new File(WLSDeployZipFileTest.UNIT_TEST_TARGET_DIR, "fileutils");
    private static final String WALLET_PATH = "wlsdeploy/wallet.zip";

    @Before
    public void initialize() throws Exception {
        if(!UNIT_TEST_TARGET_DIR.exists() && !UNIT_TEST_TARGET_DIR.mkdirs()) {
            throw new Exception("Unable to create unit test directory: " + UNIT_TEST_TARGET_DIR);
        }
    }

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

    @Test
    /* A wallet zip inside the archive must not contain an entry such as ../info.txt,
       since this creates a file overwrite security vulnerability (zip slip).
     */
    public void testZipVulnerability() throws Exception {
        String extractPath = UNIT_TEST_TARGET_DIR.getPath();

        // an entry with a simple name or path works fine
        File zipFile = buildWalletArchiveZip("info.txt");
        WLSDeployArchive deployArchive = new WLSDeployArchive(zipFile.getPath());
        FileUtils.extractZipFileContent(deployArchive, WALLET_PATH, extractPath);

        // an entry with parent directory notation should throw an exception
        try {
            zipFile = buildWalletArchiveZip("../info.txt");
            deployArchive = new WLSDeployArchive(zipFile.getPath());
            FileUtils.extractZipFileContent(deployArchive, WALLET_PATH, extractPath);
            Assert.fail("Exception not thrown for zip entry outside extract directory");

        } catch(IllegalArgumentException e) {
            // expected behavior
        }
    }

    /* Build an archive zip containing a wallet zip.
       The wallet contains a single entry with the name of the contentName argument.
     */
    private File buildWalletArchiveZip(String contentName) throws Exception {

        // create the wallet zip content
        ByteArrayOutputStream walletBytes = new ByteArrayOutputStream();
        try (ZipOutputStream zipStream = new ZipOutputStream(walletBytes)) {
            ZipEntry zipEntry = new ZipEntry(contentName);
            zipStream.putNextEntry(zipEntry);
            byte[] data = "info".getBytes();
            zipStream.write(data, 0, data.length);
            zipStream.closeEntry();
        }

        File archiveFile = new File(UNIT_TEST_TARGET_DIR, "archive.zip");

        try (ZipOutputStream zipStream = new ZipOutputStream(new FileOutputStream(archiveFile))) {
            ZipEntry zipEntry = new ZipEntry(WALLET_PATH);
            zipStream.putNextEntry(zipEntry);
            zipStream.write(walletBytes.toByteArray());
            zipStream.closeEntry();
        }

        return archiveFile;
    }

    private void assertMatch(String name, String got, String expected) {
        Assert.assertTrue(MessageFormat.format(FILE_ERR_FORMAT, name, got, expected),
            got.equals(expected));
    }
}
