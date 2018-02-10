/*
 * Copyright (c) 2017, 2018, Oracle and/or its affiliates. All rights reserved.
 * The Universal Permissive License (UPL), Version 1.0
 */
package oracle.weblogic.deploy.util;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;

import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;

import static oracle.weblogic.deploy.util.WLSDeployArchive.ARCHIVE_MODEL_TARGET_DIR;
import static oracle.weblogic.deploy.util.WLSDeployArchive.ZIP_SEP;

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

    private static final String ZIP_FILE_EXISTING_EMPTY_FILE = "my-empty-zip.zip";
    private static final String ZIP_FILE_EXISTING_BINARIES_FILE = "DiscoveredDemoDomain.zip";
    private static final String EMPTY_MODEL_ZIP_TARGET_NAME = WLSDeployZipFileTest.UNIT_TEST_TARGET_DIR +
        '/' + ZIP_FILE_EXISTING_EMPTY_FILE;
    private static final String BINARIES_MODEL_ZIP_TARGET_NAME = WLSDeployZipFileTest.UNIT_TEST_TARGET_DIR +
        '/' + ZIP_FILE_EXISTING_BINARIES_FILE;

    @Before
    public void setup() throws Exception {
        File unitTestDir = new File(WLSDeployZipFileTest.UNIT_TEST_TARGET_DIR).getCanonicalFile();
        unitTestDir.mkdirs();
    }

    @Test
    public void testAddEnvModelWithDirectory() throws Exception {
        WLSDeployArchive archive = new WLSDeployArchive(APPS_ARCHIVE_FILE_NAME);
        Assert.assertNotNull("expected archive object to not be null", archive);
        File modelFile = new File(APPS_MODEL);
        Assert.assertTrue("expected model file to exist", modelFile.exists());
        Assert.assertFalse("expected model not to be a directory", modelFile.isDirectory());
        archive.addModel(modelFile);
        String appName = archive.addApplication(new File(APP1_TO_ADD));
        Assert.assertEquals("unexpected app name: " + appName, APP1_ENTRY_NAME1, appName);
        appName = archive.addApplication(new File(APP1_TO_ADD));
        Assert.assertEquals("unexpected app name: " + appName, APP1_ENTRY_NAME2, appName);
        appName = archive.addApplication(new File(APP1_TO_ADD));
        Assert.assertEquals("unexpected app name: " + appName, APP1_ENTRY_NAME3, appName);
        appName = archive.addApplication(new File(APP1_TO_ADD));
        Assert.assertEquals("unexpected app name: " + appName, APP1_ENTRY_NAME4, appName);
        appName = archive.addApplication(new File(APP2_TO_ADD));
        Assert.assertEquals("unexpected app name: " + appName, APP2_ENTRY_NAME1, appName);
        appName = archive.addApplication(new File(APP2_TO_ADD));
        Assert.assertEquals("unexpected app name: " + appName, APP2_ENTRY_NAME2, appName);
        appName = archive.addApplication(new File(APP2_TO_ADD));
        Assert.assertEquals("unexpected app name: " + appName, APP2_ENTRY_NAME3, appName);
        archive.close();
    }

    @Test
    public void testAddRemoveModelWithEmptyZip() throws Exception {
        WLSDeployZipFileTest.copyFile(ZIP_FILE_EXISTING_EMPTY_FILE);
        WLSDeployArchive archive = new WLSDeployArchive(EMPTY_MODEL_ZIP_TARGET_NAME);
        Assert.assertNotNull("expected archive object to not be null", archive);
        File modelFile = new File(APPS_MODEL);
        Assert.assertTrue("expected model file to exist", modelFile.exists());
        Assert.assertFalse("expected model file not to be a directory", modelFile.isDirectory());
        archive.addModel(modelFile);
        File extractDir =
            new File(WLSDeployZipFileTest.UNIT_TEST_TARGET_DIR + File.separator + "extracted").getCanonicalFile();
        extractDir.mkdirs();
        archive.extractModel(extractDir);
        String modelFileName = modelFile.getName();
        File extractedModelFile = new File(extractDir, "model/" + modelFileName);
        Assert.assertTrue("expected extracted model file to exist", extractedModelFile.exists());
        Assert.assertFalse("expected extracted model file not to be a directory", extractedModelFile.isDirectory());
        archive.close();
    }

    @Test
    public void testClearAllBinariesWithEmptyZip() throws Exception {
        WLSDeployZipFileTest.copyFile(ZIP_FILE_EXISTING_BINARIES_FILE);
        WLSDeployArchive archive = new WLSDeployArchive(BINARIES_MODEL_ZIP_TARGET_NAME);
        archive.removeAllBinaries();
        File archiveFile = new File(BINARIES_MODEL_ZIP_TARGET_NAME);
        Assert.assertTrue("expected archive file to exist", archiveFile.exists());
        Assert.assertFalse("expected archive file not to be a directory", archiveFile.isDirectory());
        Assert.assertNotNull("expected archive object to not be null", archive);
        String appName = archive.addApplication(new File(APP1_TO_ADD));
        Assert.assertFalse("expected appName to be not empty", StringUtils.isEmpty(appName));
        archive.close();
    }
}
