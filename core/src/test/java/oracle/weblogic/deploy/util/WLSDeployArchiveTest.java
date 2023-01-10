/*
 * Copyright (c) 2017, 2023, Oracle Corporation and/or its affiliates.  All rights reserved.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.util;

import java.io.File;
import java.util.Arrays;
import java.util.List;
import java.util.logging.Level;

import oracle.weblogic.deploy.logging.PlatformLogger;
import oracle.weblogic.deploy.logging.WLSDeployLogFactory;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;

import static oracle.weblogic.deploy.util.WLSDeployArchive.DEFAULT_RCU_WALLET_PATH;
import static oracle.weblogic.deploy.util.WLSDeployArchive.DEFAULT_RCU_WALLET_NAME;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.junit.jupiter.api.Assertions.fail;

public class WLSDeployArchiveTest {

    private static final String APPS_MODEL = "src/test/resources/simple-model.yaml";
    private static final String APPS_ARCHIVE_FILE_NAME = "target/unit-tests/appsArchive.zip";
    private static final String APP1_TO_ADD = "src/test/resources/my-app.war";
    private static final String APP2_TO_ADD = "src/test/resources/my-other-app.war";
    private static final String APP1_ENTRY_NAME1 = "wlsdeploy/applications/my-app.war";
    private static final String APP1_ENTRY_NAME2 = "wlsdeploy/applications/my-app(1).war";
    private static final String APP1_ENTRY_NAME3 = "wlsdeploy/applications/my-app(2).war";
    private static final String APP1_ENTRY_NAME4 = "wlsdeploy/applications/my-app(3).war";
    private static final String APP2_ENTRY_NAME1 = "wlsdeploy/applications/my-other-app.war";
    private static final String APP2_ENTRY_NAME2 = "wlsdeploy/applications/my-other-app(1).war";
    private static final String APP2_ENTRY_NAME3 = "wlsdeploy/applications/my-other-app(2).war";
    private static final String INVALID_APP_ENTRY_NAME = "wlsdeploy/applications/does-not-exist.war";
    private static final String APP_DIR_TO_ADD = "src/test/resources/my-app/";
    private static final String APP_DIR_ENTRY_NAME = "wlsdeploy/applications/my-app/";
    private static final String INVALID_DIR_ENTRY_NAME = "wlsdeploy/applications/does-not-exist/";

    private static final String ZIP_FILE_EXISTING_EMPTY_FILE = "my-empty-zip.zip";
    private static final String ZIP_FILE_EXISTING_BINARIES_FILE = "DiscoveredDemoDomain.zip";
    private static final String EMPTY_MODEL_ZIP_TARGET_NAME = WLSDeployZipFileTest.UNIT_TEST_TARGET_DIR +
        '/' + ZIP_FILE_EXISTING_EMPTY_FILE;
    private static final String BINARIES_MODEL_ZIP_TARGET_NAME = WLSDeployZipFileTest.UNIT_TEST_TARGET_DIR +
        '/' + ZIP_FILE_EXISTING_BINARIES_FILE;

    private static final String RCU_EMPTY_WALLET_ARCHIVE = "src/test/resources/rcu-empty-wallet-archive.zip";
    private static final String RCU_EXPANDED_WALLET_ARCHIVE = "src/test/resources/rcu-expanded-wallet-archive.zip";
    private static final String RCU_ZIPPED_WALLET_ARCHIVE = "src/test/resources/rcu-zipped-wallet-archive.zip";

    private static final String ATP_DEPRECATED_EMPTY_ARCHIVE = "src/test/resources/atp-deprecated-empty-archive.zip";
    private static final String ATP_DEPRECATED_EXPANDED_ARCHIVE =
        "src/test/resources/atp-deprecated-expanded-archive.zip";
    private static final String ATP_DEPRECATED_ZIPPED_ARCHIVE = "src/test/resources/atp-deprecated-zipped-archive.zip";

    private static final List<String> DB_WALLET_EXPECTED_CONTENT = Arrays.asList(
        DEFAULT_RCU_WALLET_PATH + "/cwallet.sso",
        DEFAULT_RCU_WALLET_PATH + "/ewallet.p12",
        DEFAULT_RCU_WALLET_PATH + "/ewallet.pem",
        DEFAULT_RCU_WALLET_PATH + "/keystore.jks",
        DEFAULT_RCU_WALLET_PATH + "/ojdbc.properties",
        DEFAULT_RCU_WALLET_PATH + "/README",
        DEFAULT_RCU_WALLET_PATH + "/sqlnet.ora",
        DEFAULT_RCU_WALLET_PATH + "/tnsnames.ora",
        DEFAULT_RCU_WALLET_PATH + "/truststore.jks"
    );

    @BeforeAll
    static void setup() throws Exception {
        File unitTestDir = new File(WLSDeployZipFileTest.UNIT_TEST_TARGET_DIR).getCanonicalFile();
        unitTestDir.mkdirs();

        File appsArchiveFile = new File(APPS_ARCHIVE_FILE_NAME).getCanonicalFile();
        if (appsArchiveFile.exists()) {
            appsArchiveFile.delete();
        }

        PlatformLogger logger = WLSDeployLogFactory.getLogger("wlsdeploy.archive");
        logger.setLevel(Level.OFF);
    }

    @Test
    void testAddMultipleAppsWithSameNameGivesUniqueNames() throws Exception {
        WLSDeployArchive archive = new WLSDeployArchive(APPS_ARCHIVE_FILE_NAME);
        assertNotNull(archive, "expected archive object to not be null");
        String appName = archive.addApplication(APP1_TO_ADD);
        assertEquals(APP1_ENTRY_NAME1, appName, "unexpected app name: " + appName);
        appName = archive.addApplication(APP1_TO_ADD);
        assertEquals(APP1_ENTRY_NAME2, appName, "unexpected app name: " + appName);
        appName = archive.addApplication(APP1_TO_ADD);
        assertEquals(APP1_ENTRY_NAME3, appName, "unexpected app name: " + appName);
        appName = archive.addApplication(APP1_TO_ADD);
        assertEquals(APP1_ENTRY_NAME4, appName, "unexpected app name: " + appName);
        appName = archive.addApplication(APP2_TO_ADD);
        assertEquals(APP2_ENTRY_NAME1, appName, "unexpected app name: " + appName);
        appName = archive.addApplication(APP2_TO_ADD);
        assertEquals(APP2_ENTRY_NAME2, appName, "unexpected app name: " + appName);
        appName = archive.addApplication(APP2_TO_ADD);
        assertEquals(APP2_ENTRY_NAME3, appName, "unexpected app name: " + appName);
        archive.close();
    }

    @Test
    void testAddDirectory() throws Exception {
        WLSDeployArchive archive = new WLSDeployArchive(APPS_ARCHIVE_FILE_NAME);
        String appName = archive.addApplication(APP_DIR_TO_ADD);
        assertEquals(APP_DIR_ENTRY_NAME, appName, "unexpected app name: " + appName);
        archive.close();
    }

    @Test
    void testIsAFile() throws Exception {
        WLSDeployArchive archive = new WLSDeployArchive(APPS_ARCHIVE_FILE_NAME);
        archive.addApplication(APP1_TO_ADD);
        assertTrue(archive.containsFile(APP1_ENTRY_NAME1), "File not found in archive: " + APP1_ENTRY_NAME1);
        assertTrue(archive.containsFileOrPath(APP1_ENTRY_NAME1), "File not found in archive: " + APP1_ENTRY_NAME1);
        assertFalse(archive.containsFile(APP_DIR_ENTRY_NAME), "Is not a File");
        assertFalse(archive.containsFileOrPath(INVALID_APP_ENTRY_NAME), "File should not exist");
        archive.close();
    }

    @Test
    void testIsAPath() throws Exception {
        WLSDeployArchive archive = new WLSDeployArchive(APPS_ARCHIVE_FILE_NAME);
        archive.addApplication(APP_DIR_TO_ADD);
        assertTrue(archive.containsPath(APP_DIR_ENTRY_NAME), "Path not found in archive: " + APP_DIR_ENTRY_NAME);
        assertTrue(                archive.containsFileOrPath(APP_DIR_ENTRY_NAME), "Path not found in archive: " + APP_DIR_ENTRY_NAME);
        assertFalse(archive.containsPath(APP1_ENTRY_NAME1), "Is not a Path");
        assertFalse(archive.containsFileOrPath(INVALID_DIR_ENTRY_NAME), "Path should not exist");
    }

    @Test
    void testClearAllBinariesWithEmptyZip() throws Exception {
        WLSDeployZipFileTest.copyFile(ZIP_FILE_EXISTING_BINARIES_FILE);
        WLSDeployArchive archive = new WLSDeployArchive(BINARIES_MODEL_ZIP_TARGET_NAME);
        archive.removeAllBinaries();
        File archiveFile = new File(BINARIES_MODEL_ZIP_TARGET_NAME);
        assertTrue(archiveFile.exists(), "expected archive file to exist");
        assertFalse(archiveFile.isDirectory(), "expected archive file not to be a directory");
        assertNotNull(archive, "expected archive object to not be null");
        String appName = archive.addApplication(APP1_TO_ADD);
        assertFalse(StringUtils.isEmpty(appName), "expected appName to be not empty");
        archive.close();
    }

    @Test
    void testDatabaseZippedWalletExtract() throws Exception {
        WLSDeployArchive archive = new WLSDeployArchive(RCU_ZIPPED_WALLET_ARCHIVE);
        File domainHome = new File("target/unit-tests/rcu-zipped");
        if (!domainHome.exists() && !domainHome.mkdirs()) {
            fail("Failed to create test domain home directory " + domainHome.getAbsolutePath());
        }

        String path = archive.extractDatabaseWallet(domainHome, DEFAULT_RCU_WALLET_NAME);

        File rcuWalletDir = new File(domainHome, DEFAULT_RCU_WALLET_PATH).getCanonicalFile();
        assertEquals(rcuWalletDir.getAbsolutePath(), path, "expected extractDatabaseWallet to return correct path");
        assertTrue(rcuWalletDir.exists(), "expected " + DEFAULT_RCU_WALLET_NAME + " directory to exist");
        assertTrue(rcuWalletDir.isDirectory(), "expected " + DEFAULT_RCU_WALLET_NAME + " to be a directory");

        for (String walletExpectedFile : DB_WALLET_EXPECTED_CONTENT) {
            File walletFile = new File(domainHome, walletExpectedFile);
            assertTrue(walletFile.exists(), "expected " + walletExpectedFile + " to exist");
        }
    }

    @Test
    void testDatabaseExpandedWalletExtract() throws Exception {
        WLSDeployArchive archive = new WLSDeployArchive(RCU_EXPANDED_WALLET_ARCHIVE);
        File domainHome = new File("target/unit-tests/rcu-unzipped");
        if (!domainHome.exists() && !domainHome.mkdirs()) {
            fail("Failed to create test domain home directory " + domainHome.getAbsolutePath());
        }

        String path = archive.extractDatabaseWallet(domainHome, DEFAULT_RCU_WALLET_NAME);

        File rcuWalletDir = new File(domainHome, DEFAULT_RCU_WALLET_PATH).getCanonicalFile();
        assertEquals(rcuWalletDir.getAbsolutePath(), path, "expected extractATPWallet to return correct path");
        assertTrue(rcuWalletDir.exists(), "expected " + DEFAULT_RCU_WALLET_PATH + " directory to exist");
        assertTrue(rcuWalletDir.isDirectory(), "expected " + DEFAULT_RCU_WALLET_PATH + " to be a directory");

        for (String walletExpectedFile : DB_WALLET_EXPECTED_CONTENT) {
            File walletFile = new File(domainHome, walletExpectedFile);
            assertTrue(walletFile.exists(), "expected " + walletExpectedFile + " to exist");
        }
    }

    @Test
    void testDatabaseEmptyWalletExtract() throws Exception {
        WLSDeployArchive archive = new WLSDeployArchive(RCU_EMPTY_WALLET_ARCHIVE);
        File domainHome = new File("target/unit-tests/rcu-empty");
        if (!domainHome.exists() && !domainHome.mkdirs()) {
            fail("Failed to create test domain home directory " + domainHome.getAbsolutePath());
        }

        String path = archive.extractDatabaseWallet(domainHome, DEFAULT_RCU_WALLET_NAME);
        assertNull(path, "expected extractDatabaseWallet to return null");
        File rcuWalletDir = new File(domainHome, DEFAULT_RCU_WALLET_PATH).getCanonicalFile();
        assertFalse(rcuWalletDir.exists(), "expected " + DEFAULT_RCU_WALLET_PATH + " directory to not exist");
    }

    @Test
    void testDeprecatedATPZippedWalletExtract() throws Exception {
        WLSDeployArchive archive = new WLSDeployArchive(ATP_DEPRECATED_ZIPPED_ARCHIVE);
        File domainHome = new File("target/unit-tests/deprecated-atp-zipped");
        if (!domainHome.exists() && !domainHome.mkdirs()) {
            fail("Failed to create test domain home directory " + domainHome.getAbsolutePath());
        }

        String path = archive.extractDatabaseWallet(domainHome, DEFAULT_RCU_WALLET_NAME);

        File rcuWalletDir = new File(domainHome, DEFAULT_RCU_WALLET_PATH).getCanonicalFile();
        assertEquals(rcuWalletDir.getAbsolutePath(), path, "expected extractDatabaseWallet to return correct path");
        assertTrue(rcuWalletDir.exists(), "expected " + DEFAULT_RCU_WALLET_PATH + " directory to exist");
        assertTrue(rcuWalletDir.isDirectory(), "expected " + DEFAULT_RCU_WALLET_PATH + " to be a directory");

        for (String walletExpectedFile : DB_WALLET_EXPECTED_CONTENT) {
            File walletFile = new File(domainHome, walletExpectedFile);
            assertTrue(walletFile.exists(), "expected " + walletExpectedFile + " to exist");
        }
    }

    @Test
    void testDeprecatedATPExpandedWalletExtract() throws Exception {
        WLSDeployArchive archive = new WLSDeployArchive(ATP_DEPRECATED_EXPANDED_ARCHIVE);
        File domainHome = new File("target/unit-tests/deprecated-atp-unzipped");
        if (!domainHome.exists() && !domainHome.mkdirs()) {
            fail("Failed to create test domain home directory " + domainHome.getAbsolutePath());
        }

        String path = archive.extractDatabaseWallet(domainHome, DEFAULT_RCU_WALLET_NAME);

        File rcuWalletDir = new File(domainHome, DEFAULT_RCU_WALLET_PATH).getCanonicalFile();
        assertEquals(rcuWalletDir.getAbsolutePath(), path, "expected extractDatabaseWallet to return correct path");
        assertTrue(rcuWalletDir.exists(), "expected " + DEFAULT_RCU_WALLET_PATH + " directory to exist");
        assertTrue(rcuWalletDir.isDirectory(), "expected " + DEFAULT_RCU_WALLET_PATH + " to be a directory");

        for (String walletExpectedFile : DB_WALLET_EXPECTED_CONTENT) {
            File walletFile = new File(domainHome, walletExpectedFile);
            assertTrue(walletFile.exists(), "expected " + walletExpectedFile + " to exist");
        }
    }

    @Test
    void testDeprecatedATPEmptyWalletExtract() throws Exception {
        WLSDeployArchive archive = new WLSDeployArchive(ATP_DEPRECATED_EMPTY_ARCHIVE);
        File domainHome = new File("target/unit-tests/deprecated-atp-empty");
        if (!domainHome.exists() && !domainHome.mkdirs()) {
            fail("Failed to create test domain home directory " + domainHome.getAbsolutePath());
        }

        String path = archive.extractDatabaseWallet(domainHome, DEFAULT_RCU_WALLET_NAME);
        assertNull(path, "expected extractDatabaseWallet to return null");
        File atpWalletDir = new File(domainHome, DEFAULT_RCU_WALLET_PATH).getCanonicalFile();
        assertFalse(atpWalletDir.exists(), "expected " + DEFAULT_RCU_WALLET_PATH + " directory to not exist");
    }
}
