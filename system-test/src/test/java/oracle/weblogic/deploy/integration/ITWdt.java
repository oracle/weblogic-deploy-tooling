// Copyright 2019, 2021, Oracle Corporation and/or its affiliates.
// Licensed under the Universal Permissive License v 1.0 as shown at
// http://oss.oracle.com/licenses/upl.

package oracle.weblogic.deploy.integration;

import java.io.BufferedWriter;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.OutputStreamWriter;
import java.io.PrintWriter;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardCopyOption;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.logging.Logger;

import oracle.weblogic.deploy.integration.annotations.IntegrationTest;
import oracle.weblogic.deploy.integration.annotations.TestingLogger;
import oracle.weblogic.deploy.integration.utils.CommandResult;
import oracle.weblogic.deploy.integration.utils.Runner;
import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.MethodOrderer;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestInfo;
import org.junit.jupiter.api.TestMethodOrder;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.junit.jupiter.api.Assumptions.assumeTrue;

@IntegrationTest
@TestMethodOrder(MethodOrderer.MethodName.class)
public class ITWdt extends BaseTest {
    @TestingLogger
    private static final Logger logger = Logger.getLogger("integration.tests");

    private static boolean rcuDomainCreated = false;

    @BeforeAll
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

    @AfterAll
    public static void staticUnprepare() throws Exception {
        logger.info("cleaning up after the test ...");
        cleanup();
    }

    private static Path getTestOutputPath(TestInfo testInfo) throws IOException {
        if (!testInfo.getTestMethod().isPresent()) {
            throw new IllegalArgumentException("Method is not present in this context, and this method cannot be used");
        }
        String methodName = testInfo.getTestMethod().get().getName();
        Path outputPath = Paths.get("target", "test-output", methodName);
        if (!Files.exists(outputPath)) {
            Files.createDirectories(outputPath);
        }
        return outputPath;
    }

    private static Map<String,String> getTestMethodEnvironment(TestInfo testInfo) throws IOException {
        Map<String,String> env = new HashMap<>();
        env.put("WLSDEPLOY_LOG_DIRECTORY", getTestOutputPath(testInfo).toString());
        return env;
    }

    private static PrintWriter getTestMethodWriter(TestInfo testInfo) throws IOException {
        if (!testInfo.getTestMethod().isPresent()) {
            throw new IllegalArgumentException("Method is not present in this context, and this method cannot be used");
        }

        String methodName = testInfo.getTestMethod().get().getName();
        // create a output file in the build folder with the name {test method name}.stdout
        Path outputPath = getTestOutputPath(testInfo);
        logger.info("Test log: " + outputPath);
        return new PrintWriter(
            new BufferedWriter(new OutputStreamWriter(
                new FileOutputStream(outputPath.resolve(Paths.get(methodName + ".out")).toString()))), true);
    }

    /**
     * test createDomain.sh with only -oracle_home argument
     * @throws Exception - if any error occurs
     */
    @DisplayName("Test 1: createDomain bad arguments")
    @Tag("gate")
    @Test
    public void test1CreateDomainNoDomainHome(TestInfo testInfo) throws Exception {
        String cmd = createDomainScript + " -oracle_home " + mwhome_12213;
        try (PrintWriter out = getTestMethodWriter(testInfo)) {
            CommandResult result = Runner.run(cmd, getTestMethodEnvironment(testInfo), out);
            assertEquals(99, result.exitValue(), "Unexpected return code");
            assertTrue(result.stdout().contains("WLSDPLY-20008"), "Output did not contain expected WLSDPLY-20008");
        }
    }

    /**
     * test createDomain.sh with only -oracle_home and -domain_type arguments
     * @throws Exception - if any error occurs
     */
    @DisplayName("Test 2: createDomain bad arguments")
    @Tag("gate")
    @Test
    public void test2CreateDomainNoDomainHome(TestInfo testInfo) throws Exception {
        String cmd = createDomainScript + " -oracle_home " + mwhome_12213 + " -domain_type WLS";
        try (PrintWriter out = getTestMethodWriter(testInfo)) {
            CommandResult result = Runner.run(cmd, getTestMethodEnvironment(testInfo), out);
            assertEquals(99, result.exitValue(), "Unexpected return code");
            // command should fail because of invalid arguments
            assertTrue(result.stdout().contains("WLSDPLY-20008"), "Output did not contain expected WLSDPLY-20008");
        }
    }

    /**
     * test createDomain.sh without model file
     * @throws Exception - if any error occurs
     */
    @DisplayName("Test 3: createDomain bad arguments")
    @Tag("gate")
    @Test
    public void test3CreateDomainNoModelfile(TestInfo testInfo) throws Exception {
        String cmd = createDomainScript + " -oracle_home " + mwhome_12213 + " -domain_parent " + domainParentDir;
        try (PrintWriter out = getTestMethodWriter(testInfo)) {
            CommandResult result = Runner.run(cmd, getTestMethodEnvironment(testInfo), out);
            assertEquals(99, result.exitValue(), "Unexpected return code");
            // command should fail because of invalid arguments
            assertTrue(result.stdout().contains("WLSDPLY-20008"), "Output did not contain expected WLSDPLY-20008");
        }
    }

    /**
     * test createDomain.sh without archive file
     * @throws Exception - if output file could not be created or written
     */
    @DisplayName("Test 4: createDomain without archive file")
    @Tag("gate")
    @Test
    public void test4CreateDomainNoArchivefile(TestInfo testInfo) throws Exception {
        String cmd = createDomainScript + " -oracle_home " + mwhome_12213 + " -domain_parent " + domainParentDir +
                " -model_file " + getSampleModelFile("-constant") ;
        try (PrintWriter out = getTestMethodWriter(testInfo)) {
            CommandResult result = Runner.run(cmd, getTestMethodEnvironment(testInfo), out);
            assertEquals(2, result.exitValue(), "Unexpected return code");
            // command should fail because of invalid arguments
            assertTrue(result.stdout().contains("WLSDPLY-05025"), "Output did not contain expected WLSDPLY-05025");
        }
    }

    /**
     * test createDomain.sh with required arguments
     * @throws Exception - if any error occurs
     */
    @DisplayName("Test 5: createDomain with domain_parent")
    @Tag("gate")
    @Test
    public void test5CreateDomain(TestInfo testInfo) throws Exception {
        String cmd = createDomainScript + " -oracle_home " + mwhome_12213 + " -domain_parent " + domainParentDir +
                " -model_file " + getSampleModelFile("-constant") +
                " -archive_file " + getSampleArchiveFile();
        try (PrintWriter out = getTestMethodWriter(testInfo)) {
            CommandResult result = Runner.run(cmd, getTestMethodEnvironment(testInfo), out);
            assertEquals(0, result.exitValue(), "Unexpected return code");
            assertTrue(result.stdout().contains("createDomain.sh completed successfully"), "Create failed");
        }
    }

    /**
     * test createDomain.sh with different domain name in -domain_home and model file
     * in model file, it specifies the domain name as 'domain1'
     * in -domain_home argument, it specifies the domain home as 'domain2'
     * @throws Exception - if any error occurs
     */
    @DisplayName("Test 6: createDomain with domain_home")
    @Tag("gate")
    @Test
    public void test6CreateDomainDifferentDomainName(TestInfo testInfo) throws Exception {
        String cmd = createDomainScript
            + " -oracle_home " + mwhome_12213
            + " -domain_home " + domainParentDir + FS + "domain2"
            + " -model_file " + getSampleModelFile("-constant")
            + " -archive_file " + getSampleArchiveFile();
        try (PrintWriter out = getTestMethodWriter(testInfo)) {
            CommandResult result = Runner.run(cmd, getTestMethodEnvironment(testInfo), out);
            assertEquals(0, result.exitValue(), "Unexpected return code");
            assertTrue(result.stdout().contains("createDomain.sh completed successfully"), "Create failed");
        }
    }

    /**
     * test createDomain.sh with WLS domain_type
     * @throws Exception -if any error occurs
     */
    @Tag("gate")
    @Test
    public void test7CreateDomainWLSType(TestInfo testInfo) throws Exception {
        String cmd = createDomainScript + " -oracle_home " + mwhome_12213 + " -domain_home " +
            domainParentDir + FS + "domain2 -model_file " +
                getSampleModelFile("-constant") + " -archive_file " + getSampleArchiveFile() +
                " -domain_type WLS";
        try (PrintWriter out = getTestMethodWriter(testInfo)) {
            CommandResult result = Runner.run(cmd, getTestMethodEnvironment(testInfo), out);
            assertEquals(0, result.exitValue(), "Unexpected return code");
            assertTrue(result.stdout().contains("createDomain.sh completed successfully"), "Create failed");
        }
    }

    /**
     * test createDomain.sh, model file contains variables but no variable_file specified
     * @throws Exception - if any error occurs
     */
    @DisplayName("Test 8: createDomain but needs variable file")
    @Tag("gate")
    @Test
    public void test8CreateDomainNoVariableFile(TestInfo testInfo) throws Exception {
        String cmd = createDomainScript + " -oracle_home " + mwhome_12213 + " -domain_parent " + domainParentDir +
                " -model_file " + getSampleModelFile("1") +
                " -archive_file " + getSampleArchiveFile()  ;
        try (PrintWriter out = getTestMethodWriter(testInfo)) {
            CommandResult result = Runner.run(cmd, getTestMethodEnvironment(testInfo), out);
            assertEquals(2, result.exitValue(), "Unexpected return code");
            // command should fail because of invalid arguments
            assertTrue(result.stdout().contains("WLSDPLY-20004"), "Output did not contain expected WLSDPLY-20004");
        }
    }

    /**
     * test createDomain.sh with variable_file argument
     * @throws Exception - if any error occurs
     */
    @DisplayName("Test 9: createDomain with variable file")
    @Tag("gate")
    @Test
    public void test9CreateDomainWithVariableFile(TestInfo testInfo) throws Exception {
        String cmd = createDomainScript + " -oracle_home " + mwhome_12213 + " -domain_home " +
            domainParentDir + FS + "domain2 -model_file " +
                getSampleModelFile("1") + " -archive_file " + getSampleArchiveFile() +
                " -domain_type WLS -variable_file " + getSampleVariableFile();
        try (PrintWriter out = getTestMethodWriter(testInfo)) {
            CommandResult result = Runner.run(cmd, getTestMethodEnvironment(testInfo), out);
            assertEquals(0, result.exitValue(), "Unexpected return code");
            assertTrue(result.stdout().contains("createDomain.sh completed successfully"), "Create failed");
        }
    }

    /**
     * test createDomain.sh with wlst_path set to mwhome/wlserver
     * @throws Exception - if any error occurs
     */
    @DisplayName("Test 10: createDomain with WLS wlst_path")
    @Tag("gate")
    @Test
    public void testACreateDomainWithWlstPath(TestInfo testInfo) throws Exception {
        String cmd = createDomainScript + " -oracle_home " + mwhome_12213 + " -domain_home " +
            domainParentDir + FS + "domain2 -model_file " +
                getSampleModelFile("1") + " -archive_file " + getSampleArchiveFile() +
                " -domain_type WLS -variable_file " + getSampleVariableFile() + " -wlst_path " +
                mwhome_12213 + FS + "wlserver";
        try (PrintWriter out = getTestMethodWriter(testInfo)) {
            CommandResult result = Runner.run(cmd, getTestMethodEnvironment(testInfo), out);
            assertEquals(0, result.exitValue(), "Unexpected return code");
            assertTrue(result.stdout().contains("createDomain.sh completed successfully"), "Create failed");
        }
    }

    /**
     * test createDomain.sh with -wlst_path set to mwhome/oracle_common
     * @throws Exception - if any error occurs
     */
    @DisplayName("Test 11: createDomain with oracle_commmon wlst_path")
    @Tag("gate")
    @Test
    public void testBCreateDomainWithOracleCommonWlstPath(TestInfo testInfo) throws Exception {
        String cmd = createDomainScript + " -oracle_home " + mwhome_12213 + " -domain_home " +
            domainParentDir + FS + "domain2 -model_file " +
                getSampleModelFile("1") + " -archive_file " + getSampleArchiveFile() +
                " -domain_type WLS -variable_file " + getSampleVariableFile() + " -wlst_path " +
                mwhome_12213 + FS + "oracle_common";
        try (PrintWriter out = getTestMethodWriter(testInfo)) {
            CommandResult result = Runner.run(cmd, getTestMethodEnvironment(testInfo), out);
            assertEquals(0, result.exitValue(), "Unexpected return code");
            assertTrue(result.stdout().contains("createDomain.sh completed successfully"), "Create failed");
        }
    }

    /**
     * test createDomain.sh, create JRF domain without -run_rcu argument
     * @throws Exception - if any error occurs
     */
    @DisplayName("Test 12: createDomain JRF domain without DB")
    @Tag("gate")
    @Test
    public void testCCreateJRFDomainNoRunRCU(TestInfo testInfo) throws Exception {
        try (PrintWriter out = getTestMethodWriter(testInfo)) {
            Path source = Paths.get(getSampleModelFile("2"));
            Path modelOut = getTestOutputPath(testInfo).resolve(SAMPLE_MODEL_FILE_PREFIX + "2.yaml");
            // create wdt model file to use in create, after substitution of DB host/ip
            replaceStringInFile(source, modelOut, "%DB_HOST%", getDBContainerIP());

            String cmd = createDomainScript + " -oracle_home " + mwhome_12213 + " -domain_home " +
                domainParentDir + FS + "domain2 -model_file " +
                modelOut + " -archive_file " + getSampleArchiveFile() + " -domain_type JRF";

            CommandResult result = Runner.run(cmd, getTestMethodEnvironment(testInfo), out);
            assertEquals(2, result.exitValue(), "Unexpected return code");
            assertTrue(result.stdout().contains("WLSDPLY-12409"), "Output did not contain expected WLSDPLY-12409");
        }
    }

    /**
     * test createDomain.sh, create JRF domain with -run_rcu argument
     * @throws Exception - if any error occurs
     */
    @DisplayName("Test 13: createDomain JRF domain and run RCU")
    @Tag("gate")
    @Test
    public void testDCreateJRFDomainRunRCU(TestInfo testInfo) throws Exception {
        waitForDatabase();
        try (PrintWriter out = getTestMethodWriter(testInfo)) {
            Path source = Paths.get(getSampleModelFile("2"));
            Path modelOut = getTestOutputPath(testInfo).resolve(SAMPLE_MODEL_FILE_PREFIX + "2.yaml");
            // create wdt model file to use in create, after substitution of DB host/ip
            replaceStringInFile(source, modelOut, "%DB_HOST%", getDBContainerIP());

            String cmd = createDomainScript + " -oracle_home " + mwhome_12213 + " -domain_home " +
                domainParentDir + FS + "jrfDomain1 -model_file " +
                modelOut + " -archive_file " + getSampleArchiveFile() + " -domain_type JRF -run_rcu";

            CommandResult result = Runner.run(cmd, getTestMethodEnvironment(testInfo), out);
            assertEquals(0, result.exitValue(), "Unexpected return code");
            // command should fail because of invalid arguments
            assertTrue(result.stdout().contains("createDomain.sh completed successfully"), "Create failed");
            rcuDomainCreated = true;
        }
    }


    /**
     * testDOnlineUpdate1 check for 103 return code if an update requires restart.
     * @throws Exception - if any error occurs
     */
    @DisplayName("Test 14: Update JRF domain that requires restart")
    @Tag("gate")
    @Test
    public void testDOnlineUpdate1(TestInfo testInfo) throws Exception {
        assumeTrue(rcuDomainCreated, "testDOnlineUpdate skipped because testDCreateJRFDomainRunRCU failed");

        // Setup boot.properties
        // domainParent12213  - is relative !
        String domainHome = domainParentDir + FS + "jrfDomain1";
        setUpBootProperties(domainHome, "admin-server", "weblogic", "welcome1");
        Path adminServerOut = getTestOutputPath(testInfo).resolve("admin-server.out");
        boolean isServerUp = startAdminServer(domainHome, adminServerOut);

        if (isServerUp) {
            try (PrintWriter out = getTestMethodWriter(testInfo)) {
                // update wdt model file
                Path source = Paths.get(getSampleModelFile("-onlineUpdate"));
                Path model = getTestOutputPath(testInfo).resolve(SAMPLE_MODEL_FILE_PREFIX + "-onlineUpdate.yaml");
                Files.copy(source, model, StandardCopyOption.REPLACE_EXISTING);

                String cmd = "echo welcome1 | "
                    + updateDomainScript
                    + " -oracle_home " + mwhome_12213
                    + " -domain_home " + domainParentDir + FS + "jrfDomain1"
                    + " -model_file " + model
                    + " -admin_url t3://localhost:7001 -admin_user weblogic";
                CommandResult result = Runner.run(cmd, getTestMethodEnvironment(testInfo), out);

                stopAdminServer(domainHome);
                assertEquals(103, result.exitValue(), "onlineUpdate is expecting return code of 103");
            }

        } else {
            // Best effort to clean up server
            tryKillTheAdminServer(domainHome, "admin-server");
            throw new Exception("testDOnlineUpdate failed - cannot bring up server");
        }
    }


    /**
     * testDOnlineUpdate2 check for 104 return code if an update cancel changes.
     * @throws Exception - if any error occurs
     */
    @DisplayName("Test 15: Update JRF domain that requires restart, but cancel changes")
    @Tag("gate")
    @Test
    public void testDOnlineUpdate2(TestInfo testInfo) throws Exception {
        assumeTrue(rcuDomainCreated, "testDOnlineUpdate2 skipped because testDCreateJRFDomainRunRCU failed");

        String domainHome = domainParentDir + FS + "jrfDomain1";
        Path adminServerOut = getTestOutputPath(testInfo).resolve("admin-server.out");
        boolean isServerUp = startAdminServer(domainHome, adminServerOut);

        if (isServerUp) {
            try (PrintWriter out = getTestMethodWriter(testInfo)) {
                Path source = Paths.get(getSampleModelFile("-onlineUpdate2"));
                Path model = getTestOutputPath(testInfo).resolve(SAMPLE_MODEL_FILE_PREFIX + "-onlineUpdate2.yaml");
                Files.copy(source, model, StandardCopyOption.REPLACE_EXISTING);

                String cmd = "echo welcome1 | "
                    + updateDomainScript
                    + " -oracle_home " + mwhome_12213
                    + " -domain_home " + domainParentDir + FS + "jrfDomain1"
                    + " -model_file " + model
                    + " -admin_url t3://localhost:7001 -admin_user weblogic"
                    + " -cancel_changes_if_restart_required";
                CommandResult result = Runner.run(cmd, getTestMethodEnvironment(testInfo), out);

                stopAdminServer(domainHome);
                assertEquals(104, result.exitValue(), "onlineUpdate2 is expecting return code of 104");
            }
        } else {
            // Best effort to clean up server
            tryKillTheAdminServer(domainHome, "admin-server");
            throw new Exception("testDOnlineUpdate2 failed - cannot bring up WLS server");
        }
    }


    /**
     * test createDomain.sh, create restrictedJRF domain
     * @throws Exception - if any error occurs
     */
    @DisplayName("Test 16: create restricted JRF domain")
    @Tag("gate")
    @Test
    public void testECreateRestrictedJRFDomain(TestInfo testInfo) throws Exception {
        String cmd = createDomainScript + " -oracle_home " + mwhome_12213 + " -domain_home " +
            domainParentDir + FS + "restrictedJRFD1 -model_file " +
                getSampleModelFile("-constant") + " -archive_file " + getSampleArchiveFile() +
                " -domain_type RestrictedJRF";
        try (PrintWriter out = getTestMethodWriter(testInfo)) {
            CommandResult result = Runner.run(cmd, getTestMethodEnvironment(testInfo), out);
            assertEquals(0, result.exitValue(), "Unexpected return code");
            // command should fail because of invalid arguments
            assertTrue(result.stdout().contains("createDomain.sh completed successfully"), "Create failed");
        }
    }

    /**
     * test discoverDomain.sh with required arguments
     * @throws Exception - if any error occurs
     */
    @DisplayName("Test 17: Discover domain restrictedJRFD1")
    @Tag("gate")
    @Test
    public void testFDiscoverDomainWithRequiredArgument(TestInfo testInfo) throws Exception {
        try (PrintWriter out = getTestMethodWriter(testInfo)) {
            Path discoveredArchive = getTestOutputPath(testInfo).resolve("discoveredArchive.zip");
            String cmd = discoverDomainScript
                + " -oracle_home " + mwhome_12213
                + " -domain_home " + domainParentDir + FS + "restrictedJRFD1"
                + " -archive_file " + discoveredArchive
                + " -domain_type RestrictedJRF";
            CommandResult result = Runner.run(cmd, getTestMethodEnvironment(testInfo), out);

            verifyResult(result, "discoverDomain.sh completed successfully");

            // unzip discoveredArchive.zip
            cmd = "unzip -o " + discoveredArchive + " -d " + getTestOutputPath(testInfo);
            Runner.run(cmd, getTestMethodEnvironment(testInfo), out);

            // verify model file
            Path expectedModelFile = getTestOutputPath(testInfo).resolve("model").resolve("restrictedJRFD1.yaml");
            verifyModelFile(expectedModelFile.toString());
            verifyFDiscoverDomainWithRequiredArgument(expectedModelFile.toString());
        }
    }

    private void verifyFDiscoverDomainWithRequiredArgument(String expectedModelFile) throws Exception {
         List<String> checkContents = new ArrayList<>();
         checkContents.add("domainInfo:");
         checkContents.add("AdminUserName: --FIX ME--");
         checkContents.add("CoherenceClusterSystemResource: defaultCoherenceCluster");
         checkContents.add("PublicAddress: kubernetes");
         checkContents.add("Trust Service Identity Asserter:");
         checkContents.add("appDeployments:");
         checkContents.add("SourcePath: wlsdeploy/applications/simple-app.war");
        verifyModelFileContents(expectedModelFile, checkContents);
    }

    /**
     * test discoverDomain.sh with -model_file argument
     * @throws Exception - if any error occurs
     */
    @DisplayName("Test 18: Discover domain restrictedJRFD1 using model_file arg")
    @Tag("gate")
    @Test
    public void testGDiscoverDomainWithModelFile(TestInfo testInfo) throws Exception {
        Path discoveredArchive = getTestOutputPath(testInfo).resolve("discoveredArchive.zip");
        Path discoveredModelFile = getTestOutputPath(testInfo).resolve("discoveredRestrictedJRFD1.yaml");
        String cmd = discoverDomainScript + " -oracle_home " + mwhome_12213 + " -domain_home " +
            domainParentDir + FS + "restrictedJRFD1 -archive_file " + discoveredArchive +
                " -model_file " + discoveredModelFile;
        try (PrintWriter out = getTestMethodWriter(testInfo)) {
            CommandResult result = Runner.run(cmd, getTestMethodEnvironment(testInfo), out);

            verifyResult(result, "discoverDomain.sh completed successfully");

            // verify model file
            verifyModelFile(discoveredModelFile.toString());
        }
    }

  /**
   * test discoverDomain.sh with -variable_file argument
   * @throws Exception - if any error occurs
   */
  @DisplayName("Test 19: Discover domain restrictedJRFD1 using variable file")
  @Tag("gate")
  @Test
  public void testGDiscoverDomainWithVariableFile(TestInfo testInfo) throws Exception {
      Path discoveredArchive = getTestOutputPath(testInfo).resolve("discoveredArchive.zip");
      Path discoveredModelFile = getTestOutputPath(testInfo).resolve("discoveredRestrictedJRFD1.yaml");
      Path discoveredVariableFile = getTestOutputPath(testInfo).resolve("discoveredRestrictedJRFD1.properties");

      String cmd = discoverDomainScript
          + " -oracle_home " + mwhome_12213
          + " -domain_home " + domainParentDir + FS + "restrictedJRFD1"
          + " -archive_file " + discoveredArchive
          + " -model_file " + discoveredModelFile
          + " -variable_file " + discoveredVariableFile;

      try (PrintWriter out = getTestMethodWriter(testInfo)) {
          CommandResult result = Runner.run(cmd, getTestMethodEnvironment(testInfo), out);
          verifyResult(result, "discoverDomain.sh completed successfully");

          // verify model file and variable file
          verifyModelFile(discoveredModelFile.toString());
          verifyModelFile(discoveredVariableFile.toString());
          verifyGDiscoverDomainWithVariableFile(discoveredModelFile.toString());
      }
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
    @DisplayName("Test 20: Discover domain domain_type JRF")
    @Tag("gate")
    @Test
    public void testHDiscoverDomainJRFDomainType(TestInfo testInfo) throws Exception {
        try (PrintWriter out = getTestMethodWriter(testInfo)) {
            Path discoveredArchive = getTestOutputPath(testInfo).resolve("discoveredArchive.zip");
            Path discoveredModelFile = getTestOutputPath(testInfo).resolve("discoveredJRFD1.yaml");
            String cmd = discoverDomainScript
                + " -oracle_home " + mwhome_12213
                + " -domain_home " + domainParentDir + FS + "jrfDomain1"
                + " -archive_file " + discoveredArchive
                + " -model_file " + discoveredModelFile
                + " -domain_type JRF";

            CommandResult result = Runner.run(cmd, getTestMethodEnvironment(testInfo), out);

            verifyResult(result, "discoverDomain.sh completed successfully");

            // verify model file
            verifyModelFile(discoveredModelFile.toString());
            verifyHDiscoverDomainJRFDomainType(discoveredModelFile.toString());
        }
    }

    private void verifyHDiscoverDomainJRFDomainType(String expectedModelFile) {
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
    @DisplayName("Test 21: Update domain dynamic server count")
    @Tag("gate")
    @Test
    public void testIUpdateDomain(TestInfo testInfo) throws Exception {
        try (PrintWriter out = getTestMethodWriter(testInfo)) {
            Path source = Paths.get(getSampleVariableFile());
            Path variableFile = getTestOutputPath(testInfo).resolve(SAMPLE_VARIABLE_FILE);

            replaceStringInFile(source, variableFile, "CONFIGURED_MANAGED_SERVER_COUNT=2",
                "CONFIGURED_MANAGED_SERVER_COUNT=4");

            String cmd = updateDomainScript
                + " -oracle_home " + mwhome_12213
                + " -domain_home " + domainParentDir + FS + "domain2"
                + " -model_file " + getSampleModelFile("1")
                + " -archive_file " + getSampleArchiveFile()
                + " -domain_type WLS"
                + " -variable_file " + variableFile;

            CommandResult result = Runner.run(cmd, getTestMethodEnvironment(testInfo), out);
            verifyResult(result, "updateDomain.sh completed successfully");

            // Expecting grep return code of 0.  Grep will return 0 if found, and 1 if the requested text is not found.
            cmd = "grep -q '<max-dynamic-cluster-size>4</max-dynamic-cluster-size>' " + domainParentDir + FS +
                "domain2" + FS + "config" + FS + "config.xml";
            CommandResult result2 = Runner.run(cmd, getTestMethodEnvironment(testInfo), out);
            assertEquals(0, result2.exitValue(), "config.xml does not appear to reflect the update");
        }
    }

    /**
     * Test deployApp with missing model in archive.
     * Negative test, expects error message.
     * @throws Exception - if any error occurs
     */
    @DisplayName("Test 22: Deploy App negative test")
    @Tag("gate")
    @Test
    public void testJDeployAppWithoutModelfile(TestInfo testInfo) throws Exception {
        try (PrintWriter out = getTestMethodWriter(testInfo)) {
            String cmd = deployAppScript
                + " -oracle_home " + mwhome_12213
                + " -domain_home " + domainParentDir + FS + "domain2"
                + " -archive_file " + getSampleArchiveFile();
            CommandResult result = Runner.run(cmd, getTestMethodEnvironment(testInfo), out);
            verifyErrorMsg(result, "deployApps failed to find a model file in archive");
        }
    }

    /**
     * Test deployApps.
     * @throws Exception - if any error occurs
     */
    @DisplayName("Test 22: Deploy App")
    @Tag("gate")
    @Test
    public void testKDeployAppWithModelfile(TestInfo testInfo) throws Exception {
        try (PrintWriter out = getTestMethodWriter(testInfo)) {
            String cmd = deployAppScript
                + " -oracle_home " + mwhome_12213
                + " -domain_home " + domainParentDir + FS + "domain2"
                + " -archive_file " + getSampleArchiveFile()
                + " -model_file " + getSampleModelFile("-constant");
            CommandResult result = Runner.run(cmd, getTestMethodEnvironment(testInfo), out);
            verifyResult(result, "deployApps.sh completed successfully");
        }
    }

    /**
     * test validateModel.sh with -oracle_home only
     * @throws Exception - if any error occurs
     */
    @DisplayName("Test 23: Validate model negative (no model)")
    @Tag("gate")
    @Test
    public void testLValidateModelWithOracleHomeOnly(TestInfo testInfo) throws Exception {
        try (PrintWriter out = getTestMethodWriter(testInfo)) {
            String cmd = validateModelScript + " -oracle_home " + mwhome_12213;
            CommandResult result = Runner.run(cmd, getTestMethodEnvironment(testInfo), out);
            verifyErrorMsg(result, "validateModel requires a model file to run");
        }
    }

    /**
     * test validateModel.sh with -oracle_home and -model_file
     * @throws Exception - if any error occurs
     */
    @DisplayName("Test 24: Validate model negative (no archive)")
    @Tag("gate")
    @Test
    public void testMValidateModelWithOracleHomeModelFile(TestInfo testInfo) throws Exception {
        try (PrintWriter out = getTestMethodWriter(testInfo)) {
            String cmd = validateModelScript + " -oracle_home " + mwhome_12213 + " -model_file " +
                getSampleModelFile("-constant");
            CommandResult result = Runner.run(cmd, getTestMethodEnvironment(testInfo), out);
            verifyResult(result, "the archive file was not provided");
        }
    }

    /**
     * test validateModel.sh without -variable_file
     * @throws Exception - if any error occurs
     */
    @DisplayName("Test 25: Validate model negative (no variable file)")
    @Tag("gate")
    @Test
    public void testNValidateModelWithoutVariableFile(TestInfo testInfo) throws Exception {
        try (PrintWriter out = getTestMethodWriter(testInfo)) {
            String cmd = validateModelScript
                + " -oracle_home " + mwhome_12213
                + " -model_file " + getSampleModelFile("1");
            CommandResult result = Runner.run(cmd, getTestMethodEnvironment(testInfo), out);
            verifyErrorMsg(result, ", but no variables file was specified");
        }
    }

    /**
     * test compareModel.sh with only attribute difference.  The files existences test whether it impacts WKO operation
     * @throws Exception - if any error occurs
     */
    @DisplayName("Test 26: Compare model")
    @Tag("gate")
    @Test
    public void testCompareModelRemoveAttribute(TestInfo testInfo) throws Exception {
        try (PrintWriter out = getTestMethodWriter(testInfo)) {
            Path outputDir = getTestOutputPath(testInfo).resolve("wdt_temp_output");
            Files.createDirectories(outputDir);
            String cmd = compareModelScript
                + " -oracle_home " + mwhome_12213
                + " -output_dir " + outputDir
                + " " + getSampleModelFile("1-lessattribute")
                + " " + getSampleModelFile("1");
            CommandResult result = Runner.run(cmd, getTestMethodEnvironment(testInfo), out);
            verifyResult(result, "compareModel.sh completed successfully");

            verifyFileExists(outputDir.resolve("compare_model_stdout").toString());
            verifyFileDoesNotExists(outputDir.resolve("diffed_model.yaml").toString());
        }
    }

    /**
     * test validateModel.sh with invalid model file
     * @throws Exception - if any error occurs
     */
    @DisplayName("Test 27: Validate model negative (invalid model)")
    @Tag("gate")
    @Test
    public void testOValidateModelWithInvalidModelfile(TestInfo testInfo) throws Exception {
        try (PrintWriter out = getTestMethodWriter(testInfo)) {
            String cmd = validateModelScript
                + " -oracle_home " + mwhome_12213
                + " -model_file " + getSampleModelFile("-invalid")
                + " -variable_file " + getSampleVariableFile();
            CommandResult result = Runner.run(cmd, getTestMethodEnvironment(testInfo), out);
            verifyErrorMsg(result, "exit code = 2");
        }
    }

    @DisplayName("Test 28: Encrypt model")
    @Tag("gate")
    @Test
    public void testPEncryptModel(TestInfo testInfo) throws Exception {
        try (PrintWriter out = getTestMethodWriter(testInfo)) {
            Path source = Paths.get(getSampleModelFile("-constant"));
            Path model = getTestOutputPath(testInfo).resolve(SAMPLE_MODEL_FILE_PREFIX + "-constant.yaml");
            Files.copy(source, model, StandardCopyOption.REPLACE_EXISTING);

            String cmd = encryptModelScript
                + " -oracle_home " + mwhome_12213
                + " -model_file " + model + " < " + getResourcePath().resolve("passphrase.txt");
            CommandResult result = Runner.run(cmd, getTestMethodEnvironment(testInfo), out);
            verifyResult(result, "encryptModel.sh completed successfully");

            // create the domain using -use_encryption
            cmd = createDomainScript
                + " -oracle_home " + mwhome_12213
                + " -domain_home " + domainParentDir + FS + "domain10"
                + " -model_file " + model
                + " -archive_file " + getSampleArchiveFile()
                + " -domain_type WLS"
                + " -use_encryption < " + getResourcePath().resolve("passphrase.txt");
            CommandResult result2 = Runner.run(cmd, getTestMethodEnvironment(testInfo), out);
            verifyResult(result2, "createDomain.sh completed successfully");
        }
    }

    private boolean startAdminServer(String domainHome, Path outputFile) throws Exception {
        boolean isServerUp = false;
        String cmd = "nohup " + domainHome + "/bin/startWebLogic.sh > " + outputFile + " 2>&1 &";

        CommandResult result = Runner.run(cmd);
        if (result.exitValue() != 0 ) {
            logger.info("startAdminServer: result.stdout=" + result.stdout());
            cmd = "cat " + outputFile;
            result = Runner.run(cmd);
            logger.info(result.stdout());
            throw new Exception("startAdminServer: failed to execute command " + cmd);
        }

        try {
            Thread.sleep(60000);
            String readinessCmd = "export no_proxy=localhost && curl -sw '%{http_code}' http://localhost:7001/weblogic/ready";
            result = Runner.run(readinessCmd);
            for (int i=0; i < 60; i++) {
                String stdout = result.stdout();
                if (stdout != null && stdout.length() > 3) {
                    stdout = stdout.substring(0,3);
                }
                logger.info("Server status: '" + stdout + "'");
                if ("200".equals(stdout)) {
                    logger.info("Server is running");
                    isServerUp = true;
                    break;
                }
                Thread.sleep(5000);
                result = Runner.run(readinessCmd);
                logger.info("Server is starting...");
            }

        } catch (InterruptedException ite) {
            Thread.currentThread().interrupt();
            throw ite;
        }

        if (!isServerUp) {
            cmd = "cat " + outputFile;
            result = Runner.run(cmd);
            logger.info(result.stdout());
        }

        return isServerUp;
    }

    private void stopAdminServer(String domainHome) throws Exception {
        logger.info("Stopping the WebLogic admin server");
        String cmd = domainHome + "/bin/stopWebLogic.sh";
        CommandResult result = Runner.run(cmd);
        if (result.exitValue() != 0) {
            logger.info("Stop WLS FAILED. stdout=" + result.stdout());
            tryKillTheAdminServer(domainHome, "admin-server");
        }
    }

    private void setUpBootProperties(String domainHome, String server, String username, String password)
        throws Exception {

        File adminSecurityDir = new File(domainHome + FS + "servers" + FS + server + FS + "security");
        adminSecurityDir.mkdirs();
        try (PrintWriter pw = new PrintWriter(adminSecurityDir + FS + "boot.properties")) {
            pw.println("username=" + username);
            pw.println("password=" + password);
        }
    }

    private void tryKillTheAdminServer(String domainHome, String server) throws Exception {

        File domainDir = new File(domainHome);

        String cmd_format = "ps axww | " +
            "grep weblogic.Server | " +
            "grep \"%s\" | " +
            "grep \"\\-DINSTANCE_HOME=%s\" | " +
            "cut -f1 -d' '";
        CommandResult result = Runner.run(String.format(cmd_format, server, domainDir.getCanonicalPath()));
        logger.info("DEBUG: process id is [" + result.stdout() + "]");
        String pid = result.stdout();
        if (! "".equals(pid)) {
            try {
                Integer.parseInt(pid);
            } catch (NumberFormatException ne) {
                logger.info("ps does not return integer " + pid);
                return;
            }
        String cmd = "kill -9 " + pid;
        result = Runner.run(cmd);
        logger.info("DEBUG: " + cmd + " returns " + result.stdout());
        }

    }
}
