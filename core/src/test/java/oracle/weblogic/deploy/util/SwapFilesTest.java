/*
 * Copyright (c) 2017, 2019, Oracle and/or its affiliates. All rights reserved.
 * Licensed under the Universal Permissive License v 1.0 as shown at http://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.util;

import java.io.File;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.security.MessageDigest;

import javax.xml.bind.DatatypeConverter;

import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;


public class SwapFilesTest {
    private static final String UNIT_TEST_TARGET_DIR = "target" + File.separator + "unit-tests";
    private static final String SOURCE_MODEL_FILE = "src/test/resources/simple-model.yaml";
    private static final String SOURCE_APP_FILE = "src/test/resources/my-app.war";
    private static final String TARGET_MODEL_FILE = UNIT_TEST_TARGET_DIR + "/model/simple-model.yaml";
    private static final String TARGET_APP_ARCHIVE_LOCATION = "wlsdeploy/applications/my-app.war";
    private static final String TARGET_APP_FILE = UNIT_TEST_TARGET_DIR + "/" + TARGET_APP_ARCHIVE_LOCATION;

    private WLSDeployArchive archive;

    @Before
    public void init() throws Exception {
        File folder = new File(UNIT_TEST_TARGET_DIR);
        File archiveFile = new File(folder, "swapFileTests.zip");

        if ( !folder.exists() ) {
            Assert.assertTrue("Could not create directory " + folder.getPath(), folder.mkdirs());
        }
        archive = new WLSDeployArchive( archiveFile.getAbsolutePath() );
    }

    @Test
    public void updateTwoThings() throws Exception {
        File sourceModel = new File(SOURCE_MODEL_FILE);
        archive.addModel(sourceModel);

        File unitTestDir = new File(UNIT_TEST_TARGET_DIR);
        archive.extractModel(unitTestDir);
        File targetModel = new File(TARGET_MODEL_FILE);

        Assert.assertTrue("Target model file does not exist", targetModel.exists());
        String sourceHash = getMD5Hash(sourceModel);
        String targetHash = getMD5Hash(targetModel);
        Assert.assertEquals("source and target models are different", sourceHash, targetHash);

        archive.removeAllBinaries();
        File sourceApp = new File(SOURCE_APP_FILE);
        archive.addApplication(sourceApp);
        archive.extractFileFromZip(TARGET_APP_ARCHIVE_LOCATION, unitTestDir);
        File targetApp = new File(TARGET_APP_FILE);

        Assert.assertTrue("Target app file does not exist", targetApp.exists());
        sourceHash = getMD5Hash(sourceApp);
        targetHash = getMD5Hash(targetApp);
        Assert.assertEquals("source and target apps are different", sourceHash, targetHash);
        archive.close();
    }

    @Test
    public void updateModel() throws Exception {
        File sourceModel = new File(SOURCE_MODEL_FILE);
        archive.addModel(sourceModel);

        File unitTestDir = new File(UNIT_TEST_TARGET_DIR);
        archive.extractModel(unitTestDir);
        File targetModel = new File(TARGET_MODEL_FILE);

        Assert.assertTrue("Target model file does not exist", targetModel.exists());
        String sourceHash = getMD5Hash(sourceModel);
        String targetHash = getMD5Hash(targetModel);
        Assert.assertEquals("source and target models are different", sourceHash, targetHash);
        archive.close();
    }

    @Test
    public void updateApp() throws Exception {
        File unitTestDir = new File(UNIT_TEST_TARGET_DIR);

        archive.removeAllBinaries();
        File sourceApp = new File(SOURCE_APP_FILE);
        archive.addApplication(sourceApp);
        archive.extractFileFromZip(TARGET_APP_ARCHIVE_LOCATION, unitTestDir);
        File targetApp = new File(TARGET_APP_FILE);

        Assert.assertTrue("Target app file does not exist", targetApp.exists());
        String sourceHash = getMD5Hash(sourceApp);
        String targetHash = getMD5Hash(targetApp);
        Assert.assertEquals("source and target apps are different", sourceHash, targetHash);
        archive.close();
    }

    private String getMD5Hash(File f) throws Exception {
        byte[] b = Files.readAllBytes(Paths.get(f.getAbsolutePath()));
        byte[] hash = MessageDigest.getInstance("MD5").digest(b);
        return DatatypeConverter.printHexBinary(hash);
    }
}
