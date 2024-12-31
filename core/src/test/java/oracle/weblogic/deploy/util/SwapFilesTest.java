/*
 * Copyright (c) 2017, 2023, Oracle Corporation and/or its affiliates.  All rights reserved.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.util;

import java.io.File;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.security.MessageDigest;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;


public class SwapFilesTest {
    private static final String UNIT_TEST_TARGET_DIR = "target" + File.separator + "unit-tests";
    private static final String SOURCE_APP_FILE = "src/test/resources/my-app.war";
    private static final String TARGET_APP_ARCHIVE_LOCATION = "wlsdeploy/applications/my-app.war";
    private static final String TARGET_APP_FILE = UNIT_TEST_TARGET_DIR + "/" + TARGET_APP_ARCHIVE_LOCATION;

    private WLSDeployArchive archive;

    @BeforeEach
    void init() {
        File folder = new File(UNIT_TEST_TARGET_DIR);
        File archiveFile = new File(folder, "swapFileTests.zip");

        if ( !folder.exists() ) {
            assertTrue(folder.mkdirs(), "Could not create directory " + folder.getPath());
        }
        archive = new WLSDeployArchive( archiveFile.getAbsolutePath() );
    }

    @Test
    void updateApp() throws Exception {
        File unitTestDir = new File(UNIT_TEST_TARGET_DIR);

        archive.removeAllBinaries();
        File sourceApp = new File(SOURCE_APP_FILE);
        archive.addApplication(SOURCE_APP_FILE);
        archive.extractFileFromZip(TARGET_APP_ARCHIVE_LOCATION, unitTestDir);
        File targetApp = new File(TARGET_APP_FILE);

        assertTrue(targetApp.exists(), "Target app file does not exist");
        String sourceHash = getMD5Hash(sourceApp);
        String targetHash = getMD5Hash(targetApp);
        assertEquals(sourceHash, targetHash, "source and target apps are different");
        archive.close();
    }

    private String getMD5Hash(File f) throws Exception {
        byte[] b = Files.readAllBytes(Paths.get(f.getAbsolutePath()));
        byte[] hash = MessageDigest.getInstance("MD5").digest(b);
        return JaxbDatatypeConverter.printHexBinary(hash);
    }
}
