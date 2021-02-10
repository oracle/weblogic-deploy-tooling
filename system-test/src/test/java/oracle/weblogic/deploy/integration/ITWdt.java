// Copyright 2019, 2021, Oracle Corporation and/or its affiliates.
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

import java.io.File;
import java.io.PrintWriter;
import java.util.ArrayList;
import java.util.List;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardCopyOption;
@FixMethodOrder(MethodSorters.NAME_ASCENDING)
public class ITWdt extends BaseTest {

    private static boolean rcuDomainCreated = false;

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
        // pull FMW 12214 image
    //  pullOracleFMW12213Image();

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
        rcuDomainCreated = true;
        logTestEnd(testMethodName);
    }


    /**
     * testDOnlineUpdate1 check for 103 return code if an update requires restart.
     * @throws Exception - if any error occurs
     */
    @Test
    public void testDOnlineUpdate1() throws Exception {

        if (!rcuDomainCreated) {
            throw new Exception("testDOnlineUpdate skipped because testDCreateJRFDomainRunRCU failed");
        }

        String testMethodName = new Object() {}.getClass().getEnclosingMethod().getName();
        logTestBegin(testMethodName);

        // Setup boot.properties
        // domainParent12213  - is relative !
        String domainHome = domainParent12213 + FS + "jrfDomain1";
        setUpBootProperties(domainHome, "admin-server", "weblogic", "welcome1");
        boolean isServerUp = startAdminServer(domainHome);

        if (isServerUp) {
            String wdtModel = getSampleModelFile("-onlineUpdate");
            logger.info("DEBUG: wdtModel=" + wdtModel);
            String tmpWdtModel = System.getProperty("java.io.tmpdir") + FS + SAMPLE_MODEL_FILE_PREFIX
                + "-onlineUpdate.yaml";
            logger.info("DEBUG: tmpWdtModel=" + tmpWdtModel);

            // update wdt model file
            Path source = Paths.get(wdtModel);
            Path dest = Paths.get(tmpWdtModel);
            Files.copy(source, dest, StandardCopyOption.REPLACE_EXISTING);

            String cmd = "echo welcome1 | " + updateDomainScript + " -oracle_home " + mwhome_12213 + " -domain_home " +
                domainParent12213 + FS + "jrfDomain1 -model_file " +
                tmpWdtModel + " -admin_url t3://localhost:7001 -admin_user weblogic";
            logger.info("executing command: " + cmd);
            ExecResult result = ExecCommand.exec(cmd);
            int updateResult = result.exitValue();
            if (updateResult != 0 || updateResult != 103) {
                logger.info("DEBUG: result.stderr=" + result.stderr());
                logger.info("DEBUG: result.stdout=" + result.stdout());
            }

            stopAdminServer(domainHome);
            ExecCommand.exec("rm /tmp/admin-server.out");
            if (updateResult != 103) {
                throw new Exception("onlineUpdate is expecting return code of 103 but got " + result.exitValue());
            }

        } else {
            // Best effort to clean up server
            tryKillTheAdminServer(domainHome, "admin-server");
            ExecCommand.exec("rm /tmp/admin-server.out");
            throw new Exception("testDOnlineUpdate failed - cannot bring up server");
        }

        logTestEnd(testMethodName);
    }



    /**
     * testDOnlineUpdate2 check for 104 return code if an update cancel changes.
     * @throws Exception - if any error occurs
     */
    @Test
    public void testDOnlineUpdate2() throws Exception {

        if (!rcuDomainCreated) {
            throw new Exception("testDOnlineUpdate skipped because testDCreateJRFDomainRunRCU failed");
        }

        String testMethodName = new Object() {}.getClass().getEnclosingMethod().getName();
        logTestBegin(testMethodName);

        // Setup boot.properties

        String domainHome = domainParent12213 + FS + "jrfDomain1";

        boolean isServerUp = startAdminServer(domainHome);

        if (isServerUp) {

            String wdtModel = getSampleModelFile("-onlineUpdate2");
            logger.info("DEBUG: wdtModel=" + wdtModel);
            String tmpWdtModel = System.getProperty("java.io.tmpdir") + FS + SAMPLE_MODEL_FILE_PREFIX
                + "-onlineUpdate2.yaml";
            logger.info("DEBUG: tmpWdtModel=" + tmpWdtModel);

            // update wdt model file
            Path source = Paths.get(wdtModel);
            Path dest = Paths.get(tmpWdtModel);
            Files.copy(source, dest, StandardCopyOption.REPLACE_EXISTING);

            String cmd = "echo welcome1 | " + updateDomainScript + " -oracle_home " + mwhome_12213 + " -domain_home " +
                domainParent12213 + FS + "jrfDomain1 -model_file " +
                tmpWdtModel + " -admin_url t3://localhost:7001 -admin_user weblogic -cancel_changes_if_restart_required ";
            ExecResult result = ExecCommand.exec(cmd);
            int updateResult = result.exitValue();
            if (updateResult != 0 || updateResult != 104) {
                logger.info("DEBUG: result.stderr=" + result.stderr());
                logger.info("DEBUG: result.stdout=" + result.stdout());
            }

            stopAdminServer(domainHome);
            ExecCommand.exec("rm /tmp/admin-server.out");

            if (updateResult != 104) {
                throw new Exception("onlineUpdate is expecting return code of 103 but got " + result.exitValue());
            }

        } else {
            // Best effort to clean up server
            tryKillTheAdminServer(domainHome, "admin-server");
            ExecCommand.exec("rm /tmp/admin-server.out");
            throw new Exception("testDOnlineUpdate failed - cannot bring up server");
        }

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
        verifyFDiscoverDomainWithRequiredArgument(expectedModelFile);
        System.out.println("model file=" + expectedModelFile);

        logTestEnd(testMethodName);
    }

    private void verifyFDiscoverDomainWithRequiredArgument(String expectedModelFile) throws Exception {
         List<String> checkContents = new ArrayList<>();
         checkContents.add("domainInfo:");
         checkContents.add("AdminUserName: '--FIX ME--'");
         checkContents.add("CoherenceClusterSystemResource: defaultCoherenceCluster");
         checkContents.add("PublicAddress: kubernetes");
         checkContents.add("Trust Service Identity Asserter:");
         checkContents.add("appDeployments:");
         checkContents.add("SourcePath: 'wlsdeploy/applications/simple-app.war'");
        verifyModelFileContents(expectedModelFile, checkContents);
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
   * test discoverDomain.sh with -variable_file argument
   * @throws Exception - if any error occurs
   */
  @Test
  public void testGDiscoverDomainWithVariableFile() throws Exception {
    String testMethodName = new Object() {}.getClass().getEnclosingMethod().getName();
    logTestBegin(testMethodName);

    String discoveredArchive = System.getProperty("java.io.tmpdir") + FS + "discoveredArchive.zip";
    String discoveredModelFile = System.getProperty("java.io.tmpdir") + FS + "discoveredRestrictedJRFD1.yaml";
    String discoveredVaribleFile = System.getProperty("java.io.tmpdir") + FS + "discoveredRestrictedJRFD1.properties";
    String cmd = discoverDomainScript + " -oracle_home " + mwhome_12213 + " -domain_home " +
        domainParent12213 + FS + "restrictedJRFD1 -archive_file " + discoveredArchive +
        " -model_file " + discoveredModelFile + " -variable_file " + discoveredVaribleFile;

    logger.info("executing command: " + cmd);
    ExecResult result = ExecCommand.exec(cmd);

    verifyResult(result, "discoverDomain.sh completed successfully");

    // verify model file and variable file
    verifyModelFile(discoveredModelFile);
    verifyModelFile(discoveredVaribleFile);
    verifyGDiscoverDomainWithVariableFile(discoveredModelFile);

    logTestEnd(testMethodName);
  }

  private void verifyGDiscoverDomainWithVariableFile(String expectedModelFile) throws Exception {
    List<String> checkContents = new ArrayList<>();
    checkContents.add("AdminUserName: '@@PROP:AdminUserName@@'");
    verifyModelFileContents(expectedModelFile, checkContents);
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
        verifyHDiscoverDomainJRFDomainType(discoveredModelFile);
        logTestEnd(testMethodName);
    }

    private void verifyHDiscoverDomainJRFDomainType(String expectedModelFile) throws Exception {
      List<String> checkContents = new ArrayList<>();
      checkContents.add("AWT Application Context Startup Class");
      try {
        verifyModelFileContents(expectedModelFile, checkContents);
        throw new Exception("JRF blacklist components found in model file");
      } catch (Exception e) {
        // empty this is expected result
      }
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
     * test compareModel.sh with only attribute difference.  The files existences test whether it impacts WKO operation
     * @throws Exception - if any error occurs
     */
    @Test
    public void testCompareModelRemoveAttribute() throws Exception {
        String testMethodName = new Object() {}.getClass().getEnclosingMethod().getName();
        logTestBegin(testMethodName);
        Path tempPath = Files.createTempDirectory("wdt_temp_output");
        String tmpdir = tempPath.toFile().getAbsolutePath();
        tempPath.toFile().deleteOnExit();
        String cmd = compareModelScript + " -oracle_home " + mwhome_12213 + " -output_dir " + tmpdir
            + " " + getSampleModelFile("1-lessattribute") + " " +  getSampleModelFile("1");
        logger.info("Executing command: " + cmd);
        ExecResult result = ExecCommand.exec(cmd);
        verifyResult(result, "compareModel.sh completed successfully");

        String diffedModelYaml = tmpdir + File.separator + "diffed_model.yaml";
        String compareModelStdout = tmpdir + File.separator + "compare_model_stdout";
        verifyFileExists(compareModelStdout);
        verifyFileDoesNotExists(diffedModelYaml);

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

    private boolean startAdminServer(String domainHome) throws Exception {
        boolean isServerUp = false;
        String cmd = "nohup " + domainHome + "/bin/startWebLogic.sh > /tmp/admin-server.out 2>&1 &";

        ExecResult result = ExecCommand.exec(cmd);
        if (result.exitValue() != 0 ) {
            logger.info("startAdminServer: result.stderr=" + result.stderr());
            logger.info("startAdminServer: result.stdout=" + result.stdout());
            cmd = "cat /tmp/admin-server.out";
            result = ExecCommand.exec(cmd);
            logger.info(result.stdout());
            throw new Exception("startAdminServer: failed to execute command " + cmd);
        }

        try {
            Thread.sleep(60000);
            String readinessCmd = "export no_proxy=localhost && curl -sw '%{http_code}' http://localhost:7001/weblogic/ready";
            result = ExecCommand.exec(readinessCmd);
            for (int i=0; i < 60; i++) {
                logger.info("Server status: " + result.stdout());
                if ("200".equals(result.stdout())) {
                    logger.info("Server is running");
                    isServerUp = true;
                    break;
                }
                Thread.sleep(5000);
                result = ExecCommand.exec(readinessCmd);
                logger.info("Server is starting...");
            }

        } catch (InterruptedException ite) {
            Thread.currentThread().interrupt();
            throw ite;
        }

        if (!isServerUp) {
            cmd = "cat /tmp/admin-server.out";
            result = ExecCommand.exec(cmd);
            logger.info(result.stdout());
        }

        return isServerUp;
    }

    private void stopAdminServer(String domainHome) throws Exception {
        logger.info("Stopping the server");
        String cmd = domainHome + "/bin/stopWebLogic.sh";
        ExecResult result = ExecCommand.exec(cmd);
        if (result.exitValue() != 0) {
            logger.info("DEBUG: result.stderr=" + result.stderr());
            logger.info("DEBUG: result.stdout=" + result.stdout());
        }

    }

    private void setUpBootProperties(String domainHome, String server, String username, String password)
        throws Exception {

        File adminSecurityDir = new File(domainHome + FS + "servers" + FS + server + FS + "security");
        adminSecurityDir.mkdirs();
        PrintWriter pw = new PrintWriter(new File(adminSecurityDir + FS + "boot.properties"));
        pw.println("username=" + username);
        pw.println("password=" + password);
        pw.close();

    }

    private void tryKillTheAdminServer(String domainHome, String server) throws Exception {

        File domainDir = new File(domainHome);

        String cmd_format = "ps axww | " +
            "grep weblogic.Server | " +
            "grep \"%s\" | " +
            "grep \"\\-DINSTANCE_HOME=%s\" | " +
            "cut -f1 -d' '";
        logger.info("DEBUG: command is " + String.format(cmd_format, server, domainDir.getCanonicalPath()));
        ExecResult result = ExecCommand.exec(String.format(cmd_format, server, domainDir.getCanonicalPath()));
        logger.info("DEBUG: process id is [" + result.stdout() + "]");
        String pid = result.stderr();
        if (! "".equals(pid)) {
            try {
                Integer.parseInt(pid);
            } catch (NumberFormatException ne) {
                logger.info("ps does not return integer " + pid);
                return;
            }
        String cmd = "kill -9 " + pid;
        result = ExecCommand.exec(cmd);
        logger.info("DEBUG: " + cmd + " returns " + result.stdout());
        }

    }


}

