// Copyright 2019, 2021, Oracle Corporation and/or its affiliates.
// Licensed under the Universal Permissive License v 1.0 as shown at http://oss.oracle.com/licenses/upl.

package oracle.weblogic.deploy.integration;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.List;

import oracle.weblogic.deploy.integration.annotations.TestingLogger;
import oracle.weblogic.deploy.integration.utils.CommandResult;
import oracle.weblogic.deploy.integration.utils.Runner;
import oracle.weblogic.deploy.logging.PlatformLogger;
import oracle.weblogic.deploy.logging.WLSDeployLogFactory;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

public class BaseTest {
    @TestingLogger
    private static final PlatformLogger logger = WLSDeployLogFactory.getLogger("integration.tests");
    protected static final String FS = File.separator;
    private static final String SAMPLE_ARCHIVE_FILE = "archive.zip";
    private static final String WDT_ZIPFILE = "weblogic-deploy.zip";
    private static final String WDT_HOME_DIR = "weblogic-deploy";
    protected static final String SAMPLE_MODEL_FILE_PREFIX = "simple-topology";
    protected static final String SAMPLE_VARIABLE_FILE = "domain.properties";
    private static final int maxIterations = 50;
    private static final int waitTime = 5;
    protected static String mwhome_12213 = "";
    protected static String createDomainScript = "";
    protected static String compareModelScript = "";
    protected static String discoverDomainScript = "";
    protected static String updateDomainScript = "";
    protected static String deployAppScript = "";
    protected static String encryptModelScript = "";
    protected static String validateModelScript = "";
    protected static String domainParentDir = "";
    protected static final String ORACLE_DB_IMG = "phx.ocir.io/weblogick8s/database/enterprise";
    protected static final String ORACLE_DB_IMG_TAG = "12.2.0.1-slim";
    private static final String DB_CONTAINER_NAME = "InfraDB";

    protected static void initialize() {

        logger.info("Initializing the tests ...");
        mwhome_12213 = System.getProperty("MW_HOME");

        createDomainScript = getWDTScriptsHome() + FS + "createDomain.sh";
        discoverDomainScript = getWDTScriptsHome() + FS + "discoverDomain.sh";
        updateDomainScript = getWDTScriptsHome() + FS + "updateDomain.sh";
        deployAppScript = getWDTScriptsHome() + FS + "deployApps.sh";
        encryptModelScript = getWDTScriptsHome() + FS + "encryptModel.sh";
        validateModelScript = getWDTScriptsHome() + FS + "validateModel.sh";
        compareModelScript = getWDTScriptsHome() + FS + "compareModel.sh";

        domainParentDir = "." + FS + "target" + FS + "domains";
    }

    protected static void setup() throws Exception {

        logger.info("Setting up the test environment ...");
        logger.info("building WDT sample archive file");
        buildSampleArchive();

        // unzip weblogic-deploy-tooling/installer/target/weblogic-deploy.zip
        String cmd = "unzip -q " + getInstallerTargetDir() + FS + WDT_ZIPFILE + " -d " + getTargetDir();
        executeAndVerify(cmd);

        // create domain_parent directory if not existing
        File domainParentDir = new File(BaseTest.domainParentDir);
        if(!domainParentDir.exists()) {
            assertTrue(domainParentDir.mkdir(), "Setup failed to create Domain parent directory");
        }
    }

    protected static void cleanup() throws Exception {
        logger.info("cleaning up the test environment ...");

        String command = "docker rm -f " + DB_CONTAINER_NAME;
        Runner.run(command);
    }

    protected static Path getTargetDir() {
        return Paths.get("target");
    }

    protected static void chmodScriptFiles(String... filenames) throws Exception {
        for(String filename : filenames) {
            String cmd = "chmod +x " + filename;
            //executeNoVerify(cmd);
            executeAndVerify(cmd);
        }
    }

    protected static void pullOracleDBDockerImage() throws Exception {
        logger.info("Pulling Oracle DB image from OCIIR ...");

        pullDockerImage(ORACLE_DB_IMG, ORACLE_DB_IMG_TAG);
    }

    private static void pullDockerImage(String imagename, String imagetag) throws Exception {

        String cmd = "docker pull " + imagename + ":" + imagetag;
        CommandResult result = Runner.run(cmd);
        assertEquals(0, result.exitValue(), "Docker pull failed for " + imagename);

        // verify the docker image is pulled
        result = Runner.run("docker images | grep " + imagename  + " | grep " +
                imagetag + "| wc -l");
        String resultString = result.stdout();
        if(Integer.parseInt(resultString.trim()) != 1) {
            throw new Exception("docker image " + imagename + ":" + imagetag + " is not pulled as expected."
                    + " Expected 1 image, found " + resultString);
        }
    }

    protected static String getWDTScriptsHome() {
        return getTargetDir() + FS + WDT_HOME_DIR + FS + "bin";
    }

    protected void verifyResult(CommandResult result, String matchString) throws Exception {
        if(result.exitValue() != 0 || !result.stdout().contains(matchString)) {
            logger.info("DEBUG: result.exitValue=" + result.exitValue());
            logger.info("DEBUG: result.stdout=" + result.stdout());
            throw new Exception("result stdout does not contains the expected string: " + matchString);
        }
    }

    protected static void verifyExitValue(CommandResult result, String command) throws Exception {
        if(result.exitValue() != 0) {
            logger.info(result.stdout());
            throw new Exception("executing the following command failed: " + command);
        }
    }

    protected void verifyErrorMsg(CommandResult result, String errorMsg) throws Exception {
        if(result.exitValue() == 0 || !result.stdout().contains(errorMsg)) {
            logger.info("DEBUG: result stderr: " + result.stdout());
            throw new Exception("test result does not contain the expected error msg: " + errorMsg);
        }
    }

    protected void verifyModelFile(String modelFile) throws Exception {
        String cmd = "ls " + modelFile + " | wc -l";
        CommandResult result = Runner.run(cmd);
        if(Integer.parseInt(result.stdout().trim()) != 1) {
            throw new Exception("no model file is created as expected");
        }
    }

    protected void verifyFileExists(String filePath) throws Exception {
      if (!Files.exists(Paths.get(filePath))) {
        throw new Exception("File does not exists but should " + filePath);
      }
    }

    protected void verifyFileDoesNotExists(String filePath) throws Exception {
      if (Files.exists(Paths.get(filePath))) {
        throw new Exception("File exists but should not " + filePath);
      }
    }

    protected static Path getResourcePath() {
        return Paths.get("src", "test", "resources");
    }

    protected static String getGeneratedResourcePath() {
        return getTargetDir() + FS + "resources";
    }

    protected static CommandResult buildSampleArchive() throws Exception {
        logger.info("Building WDT archive ...");
        String command = "sh " + getResourcePath() + FS + "build-archive.sh";
        return executeAndVerify(command);
    }

    protected static String getSampleArchiveFile() {
        return getGeneratedResourcePath() + FS + SAMPLE_ARCHIVE_FILE;
    }

    protected static String getSampleModelFile(String suffix) {
        return getResourcePath() + FS + SAMPLE_MODEL_FILE_PREFIX + suffix + ".yaml";
    }

    protected static Path getInstallerTargetDir() {
        return Paths.get("..", "installer", "target");
    }

    protected static String getSampleVariableFile() {
        return getResourcePath() + FS + SAMPLE_VARIABLE_FILE;
    }

    protected static void createDBContainer() throws Exception {
        logger.info("Creating an Oracle db docker container ...");
        String command = "docker rm -f " + DB_CONTAINER_NAME;
        Runner.run(command);

        String exposePort = "";
        if (System.getProperty("db.use.container.network").equals("false")) {
            exposePort = " -p1521:1521 -p5500:5500 ";
        }

        command = "docker run -d --name " + DB_CONTAINER_NAME + " --env=\"DB_PDB=InfraPDB1\"" +
                " --env=\"DB_DOMAIN=us.oracle.com\" --env=\"DB_BUNDLE=basic\" " + exposePort
            + ORACLE_DB_IMG + ":" + ORACLE_DB_IMG_TAG;
        Runner.run(command);
    }

    static void waitForDatabase() throws IOException, InterruptedException {
        // Wait for the database container to be healthy before continuing
        String command = "docker inspect --format='{{json .State.Health}}' " + DB_CONTAINER_NAME;
        checkCmdInLoop(command, "\"Status\":\"healthy");
    }

    protected static void replaceStringInFile(Path original, Path output, String originalString, String newString)
            throws Exception {

        String content = new String(Files.readAllBytes(original));
        content = content.replaceAll(originalString, newString);
        Files.write(output, content.getBytes());
    }

    protected String getDBContainerIP() throws Exception {
        if (System.getProperty("db.use.container.network").equals("false")) {
            return "localhost";
        }
        String getDBContainerIP = "docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' " +
                DB_CONTAINER_NAME;
        String dbhost = Runner.run(getDBContainerIP).stdout().trim();
        logger.info("DEBUG: DB_HOST=" + dbhost);
        return dbhost;
    }

    protected void verifyModelFileContents(String modelFileName, List<String> textToFind) throws Exception {
        BufferedReader model = inputYaml(modelFileName);
        List<String> checkList = new ArrayList<>(textToFind);
        while (model.ready()) {
            String nextLine = model.readLine();
            if (nextLine != null) {
                for (String textLine : textToFind) {
                    if (nextLine.contains(textLine)) {
                        checkList.remove(textLine);
                        break;
                    }
                }
            }
        }
        if (checkList.size() > 0) {
            for (String leftover : checkList) {
                System.err.println("Model file did not contain " + leftover);
            }
            throw new Exception("Model file did not contain expected results");
        }
    }

    protected BufferedReader inputYaml(String yamlFileName)  throws Exception {
        File model = new File(yamlFileName);
        return new BufferedReader(new FileReader(model));
    }

    private static CommandResult executeAndVerify(String command) throws Exception {
        CommandResult result = Runner.run(command);
        verifyExitValue(result, command);
        return result;
    }

    private static void checkCmdInLoop(String cmd, String matchStr) throws IOException, InterruptedException {
        int i = 0;
        while (i < maxIterations) {
            CommandResult result = Runner.run(cmd);

            // pod might not have been created or if created loop till condition
            if (result.exitValue() != 0
                || (result.exitValue() == 0 && !result.stdout().contains(matchStr))) {

                logger.info("Output for '" + cmd + "'\n" + result.stdout() + "\n " + result.stdout());
                // check for last iteration
                if (i == (maxIterations - 1)) {
                    throw new RuntimeException(
                            "FAILURE: " + cmd + " does not return the expected string " + matchStr + ", exiting!");
                }
                logger.info(
                        "Waiting for the expected String " + matchStr
                                + ": Ite ["
                                + i
                                + "/"
                                + maxIterations
                                + "], sleeping "
                                + waitTime
                                + " seconds more");

                Thread.sleep(waitTime * 1000);
                i++;
            } else {
                logger.info("Found expected result: " + matchStr);
                break;
            }
        }
    }
}
