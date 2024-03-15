/*
 * Copyright (c) 2019, 2024, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
*/

package oracle.weblogic.deploy.integration;

import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.OutputStreamWriter;
import java.io.PrintWriter;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.file.FileSystems;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardCopyOption;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.jar.Attributes;
import java.util.jar.JarFile;
import java.util.jar.Manifest;
import java.util.logging.Logger;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import oracle.weblogic.deploy.integration.annotations.IntegrationTest;
import oracle.weblogic.deploy.integration.annotations.TestingLogger;
import oracle.weblogic.deploy.integration.utils.CommandResult;
import oracle.weblogic.deploy.integration.utils.Runner;
import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.MethodOrderer;
import org.junit.jupiter.api.Order;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestInfo;
import org.junit.jupiter.api.TestMethodOrder;

import static org.junit.jupiter.api.Assertions.*;
import static org.junit.jupiter.api.Assumptions.assumeTrue;

@IntegrationTest
@TestMethodOrder(MethodOrderer.OrderAnnotation.class)
public class ITWdt extends BaseTest {
    @TestingLogger
    private static final Logger logger = Logger.getLogger("integration.tests");

    private static final String BASE_REST_URL = "http://localhost:7001/MyWebServicesApp/api/test";
    private static final String REST_PLAN_URL_STRING = BASE_REST_URL + "/plan";
    private static final String REST_OVERRIDES_URL_TEMPLATE = BASE_REST_URL + "/overrides/%s/property1";

    private static boolean rcuDomainCreated = false;

    private static boolean test11DomainCreated = false;

    private static boolean discover17DomainCreated = false;

    private static boolean discover33DomainCreated = false;

    @BeforeAll
    public static void staticPrepare() throws Exception {
        logger.info("prepare for WDT testing ...");

        initialize();
        // clean up the env first
        cleanup();

        // setup the test environment
        setup();

        if (!SKIP_JRF_TESTS) {
            // verify that Docker works inside the container...
            verifyDockerWorks();

            // pull Oracle DB image for FMW RCU testing
            pullOracleDBDockerImage();
            // create a db container for RCU
            createDBContainer();
        }
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
        Path outputPath = Paths.get("target", "test-output", methodName).normalize();
        if (!Files.exists(outputPath)) {
            Files.createDirectories(outputPath);
        }
        return outputPath;
    }

    private static Map<String, String> getTestMethodEnvironment(TestInfo testInfo) throws IOException {
        Map<String, String> env = new HashMap<>();
        env.put("WLSDEPLOY_LOG_DIRECTORY", getTestOutputPath(testInfo).toString());
        return env;
    }

    private static PrintWriter getTestMethodWriter(TestInfo testInfo) throws IOException {
        return getTestMethodWriter(testInfo, "");
    }

    private static PrintWriter getTestMethodWriter(TestInfo testInfo, String suffixName) throws IOException {
        if (!testInfo.getTestMethod().isPresent()) {
            throw new IllegalArgumentException("Method is not present in this context, and this method cannot be used");
        }

        String methodName = testInfo.getTestMethod().get().getName();
        // create a output file in the build folder with the name {test method name}.stdout
        Path outputPath = getTestOutputPath(testInfo);
        logger.info("Test log: " + outputPath);
        return new PrintWriter(
            new BufferedWriter(new OutputStreamWriter(
                new FileOutputStream(outputPath.resolve(Paths.get(methodName +
                    suffixName + ".out")).toString()))), true);
    }

    /**
     * test createDomain.sh with only -oracle_home argument
     *
     * @throws Exception - if any error occurs
     */
    @DisplayName("Test 1: createDomain bad arguments")
    @Order(1)
    @Tag("gate")
    @Test
    void test01CreateDomainNoDomainHome(TestInfo testInfo) throws Exception {
        String cmd = createDomainScript + " -oracle_home " + mwhome_12213;
        try (PrintWriter out = getTestMethodWriter(testInfo)) {
            CommandResult result = Runner.run(cmd, getTestMethodEnvironment(testInfo), out);
            assertEquals(99, result.exitValue(), "Unexpected return code");
            assertTrue(result.stdout().contains("WLSDPLY-20008"), "Output did not contain expected WLSDPLY-20008");
        }
    }

    /**
     * test createDomain.sh with only -oracle_home and -domain_type arguments
     *
     * @throws Exception - if any error occurs
     */
    @DisplayName("Test 2: createDomain bad arguments")
    @Order(2)
    @Tag("gate")
    @Test
    void test02CreateDomainNoDomainHome(TestInfo testInfo) throws Exception {
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
     *
     * @throws Exception - if any error occurs
     */
    @DisplayName("Test 3: createDomain bad arguments")
    @Order(3)
    @Tag("gate")
    @Test
    void test03CreateDomainNoModelfile(TestInfo testInfo) throws Exception {
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
     *
     * @throws Exception - if output file could not be created or written
     */
    @DisplayName("Test 4: createDomain without archive file")
    @Order(4)
    @Tag("gate")
    @Test
    void test04CreateDomainNoArchivefile(TestInfo testInfo) throws Exception {
        String cmd = createDomainScript + " -oracle_home " + mwhome_12213 + " -domain_parent " + domainParentDir +
            " -model_file " + getSampleModelFile("-constant");
        try (PrintWriter out = getTestMethodWriter(testInfo)) {
            CommandResult result = Runner.run(cmd, getTestMethodEnvironment(testInfo), out);
            assertEquals(2, result.exitValue(), "Unexpected return code");
            // command should fail because of invalid arguments
            assertTrue(result.stdout().contains("WLSDPLY-05025"), "Output did not contain expected WLSDPLY-05025");
        }
    }

    /**
     * test createDomain.sh with required arguments using simple-topology-constant.yaml (domain = domain1)
     *
     * @throws Exception - if any error occurs
     */
    @DisplayName("Test 5: createDomain with domain_parent")
    @Order(5)
    @Tag("gate")
    @Test
    void test05CreateDomain(TestInfo testInfo) throws Exception {
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
     * test createDomain.sh using simple-topology-constant.yaml with different domain name in
     * -domain_home and model file in model file, it specifies the domain name as 'domain1'
     * in -domain_home argument, it specifies the domain home as 'domain2'
     *
     * @throws Exception - if any error occurs
     */
    @DisplayName("Test 6: createDomain with domain_home")
    @Order(6)
    @Tag("gate")
    @Test
    void test06CreateDomainDifferentDomainName(TestInfo testInfo) throws Exception {
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
     * test createDomain.sh with WLS domain_type using simple-topology-constant.yaml (domain = domain2)
     *
     * @throws Exception -if any error occurs
     */
    @Order(7)
    @Tag("gate")
    @Test
    void test07CreateDomainWLSType(TestInfo testInfo) throws Exception {
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
     *
     * @throws Exception - if any error occurs
     */
    @DisplayName("Test 8: createDomain but needs variable file")
    @Order(8)
    @Tag("gate")
    @Test
    void test08CreateDomainNoVariableFile(TestInfo testInfo) throws Exception {
        String cmd = createDomainScript + " -oracle_home " + mwhome_12213 + " -domain_parent " + domainParentDir +
            " -model_file " + getSampleModelFile("1") +
            " -archive_file " + getSampleArchiveFile();
        try (PrintWriter out = getTestMethodWriter(testInfo)) {
            CommandResult result = Runner.run(cmd, getTestMethodEnvironment(testInfo), out);
            assertEquals(2, result.exitValue(), "Unexpected return code");
            // command should fail because of invalid arguments
            assertTrue(result.stdout().contains("WLSDPLY-20004"), "Output did not contain expected WLSDPLY-20004");
        }
    }

    /**
     * test createDomain.sh with variable_file argument using simple-topology1.yaml (domain = domain2)
     *
     * @throws Exception - if any error occurs
     */
    @DisplayName("Test 9: createDomain with variable file")
    @Order(9)
    @Tag("gate")
    @Test
    void test09CreateDomainWithVariableFile(TestInfo testInfo) throws Exception {
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
     * test createDomain.sh with wlst_path set to mwhome/wlserver using simple-topology1.yaml (domain = domain2)
     *
     * @throws Exception - if any error occurs
     */
    @DisplayName("Test 10: createDomain with WLS wlst_path")
    @Order(10)
    @Tag("gate")
    @Test
    void test10CreateDomainWithWlstPath(TestInfo testInfo) throws Exception {
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
     * test createDomain.sh with -wlst_path set to mwhome/oracle_common using simple-topology1.yaml (domain = domain2)
     *
     * @throws Exception - if any error occurs
     */
    @DisplayName("Test 11: createDomain with oracle_commmon wlst_path")
    @Order(11)
    @Tag("gate")
    @Test
    void test11CreateDomainWithOracleCommonWlstPath(TestInfo testInfo) throws Exception {
        String cmd = createDomainScript + " -oracle_home " + mwhome_12213 + " -domain_home " +
            domainParentDir + FS + "domain2 -model_file " +
            getSampleModelFile("1") + " -archive_file " + getSampleArchiveFile() +
            " -domain_type WLS -variable_file " + getSampleVariableFile() + " -wlst_path " +
            mwhome_12213 + FS + "oracle_common";
        try (PrintWriter out = getTestMethodWriter(testInfo)) {
            CommandResult result = Runner.run(cmd, getTestMethodEnvironment(testInfo), out);
            assertEquals(0, result.exitValue(), "Unexpected return code");
            assertTrue(result.stdout().contains("createDomain.sh completed successfully"), "Create failed");
            test11DomainCreated = true;
        }
    }

    /**
     * test createDomain.sh, create JRF domain without -run_rcu argument
     *
     * @throws Exception - if any error occurs
     */
    @DisplayName("Test 12: createDomain JRF domain without DB")
    @Order(12)
    @Tag("gate")
    @Test
    void test12CreateJRFDomainNoRunRCU(TestInfo testInfo) throws Exception {
        assumeTrue(new JrfChecker(), "User specified skipping JRF tests");
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
     *
     * @throws Exception - if any error occurs
     */
    @DisplayName("Test 13: createDomain JRF domain and run RCU")
    @Order(13)
    @Tag("gate")
    @Test
    void test13CreateJRFDomainRunRCU(TestInfo testInfo) throws Exception {
        assumeTrue(new JrfChecker(), "User specified skipping JRF tests");
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
     *
     * @throws Exception - if any error occurs
     */
    @DisplayName("Test 14: Update JRF domain that requires restart")
    @Order(14)
    @Tag("gate")
    @Test
    void test14OnlineUpdate1(TestInfo testInfo) throws Exception {
        assumeTrue(new JrfChecker(), "User specified skipping JRF tests");
        assumeTrue(rcuDomainCreated, "testDOnlineUpdate skipped because testDCreateJRFDomainRunRCU failed");

        // Setup boot.properties
        // domainParent12213  - is relative !
        String domainHome = domainParentDir + FS + "jrfDomain1";
        setUpBootProperties(domainHome, "admin-server", "weblogic", "welcome1");
        Path adminServerOut = getTestOutputPath(testInfo).resolve("admin-server.out");
        boolean isServerUp = startAdminServer(domainHome, adminServerOut);

        if (isServerUp) {
            try {
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
                        + " -domain_type JRF"
                        + " -admin_url t3://localhost:7001 -admin_user weblogic";
                    CommandResult result = Runner.run(cmd, getTestMethodEnvironment(testInfo), out);
                    assertEquals(103, result.exitValue(), "onlineUpdate is expecting return code of 103");
                }
            } finally {
                stopAdminServer(domainHome);
            }
        } else {
            // Best effort to clean up server
            tryKillTheAdminServer(domainHome, "admin-server");
            throw new Exception("testDOnlineUpdate failed - cannot bring up server");
        }
    }


    /**
     * testDOnlineUpdate2 check for 104 return code if an update cancel changes.
     *
     * @throws Exception - if any error occurs
     */
    @DisplayName("Test 15: Update JRF domain that requires restart, but cancel changes")
    @Order(15)
    @Tag("gate")
    @Test
    void test15OnlineUpdate2(TestInfo testInfo) throws Exception {
        assumeTrue(new JrfChecker(), "User specified skipping JRF tests");
        assumeTrue(rcuDomainCreated, "testDOnlineUpdate2 skipped because testDCreateJRFDomainRunRCU failed");

        String domainHome = domainParentDir + FS + "jrfDomain1";
        Path adminServerOut = getTestOutputPath(testInfo).resolve("admin-server.out");
        boolean isServerUp = startAdminServer(domainHome, adminServerOut);
        if (isServerUp) {
            try {
                try (PrintWriter out = getTestMethodWriter(testInfo)) {
                    Path source = Paths.get(getSampleModelFile("-onlineUpdate2"));
                    Path model = getTestOutputPath(testInfo).resolve(SAMPLE_MODEL_FILE_PREFIX + "-onlineUpdate2.yaml");
                    Files.copy(source, model, StandardCopyOption.REPLACE_EXISTING);

                    String cmd = "echo welcome1 | "
                        + updateDomainScript
                        + " -oracle_home " + mwhome_12213
                        + " -domain_home " + domainParentDir + FS + "jrfDomain1"
                        + " -model_file " + model
                        + " -domain_type JRF"
                        + " -admin_url t3://localhost:7001 -admin_user weblogic"
                        + " -cancel_changes_if_restart_required";
                    CommandResult result = Runner.run(cmd, getTestMethodEnvironment(testInfo), out);
                    assertEquals(104, result.exitValue(), "onlineUpdate2 is expecting return code of 104");
                }
            } finally {
                stopAdminServer(domainHome);
            }
        } else {
            // Best effort to clean up server
            tryKillTheAdminServer(domainHome, "admin-server");
            throw new Exception("testDOnlineUpdate2 failed - cannot bring up WLS server");
        }
    }


    /**
     * test createDomain.sh, create restrictedJRF domain
     *
     * @throws Exception - if any error occurs
     */
    @DisplayName("Test 16: create restricted JRF domain")
    @Order(16)
    @Tag("gate")
    @Test
    void test16CreateRestrictedJRFDomain(TestInfo testInfo) throws Exception {
        assumeTrue(new RestrictedJrfChecker(), "User specified skipping Restricted JRF tests");
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
     *
     * @throws Exception - if any error occurs
     */
    @DisplayName("Test 17: Discover domain restrictedJRFD1")
    @Order(17)
    @Tag("gate")
    @Test
    void test17DiscoverDomainWithRequiredArgument(TestInfo testInfo) throws Exception {
        assumeTrue(new RestrictedJrfChecker(), "User specified skipping Restricted JRF tests");
        String cmd = createDomainScript + " -oracle_home " + mwhome_12213 + " -domain_home " +
            domainParentDir + FS + "restrictedJRFD1-discover17-18-19 -model_file " +
            getSampleModelFile("-constant") + " -archive_file " + getSampleArchiveFile() +
            " -domain_type RestrictedJRF";
        try (PrintWriter out = getTestMethodWriter(testInfo, "CreateDomain")) {
            CommandResult result = Runner.run(cmd, getTestMethodEnvironment(testInfo), out);
            assertEquals(0, result.exitValue(), "Unexpected return code");
            discover17DomainCreated = true;
        }

        try (PrintWriter out = getTestMethodWriter(testInfo, "DiscoverDomain")) {
            Path discoveredModel = getTestOutputPath(testInfo).resolve("discoveredModel.yaml");
            Path discoveredArchive = getTestOutputPath(testInfo).resolve("discoveredArchive.zip");
            cmd = discoverDomainScript
                + " -oracle_home " + mwhome_12213
                + " -domain_home " + domainParentDir + FS + "restrictedJRFD1-discover17-18-19"
                + " -model_file " + discoveredModel
                + " -archive_file " + discoveredArchive
                + " -domain_type RestrictedJRF";
            CommandResult result = Runner.run(cmd, getTestMethodEnvironment(testInfo), out);
            // SecurityConfiguration warning
            assertEquals(0, result.exitValue(), "Unexpected return code");

            // verify model file
            verifyModelFile(discoveredModel.toString());
            verifyDiscoverDomainWithRequiredArgument(discoveredModel.toString());
        }
    }

    private void verifyDiscoverDomainWithRequiredArgument(String expectedModelFile) throws Exception {
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
     *
     * @throws Exception - if any error occurs
     */
    @DisplayName("Test 18: Discover domain restrictedJRFD1 using model_file arg")
    @Order(18)
    @Tag("gate")
    @Test
    void test18DiscoverDomainWithModelFile(TestInfo testInfo) throws Exception {
        assumeTrue(new RestrictedJrfChecker(), "User specified skipping Restricted JRF tests");
        assertTrue(discover17DomainCreated, "Domain not created cannot run test");

        Path discoveredArchive = getTestOutputPath(testInfo).resolve("discoveredArchive.zip");
        Path discoveredModelFile = getTestOutputPath(testInfo).resolve("discoveredRestrictedJRFD1.yaml");
        String cmd = discoverDomainScript + " -oracle_home " + mwhome_12213 + " -domain_home " +
            domainParentDir + FS + "restrictedJRFD1-discover17-18-19 -archive_file " + discoveredArchive +
            " -model_file " + discoveredModelFile;
        try (PrintWriter out = getTestMethodWriter(testInfo)) {
            CommandResult result = Runner.run(cmd, getTestMethodEnvironment(testInfo), out);
            // SecurityConfiguration warning
            assertEquals(0, result.exitValue(), "Unexpected return code");

            // verify model file
            verifyModelFile(discoveredModelFile.toString());
        }
    }

    /**
     * test discoverDomain.sh with -variable_file argument
     *
     * @throws Exception - if any error occurs
     */
    @DisplayName("Test 19: Discover domain restrictedJRFD1 using variable file")
    @Order(19)
    @Tag("gate")
    @Test
    void test19DiscoverDomainWithVariableFile(TestInfo testInfo) throws Exception {
        assumeTrue(new JrfChecker(), "User specified skipping JRF tests");
        assertTrue(discover17DomainCreated, "Domain not created and cannot be discovered");
        Path discoveredArchive = getTestOutputPath(testInfo).resolve("discoveredArchive.zip");
        Path discoveredModelFile = getTestOutputPath(testInfo).resolve("discoveredRestrictedJRFD1.yaml");
        Path discoveredVariableFile = getTestOutputPath(testInfo).resolve("discoveredRestrictedJRFD1.properties");

        String cmd = discoverDomainScript
            + " -oracle_home " + mwhome_12213
            + " -domain_home " + domainParentDir + FS + "restrictedJRFD1-discover17-18-19"
            + " -archive_file " + discoveredArchive
            + " -model_file " + discoveredModelFile
            + " -variable_file " + discoveredVariableFile;

        try (PrintWriter out = getTestMethodWriter(testInfo)) {
            CommandResult result = Runner.run(cmd, getTestMethodEnvironment(testInfo), out);
            // SecurityConfiguration warning
            assertEquals(0, result.exitValue(), "Unexpected return code");

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
     *
     * @throws Exception - if any error occurs
     */
    @DisplayName("Test 20: Discover domain domain_type JRF")
    @Order(20)
    @Tag("gate")
    @Test
    void test20DiscoverDomainJRFDomainType(TestInfo testInfo) throws Exception {
        assumeTrue(new JrfChecker(), "User specified skipping JRF tests");
        waitForDatabase();
        try (PrintWriter out = getTestMethodWriter(testInfo, "CreateDomain")) {
            Path source = Paths.get(getSampleModelFile("2"));
            Path modelOut = getTestOutputPath(testInfo).resolve(SAMPLE_MODEL_FILE_PREFIX + "2.yaml");
            // create wdt model file to use in create, after substitution of DB host/ip
            replaceStringInFile(source, modelOut, "%DB_HOST%", getDBContainerIP());

            String cmd = createDomainScript + " -oracle_home " + mwhome_12213 + " -domain_home " +
                domainParentDir + FS + "jrfDomain1-discover20 -model_file " +
                modelOut + " -archive_file " + getSampleArchiveFile() + " -domain_type JRF -run_rcu";

            CommandResult result = Runner.run(cmd, getTestMethodEnvironment(testInfo), out);
            assertEquals(0, result.exitValue(), "Unexpected return code");
        }
        try (PrintWriter out = getTestMethodWriter(testInfo, "DiscoverDomain")) {
            Path discoveredArchive = getTestOutputPath(testInfo).resolve("discoveredArchive.zip");
            Path discoveredModelFile = getTestOutputPath(testInfo).resolve("discoveredJRFD1.yaml");
            String cmd = discoverDomainScript
                + " -oracle_home " + mwhome_12213
                + " -domain_home " + domainParentDir + FS + "jrfDomain1-discover20"
                + " -archive_file " + discoveredArchive
                + " -model_file " + discoveredModelFile
                + " -domain_type JRF";

            CommandResult result = Runner.run(cmd, getTestMethodEnvironment(testInfo), out);
            // SecurityConfiguration warning
            assertEquals(0, result.exitValue(), "Unexpected return code");

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
     *
     * @throws Exception - if any error occurs
     */
    @DisplayName("Test 21: Update domain dynamic server count")
    @Order(21)
    @Tag("gate")
    @Test
    void test21UpdateDomain(TestInfo testInfo) throws Exception {
        assumeTrue(test11DomainCreated, "Skipping test 21 because dependent domain was not created");
        try (PrintWriter out = getTestMethodWriter(testInfo, "UpdateDomain")) {
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
        }
        try (PrintWriter out = getTestMethodWriter(testInfo, "GrepResults")) {
            // Expecting grep return code of 0.  Grep will return 0 if found, and 1 if the requested text is not found.
            String cmd = "grep -q '<max-dynamic-cluster-size>4</max-dynamic-cluster-size>' " + domainParentDir + FS +
                "domain2" + FS + "config" + FS + "config.xml";
            CommandResult result2 = Runner.run(cmd, getTestMethodEnvironment(testInfo), out);
            assertEquals(0, result2.exitValue(), "config.xml does not appear to reflect the update");
        }
    }

    /**
     * Test deployApp with missing model in archive.
     * Negative test, expects error message.
     *
     * @throws Exception - if any error occurs
     */
    @DisplayName("Test 22: Deploy App negative test")
    @Order(22)
    @Tag("gate")
    @Test
    void test22DeployAppWithoutModelFile(TestInfo testInfo) throws Exception {
        assumeTrue(test11DomainCreated, "Skipping test 22 because dependent domain was not created");
        try (PrintWriter out = getTestMethodWriter(testInfo)) {
            String cmd = deployAppScript
                + " -oracle_home " + mwhome_12213
                + " -domain_home " + domainParentDir + FS + "domain2"
                + " -archive_file " + getSampleArchiveFile();
            CommandResult result = Runner.run(cmd, getTestMethodEnvironment(testInfo), out);
            verifyErrorMsg(result, "deployApps invoked with missing required argument: -model_file");
        }
    }

    /**
     * Test deployApps.
     *
     * @throws Exception - if any error occurs
     */
    @DisplayName("Test 23: Deploy App")
    @Order(23)
    @Tag("gate")
    @Test
    void test23DeployAppWithModelfile(TestInfo testInfo) throws Exception {
        assumeTrue(test11DomainCreated, "Skipping test 23 because dependent domain was not created");
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
     *
     * @throws Exception - if any error occurs
     */
    @DisplayName("Test 24: Validate model negative (no model)")
    @Order(24)
    @Tag("gate")
    @Test
    void test24ValidateModelWithOracleHomeOnly(TestInfo testInfo) throws Exception {
        try (PrintWriter out = getTestMethodWriter(testInfo)) {
            String cmd = validateModelScript + " -oracle_home " + mwhome_12213;
            CommandResult result = Runner.run(cmd, getTestMethodEnvironment(testInfo), out);
            verifyErrorMsg(result, "validateModel requires a model file to run");
        }
    }

    /**
     * test validateModel.sh with -oracle_home and -model_file
     *
     * @throws Exception - if any error occurs
     */
    @DisplayName("Test 25: Validate model negative (no archive)")
    @Order(25)
    @Tag("gate")
    @Test
    void test25ValidateModelWithOracleHomeModelFile(TestInfo testInfo) throws Exception {
        try (PrintWriter out = getTestMethodWriter(testInfo)) {
            String cmd = validateModelScript + " -oracle_home " + mwhome_12213 + " -model_file " +
                getSampleModelFile("-constant");
            CommandResult result = Runner.run(cmd, getTestMethodEnvironment(testInfo), out);
            verifyErrorMsg(result, "the archive file was not provided");
        }
    }

    /**
     * test validateModel.sh without -variable_file
     *
     * @throws Exception - if any error occurs
     */
    @DisplayName("Test 26: Validate model negative (no variable file)")
    @Order(26)
    @Tag("gate")
    @Test
    void test26ValidateModelWithoutVariableFile(TestInfo testInfo) throws Exception {
        try (PrintWriter out = getTestMethodWriter(testInfo)) {
            String cmd = validateModelScript
                + " -oracle_home " + mwhome_12213
                + " -model_file " + getSampleModelFile("1");
            CommandResult result = Runner.run(cmd, getTestMethodEnvironment(testInfo), out);
            verifyErrorMsg(result, " and no properties file was provided");
        }
    }

    /**
     * test compareModel.sh with only attribute difference.  The files existences test whether it impacts WKO operation
     *
     * @throws Exception - if any error occurs
     */
    @DisplayName("Test 27: Compare model")
    @Order(27)
    @Tag("gate")
    @Test
    void test27CompareModelRemoveAttribute(TestInfo testInfo) throws Exception {
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
     *
     * @throws Exception - if any error occurs
     */
    @DisplayName("Test 28: Validate model negative (invalid model)")
    @Order(28)
    @Tag("gate")
    @Test
    void test28ValidateModelWithInvalidModelfile(TestInfo testInfo) throws Exception {
        try (PrintWriter out = getTestMethodWriter(testInfo)) {
            String cmd = validateModelScript
                + " -oracle_home " + mwhome_12213
                + " -model_file " + getSampleModelFile("-invalid")
                + " -variable_file " + getSampleVariableFile();
            CommandResult result = Runner.run(cmd, getTestMethodEnvironment(testInfo), out);
            verifyErrorMsg(result, "exit code = 2");
        }
    }

    @DisplayName("Test 29: Encrypt model")
    @Order(29)
    @Tag("gate")
    @Test
    void test29EncryptModel(TestInfo testInfo) throws Exception {
        Path source = Paths.get(getSampleModelFile("-constant"));
        Path model = getTestOutputPath(testInfo).resolve(SAMPLE_MODEL_FILE_PREFIX + "-constant.yaml");
        try (PrintWriter out = getTestMethodWriter(testInfo, "EncryptModel")) {
            Files.copy(source, model, StandardCopyOption.REPLACE_EXISTING);

            String cmd = encryptModelScript
                + " -oracle_home " + mwhome_12213
                + " -model_file " + model + " < " + getResourcePath().resolve("passphrase.txt");
            CommandResult result = Runner.run(cmd, getTestMethodEnvironment(testInfo), out);
            verifyResult(result, "encryptModel.sh completed successfully");
        }
        try (PrintWriter out = getTestMethodWriter(testInfo, "CreateDomain")) {
            // create the domain using -use_encryption
            String cmd = createDomainScript
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

    /**
     * test updateDomain.sh online with untargeting, deploy, and app update
     *
     * @throws Exception - if any error occurs
     */
    @DisplayName("Test 30: createDomain and run updateDomain online for application")
    @Order(30)
    @Tag("gate")
    @Test
    void test30OnlineUpdateApp(TestInfo testInfo) throws Exception {
        String domainDir = "domain2-test30";
        String cmd = createDomainScript
            + " -oracle_home " + mwhome_12213
            + " -domain_home " + domainParentDir + FS + domainDir
            + " -model_file " + getSampleModelFile("-onlinebase")
            + " -archive_file " + getSampleArchiveFile();

        try (PrintWriter out = getTestMethodWriter(testInfo, "CreateDomain")) {
            CommandResult result = Runner.run(cmd, getTestMethodEnvironment(testInfo), out);
            assertEquals(0, result.exitValue(), "Unexpected return code");
            assertTrue(result.stdout().contains("createDomain.sh completed successfully"), "Create failed");
        }

        Path source = Paths.get(getSampleModelFile("-untargetapp"));
        Path model = getTestOutputPath(testInfo).resolve(SAMPLE_MODEL_FILE_PREFIX + "-onlineUpdate.yaml");

        String domainHome = domainParentDir + FS + domainDir;
        setUpBootProperties(domainHome, "admin-server", "weblogic", "welcome1");
        Path adminServerOut = getTestOutputPath(testInfo).resolve("admin-server.out");
        boolean isServerUp = startAdminServer(domainHome, adminServerOut);
        if (isServerUp) {
            try {
                try (PrintWriter out = getTestMethodWriter(testInfo, "UpdateDomain-1")) {
                    // update wdt model file
                    Files.copy(source, model, StandardCopyOption.REPLACE_EXISTING);

                    cmd = "echo welcome1 | "
                        + updateDomainScript
                        + " -oracle_home " + mwhome_12213
                        + " -model_file " + model
                        + " -archive_file " + getSampleArchiveFile()
                        + " -admin_url t3://localhost:7001 -admin_user weblogic";
                    CommandResult result = Runner.run(cmd, getTestMethodEnvironment(testInfo), out);

                    moveWDTLogFile(getTestOutputPath(testInfo), "updateDomain.log", "updateDomain-1.log");

                    assertEquals(0, result.exitValue(), "Unexpected return code for untargeting app");
                    assertTrue(result.stdout().contains("<__remove_app_from_deployment> <WLSDPLY-09339>"),
                        "Update does not contains expected message WLSDPLY-09339");
                }
                try (PrintWriter out = getTestMethodWriter(testInfo, "UpdateDomain-2")) {
                    // Check result
                    source = Paths.get(getSampleModelFile("-targetapp"));
                    model = getTestOutputPath(testInfo).resolve(SAMPLE_MODEL_FILE_PREFIX + "-onlineUpdate.yaml");
                    Files.copy(source, model, StandardCopyOption.REPLACE_EXISTING);

                    cmd = "echo welcome1 | "
                        + updateDomainScript
                        + " -oracle_home " + mwhome_12213
                        + " -domain_home " + domainParentDir + FS + domainDir
                        + " -model_file " + model
                        + " -archive_file " + getSampleArchiveFile()
                        + " -admin_url t3://localhost:7001 -admin_user weblogic";
                    CommandResult result = Runner.run(cmd, getTestMethodEnvironment(testInfo), out);

                    moveWDTLogFile(getTestOutputPath(testInfo), "updateDomain.log", "updateDomain-2.log");

                    assertEquals(0, result.exitValue(), "Unexpected return code for targeting app");
                    assertTrue(result.stdout().contains("<__deploy_app_or_library> <WLSDPLY-09316>"),
                        "Update does not contains expected message WLSDPLY-09316");
                    assertTrue(result.stdout().contains("<__start_app> <WLSDPLY-09313>"),
                        "Update does not contains expected message WLSDPLY-09313");
                }
                try (PrintWriter out = getTestMethodWriter(testInfo, "UpdateDomain-online")) {
                    source = Paths.get(getSampleModelFile("-targetapp"));
                    model = getTestOutputPath(testInfo).resolve(SAMPLE_MODEL_FILE_PREFIX + "-onlineUpdate.yaml");
                    Files.copy(source, model, StandardCopyOption.REPLACE_EXISTING);

                    cmd = "echo welcome1 | "
                        + updateDomainScript
                        + " -oracle_home " + mwhome_12213
                        + " -domain_home " + domainParentDir + FS + domainDir
                        + " -model_file " + model
                        + " -archive_file " + getUpdatedSampleArchiveFile()
                        + " -admin_url t3://localhost:7001 -admin_user weblogic";
                    CommandResult result = Runner.run(cmd, getTestMethodEnvironment(testInfo), out);

                    moveWDTLogFile(getTestOutputPath(testInfo), "updateDomain.log", "updateDomain-3.log");

                    assertEquals(0, result.exitValue(), "Unexpected return code for updating domain with new archive");
                    assertTrue(result.stdout().contains("<__stop_app> <WLSDPLY-09312>"),
                        "Update does not contains expected message WLSDPLY-09312");
                    assertTrue(result.stdout().contains("<__undeploy_app> <WLSDPLY-09314>"),
                        "Update does not contains expected message WLSDPLY-09314");
                    assertTrue(result.stdout().contains("<__deploy_app_or_library> <WLSDPLY-09316>"),
                        "Update does not contains expected message WLSDPLY-09316");
                    assertTrue(result.stdout().contains("<__start_app> <WLSDPLY-09313>"),
                        "Update does not contains expected message WLSDPLY-09313");

                    cmd = "echo welcome1 | "
                        + updateDomainScript
                        + " -oracle_home " + mwhome_12213
                        + " -domain_home " + domainParentDir + FS + domainDir
                        + " -model_file " + model
                        + " -remote"
                        + " -archive_file " + getUpdatedSampleArchiveFile()
                        + " -admin_url t3://localhost:7001 -admin_user weblogic";
                    result = Runner.run(cmd, getTestMethodEnvironment(testInfo), out);

                    moveWDTLogFile(getTestOutputPath(testInfo), "updateDomain.log", "updateDomain-4.log");

                    assertEquals(0, result.exitValue(), "Unexpected return code for remote updating domain with new archive");

                    Path sourcePyfile = Paths.get(getResourcePath() + FS + SAMPLE_MODEL_FILE_PREFIX + "-chk-srcpath.py");
                    Path testPyFile = getTestOutputPath(testInfo).resolve(SAMPLE_MODEL_FILE_PREFIX + "-chk-srcpath.py");
                    Files.copy(sourcePyfile, testPyFile, StandardCopyOption.REPLACE_EXISTING);
                    cmd = mwhome_12213 + "/oracle_common/common/bin/wlst.sh " + testPyFile + " " + domainParentDir + FS +
                        domainDir;
                    result = Runner.run(cmd, getTestMethodEnvironment(testInfo), out);
                    assertEquals(0, result.exitValue(), "Unexpected return code for running wlst to find app sourcepath");
                    Pattern pattern = Pattern.compile("SRCPATH=(.*)");
                    Matcher matcher = pattern.matcher(result.stdout());
                    String srcPath = "Unknown";
                    if (matcher.find()) {
                        srcPath = matcher.group(1);
                    }
                    assertTrue(srcPath.equals("servers/admin-server/upload/simple-app/app/simple-app.war"),
                        "App SourcePath returned " + srcPath + " does not match the expected value");
                }
            } finally {
                stopAdminServer(domainHome);
            }
        } else {
            // Best effort to clean up server
            tryKillTheAdminServer(domainHome, "admin-server");
            throw new Exception("testDOnlineUpdate failed - cannot bring up server");
        }
    }

    /**
     * test discoverDomain.sh that model can create a working domain
     *
     * @throws Exception - if any error occurs
     */
    @DisplayName("Test 31: Discover domain and then create a new domain from the model")
    @Order(31)
    @Tag("gate")
    @Test
    void test31DiscoverDomainWithModelFile(TestInfo testInfo) throws Exception {
        String domainDir = "domain2-discover31";
        String cmd = createDomainScript
            + " -oracle_home " + mwhome_12213
            + " -domain_home " + domainParentDir + FS + domainDir
            + " -model_file " + getSampleModelFile("-onlinebase")
            + " -archive_file " + getSampleArchiveFile();

        try (PrintWriter out = getTestMethodWriter(testInfo, "CreateDomain")) {
            CommandResult result = Runner.run(cmd, getTestMethodEnvironment(testInfo), out);

            moveWDTLogFile(getTestOutputPath(testInfo), "createDomain.log", "createDomain-1.log");

            assertEquals(0, result.exitValue(), "Unexpected return code");
        }
        Path discoveredArchive = getTestOutputPath(testInfo).resolve("discoveredArchive.zip");
        Path discoveredModelFile = getTestOutputPath(testInfo).resolve("discoveredModel.yaml");
        Path discoveredVariableFile = getTestOutputPath(testInfo).resolve("discoveredVariable.properties");
        cmd = discoverDomainScript + " -oracle_home " + mwhome_12213 + " -domain_home " +
            domainParentDir + FS + "domain2-discover31 -archive_file " + discoveredArchive +
            " -model_file " + discoveredModelFile + " -variable_file " + discoveredVariableFile;
        try (PrintWriter out = getTestMethodWriter(testInfo, "DiscoverDomain")) {
            CommandResult result = Runner.run(cmd, getTestMethodEnvironment(testInfo), out);

            verifyResult(result, "discoverDomain.sh completed successfully");

            // verify model file
            verifyModelFile(discoveredModelFile.toString());

        }
        try (PrintWriter out = getTestMethodWriter(testInfo, "CreateDomainFromDiscover")) {
            String domainHome = domainParentDir + FS + "createDomainFromDiscover";
            cmd = createDomainScript + " -oracle_home " + mwhome_12213 + " -domain_home " +
                domainHome + " -archive_file " + discoveredArchive +
                " -model_file " + discoveredModelFile + " -variable_file " + getSampleVariableFile();
            CommandResult result = Runner.run(cmd, getTestMethodEnvironment(testInfo), out);

            moveWDTLogFile(getTestOutputPath(testInfo), "createDomain.log", "createDomain-2.log");

            verifyResult(result, "createDomain.sh completed successfully");

            setUpBootProperties(domainHome, "AdminServer", "weblogic", "welcome1");
            Path adminServerOut = getTestOutputPath(testInfo).resolve("AdminServer.out");
            boolean isServerUp = startAdminServer(domainHome, adminServerOut);
            if (!isServerUp) {
                tryKillTheAdminServer(domainHome, "AdminServer");
                throw new Exception("Admin server did not come up after createDomain from discoverDomain");
            }
            stopAdminServer(domainHome);
        }
    }

    /**
     * test prepareModel.sh with -target as wko
     *
     * @throws Exception - if any error occurs
     */
    @DisplayName("Test 32: Prepare model")
    @Order(32)
    @Tag("gate")
    @Test
    void test32PrepareModel(TestInfo testInfo) throws Exception {

        Path outputFiles = getTestOutputPath(testInfo);
        try (PrintWriter out = getTestMethodWriter(testInfo, "PrepareModel")) {
            String wkoModelFile = getSampleModelFile("-targetwko");
            String cmd = prepareModelScript
                + " -oracle_home " + mwhome_12213
                + " -output_dir " + outputFiles
                + " -model_file " + wkoModelFile
                + " -target " + "wko";

            CommandResult result = Runner.run(cmd, getTestMethodEnvironment(testInfo), out);
            // ListenPort differences warning
            assertEquals(1, result.exitValue(), "Unexpected return code");
        }
        try (PrintWriter out = getTestMethodWriter(testInfo, "GrepResults")) {
            // verify model file
            String tempWkoModel = outputFiles + FS + "simple-topology-targetwko.yaml";
            String cmd = "grep  \"PasswordEncrypted: '@@SECRET\" " + tempWkoModel;
            CommandResult result2 = Runner.run(cmd, getTestMethodEnvironment(testInfo), out);
            assertEquals(0, result2.exitValue(), "Missing JDBC Secret");
            cmd = "grep -c 'Machine' " + tempWkoModel;
            CommandResult result3 = Runner.run(cmd, getTestMethodEnvironment(testInfo), out);
            assertNotEquals(0, result3.exitValue(), "Machine section was not removed from model");
        }
    }

    /**
     * Test Discover Domain using the -skip_archive argument
     *
     * @throws Exception - if any error occurs
     */
    @DisplayName("Test 33: Skip archive")
    @Order(33)
    @Tag("gate")
    @Test
    void test33DiscoverSkipArchive(TestInfo testInfo) throws Exception {
        String cmd = createDomainScript + " -oracle_home " + mwhome_12213 + " -domain_home " +
            domainParentDir + FS + "discoverDomainSkipArchive-33-34 -model_file " +
            getSampleModelFile("-onlinebase") + " -archive_file " + getSampleArchiveFile();
        try (PrintWriter out = getTestMethodWriter(testInfo, "CreateDomain")) {
            CommandResult result = Runner.run(cmd, getTestMethodEnvironment(testInfo), out);
            assertEquals(0, result.exitValue(), "Unexpected return code");
            discover33DomainCreated = true;
        }

        try (PrintWriter out = getTestMethodWriter(testInfo, "DiscoverDomain")) {
            Path discoveredModel = getTestOutputPath(testInfo).resolve("discoveredModel.yaml");
            cmd = discoverDomainScript
                + " -oracle_home " + mwhome_12213
                + " -domain_home " + domainParentDir + FS + "discoverDomainSkipArchive-33-34"
                + " -model_file " + discoveredModel
                + " -skip_archive ";
            CommandResult result = Runner.run(cmd, getTestMethodEnvironment(testInfo), out);
            // SecurityConfiguration warning
            assertEquals(0, result.exitValue(), "Unexpected return code");
        }
    }

    /**
     * Test Discover Domain using the -run_remote argument
     *
     * @throws Exception - if any error occurs
     */
    @DisplayName("Test 34: remote discovery")
    @Order(34)
    @Tag("gate")
    @Test
    void test34DiscoverRemote(TestInfo testInfo) throws Exception {
        assertTrue(discover33DomainCreated, "step skipped because Domain creation failed in step test33DiscoverSkipArchive");
        String domainHome = domainParentDir + FS + "discoverDomainSkipArchive-33-34";
        setUpBootProperties(domainHome, "admin-server", "weblogic", "welcome1");
        Path adminServerOut = getTestOutputPath(testInfo).resolve("admin-server.out");
        boolean isServerUp = startAdminServer(domainHome, adminServerOut);
        if (isServerUp) {
            try {
                try (PrintWriter out = getTestMethodWriter(testInfo)) {
                    Path discoveredModel = getTestOutputPath(testInfo).resolve("discoveredModel.yaml");
                    String cmd = discoverDomainScript
                        + " -oracle_home " + mwhome_12213
                        + " -domain_home " + domainHome
                        + " -model_file " + discoveredModel
                        + " -admin_user weblogic -admin_pass welcome1 -admin_url t3://localhost:7001"
                        + " -remote";
                    CommandResult result = Runner.run(cmd, getTestMethodEnvironment(testInfo), out);
                    // SecurityConfiguration warning
                    verifyResult(result, "Remote discovery created a model that references files or directories" +
                        " on the remote machine");
                }
            } finally {
                stopAdminServer(domainHome);
            }
        } else {
            // Best effort to clean up server
            tryKillTheAdminServer(domainHome, "admin-server");
            throw new Exception("test34DiscoverRemote failed - cannot bring up server");
        }
    }

    /**
     * test create and discover domain with jdbc wallet.
     *
     * @throws Exception - if any error occurs
     */
    @DisplayName("Test 35: test create and discover domain with jdbc wallet")
    @Order(35)
    @Tag("gate")
    @Test
    void test35DiscoverDomainWithJDBCWallet(TestInfo testInfo) throws Exception {
        String domainDir = "domain2-discover35";
        Path genJDBCArchive = getTestOutputPath(testInfo).resolve("gen-wallet-archive.zip");
        String cmd = archiveHelperScript
            + " add databaseWallet "
            + " -source " + getSampleKeyStoreFile()
            + " -wallet_name acmeWallet "
            + " -archive_file " + genJDBCArchive;

        try (PrintWriter out = getTestMethodWriter(testInfo, "archiveHelper")) {
            CommandResult result = Runner.run(cmd, getTestMethodEnvironment(testInfo), out);
            assertEquals(0, result.exitValue(), "Unexpected return code");
        }

        cmd = createDomainScript
            + " -oracle_home " + mwhome_12213
            + " -domain_home " + domainParentDir + FS + domainDir
            + " -model_file " + getSampleModelFile("-jdbcwallet")
            + " -archive_file " + genJDBCArchive;

        try (PrintWriter out = getTestMethodWriter(testInfo, "CreateDomain")) {
            CommandResult result = Runner.run(cmd, getTestMethodEnvironment(testInfo), out);
            assertEquals(0, result.exitValue(), "Unexpected return code");
        }

        Path discoveredArchive = getTestOutputPath(testInfo).resolve("discoveredArchive.zip");
        Path discoveredModelFile = getTestOutputPath(testInfo).resolve("discoveredModel.yaml");
        Path discoveredVariableFile = getTestOutputPath(testInfo).resolve("discoveredVariable.properties");
        cmd = discoverDomainScript + " -oracle_home " + mwhome_12213 + " -domain_home " +
            domainParentDir + FS + domainDir + " -archive_file " + discoveredArchive +
            " -model_file " + discoveredModelFile + " -variable_file " + discoveredVariableFile;
        try (PrintWriter out = getTestMethodWriter(testInfo, "DiscoverDomain")) {
            CommandResult result = Runner.run(cmd, getTestMethodEnvironment(testInfo), out);

            verifyResult(result, "discoverDomain.sh completed successfully");

            verifyDiscoveredJDBCWalletModelFile(discoveredModelFile.toString());

        }
    }

    @DisplayName("Test 36: Create domain with structured app and then discover it")
    @Order(36)
    @Tag("gate")
    @Test
    void test36CreateDomainAndDiscoverOfflineWithStructuredApp(TestInfo testInfo) throws Exception {
        String domainDir = "domain36";
        String domainHome = domainParentDir + FS + domainDir;
        String cmd = createDomainScript
            + " -oracle_home " + mwhome_12213
            + " -domain_home " + domainHome
            + " -model_file " + getSampleModelFile("-structured-offline")
            + " -variable_file " + getSampleVariableFile()
            + " -archive_file " + getTargetDir() + FS + "archive36.zip";

        try (PrintWriter out = getTestMethodWriter(testInfo, "CreateDomain")) {
            CommandResult result = Runner.run(cmd, getTestMethodEnvironment(testInfo), out);
            assertEquals(0, result.exitValue(), "Unexpected return code");

            // Verify that the structured application's directory is extracted to the expected location.
            verifyStructuredAppDirectoryStructure(domainHome);
        }

        try (PrintWriter out = getTestMethodWriter(testInfo, "UpdateDomain")) {
            cmd = updateDomainScript
                + " -oracle_home " + mwhome_12213
                + " -domain_home " + domainHome
                + " -model_file " + getSampleModelFile("-structured-online-update")
                + " -variable_file " + getSampleVariableFile()
                + " -archive_file " + getTargetDir() + FS + "archive38.zip";
            CommandResult result = Runner.run(cmd, getTestMethodEnvironment(testInfo), out);
            verifyResult(result, "updateDomain.sh completed successfully");

            verifyStructuredAppDirectoryStructure(domainHome, "Domain Home", "OverridesConfig.properties",
                "ConfigOverrides.properties");
        }

        Path discoveredArchive = getTestOutputPath(testInfo).resolve("discoveredArchive.zip");
        Path discoveredModelFile = getTestOutputPath(testInfo).resolve("discoveredModel.yaml");
        Path discoveredVariableFile = getTestOutputPath(testInfo).resolve("discoveredVariable.properties");
        cmd = discoverDomainScript + " -oracle_home " + mwhome_12213 + " -domain_home " +
            domainHome + " -archive_file " + discoveredArchive +
            " -model_file " + discoveredModelFile + " -variable_file " + discoveredVariableFile;
        try (PrintWriter out = getTestMethodWriter(testInfo, "DiscoverDomain")) {
            CommandResult result = Runner.run(cmd, getTestMethodEnvironment(testInfo), out);

            verifyResult(result, "discoverDomain.sh completed successfully");
        }

        try (PrintWriter out = getTestMethodWriter(testInfo, "ArchiveHelperOnDiscoveredArchive")) {
            Path archiveExtractDir = getTestOutputPath(testInfo);

            cmd = archiveHelperScript + " extract structuredApplication -name MyWebServicesApp " +
                " -target " + archiveExtractDir + " -archive_file " + discoveredArchive;
            CommandResult result = Runner.run(cmd, getTestMethodEnvironment(testInfo), out);

            assertEquals(0, result.exitValue(), "Unexpected return code");

            verifyStructuredAppDirectoryStructure(archiveExtractDir.toString(), "Archive Extract",
                "OverridesConfig.properties", "ConfigOverrides.properties");
        }
    }

    @DisplayName("Test 37: Create empty domain and deploy structured app in online mode and then discover it")
    @Order(37)
    @Tag("gate")
    @Test
    void test37OnlineUpdateDomainWithStructuredApp(TestInfo testInfo) throws Exception {
        String domainDir = "domain37";
        String domainHome = domainParentDir + FS + domainDir;
        String cmd = createDomainScript
            + " -oracle_home " + mwhome_12213
            + " -domain_home " + domainHome
            + " -model_file " + getSampleModelFile("-structured-online-create")
            + " -variable_file " + getSampleVariableFile();

        try (PrintWriter out = getTestMethodWriter(testInfo, "CreateDomain")) {
            CommandResult result = Runner.run(cmd, getTestMethodEnvironment(testInfo), out);
            assertEquals(0, result.exitValue(), "Unexpected return code");
        }

        Path adminServerOut = getTestOutputPath(testInfo).resolve("admin-server.out");
        boolean isServerUp = startAdminServer(domainHome, adminServerOut);
        if (isServerUp) {
            try {
                try (PrintWriter out = getTestMethodWriter(testInfo, "UpdateDomain")) {
                    cmd = updateDomainScript
                        + " -oracle_home " + mwhome_12213
                        + " -model_file " + getSampleModelFile("-structured-online-update")
                        + " -variable_file " + getSampleVariableFile()
                        + " -archive_file " + getTargetDir() + FS + "archive36.zip"
                        + " -admin_user weblogic -admin_pass welcome1 -admin_url t3://localhost:7001";
                    CommandResult result = Runner.run(cmd, getTestMethodEnvironment(testInfo), out);
                    verifyResult(result, "updateDomain.sh completed successfully");

                    verifyStructuredAppDirectoryStructure(domainHome);
                    verifyStructuredAppIsWorking("ConfigOverrides.properties", "updated");
                }

                Path discoveredArchive = getTestOutputPath(testInfo).resolve("discoveredArchive.zip");
                Path discoveredModelFile = getTestOutputPath(testInfo).resolve("discoveredModel.yaml");
                Path discoveredVariableFile = getTestOutputPath(testInfo).resolve("discoveredVariable.properties");
                cmd = discoverDomainScript + " -oracle_home " + mwhome_12213
                    + " -model_file " + discoveredModelFile + " -variable_file " + discoveredVariableFile
                    + " -archive_file " + discoveredArchive
                    + " -admin_user weblogic -admin_pass welcome1 -admin_url t3://localhost:7001";
                try (PrintWriter out = getTestMethodWriter(testInfo, "DiscoverDomain")) {
                    CommandResult result = Runner.run(cmd, getTestMethodEnvironment(testInfo), out);

                    verifyResult(result, "discoverDomain.sh completed successfully");
                }

                try (PrintWriter out = getTestMethodWriter(testInfo, "ArchiveHelperOnDiscoveredArchive")) {
                    Path archiveExtractDir = getTestOutputPath(testInfo);

                    cmd = archiveHelperScript + " extract structuredApplication -name MyWebServicesApp " +
                        " -target " + archiveExtractDir + " -archive_file " + discoveredArchive;
                    CommandResult result = Runner.run(cmd, getTestMethodEnvironment(testInfo), out);

                    assertEquals(0, result.exitValue(), "Unexpected return code");

                    verifyStructuredAppDirectoryStructure(archiveExtractDir.toString(), "Archive Extract");
                }
            } finally {
                stopAdminServer(domainHome);
            }
        } else {
            // Best effort to clean up server
            tryKillTheAdminServer(domainHome, "admin-server");
            throw new Exception("test37OnlineUpdateDomainWithStructuredApp failed - cannot bring up server");
        }
    }

    @DisplayName("Test 38: Create domain with structured app and use online update the redeploy it")
    @Order(38)
    @Tag("gate")
    @Test
    void test38OnlineRedeployStructuredApp(TestInfo testInfo) throws Exception {
        String domainDir = "domain38";
        String domainHome = domainParentDir + FS + domainDir;
        String cmd = createDomainScript
            + " -oracle_home " + mwhome_12213
            + " -domain_home " + domainHome
            + " -model_file " + getSampleModelFile("-structured-online")
            + " -variable_file " + getSampleVariableFile()
            + " -archive_file " + getTargetDir() + FS + "archive36.zip";

        try (PrintWriter out = getTestMethodWriter(testInfo, "CreateDomain")) {
            CommandResult result = Runner.run(cmd, getTestMethodEnvironment(testInfo), out);
            assertEquals(0, result.exitValue(), "Unexpected return code");

            verifyStructuredAppDirectoryStructure(domainHome);
        }

        Path adminServerOut = getTestOutputPath(testInfo).resolve("admin-server.out");
        boolean isServerUp = startAdminServer(domainHome, adminServerOut);
        if (isServerUp) {
            try {
                verifyStructuredAppIsWorking("ConfigOverrides.properties", "updated");

                try (PrintWriter out = getTestMethodWriter(testInfo, "UpdateDomain")) {
                    cmd = updateDomainScript
                        + " -oracle_home " + mwhome_12213
                        + " -model_file " + getSampleModelFile("-structured-online-update")
                        + " -variable_file " + getSampleVariableFile()
                        + " -archive_file " + getTargetDir() + FS + "archive38.zip"
                        + " -admin_user weblogic -admin_pass welcome1 -admin_url t3://localhost:7001";
                    CommandResult result = Runner.run(cmd, getTestMethodEnvironment(testInfo), out);
                    verifyResult(result, "updateDomain.sh completed successfully");

                    verifyStructuredAppDirectoryStructure(domainHome, "Domain Home", "OverridesConfig.properties",
                        "ConfigOverrides.properties");

                    verifyStructuredAppIsWorking("OverridesConfig.properties", "new");
                }

                Path discoveredArchive = getTestOutputPath(testInfo).resolve("discoveredArchive.zip");
                Path discoveredModelFile = getTestOutputPath(testInfo).resolve("discoveredModel.yaml");
                Path discoveredVariableFile = getTestOutputPath(testInfo).resolve("discoveredVariable.properties");
                cmd = discoverDomainScript + " -oracle_home " + mwhome_12213
                    + " -model_file " + discoveredModelFile + " -variable_file " + discoveredVariableFile
                    + " -archive_file " + discoveredArchive
                    + " -admin_user weblogic -admin_pass welcome1 -admin_url t3://localhost:7001";
                try (PrintWriter out = getTestMethodWriter(testInfo, "DiscoverDomain")) {
                    CommandResult result = Runner.run(cmd, getTestMethodEnvironment(testInfo), out);

                    verifyResult(result, "discoverDomain.sh completed successfully");
                }

                try (PrintWriter out = getTestMethodWriter(testInfo, "ArchiveHelperOnDiscoveredArchive")) {
                    Path archiveExtractDir = getTestOutputPath(testInfo);

                    cmd = archiveHelperScript + " extract structuredApplication -name MyWebServicesApp " +
                        " -target " + archiveExtractDir + " -archive_file " + discoveredArchive;
                    CommandResult result = Runner.run(cmd, getTestMethodEnvironment(testInfo), out);

                    assertEquals(0, result.exitValue(), "Unexpected return code");

                    verifyStructuredAppDirectoryStructure(domainHome, "Archive Extract", "OverridesConfig.properties",
                        "ConfigOverrides.properties");
                }
            } finally {
                stopAdminServer(domainHome);
            }
        } else {
            // Best effort to clean up server
            tryKillTheAdminServer(domainHome, "admin-server");
            throw new Exception("test38OnlineRedeployStructuredApp failed - cannot bring up server");
        }
    }

    @DisplayName("Test 39: Structured app remote online update without an archive")
    @Order(39)
    @Tag("gate")
    @Test
    void test39OnlineRemoteDeployStructuredAppOutsideArchiveFile(TestInfo testInfo) throws Exception {
        String cmd;
        String archiveToExplode =
            FileSystems.getDefault().getPath(getTargetDir().toString(), "archive36.zip").toAbsolutePath().toString();
        try (PrintWriter out = getTestMethodWriter(testInfo, "ArchiveHelperExtractAppFromArchive")) {
            Path archiveExtractDir = getTestOutputPath(testInfo);

            cmd = archiveHelperScript + " extract structuredApplication -name MyWebServicesApp " +
                " -target " + archiveExtractDir + " -archive_file " + archiveToExplode;
            CommandResult result = Runner.run(cmd, getTestMethodEnvironment(testInfo), out);
            assertEquals(0, result.exitValue(), "Unexpected return code");
        }

        String domainDir = "domain39";
        String domainHome = domainParentDir + FS + domainDir;
        cmd = createDomainScript
            + " -oracle_home " + mwhome_12213
            + " -domain_home " + domainHome
            + " -model_file " + getSampleModelFile("-structured-online-create-39")
            + " -variable_file " + getSampleVariableFile();

        try (PrintWriter out = getTestMethodWriter(testInfo, "CreateDomain")) {
            CommandResult result = Runner.run(cmd, getTestMethodEnvironment(testInfo), out);
            assertEquals(0, result.exitValue(), "Unexpected return code");
        }

        Path adminServerOut = getTestOutputPath(testInfo).resolve("admin-server.out");
        boolean isServerUp = startAdminServer(domainHome, adminServerOut);
        if (isServerUp) {
            try {
                try (PrintWriter out = getTestMethodWriter(testInfo, "UpdateDomain")) {
                    cmd = updateDomainScript
                        + " -oracle_home " + mwhome_12213
                        + " -model_file " + getSampleModelFile("-structured-online-update-39")
                        + " -variable_file " + getSampleVariableFile()
                        + " -remote -admin_user weblogic -admin_pass welcome1 -admin_url t3://localhost:7001";
                    CommandResult result = Runner.run(cmd, getTestMethodEnvironment(testInfo), out);
                    verifyResult(result, "updateDomain.sh completed successfully");

                    verifyStructuredAppIsWorking("ConfigOverrides.properties", "updated");
                }

                Path discoveredArchive = getTestOutputPath(testInfo).resolve("discoveredArchive.zip");
                Path discoveredModelFile = getTestOutputPath(testInfo).resolve("discoveredModel.yaml");
                Path discoveredVariableFile = getTestOutputPath(testInfo).resolve("discoveredVariable.properties");
                cmd = discoverDomainScript + " -oracle_home " + mwhome_12213
                    + " -model_file " + discoveredModelFile + " -variable_file " + discoveredVariableFile
                    + " -archive_file " + discoveredArchive
                    + " -admin_user weblogic -admin_pass welcome1 -admin_url t3://localhost:7001";
                try (PrintWriter out = getTestMethodWriter(testInfo, "DiscoverDomain")) {
                    CommandResult result = Runner.run(cmd, getTestMethodEnvironment(testInfo), out);

                    verifyResult(result, "discoverDomain.sh completed successfully");
                    File discoveredArchiveFile = discoveredArchive.toFile();
                    assertTrue(discoveredArchiveFile.exists(),
                        "discovery should have created archive file " + discoveredArchive);
                }

                try (PrintWriter out = getTestMethodWriter(testInfo, "ArchiveHelperOnDiscoveredArchive")) {
                    Path archiveExtractDir = getTestOutputPath(testInfo);

                    cmd = archiveHelperScript + " extract structuredApplication -name MyWebServicesApp " +
                        " -target " + archiveExtractDir + " -archive_file " + discoveredArchive;
                    CommandResult result = Runner.run(cmd, getTestMethodEnvironment(testInfo), out);

                    assertEquals(0, result.exitValue(), "Unexpected return code");

                    verifyStructuredAppDirectoryStructure(archiveExtractDir.toString(), "Archive Extract");
                }
            } finally {
                stopAdminServer(domainHome);
            }
        } else {
            // Best effort to clean up server
            tryKillTheAdminServer(domainHome, "admin-server");
            throw new Exception("test39OnlineRemoteDeployStructuredAppOutsideArchiveFile failed - cannot bring up server");
        }
    }

    @DisplayName("Test 40: Create domain with versioned app and use online update the redeploy a new version")
    @Order(40)
    @Tag("gate")
    @Test
    void test40OnlineRedeployVersionedApp(TestInfo testInfo) throws Exception {
        String domainDir = "domain40";
        String domainHome = domainParentDir + FS + domainDir;
        String cmd = createDomainScript
            + " -oracle_home " + mwhome_12213
            + " -domain_home " + domainHome
            + " -model_file " + getSampleModelFile("-versioned-online")
            + " -variable_file " + getSampleVariableFile()
            + " -archive_file " + getTargetDir() + FS + "archive40.zip";

        try (PrintWriter out = getTestMethodWriter(testInfo, "CreateDomain")) {
            CommandResult result = Runner.run(cmd, getTestMethodEnvironment(testInfo), out);
            assertEquals(0, result.exitValue(), "Unexpected return code");
        }

        Path adminServerOut = getTestOutputPath(testInfo).resolve("admin-server.out");
        boolean isServerUp = startAdminServer(domainHome, adminServerOut);
        if (isServerUp) {
            try {
                try (PrintWriter out = getTestMethodWriter(testInfo, "UpdateDomainSameVersion")) {
                    cmd = updateDomainScript
                        + " -oracle_home " + mwhome_12213
                        + " -model_file " + getSampleModelFile("-versioned-online-redeploy")
                        + " -variable_file " + getSampleVariableFile()
                        + " -archive_file " + getTargetDir() + FS + "archive40.zip"
                        + " -admin_user weblogic -admin_pass welcome1 -admin_url t3://localhost:7001";
                    CommandResult result = Runner.run(cmd, getTestMethodEnvironment(testInfo), out);

                    moveWDTLogFile(getTestOutputPath(testInfo), "updateDomain.log", "updateDomain-1.log");

                    verifyResult(result, "updateDomain.sh completed successfully");
                }

                try (PrintWriter out = getTestMethodWriter(testInfo, "UpdateDomainRemoteNewVersion")) {
                    cmd = updateDomainScript
                        + " -oracle_home " + mwhome_12213
                        + " -model_file " + getSampleModelFile("-versioned-online-redeploy")
                        + " -variable_file " + getSampleVariableFile()
                        + " -archive_file " + getTargetDir() + FS + "archive40-updated.zip"
                        + " -remote -admin_user weblogic -admin_pass welcome1 -admin_url t3://localhost:7001";
                    CommandResult result = Runner.run(cmd, getTestMethodEnvironment(testInfo), out);

                    moveWDTLogFile(getTestOutputPath(testInfo), "updateDomain.log", "updateDomain-2.log");

                    verifyResult(result, "updateDomain.sh completed successfully");
                }

                Path discoveredArchive = getTestOutputPath(testInfo).resolve("discoveredArchive.zip");
                Path discoveredModelFile = getTestOutputPath(testInfo).resolve("discoveredModel.yaml");
                Path discoveredVariableFile = getTestOutputPath(testInfo).resolve("discoveredVariable.properties");
                cmd = discoverDomainScript + " -oracle_home " + mwhome_12213
                    + " -model_file " + discoveredModelFile + " -variable_file " + discoveredVariableFile
                    + " -archive_file " + discoveredArchive
                    + " -admin_user weblogic -admin_pass welcome1 -admin_url t3://localhost:7001";
                try (PrintWriter out = getTestMethodWriter(testInfo, "DiscoverDomain")) {
                    CommandResult result = Runner.run(cmd, getTestMethodEnvironment(testInfo), out);

                    verifyResult(result, "discoverDomain.sh completed successfully");
                }

                try (PrintWriter out = getTestMethodWriter(testInfo, "ArchiveHelperOnDiscoveredArchive")) {
                    Path archiveExtractDir = getTestOutputPath(testInfo);

                    cmd = archiveHelperScript + " extract all -target " + archiveExtractDir +
                        " -archive_file " + discoveredArchive;
                    CommandResult result = Runner.run(cmd, getTestMethodEnvironment(testInfo), out);

                    assertEquals(0, result.exitValue(), "Unexpected return code");
                }
            } finally {
                stopAdminServer(domainHome);
            }
        } else {
            // Best effort to clean up server
            tryKillTheAdminServer(domainHome, "admin-server");
            throw new Exception("test40OnlineRedeployVersionedApp failed - cannot bring up server");
        }
    }

    private void verifyVersionedAppVersion(File archivedAppFile, String version) throws Exception {
        JarFile warFile = new JarFile(archivedAppFile.getAbsolutePath());
        Manifest manifest = warFile.getManifest();
        Attributes attributes = manifest.getAttributes("Weblogic-Application-Version");
        String archiveVersion = attributes.getValue("Weblogic-Application-Version");
        assertEquals(version, archiveVersion, "Expected the archive version to match the expected version");
    }

    private void verifyStructuredAppDirectoryStructure(String domainHomeDir) throws Exception {
        verifyStructuredAppDirectoryStructure(domainHomeDir, "Domain Home");
    }

    private void verifyStructuredAppDirectoryStructure(String domainHomeDir, String dirName) throws Exception {
        verifyStructuredAppDirectoryStructure(domainHomeDir, dirName, "ConfigOverrides.properties", null);
    }

    private void verifyStructuredAppDirectoryStructure(String domainHomeDir, String dirName, String propertiesFileName,
                                                       String excludedPropertiesFileName) throws Exception {
        File domainHomeDirFile = new File(domainHomeDir);
        assertTrue(domainHomeDirFile.isDirectory(), dirName + " directory " +
            domainHomeDirFile.getAbsolutePath() + " does not exist");

        String pathToStructuredAppDir = "wlsdeploy" + FS + "structuredApplications" + FS + "MyWebServicesApp";
        File appDirFile = new File(domainHomeDirFile, pathToStructuredAppDir);
        assertTrue(appDirFile.isDirectory(), "Structured application MyWebServicesApp directory " +
            appDirFile.getAbsolutePath() + " does not exist");

        String pathToWar = "app" + FS + "MyWebServicesApp.war";
        File warFile = new File(appDirFile, pathToWar);
        assertTrue(warFile.isFile(), "Structured application MyWebServicesApp war file " +
            warFile.getAbsolutePath() + " does not exist");

        File planDirFile = new File(appDirFile, "plan");
        assertTrue(planDirFile.isDirectory(), "Structured application MyWebServicesApp plan directory " +
            planDirFile.getAbsolutePath() + " does not exist");

        File planFile = new File(planDirFile, "Plan.xml");
        assertTrue(planFile.isFile(), "Structured application MyWebServicesApp plan file " +
            planFile.getAbsolutePath() + " does not exist");

        File appFileOverridesDirFile = new File(planDirFile, "AppFileOverrides");
        assertTrue(planDirFile.isDirectory(), "Structured application MyWebServicesApp AppFileOverrides directory " +
            appFileOverridesDirFile.getAbsolutePath() + " does not exist");

        File configOverridesFile = new File(appFileOverridesDirFile, propertiesFileName);
        assertTrue(configOverridesFile.isFile(), "Structured application " + propertiesFileName + " file " +
            configOverridesFile.getAbsolutePath() + " does not exist");

        if (excludedPropertiesFileName != null) {
            File oldConfigOverridesFile = new File(appFileOverridesDirFile, excludedPropertiesFileName);
            assertFalse(oldConfigOverridesFile.isFile(), "Structured application " + oldConfigOverridesFile +
                " file " + configOverridesFile.getAbsolutePath() + " exists when it should not");
        }
    }

    private void verifyDiscoveredJDBCWalletModelFile(String expectedModelFile) throws Exception {
        List<String> checkContents = new ArrayList<>();

        checkContents.add("domainInfo:");
        checkContents.add("    AdminUserName: '@@PROP:AdminUserName@@'");
        checkContents.add("    AdminPassword: '@@PROP:AdminPassword@@'");
        checkContents.add("topology:");
        checkContents.add("    Name: domain2");
        checkContents.add("    AdminServerName: admin-server");
        checkContents.add("    ProductionModeEnabled: true");
        checkContents.add("    NMProperties:");

        // Don't include the JavaHome path in the check since it will vary when running system-tests locally...
        //
        checkContents.add("        JavaHome: ");
        checkContents.add("    Server:");
        checkContents.add("        admin-server: {}");
        checkContents.add("    SecurityConfiguration:");
        checkContents.add("        NodeManagerUsername: '@@PROP:SecurityConfig.NodeManagerUsername@@'");
        checkContents.add("resources:");
        checkContents.add("    JDBCSystemResource:");
        checkContents.add("        testds:");
        checkContents.add("            Target: admin-server");
        checkContents.add("            JdbcResource:");
        checkContents.add("                DatasourceType: GENERIC");
        checkContents.add("                JDBCConnectionPoolParams:");
        checkContents.add("                    TestTableName: SQL ISVALID");
        checkContents.add("                JDBCDataSourceParams:");
        checkContents.add("                    GlobalTransactionsProtocol: OnePhaseCommit");
        checkContents.add("                    JNDIName: testds");
        checkContents.add("                JDBCDriverParams:");
        checkContents.add("                    URL: jdbc:oracle:thin:@//localhost:1522/orclpdb1.localdomain");
        checkContents.add("                    PasswordEncrypted: '@@PROP:JDBC.testds.PasswordEncrypted@@'");
        checkContents.add("                    DriverName: oracle.jdbc.OracleDriver");
        checkContents.add("                    Properties:");
        checkContents.add("                        user:");
        checkContents.add("                            Value: '@@PROP:JDBC.testds.user.Value@@'");
        checkContents.add("                        javax.net.ssl.trustStore:");
        checkContents.add("                            Value: config/wlsdeploy/dbWallets/testds/cwallet.sso");
        checkContents.add("                        javax.net.ssl.trustStoreType:");
        checkContents.add("                            Value: SSO");
        checkContents.add("                        javax.net.ssl.keyStore:");
        checkContents.add("                            Value: config/wlsdeploy/dbWallets/testds/cwallet.sso");
        checkContents.add("                        javax.net.ssl.keyStoreType:");
        checkContents.add("                            Value: SSO");
        checkContents.add("                        oracle.net.tns_admin:");
        checkContents.add("                            Value: config/wlsdeploy/dbWallets/testds/");

        verifyModelFileContents(expectedModelFile, checkContents);
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
        assertTrue(adminSecurityDir.mkdirs(), "mkdir for boot.properties failed");
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

    private void moveWDTLogFile(Path testDirectory, String originalName, String newName) throws Exception {
        Path sourceFile = testDirectory.resolve(originalName);
        Path targetFile = testDirectory.resolve(newName);
        Files.move(sourceFile, targetFile, StandardCopyOption.REPLACE_EXISTING);
    }

    private void verifyStructuredAppIsWorking(String overridesFileName, String expectedResult) throws Exception {
        verifyHttpGetResponse(REST_PLAN_URL_STRING, expectedResult);

        // This part of the code is not currently working.
        // See Bug 36409111.
        //
        // String overridesUrlString = String.format(REST_OVERRIDES_URL_TEMPLATE, overridesFileName);
        // verifyHttpGetResponse(overridesUrlString, expectedResult);
    }

    private void verifyHttpGetResponse(String urlString, String expectedResult) throws Exception {
        URL url = new URL(urlString);
        HttpURLConnection conn = (HttpURLConnection) url.openConnection();
        conn.setRequestMethod("GET");
        conn.setConnectTimeout(5000);
        conn.setReadTimeout(5000);

        int status = conn.getResponseCode();
        assertEquals(200, status, "Expected HTTP GET to " + urlString + " response to be 200");

        String actualResult;
        try (BufferedReader in = new BufferedReader(new InputStreamReader(conn.getInputStream()))) {
            actualResult = in.readLine();
            if (actualResult != null) {
                actualResult = actualResult.trim();
            }
        }
        assertEquals(expectedResult, actualResult,
            "Expected HTTP GET to " + urlString + " response to be: " + expectedResult);
    }
}
