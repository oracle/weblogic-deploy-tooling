// Copyright 2019, 2020, Oracle Corporation and/or its affiliates.  All rights reserved.
// Licensed under the Universal Permissive License v 1.0 as shown at
// http://oss.oracle.com/licenses/upl.

package oracle.weblogic.deploy.integration;

import oracle.weblogic.deploy.integration.utils.ExecCommand;
import oracle.weblogic.deploy.integration.utils.ExecResult;
import org.junit.FixMethodOrder;
import org.junit.runners.MethodSorters;
import org.junit.BeforeClass;
import org.junit.AfterClass;
import org.junit.Rule;
import org.junit.Test;
import org.junit.rules.TestWatcher;
import org.junit.runner.Description;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardCopyOption;

@FixMethodOrder(MethodSorters.NAME_ASCENDING)
public class ITWdt extends BaseTest {

    @BeforeClass
    public static void staticPrepare() throws Exception {
        logger.info("prepare for WDT testing ...");

        initialize();
        // clean up the env first
        cleanup();

        // setup the test environment
        setup();

        // pull Oracle DB image for FMW RCU testing
        pullOracleDBDockerImage();
        // create a db container for RCU
        createDBContainer();

    }

    @AfterClass
    public static void staticUnprepare() throws Exception {
        logger.info("cleaning up after the test ...");
        cleanup();
    }


    @Rule
    public TestWatcher watcher = new TestWatcher() {
        @Override
        protected void failed(Throwable e, Description description) {
            if (e != null) {
                logger.info("Method " + description.getMethodName() + " Exception: " + e.getLocalizedMessage());
            }
            try {
                saveLogFiles(description.getMethodName());
            } catch (Exception le) {
                logger.info("Unable to save log files : " + le.getLocalizedMessage());
            }
        }
    };

    /**
     * test createDomain.sh with only -oracle_home argument
     * @throws Exception - if any error occurs
     */
    @Test
    public void test1CreateDomainNoDomainHome() throws Exception {
        String testMethodName = new Object() {}.getClass().getEnclosingMethod().getName();
        logTestBegin(testMethodName);

        String cmd = createDomainScript + " -oracle_home " + mwhome_12213;
        logger.info("executing command: " + cmd);
        ExecResult result = ExecCommand.exec(cmd);
        logger.info("NEGATIVE TEST: returned error msg: " + result.stderr());
        String expectedErrorMsg = "For createDomain, specify the -domain_parent or -domain_home argument, but not both";
        verifyErrorMsg(result, expectedErrorMsg);

        logTestEnd(testMethodName);
    }

    /**
     * test createDomain.sh with only -oracle_home and -domain_type arguments
     * @throws Exception - if any error occurs
     */
    @Test
    public void test2CreateDomainNoDomainHome() throws Exception {
        String testMethodName = new Object() {}.getClass().getEnclosingMethod().getName();
        logTestBegin(testMethodName);

        String cmd = createDomainScript + " -oracle_home " + mwhome_12213 + " -domain_type WLS";
        logger.info("executing command: " + cmd);
        ExecResult result = ExecCommand.exec(cmd);
        logger.info("NEGATIVE TEST: returned error msg: " + result.stderr());
        String expectedErrorMsg = "For createDomain, specify the -domain_parent or -domain_home argument, but not both";
        verifyErrorMsg(result, expectedErrorMsg);

        logTestEnd(testMethodName);
    }

    /**
     * test createDomain.sh without model file
     * @throws Exception - if any error occurs
     */
    @Test
    public void test3CreateDomainNoModelfile() throws Exception {
        String testMethodName = new Object() {}.getClass().getEnclosingMethod().getName();
        logTestBegin(testMethodName);

        String cmd = createDomainScript + " -oracle_home " + mwhome_12213 + " -domain_parent " + domainParent12213;
        logger.info("executing command: " + cmd);
        ExecResult result = ExecCommand.exec(cmd);
        logger.info("NEGATIVE TEST: returned error msg: " + result.stderr());
        String expectedErrorMsg = "createDomain requires a model file to run but neither the -model_file or " +
                "-archive_file argument were provided";
        verifyErrorMsg(result, expectedErrorMsg);

        logTestEnd(testMethodName);
    }

    /**
     * test createDomain.sh without archive file
     * @throws Exception - if any error occurs
     */
    @Test
    public void test4CreateDomainNoArchivefile() throws Exception {
        String testMethodName = new Object() {}.getClass().getEnclosingMethod().getName();
        logTestBegin(testMethodName);

        String cmd = createDomainScript + " -oracle_home " + mwhome_12213 + " -domain_parent " + domainParent12213 +
                " -model_file " + getSampleModelFile("-constant") ;
        logger.info("executing command: " + cmd);
        ExecResult result = ExecCommand.exec(cmd);
        logger.info("NEGATIVE TEST: returned error msg: " + result.stderr());
        String expectedErrorMsg = "archive file was not provided";
        verifyErrorMsg(result, expectedErrorMsg);

        logTestEnd(testMethodName);
    }

    /**
     * test createDomain.sh with required arguments
     * @throws Exception - if any error occurs
     */
    @Test
    public void test5CreateDomain() throws Exception {
        String testMethodName = new Object() {}.getClass().getEnclosingMethod().getName();
        logTestBegin(testMethodName);

        String cmd = createDomainScript + " -oracle_home " + mwhome_12213 + " -domain_parent " + domainParent12213 +
                " -model_file " + getSampleModelFile("-constant") +
                " -archive_file " + getSampleArchiveFile();
        logger.info("executing command: " + cmd);
        ExecResult result = ExecCommand.exec(cmd);
        verifyResult(result, "createDomain.sh completed successfully");

        logTestEnd(testMethodName);
    }

    /**
     * test createDomain.sh with different domain name in -domain_home and model file
     * in model file, it specifies the domain name as 'domain1'
     * in -domain_home argument, it specifies the domain home as 'domain2'
     * @throws Exception - if any error occurs
     */
    @Test
    public void test6CreateDomainDifferentDomainName() throws Exception {
        String testMethodName = new Object() {}.getClass().getEnclosingMethod().getName();
        logTestBegin(testMethodName);

        String cmd = createDomainScript + " -oracle_home " + mwhome_12213 + " -domain_home " +
                domainParent12213 + FS + "domain2 -model_file " +
                getSampleModelFile("-constant") + " -archive_file " + getSampleArchiveFile();
        logger.info("executing command: " + cmd);
        ExecResult result = ExecCommand.exec(cmd);
        verifyResult(result, "createDomain.sh completed successfully");

        logTestEnd(testMethodName);
    }

    /**
     * test createDomain.sh with WLS domain_type
     * @throws Exception -if any error occurs
     */
    @Test
    public void test7CreateDomainWLSType() throws Exception {
        String testMethodName = new Object() {}.getClass().getEnclosingMethod().getName();
        logTestBegin(testMethodName);

        String cmd = createDomainScript + " -oracle_home " + mwhome_12213 + " -domain_home " +
                domainParent12213 + FS + "domain2 -model_file " +
                getSampleModelFile("-constant") + " -archive_file " + getSampleArchiveFile() +
                " -domain_type WLS";
        logger.info("executing command: " + cmd);
        ExecResult result = ExecCommand.exec(cmd);
        verifyResult(result, "createDomain.sh completed successfully");

        logTestEnd(testMethodName);
    }

    /**
     * test createDomain.sh, model file contains variables but no variable_file specified
     * @throws Exception - if any error occurs
     */
    @Test
    public void test8CreateDomainNoVariableFile() throws Exception {
        String testMethodName = new Object() {}.getClass().getEnclosingMethod().getName();
        logTestBegin(testMethodName);

        String cmd = createDomainScript + " -oracle_home " + mwhome_12213 + " -domain_parent " + domainParent12213 +
                " -model_file " + getSampleModelFile("1") +
                " -archive_file " + getSampleArchiveFile()  ;
        logger.info("executing command: " + cmd);
        ExecResult result = ExecCommand.exec(cmd);
        logger.info("NEGATIVE TEST: returned error msg: " + result.stderr());
        String expectedErrorMsg = "createDomain variable substitution failed";
        verifyErrorMsg(result, expectedErrorMsg);

        logTestEnd(testMethodName);
    }

    /**
     * test createDomain.sh with variable_file argument
     * @throws Exception - if any error occurs
     */
    @Test
    public void test9CreateDomainWithVariableFile() throws Exception {
        String testMethodName = new Object() {}.getClass().getEnclosingMethod().getName();
        logTestBegin(testMethodName);

        String cmd = createDomainScript + " -oracle_home " + mwhome_12213 + " -domain_home " +
                domainParent12213 + FS + "domain2 -model_file " +
                getSampleModelFile("1") + " -archive_file " + getSampleArchiveFile() +
                " -domain_type WLS -variable_file " + getSampleVariableFile();
        logger.info("executing command: " + cmd);
        ExecResult result = ExecCommand.exec(cmd);
        verifyResult(result, "createDomain.sh completed successfully");

        logTestEnd(testMethodName);
    }

    /**
     * test createDomain.sh with wlst_path set to mwhome/wlserver
     * @throws Exception - if any error occurs
     */
    @Test
    public void testACreateDomainWithWlstPath() throws Exception {
        String testMethodName = new Object() {}.getClass().getEnclosingMethod().getName();
        logTestBegin(testMethodName);

        String cmd = createDomainScript + " -oracle_home " + mwhome_12213 + " -domain_home " +
                domainParent12213 + FS + "domain2 -model_file " +
                getSampleModelFile("1") + " -archive_file " + getSampleArchiveFile() +
                " -domain_type WLS -variable_file " + getSampleVariableFile() + " -wlst_path " +
                mwhome_12213 + FS + "wlserver";
        logger.info("executing command: " + cmd);
        ExecResult result = ExecCommand.exec(cmd);
        verifyResult(result, "createDomain.sh completed successfully");

        logTestEnd(testMethodName);
    }

    /**
     * test createDomain.sh with -wlst_path set to mwhome/oracle_common
     * @throws Exception - if any error occurs
     */
    @Test
    public void testBCreateDomainWithOracleCommaonWlstPath() throws Exception {
        String testMethodName = new Object() {}.getClass().getEnclosingMethod().getName();
        logTestBegin(testMethodName);

        String cmd = createDomainScript + " -oracle_home " + mwhome_12213 + " -domain_home " +
                domainParent12213 + FS + "domain2 -model_file " +
                getSampleModelFile("1") + " -archive_file " + getSampleArchiveFile() +
                " -domain_type WLS -variable_file " + getSampleVariableFile() + " -wlst_path " +
                mwhome_12213 + FS + "oracle_common";
        logger.info("executing command: " + cmd);
        ExecResult result = ExecCommand.exec(cmd);
        verifyResult(result, "createDomain.sh completed successfully");

        logTestEnd(testMethodName);
    }

    /**
     * test createDomain.sh, create JRF domain without -run_rcu argument
     * @throws Exception - if any error occurs
     */
    @Test
    public void testCCreateJRFDomainNoRunRCU() throws Exception {
        String testMethodName = new Object() {}.getClass().getEnclosingMethod().getName();
        logTestBegin(testMethodName);

        String wdtModel = getSampleModelFile("2");
        String tmpWdtModel = System.getProperty("java.io.tmpdir") + FS + SAMPLE_MODEL_FILE_PREFIX + "2.yaml";

        // update wdt model file
        Path source = Paths.get(wdtModel);
        Path dest = Paths.get(tmpWdtModel);
        Files.copy(source, dest, StandardCopyOption.REPLACE_EXISTING);
        replaceStringInFile(tmpWdtModel, "%DB_HOST%", getDBContainerIP());

        String cmd = createDomainScript + " -oracle_home " + mwhome_12213 + " -domain_home " +
                domainParent12213 + FS + "domain2 -model_file " +
                tmpWdtModel + " -archive_file " + getSampleArchiveFile() + " -domain_type JRF";
        logger.info("executing command: " + cmd);
        ExecResult result = ExecCommand.exec(cmd);
        logger.info("NEGATIVE TEST: returned error msg: " + result.stderr());
        String expectedErrorMsg = "Failed to get FMW infrastructure database defaults from the service table";
        verifyErrorMsg(result, expectedErrorMsg);

        logTestEnd(testMethodName);
    }

    /**
     * test createDomain.sh, create JRF domain with -run_rcu argument
     * @throws Exception - if any error occurs
     */
    @Test
    public void testDCreateJRFDomainRunRCU() throws Exception {
        String testMethodName = new Object() {}.getClass().getEnclosingMethod().getName();
        logTestBegin(testMethodName);

        String wdtModel = getSampleModelFile("2");
        logger.info("DEBUG: wdtModel=" + wdtModel);
        String tmpWdtModel = System.getProperty("java.io.tmpdir") + FS + SAMPLE_MODEL_FILE_PREFIX + "2.yaml";
        logger.info("DEBUG: tmpWdtModel=" + tmpWdtModel);

        // update wdt model file
        Path source = Paths.get(wdtModel);
        Path dest = Paths.get(tmpWdtModel);
        Files.copy(source, dest, StandardCopyOption.REPLACE_EXISTING);
        replaceStringInFile(tmpWdtModel, "%DB_HOST%", getDBContainerIP());

        String cmd = createDomainScript + " -oracle_home " + mwhome_12213 + " -domain_home " +
                domainParent12213 + FS + "jrfDomain1 -model_file " +
                tmpWdtModel + " -archive_file " + getSampleArchiveFile() + " -domain_type JRF -run_rcu";
        logger.info("executing command: " + cmd);
        ExecResult result = ExecCommand.exec(cmd);
        logger.info("DEBUG: result.stderr=" + result.stderr());
        logger.info("DEBUG: result.stdout=" + result.stdout());
        verifyResult(result, "createDomain.sh completed successfully");

        logTestEnd(testMethodName);
    }

    /**
     * test createDomain.sh, create restrictedJRF domain
     * @throws Exception - if any error occurs
     */
    @Test
    public void testECreateRestrictedJRFDomain() throws Exception {
        String testMethodName = new Object() {}.getClass().getEnclosingMethod().getName();
        logTestBegin(testMethodName);

        String cmd = createDomainScript + " -oracle_home " + mwhome_12213 + " -domain_home " +
                domainParent12213 + FS + "restrictedJRFD1 -model_file " +
                getSampleModelFile("-constant") + " -archive_file " + getSampleArchiveFile() +
                " -domain_type RestrictedJRF";
        logger.info("executing command: " + cmd);
        ExecResult result = ExecCommand.exec(cmd);
        verifyResult(result, "createDomain.sh completed successfully");

        logTestEnd(testMethodName);
    }

    /**
     * test discoverDomain.sh with required arguments
     * @throws Exception - if any error occurs
     */
    @Test
    public void testFDiscoverDomainWithRequiredArgument() throws Exception {
        String testMethodName = new Object() {}.getClass().getEnclosingMethod().getName();
        logTestBegin(testMethodName);

        String discoveredArchive = System.getProperty("java.io.tmpdir") + FS + "discoveredArchive.zip";
        String cmd = discoverDomainScript + " -oracle_home " + mwhome_12213 + " -domain_home " +
                domainParent12213 + FS + "restrictedJRFD1 " +
                " -archive_file " + discoveredArchive + " -domain_type RestrictedJRF";

        logger.info("executing command: " + cmd);
        ExecResult result = ExecCommand.exec(cmd);

        verifyResult(result, "discoverDomain.sh completed successfully");

        // unzip discoveredArchive.zip
        cmd = "unzip -o " + discoveredArchive + " -d " + System.getProperty("java.io.tmpdir");
        logger.info("executing command: " + cmd);
        executeNoVerify(cmd);

        // verify model file
        String expectedModelFile = System.getProperty("java.io.tmpdir") + FS + "model" + FS + "restrictedJRFD1.yaml";
        verifyModelFile(expectedModelFile);

        logTestEnd(testMethodName);
    }

    /**
     * test discoverDomain.sh with -model_file argument
     * @throws Exception - if any error occurs
     */
    @Test
    public void testGDiscoverDomainWithModelFile() throws Exception {
        String testMethodName = new Object() {}.getClass().getEnclosingMethod().getName();
        logTestBegin(testMethodName);

        String discoveredArchive = System.getProperty("java.io.tmpdir") + FS + "discoveredArchive.zip";
        String discoveredModelFile = System.getProperty("java.io.tmpdir") + FS + "discoveredRestrictedJRFD1.yaml";
        String cmd = discoverDomainScript + " -oracle_home " + mwhome_12213 + " -domain_home " +
                domainParent12213 + FS + "restrictedJRFD1 -archive_file " + discoveredArchive +
                " -model_file " + discoveredModelFile;

        logger.info("executing command: " + cmd);
        ExecResult result = ExecCommand.exec(cmd);

        verifyResult(result, "discoverDomain.sh completed successfully");

        // verify model file
        verifyModelFile(discoveredModelFile);

        logTestEnd(testMethodName);
    }

    /**
     * test discoverDomain.sh with -domain_type as JRF
     * @throws Exception - if any error occurs
     */
    @Test
    public void testHDiscoverDomainJRFDomainType() throws Exception {
        String testMethodName = new Object() {}.getClass().getEnclosingMethod().getName();
        logTestBegin(testMethodName);

        String discoveredArchive = System.getProperty("java.io.tmpdir") + FS + "discoveredArchive.zip";
        String discoveredModelFile = System.getProperty("java.io.tmpdir") + FS + "discoveredJRFD1.yaml";
        String cmd = discoverDomainScript + " -oracle_home " + mwhome_12213 + " -domain_home " +
                domainParent12213 + FS + "jrfDomain1 -archive_file " + discoveredArchive +
                " -model_file " + discoveredModelFile + " -domain_type JRF";

        logger.info("executing command: " + cmd);
        ExecResult result = ExecCommand.exec(cmd);

        verifyResult(result, "discoverDomain.sh completed successfully");

        // verify model file
        verifyModelFile(discoveredModelFile);

        logTestEnd(testMethodName);
    }

    /**
     * test updateDomain.sh, update the domain to set the number of dynamic servers to 4
     * @throws Exception - if any error occurs
     */
    @Test
    public void testIUpdateDomain() throws Exception {
        String testMethodName = new Object() {}.getClass().getEnclosingMethod().getName();
        logTestBegin(testMethodName);

        String variableFile = getSampleVariableFile();
        String tmpVariableFile = System.getProperty("java.io.tmpdir") + FS + SAMPLE_VARIABLE_FILE;

        // update wdt model file
        Path source = Paths.get(variableFile);
        Path dest = Paths.get(tmpVariableFile);
        Files.copy(source, dest, StandardCopyOption.REPLACE_EXISTING);
        replaceStringInFile(tmpVariableFile, "CONFIGURED_MANAGED_SERVER_COUNT=2",
                "CONFIGURED_MANAGED_SERVER_COUNT=4");

        String cmd = updateDomainScript + " -oracle_home " + mwhome_12213 + " -domain_home " +
                domainParent12213 + FS + "domain2 -model_file " +
                getSampleModelFile("1") + " -archive_file " + getSampleArchiveFile() +
                " -domain_type WLS -variable_file " + tmpVariableFile;

        logger.info("executing command: " + cmd);
        ExecResult result = ExecCommand.exec(cmd);
        verifyResult(result, "updateDomain.sh completed successfully");

        // verify the domain is updated
        cmd = "grep '<max-dynamic-cluster-size>4</max-dynamic-cluster-size>' " + domainParent12213 + FS +
                "domain2" + FS + "config" + FS + "config.xml |wc -l";
        logger.info("executing command: " + cmd);
        result = ExecCommand.exec(cmd);
        if(Integer.parseInt(result.stdout().trim()) != 1) {
            throw new Exception("the domain is not updated as expected");
        }

        logTestEnd(testMethodName);
    }

    /**
     * test deployApp.sh without model file
     * @throws Exception - if any error occurs
     */
    @Test
    public void testJDeployAppWithoutModelfile() throws Exception {
        String testMethodName = new Object() {}.getClass().getEnclosingMethod().getName();
        logTestBegin(testMethodName);

        String cmd = deployAppScript + " -oracle_home " + mwhome_12213 + " -domain_home " +
                domainParent12213 + FS + "domain2 -archive_file " + getSampleArchiveFile();
        ExecResult result = ExecCommand.exec(cmd);
        logger.info("NEGATIVE TEST: returned error msg: " + result.stderr());
        String expectedErrorMsg = "deployApps failed to find a model file in archive";
        verifyErrorMsg(result, expectedErrorMsg);

        logTestEnd(testMethodName);
    }

    /**
     * test deployApps.sh with model file
     * @throws Exception - if any error occurs
     */
    @Test
    public void testKDeployAppWithModelfile() throws Exception {
        String testMethodName = new Object() {}.getClass().getEnclosingMethod().getName();
        logTestBegin(testMethodName);

        String cmd = deployAppScript + " -oracle_home " + mwhome_12213 + " -domain_home " +
                domainParent12213 + FS + "domain2 -archive_file " + getSampleArchiveFile() +
                " -model_file " + getSampleModelFile("-constant");
        logger.info("executing command: " + cmd);
        ExecResult result = ExecCommand.exec(cmd);
        verifyResult(result, "deployApps.sh completed successfully");

        logTestEnd(testMethodName);
    }

    /**
     * test validateModel.sh with -oracle_home only
     * @throws Exception - if any error occurs
     */
    @Test
    public void testLValidateModelWithOracleHomeOnly() throws Exception {
        String testMethodName = new Object() {}.getClass().getEnclosingMethod().getName();
        logTestBegin(testMethodName);

        String cmd = validateModelScript + " -oracle_home " + mwhome_12213;
        logger.info("Executing command: " + cmd);
        ExecResult result = ExecCommand.exec(cmd);
        logger.info("NEGATIVE TEST: returned error msg: " + result.stderr());
        String expectedErrorMsg = "validateModel requires a model file to run";
        verifyErrorMsg(result, expectedErrorMsg);

        logTestEnd(testMethodName);
    }

    /**
     * test validateModel.sh with -oracle_home and -model_file
     * @throws Exception - if any error occurs
     */
    @Test
    public void testMValidateModelWithOracleHomeModelFile() throws Exception {
        String testMethodName = new Object() {}.getClass().getEnclosingMethod().getName();
        logTestBegin(testMethodName);

        String cmd = validateModelScript + " -oracle_home " + mwhome_12213 + " -model_file " +
                getSampleModelFile("-constant");
        logger.info("Executing command: " + cmd);
        ExecResult result = ExecCommand.exec(cmd);
        verifyResult(result, "the archive file was not provided");

        logTestEnd(testMethodName);
    }

    /**
     * test validateModel.sh without -variable_file
     * @throws Exception - if any error occurs
     */
    @Test
    public void testNValidateModelWithoutVariableFile() throws Exception {
        String testMethodName = new Object() {}.getClass().getEnclosingMethod().getName();
        logTestBegin(testMethodName);

        String cmd = validateModelScript + " -oracle_home " + mwhome_12213 + " -model_file " +
                getSampleModelFile("1");
        logger.info("Executing command: " + cmd);
        ExecResult result = ExecCommand.exec(cmd);
        logger.info("NEGATIVE TEST: returned msg: " + result.stderr());
        String expectedWarningMsg = ", but no variables file was specified";
        verifyErrorMsg(result, expectedWarningMsg);

        logTestEnd(testMethodName);
    }

    /**
     * test validateModel.sh with invalid model file
     * @throws Exception - if any error occurs
     */
    @Test
    public void testOValidateModelWithInvalidModelfile() throws Exception {
        String testMethodName = new Object() {}.getClass().getEnclosingMethod().getName();
        logTestBegin(testMethodName);

        String cmd = validateModelScript + " -oracle_home " + mwhome_12213 + " -model_file " +
                getSampleModelFile("-invalid") + " -variable_file " + getSampleVariableFile();
        logger.info("Executing command: " + cmd);
        ExecResult result = ExecCommand.exec(cmd);
        verifyErrorMsg(result, "exit code = 2");

        logTestEnd(testMethodName);
    }

    @Test
    public void testPEncryptModel() throws Exception {
        String testMethodName = new Object() {}.getClass().getEnclosingMethod().getName();
        logTestBegin(testMethodName);

        String clearPwdModelFile = getSampleModelFile("-constant");
        String tmpModelFile = System.getProperty("java.io.tmpdir") + FS + SAMPLE_MODEL_FILE_PREFIX +
                "-constant.yaml";

        // update wdt model file
        Path source = Paths.get(clearPwdModelFile);
        Path dest = Paths.get(tmpModelFile);
        Files.copy(source, dest, StandardCopyOption.REPLACE_EXISTING);

        String cmd = encryptModelScript + " -oracle_home " + mwhome_12213 + " -model_file " +
                tmpModelFile + " < " + getResourcePath() + FS + "passphrase.txt";
        logger.info("executing command: " + cmd);
        ExecResult result = ExecCommand.exec(cmd);
        verifyResult(result, "encryptModel.sh completed successfully");

        // create the domain using -use_encryption
        cmd = createDomainScript + " -oracle_home " + mwhome_12213 + " -domain_home " +
                domainParent12213 + FS + "domain10 -model_file " +
                tmpModelFile + " -archive_file " + getSampleArchiveFile() +
                " -domain_type WLS -use_encryption < " + getResourcePath() + FS + "passphrase.txt";
        logger.info("executing command: " + cmd);
        result = ExecCommand.exec(cmd);
        verifyResult(result, "createDomain.sh completed successfully");
        logTestEnd(testMethodName);
    }
}

