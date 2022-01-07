/*
 * Copyright (c) 2017, 2022, Oracle Corporation and/or its affiliates.  All rights reserved.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
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

import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

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

    @BeforeAll
    static void initialize() throws Exception {
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
    void testNewZipFile() throws Exception {
        testEmptyFile(ZIP_FILE_NEW_FILE);
    }

    @Test
    void testExistingEmptyFile() throws Exception {
        testEmptyFile(ZIP_FILE_EXISTING_EMPTY_FILE);
    }

    @Test
    void testExistingFile() throws Exception {
        File f = new File(UNIT_TEST_TARGET_DIR + File.separator + ZIP_FILE_EXISTING_FILE);
        assertTrue(f.exists(), "Test setup failed to copy file " + f.getAbsolutePath());
        WLSDeployZipFile zf = new WLSDeployZipFile(f);
        assertTrue(f.exists(), "Creating WLSDeployZiFile deleted file " + f.getAbsolutePath());
        assertNotNull(zf, "Expected a valid WLSDeployZipFile object");
        assertTrue(zf.getFileName().endsWith(ZIP_FILE_EXISTING_FILE), "Unexpected zip file name returned");
        assertTrue(f.exists(), "WLSDeployZiFile.getFileName() deleted file " + f.getAbsolutePath());

        InputStream stream = zf.getZipEntry(ZIP_FILE_EXISTING_FILE_KEYS[1]);
        assertTrue(f.exists(), "WLSDeployZiFile.getZipEntry() deleted file " + f.getAbsolutePath());
        assertNotNull(stream, "Expected a non-null InputStream");
        long bytesRead = readInputStream(stream);
        stream.close();
        assertEquals(ZIP_FILE_EXISTING_FILE_SIZE, bytesRead, "unexpected file size: " + bytesRead);
        zf.close();

        Map<String, InputStream> zipEntries = zf.getZipEntries();
        assertEquals(ZIP_FILE_EXISTING_FILE_KEYS.length, zipEntries.size(), "Unexpected number of entries");
        Iterator<String> keys = zipEntries.keySet().iterator();
        while (keys.hasNext()) {
            String key = keys.next();
            assertTrue(key.contains(ZIP_FILE_EXISTING_FILE_KEYS[0]), "unexpected key: " + key);
            InputStream s = zipEntries.get(key);
            assertNotNull(s, "unexpected null stream returned from zip file");
            if (key.equals(ZIP_FILE_EXISTING_FILE_KEYS[1])) {
                bytesRead = readInputStream(s);
                stream.close();
                assertEquals(ZIP_FILE_EXISTING_FILE_SIZE, bytesRead, "unexpected file size: " + bytesRead);
            } else {
                s.close();
            }
        }
        zf.close();
    }

    @Test
    void testModelFileRemove() throws Exception {
        File f = new File(UNIT_TEST_TARGET_DIR + File.separator + ZIP_FILE_EXISTING_MODEL_FILE);
        WLSDeployZipFile zf = new WLSDeployZipFile(f);
        assertNotNull(zf, "Expected a valid WLSDeployZipFile object");
        assertTrue(zf.getFileName().endsWith(ZIP_FILE_EXISTING_MODEL_FILE), "Unexpected zip file name returned");

        boolean removed = zf.removeZipEntry("foobar");
        assertFalse(removed, "expected no entry to be removed");
        removed = zf.removeZipEntry(ZIP_FILE_MODEL_ENTRY_TO_REMOVE);
        assertTrue(removed, "expected to remove entry");
        InputStream stream = zf.getZipEntry(ZIP_FILE_MODEL_ENTRY_TO_REMOVE);
        assertNull(stream, "expected removed entry to return null InputStream");
        removed = zf.removeZipEntries(ZIP_FILE_MODEL_DIR_TO_REMOVE);
        assertTrue(removed, "expected to remove entries");
        Map<String, InputStream> map = zf.getZipEntries(ZIP_FILE_MODEL_DIR_TO_REMOVE);
        assertNotNull(map, "Expected a non-null map object to be returned");
        assertEquals(0, map.size(), "expected no entries to be returned");
        zf.close();  // closes the zip file and thus, closes all of the returned InputStreams
    }

    @Test
    void testModelFileRemoveEntries() throws Exception {
        File f = new File(UNIT_TEST_TARGET_DIR + File.separator + ZIP_FILE_SIMPLE_APPS_MODEL_FILE);
        WLSDeployZipFile zf = new WLSDeployZipFile(f);
        assertNotNull(zf, "Expected a valid WLSDeployZipFile object");
        assertTrue(            zf.getFileName().endsWith(ZIP_FILE_SIMPLE_APPS_MODEL_FILE), "Unexpected zip file name returned");

        boolean removed = zf.removeZipEntries("foobar");
        assertFalse(removed, "expected no entry to be removed");
        removed = zf.removeZipEntries(ZIP_FILE_MODEL_DIR_TO_REMOVE);
        assertTrue(removed, "expected to remove entries");
        Map<String, InputStream> map = zf.getZipEntries(ZIP_FILE_MODEL_DIR_TO_REMOVE);
        assertEquals(0, map.size(), "expected no entries to be returned");
        zf.close();
    }

    @Test
    void testGetEntries() throws Exception {
        File f = new File(UNIT_TEST_TARGET_DIR + File.separator + ZIP_FILE_SIMPLE_APPS_MODEL_FILE2);
        WLSDeployZipFile zf = new WLSDeployZipFile(f);
        assertNotNull(zf, "Expected a valid WLSDeployZipFile object");
        assertTrue(            zf.getFileName().endsWith(ZIP_FILE_SIMPLE_APPS_MODEL_FILE2), "Unexpected zip file name returned");

        Map<String, InputStream> map = zf.getZipEntries("model/");
        assertEquals(2, map.size(), "expected 2 entries to be returned");
        List<String> expectedList = Arrays.asList(ZIP_FILE_SIMPLE_APPS_MODEL_FILE2_ENTRIES);
        iterateOverMap(map, expectedList);

        map = zf.getZipEntries("wlsdeploy/applications");
        assertEquals(2, map.size(), "expected 2 entries to be returned");
        expectedList = Arrays.asList(ZIP_FILE_SIMPLE_APPS_MODEL_FILE2_APSS_ENTRIES);
        iterateOverMap(map, expectedList);
        zf.close();
    }

    @Test
    public void testAddEntry() throws Exception {
        File f = new File(UNIT_TEST_TARGET_DIR + File.separator + ZIP_FILE_SIMPLE_APPS_MODEL_FILE3);
        WLSDeployZipFile zf = new WLSDeployZipFile(f);
        assertNotNull(zf, "Expected a valid WLSDeployZipFile object");
        assertTrue(            zf.getFileName().endsWith(ZIP_FILE_SIMPLE_APPS_MODEL_FILE3), "Unexpected zip file name returned");

        File logPropertiesFile = new File(LOG_PROPERTIES_SOURCE_LOCATION);
        FileInputStream inputStream = new FileInputStream(logPropertiesFile);
        boolean added = zf.addZipEntry("model/logging/log.properties", inputStream);
        assertTrue(added, "expected entry to be added");
        Map<String, InputStream> map = zf.getZipEntries("model/logging");
        assertNotNull(map, "expected map to be returned");
        assertEquals(1, map.size(), "expected 1 entry to be returned");
        InputStream stream = map.get("model/logging/log.properties");
        assertNotNull(stream, "expected non-null InputStream to be returned");
        int available = stream.available();
        assertTrue(available > 0, "expected log.properties to have more than 0 bytes available");
        zf.close();
    }

    @Test
    void testReallyMatches() {
        File f = new File(UNIT_TEST_TARGET_DIR + File.separator + ZIP_FILE_EXISTING_EMPTY_FILE);
        WLSDeployZipFile zf = new WLSDeployZipFile(f);

        boolean result = zf.entryReallyMatches(REALLY_MATCHES_NORMAL_ENTRY1, REALLY_MATCHES_NORMAL_BASENAME,
            REALLY_MATCHES_NORMAL_EXTENSION);
        assertTrue(result, "expected match");
        result = zf.entryReallyMatches(REALLY_MATCHES_NORMAL_ENTRY2, REALLY_MATCHES_NORMAL_BASENAME,
            REALLY_MATCHES_NORMAL_EXTENSION);
        assertTrue(result, "expected match");

        result = zf.entryReallyMatches(REALLY_MATCHES_NORMAL_ENTRY2, REALLY_MATCHES_NORMAL_BASENAME,
            REALLY_MATCHES_WRONG_EXTENSION);
        assertFalse(result, "expected no match");
        result = zf.entryReallyMatches(REALLY_MATCHES_NORMAL_ENTRY2, REALLY_MATCHES_NORMAL_BASENAME, "");
        assertFalse(result, "expected no match");
        result = zf.entryReallyMatches(REALLY_MATCHES_NORMAL_ENTRY2, REALLY_MATCHES_NORMAL_BASENAME, null);
        assertFalse(result, "expected no match");

        result = zf.entryReallyMatches(REALLY_MATCHES_NOMATCH_ENTRY1, REALLY_MATCHES_NORMAL_BASENAME,
            REALLY_MATCHES_NORMAL_EXTENSION);
        assertFalse(result, "expected no match");
        result = zf.entryReallyMatches(REALLY_MATCHES_NOMATCH_ENTRY2, REALLY_MATCHES_NORMAL_BASENAME,
            REALLY_MATCHES_NORMAL_EXTENSION);
        assertFalse(result, "expected no match");
        result = zf.entryReallyMatches(REALLY_MATCHES_NOMATCH_ENTRY3, REALLY_MATCHES_NORMAL_BASENAME,
            REALLY_MATCHES_NORMAL_EXTENSION);
        assertFalse(result, "expected no match");
        result = zf.entryReallyMatches(REALLY_MATCHES_NOMATCH_ENTRY4, REALLY_MATCHES_NORMAL_BASENAME,
            REALLY_MATCHES_NORMAL_EXTENSION);
        assertFalse(result, "expected no match");
        result = zf.entryReallyMatches(REALLY_MATCHES_NOMATCH_ENTRY5, REALLY_MATCHES_NORMAL_BASENAME,
            REALLY_MATCHES_NORMAL_EXTENSION);
        assertFalse(result, "expected no match");
        result = zf.entryReallyMatches(REALLY_MATCHES_NOMATCH_ENTRY6, REALLY_MATCHES_NORMAL_BASENAME,
            REALLY_MATCHES_NORMAL_EXTENSION);
        assertFalse(result, "expected no match");

        result = zf.entryReallyMatches(REALLY_MATCHES_DIR_ENTRY1, REALLY_MATCHES_NORMAL_BASENAME, "");
        assertTrue(result, "expected match");
        result = zf.entryReallyMatches(REALLY_MATCHES_DIR_ENTRY2, REALLY_MATCHES_NORMAL_BASENAME, "");
        assertTrue(result, "expected match");
        result = zf.entryReallyMatches(REALLY_MATCHES_DIR_ENTRY3, REALLY_MATCHES_NORMAL_BASENAME, "");
        assertTrue(result, "expected match");
        result = zf.entryReallyMatches(REALLY_MATCHES_DIR_ENTRY4, REALLY_MATCHES_NORMAL_BASENAME, "");
        assertTrue(result, "expected match");

        result = zf.entryReallyMatches(REALLY_MATCHES_BADDIR_ENTRY1, REALLY_MATCHES_NORMAL_BASENAME, "");
        assertFalse(result, "expected no match");
        result = zf.entryReallyMatches(REALLY_MATCHES_BADDIR_ENTRY2, REALLY_MATCHES_NORMAL_BASENAME, "");
        assertFalse(result, "expected no match");
        result = zf.entryReallyMatches(REALLY_MATCHES_BADDIR_ENTRY3, REALLY_MATCHES_NORMAL_BASENAME, "");
        assertFalse(result, "expected no match");
        result = zf.entryReallyMatches(REALLY_MATCHES_BADDIR_ENTRY4, REALLY_MATCHES_NORMAL_BASENAME, "");
        assertFalse(result, "expected no match");
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
        assertNotNull(zf, "Expected a valid WLSDeployZipFile object");
        assertTrue(zf.getFileName().endsWith(name), "Unexpected zip file name returned");
        InputStream stream = zf.getZipEntry(ZIP_FILE_EXISTING_FILE_KEYS[1]);
        assertNull(stream, "Expected a null InputStream");
        zf.close();
    }

    private void iterateOverMap(Map<String, InputStream> map, List<String> expectedList) throws Exception {
        Iterator<String> keysIterator = map.keySet().iterator();
        while (keysIterator.hasNext()) {
            String key = keysIterator.next();
            assertTrue(expectedList.contains(key), "excepted key to be in expected key list");
            InputStream stream = map.get(key);
            assertNotNull(stream, "Expected non-null InputStream");
            int available = stream.available();
            if (key.endsWith("/")) {
                assertEquals(0, available, "expected directory entry to have 0 available bytes");
            } else {
                assertTrue(available > 0, "expected file entries to have more than 0 available bytes");
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
    }
}
