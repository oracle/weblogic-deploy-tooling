/*
 * Copyright (c) 2017, 2022, Oracle Corporation and/or its affiliates.  All rights reserved.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.util;

import java.io.File;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.security.MessageDigest;
import javax.xml.bind.DatatypeConverter;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;


public class SwapFilesTest {
    private static final String UNIT_TEST_TARGET_DIR = "target" + File.separator + "unit-tests";
    private static final String SOURCE_MODEL_FILE = "src/test/resources/simple-model.yaml";
    private static final String SOURCE_APP_FILE = "src/test/resources/my-app.war";
    private static final String TARGET_MODEL_FILE = UNIT_TEST_TARGET_DIR + "/model/simple-model.yaml";
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
    void updateTwoThings() throws Exception {
        File sourceModel = new File(SOURCE_MODEL_FILE);
        archive.addModel(sourceModel);

        File unitTestDir = new File(UNIT_TEST_TARGET_DIR);
        archive.extractModel(unitTestDir);
        File targetModel = new File(TARGET_MODEL_FILE);

        assertTrue(targetModel.exists(), "Target model file does not exist");
        String sourceHash = getMD5Hash(sourceModel);
        String targetHash = getMD5Hash(targetModel);
        assertEquals(sourceHash, targetHash, "source and target models are different");

        archive.removeAllBinaries();
        File sourceApp = new File(SOURCE_APP_FILE);
        archive.addApplication(SOURCE_APP_FILE);
        archive.extractFileFromZip(TARGET_APP_ARCHIVE_LOCATION, unitTestDir);
        File targetApp = new File(TARGET_APP_FILE);

        assertTrue(targetApp.exists(), "Target app file does not exist");
        sourceHash = getMD5Hash(sourceApp);
        targetHash = getMD5Hash(targetApp);
        assertEquals(sourceHash, targetHash, "source and target apps are different");
        archive.close();
    }

    @Test
    void updateModel() throws Exception {
        File sourceModel = new File(SOURCE_MODEL_FILE);
        archive.addModel(sourceModel);

        File unitTestDir = new File(UNIT_TEST_TARGET_DIR);
        archive.extractModel(unitTestDir);
        File targetModel = new File(TARGET_MODEL_FILE);

        assertTrue(targetModel.exists(), "Target model file does not exist");
        String sourceHash = getMD5Hash(sourceModel);
        String targetHash = getMD5Hash(targetModel);
        assertEquals(sourceHash, targetHash, "source and target models are different");
        archive.close();
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
        return DatatypeConverter.printHexBinary(hash);
    }
}
