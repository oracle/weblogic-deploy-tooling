/*
 * Copyright (c) 2017, 2019, Oracle and/or its affiliates. All rights reserved.
 * Licensed under the Universal Permissive License v 1.0 as shown at http://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.util;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.util.Arrays;
import java.util.Iterator;
import java.util.List;
import java.util.Map;

import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;

public class WLSDeployZipFileTest {
    public static final String UNIT_TEST_SOURCE_DIR = "src" + File.separator + "test" + File.separator + "resources";
    public static final String UNIT_TEST_TARGET_DIR = "target" + File.separator + "unit-tests";

    private static final String ZIP_FILE_NEW_FILE = "nonExistentZip.zip";
    private static final String ZIP_FILE_EXISTING_FILE = "my-winzip-zip.zip";
    private static final String ZIP_FILE_EXISTING_EMPTY_FILE = "my-empty-zip.zip";
    private static final String[] ZIP_FILE_EXISTING_FILE_KEYS = { "dir1/", "dir1/domain.xsd" };
    private static final long ZIP_FILE_EXISTING_FILE_SIZE = 911375;

    private static final String ZIP_FILE_EXISTING_MODEL_FILE = "test-windows-archive.zip";
    private static final String ZIP_FILE_MODEL_ENTRY_TO_REMOVE = "model/simple-model.yaml";
    private static final String ZIP_FILE_MODEL_DIR_TO_REMOVE = "model/";

    private static final String ZIP_FILE_SIMPLE_APPS_MODEL_FILE = "SingleAppDomain.zip";

    private static final String ZIP_FILE_SIMPLE_APPS_MODEL_FILE2 = "sample-apps-archive2.zip";
    private static final String[] ZIP_FILE_SIMPLE_APPS_MODEL_FILE2_ENTRIES = new String[] { "model/",
        "model/SingleAppDomain.yaml", "wlsdeploy/", "wlsdeploy/applications/",
        "wlsdeploy/applications/get-listen-address-app.war", "wlsdeploy/applications/simpleear.ear",
        "wlsdeploy/sharedLibraries/", "wlsdeploy/sharedLibraries/jsf-2.0.war" };
    private static final String[] ZIP_FILE_SIMPLE_APPS_MODEL_FILE2_APSS_ENTRIES = new String[] {
       "wlsdeploy/applications/get-listen-address-app.war", "wlsdeploy/applications/simpleear.ear" };

    private static final String ZIP_FILE_SIMPLE_APPS_MODEL_FILE3 = "sample-apps-archive3.zip";
    private static final String LOG_PROPERTIES_SOURCE_LOCATION =
        UNIT_TEST_SOURCE_DIR + File.separator + "log.properties";

    private static final String REALLY_MATCHES_NORMAL_ENTRY1 = "applications/myapp(1).ear";
    private static final String REALLY_MATCHES_NORMAL_ENTRY2 = "applications/myapp(12345).ear";
    private static final String REALLY_MATCHES_NORMAL_BASENAME = "applications/myapp";
    private static final String REALLY_MATCHES_NORMAL_EXTENSION = "ear";
    private static final String REALLY_MATCHES_WRONG_EXTENSION = "war";
    private static final String REALLY_MATCHES_NOMATCH_ENTRY1 = "applications/myapp(1)fred.ear";
    private static final String REALLY_MATCHES_NOMATCH_ENTRY2 = "applications/myapp(1)";
    private static final String REALLY_MATCHES_NOMATCH_ENTRY3 = "applications/myapp(1)/ear";
    private static final String REALLY_MATCHES_NOMATCH_ENTRY4 = "applications/myapp/(1).ear";
    private static final String REALLY_MATCHES_NOMATCH_ENTRY5 = "applications/myapp(12345)fred.ear";
    private static final String REALLY_MATCHES_NOMATCH_ENTRY6 = "applications/myapp(1)/";

    private static final String REALLY_MATCHES_DIR_ENTRY1 = "application/myapp";
    private static final String REALLY_MATCHES_DIR_ENTRY2 = "application/myapp/";
    private static final String REALLY_MATCHES_DIR_ENTRY3 = "application/myapp(123)";
    private static final String REALLY_MATCHES_DIR_ENTRY4 = "application/myapp(123)/";
    private static final String REALLY_MATCHES_BADDIR_ENTRY1 = "application/myapps";
    private static final String REALLY_MATCHES_BADDIR_ENTRY2 = "application/myapps/";
    private static final String REALLY_MATCHES_BADDIR_ENTRY3 = "application/myapp(123)s";
    private static final String REALLY_MATCHES_BADDIR_ENTRY4 = "application/myapp()/";

    @Before
    public void initialize() throws Exception {
        File unitTest = new File(UNIT_TEST_TARGET_DIR);
        unitTest.mkdirs();
        copyFile(ZIP_FILE_EXISTING_FILE);
        copyFile(ZIP_FILE_EXISTING_EMPTY_FILE);
        copyFile(ZIP_FILE_EXISTING_MODEL_FILE);
        copyFile(ZIP_FILE_SIMPLE_APPS_MODEL_FILE);
        copyFile(ZIP_FILE_SIMPLE_APPS_MODEL_FILE, ZIP_FILE_SIMPLE_APPS_MODEL_FILE2);
        copyFile(ZIP_FILE_SIMPLE_APPS_MODEL_FILE, ZIP_FILE_SIMPLE_APPS_MODEL_FILE3);
    }

    @Test
    public void testNewZipFile() throws Exception {
        testEmptyFile(ZIP_FILE_NEW_FILE);
    }

    @Test
    public void testExistingEmptyFile() throws Exception {
        testEmptyFile(ZIP_FILE_EXISTING_EMPTY_FILE);
    }

    @Test
    public void testExistingFile() throws Exception {
        File f = new File(UNIT_TEST_TARGET_DIR + File.separator + ZIP_FILE_EXISTING_FILE);
        Assert.assertTrue("Test setup failed to copy file " + f.getAbsolutePath(), f.exists());
        WLSDeployZipFile zf = new WLSDeployZipFile(f);
        Assert.assertTrue("Creating WLSDeployZiFile deleted file " + f.getAbsolutePath(), f.exists());
        Assert.assertNotNull("Expected a valid WLSDeployZipFile object", zf);
        Assert.assertTrue("Unexpected zip file name returned", zf.getFileName().endsWith(ZIP_FILE_EXISTING_FILE));
        Assert.assertTrue("WLSDeployZiFile.getFileName() deleted file " + f.getAbsolutePath(), f.exists());

        InputStream stream = zf.getZipEntry(ZIP_FILE_EXISTING_FILE_KEYS[1]);
        Assert.assertTrue("WLSDeployZiFile.getZipEntry() deleted file " + f.getAbsolutePath(), f.exists());
        Assert.assertNotNull("Expected a non-null InputStream", stream);
        long bytesRead = readInputStream(stream);
        stream.close();
        Assert.assertEquals("unexpected file size: " + bytesRead, ZIP_FILE_EXISTING_FILE_SIZE, bytesRead);
        zf.close();

        Map<String, InputStream> zipEntries = zf.getZipEntries();
        Assert.assertEquals("Unexpected number of entries", ZIP_FILE_EXISTING_FILE_KEYS.length, zipEntries.size());
        Iterator<String> keys = zipEntries.keySet().iterator();
        while (keys.hasNext()) {
            String key = keys.next();
            Assert.assertTrue("unexpected key: " + key, key.contains(ZIP_FILE_EXISTING_FILE_KEYS[0]));
            InputStream s = zipEntries.get(key);
            Assert.assertNotNull("unexpected null stream returned from zip file", s);
            if (key.equals(ZIP_FILE_EXISTING_FILE_KEYS[1])) {
                bytesRead = readInputStream(s);
                stream.close();
                Assert.assertEquals("unexpected file size: " + bytesRead, ZIP_FILE_EXISTING_FILE_SIZE, bytesRead);
            } else {
                s.close();
            }
        }
        zf.close();
    }

    @Test
    public void testModelFileRemove() throws Exception {
        File f = new File(UNIT_TEST_TARGET_DIR + File.separator + ZIP_FILE_EXISTING_MODEL_FILE);
        WLSDeployZipFile zf = new WLSDeployZipFile(f);
        Assert.assertNotNull("Expected a valid WLSDeployZipFile object", zf);
        Assert.assertTrue("Unexpected zip file name returned", zf.getFileName().endsWith(ZIP_FILE_EXISTING_MODEL_FILE));

        boolean removed = zf.removeZipEntry("foobar");
        Assert.assertFalse("expected no entry to be removed", removed);
        removed = zf.removeZipEntry(ZIP_FILE_MODEL_ENTRY_TO_REMOVE);
        Assert.assertTrue("expected to remove entry", removed);
        InputStream stream = zf.getZipEntry(ZIP_FILE_MODEL_ENTRY_TO_REMOVE);
        Assert.assertNull("expected removed entry to return null InputStream", stream);
        removed = zf.removeZipEntries(ZIP_FILE_MODEL_DIR_TO_REMOVE);
        Assert.assertTrue("expected to remove entries", removed);
        Map<String, InputStream> map = zf.getZipEntries(ZIP_FILE_MODEL_DIR_TO_REMOVE);
        Assert.assertNotNull("Expected a non-null map object to be returned", map);
        Assert.assertEquals("expected no entries to be returned", 0, map.size());
        zf.close();  // closes the zip file and thus, closes all of the returned InputStreams
    }

    @Test
    public void testModelFileRemoveEntries() throws Exception {
        File f = new File(UNIT_TEST_TARGET_DIR + File.separator + ZIP_FILE_SIMPLE_APPS_MODEL_FILE);
        WLSDeployZipFile zf = new WLSDeployZipFile(f);
        Assert.assertNotNull("Expected a valid WLSDeployZipFile object", zf);
        Assert.assertTrue("Unexpected zip file name returned",
            zf.getFileName().endsWith(ZIP_FILE_SIMPLE_APPS_MODEL_FILE));

        boolean removed = zf.removeZipEntries("foobar");
        Assert.assertFalse("expected no entry to be removed", removed);
        removed = zf.removeZipEntries(ZIP_FILE_MODEL_DIR_TO_REMOVE);
        Assert.assertTrue("expected to remove entries", removed);
        Map<String, InputStream> map = zf.getZipEntries(ZIP_FILE_MODEL_DIR_TO_REMOVE);
        Assert.assertEquals("expected no entries to be returned", 0, map.size());
        zf.close();
    }

    @Test
    public void testGetEntries() throws Exception {
        File f = new File(UNIT_TEST_TARGET_DIR + File.separator + ZIP_FILE_SIMPLE_APPS_MODEL_FILE2);
        WLSDeployZipFile zf = new WLSDeployZipFile(f);
        Assert.assertNotNull("Expected a valid WLSDeployZipFile object", zf);
        Assert.assertTrue("Unexpected zip file name returned",
            zf.getFileName().endsWith(ZIP_FILE_SIMPLE_APPS_MODEL_FILE2));

        Map<String, InputStream> map = zf.getZipEntries("model/");
        Assert.assertEquals("expected 2 entries to be returned", 2, map.size());
        List<String> expectedList = Arrays.asList(ZIP_FILE_SIMPLE_APPS_MODEL_FILE2_ENTRIES);
        iterateOverMap(map, expectedList);

        map = zf.getZipEntries("wlsdeploy/applications");
        Assert.assertEquals("expected 2 entries to be returned", 2, map.size());
        expectedList = Arrays.asList(ZIP_FILE_SIMPLE_APPS_MODEL_FILE2_APSS_ENTRIES);
        iterateOverMap(map, expectedList);
        zf.close();
    }

    @Test
    public void testAddEntry() throws Exception {
        File f = new File(UNIT_TEST_TARGET_DIR + File.separator + ZIP_FILE_SIMPLE_APPS_MODEL_FILE3);
        WLSDeployZipFile zf = new WLSDeployZipFile(f);
        Assert.assertNotNull("Expected a valid WLSDeployZipFile object", zf);
        Assert.assertTrue("Unexpected zip file name returned",
            zf.getFileName().endsWith(ZIP_FILE_SIMPLE_APPS_MODEL_FILE3));

        File logPropertiesFile = new File(LOG_PROPERTIES_SOURCE_LOCATION);
        FileInputStream inputStream = new FileInputStream(logPropertiesFile);
        boolean added = zf.addZipEntry("model/logging/log.properties", inputStream);
        Assert.assertTrue("expected entry to be added", added);
        Map<String, InputStream> map = zf.getZipEntries("model/logging");
        Assert.assertNotNull("expected map to be returned", map);
        Assert.assertEquals("expected 1 entry to be returned", 1, map.size());
        InputStream stream = map.get("model/logging/log.properties");
        Assert.assertNotNull("expected non-null InputStream to be returned", stream);
        int available = stream.available();
        Assert.assertTrue("expected log.properties to have more than 0 bytes available", available > 0);
        zf.close();
    }

    @Test
    public void testReallyMatches() throws Exception {
        File f = new File(UNIT_TEST_TARGET_DIR + File.separator + ZIP_FILE_EXISTING_EMPTY_FILE);
        WLSDeployZipFile zf = new WLSDeployZipFile(f);

        boolean result = zf.entryReallyMatches(REALLY_MATCHES_NORMAL_ENTRY1, REALLY_MATCHES_NORMAL_BASENAME,
            REALLY_MATCHES_NORMAL_EXTENSION);
        Assert.assertTrue("expected match", result);
        result = zf.entryReallyMatches(REALLY_MATCHES_NORMAL_ENTRY2, REALLY_MATCHES_NORMAL_BASENAME,
            REALLY_MATCHES_NORMAL_EXTENSION);
        Assert.assertTrue("expected match", result);

        result = zf.entryReallyMatches(REALLY_MATCHES_NORMAL_ENTRY2, REALLY_MATCHES_NORMAL_BASENAME,
            REALLY_MATCHES_WRONG_EXTENSION);
        Assert.assertFalse("expected no match", result);
        result = zf.entryReallyMatches(REALLY_MATCHES_NORMAL_ENTRY2, REALLY_MATCHES_NORMAL_BASENAME, "");
        Assert.assertFalse("expected no match", result);
        result = zf.entryReallyMatches(REALLY_MATCHES_NORMAL_ENTRY2, REALLY_MATCHES_NORMAL_BASENAME, null);
        Assert.assertFalse("expected no match", result);

        result = zf.entryReallyMatches(REALLY_MATCHES_NOMATCH_ENTRY1, REALLY_MATCHES_NORMAL_BASENAME,
            REALLY_MATCHES_NORMAL_EXTENSION);
        Assert.assertFalse("expected no match", result);
        result = zf.entryReallyMatches(REALLY_MATCHES_NOMATCH_ENTRY2, REALLY_MATCHES_NORMAL_BASENAME,
            REALLY_MATCHES_NORMAL_EXTENSION);
        Assert.assertFalse("expected no match", result);
        result = zf.entryReallyMatches(REALLY_MATCHES_NOMATCH_ENTRY3, REALLY_MATCHES_NORMAL_BASENAME,
            REALLY_MATCHES_NORMAL_EXTENSION);
        Assert.assertFalse("expected no match", result);
        result = zf.entryReallyMatches(REALLY_MATCHES_NOMATCH_ENTRY4, REALLY_MATCHES_NORMAL_BASENAME,
            REALLY_MATCHES_NORMAL_EXTENSION);
        Assert.assertFalse("expected no match", result);
        result = zf.entryReallyMatches(REALLY_MATCHES_NOMATCH_ENTRY5, REALLY_MATCHES_NORMAL_BASENAME,
            REALLY_MATCHES_NORMAL_EXTENSION);
        Assert.assertFalse("expected no match", result);
        result = zf.entryReallyMatches(REALLY_MATCHES_NOMATCH_ENTRY6, REALLY_MATCHES_NORMAL_BASENAME,
            REALLY_MATCHES_NORMAL_EXTENSION);
        Assert.assertFalse("expected no match", result);

        result = zf.entryReallyMatches(REALLY_MATCHES_DIR_ENTRY1, REALLY_MATCHES_NORMAL_BASENAME, "");
        Assert.assertTrue("expected match", result);
        result = zf.entryReallyMatches(REALLY_MATCHES_DIR_ENTRY2, REALLY_MATCHES_NORMAL_BASENAME, "");
        Assert.assertTrue("expected match", result);
        result = zf.entryReallyMatches(REALLY_MATCHES_DIR_ENTRY3, REALLY_MATCHES_NORMAL_BASENAME, "");
        Assert.assertTrue("expected match", result);
        result = zf.entryReallyMatches(REALLY_MATCHES_DIR_ENTRY4, REALLY_MATCHES_NORMAL_BASENAME, "");
        Assert.assertTrue("expected match", result);

        result = zf.entryReallyMatches(REALLY_MATCHES_BADDIR_ENTRY1, REALLY_MATCHES_NORMAL_BASENAME, "");
        Assert.assertFalse("expected no match", result);
        result = zf.entryReallyMatches(REALLY_MATCHES_BADDIR_ENTRY2, REALLY_MATCHES_NORMAL_BASENAME, "");
        Assert.assertFalse("expected no match", result);
        result = zf.entryReallyMatches(REALLY_MATCHES_BADDIR_ENTRY3, REALLY_MATCHES_NORMAL_BASENAME, "");
        Assert.assertFalse("expected no match", result);
        result = zf.entryReallyMatches(REALLY_MATCHES_BADDIR_ENTRY4, REALLY_MATCHES_NORMAL_BASENAME, "");
        Assert.assertFalse("expected no match", result);
        zf.close();
    }

    private long readInputStream(InputStream s) throws IOException {
        byte[] readBuffer = new byte[4096];
        long bytesReadTotal = 0;

        while (true) {
            int bytesRead = s.read(readBuffer);
            if (bytesRead >= 0) {
                bytesReadTotal += bytesRead;
            } else {
                break;
            }
        }
        return bytesReadTotal;
    }

    private void testEmptyFile(String name) throws Exception {
        File f = new File(UNIT_TEST_TARGET_DIR + File.separator + name);
        WLSDeployZipFile zf = new WLSDeployZipFile(f);
        Assert.assertNotNull("Expected a valid WLSDeployZipFile object", zf);
        Assert.assertTrue("Unexpected zip file name returned", zf.getFileName().endsWith(name));
        InputStream stream = zf.getZipEntry(ZIP_FILE_EXISTING_FILE_KEYS[1]);
        Assert.assertNull("Expected a null InputStream", stream);
        zf.close();
    }

    private void iterateOverMap(Map<String, InputStream> map, List<String> expectedList) throws Exception {
        Iterator<String> keysIterator = map.keySet().iterator();
        while (keysIterator.hasNext()) {
            String key = keysIterator.next();
            Assert.assertTrue("excepted key to be in expected key list", expectedList.contains(key));
            InputStream stream = map.get(key);
            Assert.assertNotNull("Expected non-null InputStream", stream);
            int available = stream.available();
            if (key.endsWith("/")) {
                Assert.assertEquals("expected directory entry to have 0 available bytes", 0, available);
            } else {
                Assert.assertTrue("expected file entries to have more than 0 available bytes", available > 0);
            }
            stream.close();
        }
    }

    public static void copyFile(String filename) throws IOException {
        copyFile(filename, filename);
    }

    public static void copyFile(String filename, String targetFilename) throws IOException {
        byte[] readBuffer = new byte[4096];

        File source = new File(UNIT_TEST_SOURCE_DIR + File.separator + filename);
        File target = new File(UNIT_TEST_TARGET_DIR + File.separator + targetFilename);
        System.out.println("copying file " + source.getAbsolutePath() + " to " + target.getAbsolutePath());

        FileInputStream fis = new FileInputStream(source);
        FileOutputStream fos = new FileOutputStream(target, false);
        int bytesRead;
        int totalBytesRead = 0;
        while (true) {
            bytesRead = fis.read(readBuffer);
            if (bytesRead >= 0) {
                fos.write(readBuffer, 0, bytesRead);
                totalBytesRead += bytesRead;
            } else {
                break;
            }
        }
        fos.flush();
        fos.close();
        fis.close();
        System.out.println("copied " + totalBytesRead + " bytes from file " + source.getAbsolutePath() +
            " to " + target.getAbsolutePath());
    }
}
