// Copyright 2019, 2020, Oracle Corporation and/or its affiliates. 
// Licensed under the Universal Permissive License v 1.0 as shown at http://oss.oracle.com/licenses/upl.

package oracle.weblogic.deploy.integration;

import java.io.File;
import java.io.BufferedReader;
import java.io.FileReader;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.List;
import java.util.logging.Logger;
import oracle.weblogic.deploy.integration.utils.ExecCommand;
import oracle.weblogic.deploy.integration.utils.ExecResult;
import org.apache.commons.io.FileUtils;

public class BaseTest {

    protected static final Logger logger = Logger.getLogger(ITWdt.class.getName());
    protected static final String FS = File.separator;
    private static final String SAMPLE_ARCHIVE_FILE = "archive.zip";
    private static final String WDT_ZIPFILE = "weblogic-deploy.zip";
    private static final String WDT_HOME_DIR = "weblogic-deploy";
    protected static final String SAMPLE_MODEL_FILE_PREFIX = "simple-topology";
    protected static final String SAMPLE_VARIABLE_FILE = "domain.properties";
    private static int maxIterations = 50;
    private static int waitTime = 5;
    private static String projectRoot = "";
    protected static String mwhome_12213 = "";
    protected static String createDomainScript = "";
    protected static String compareModelScript = "";
    protected static String discoverDomainScript = "";
    protected static String updateDomainScript = "";
    protected static String deployAppScript = "";
    protected static String encryptModelScript = "";
    protected static String validateModelScript = "";
    protected static String domainParent12213 = "";
    protected static final String ORACLE_DB_IMG = "phx.ocir.io/weblogick8s/database/enterprise";
    protected static final String ORACLE_DB_IMG_TAG = "12.2.0.1-slim";
    private static final String DB_CONTAINER_NAME = "InfraDB";

    protected static void initialize() {

        logger.info("Initializing the tests ...");
        projectRoot = System.getProperty("user.dir");
        logger.info("DEBUG: projectRoot=" + projectRoot);

        mwhome_12213 = System.getProperty("MW_HOME");

        createDomainScript = getWDTScriptsHome() + FS + "createDomain.sh";
        discoverDomainScript = getWDTScriptsHome() + FS + "discoverDomain.sh";
        updateDomainScript = getWDTScriptsHome() + FS + "updateDomain.sh";
        deployAppScript = getWDTScriptsHome() + FS + "deployApps.sh";
        encryptModelScript = getWDTScriptsHome() + FS + "encryptModel.sh";
        validateModelScript = getWDTScriptsHome() + FS + "validateModel.sh";
        compareModelScript = getWDTScriptsHome() + FS + "compareModel.sh";

        domainParent12213 = "." + FS + "domains";
    }

    protected static void setup() throws Exception {

        logger.info("Setting up the test environment ...");
        logger.info("building WDT sample archive file");
        buildSampleArchive();

        // unzip weblogic-deploy-tooling/installer/target/weblogic-deploy.zip
        String cmd = "unzip " + getInstallerTargetDir() + FS + WDT_ZIPFILE + " -d " + getTargetDir();
        //executeNoVerify(cmd);
        executeAndVerify(cmd, true);

        // create domain_parent directory if not existing
        File domainParentDir = new File(domainParent12213);
        if(!domainParentDir.exists()) {
            domainParentDir.mkdir();
        }

        chmodScriptFiles(createDomainScript, discoverDomainScript, updateDomainScript, deployAppScript,
                encryptModelScript, validateModelScript);

    }

    protected static void cleanup() throws Exception {
        logger.info("cleaning up the test environment ...");

        // remove WDT script home directory
        String cmd = "rm -rf " + getTargetDir() + FS + WDT_HOME_DIR;
        executeNoVerify(cmd);

        // delete the domain directory created by the tests
        File domainParentDir = new File(domainParent12213);

        if(domainParentDir.exists()) {
            FileUtils.deleteDirectory(domainParentDir);
        }
    }

    protected static void saveLogFiles(String testMethodName) throws Exception {
        logger.info("saving log files ...");

        // save the logs for this test instance in the workspace target directory
        String cmd = "tar -cvf" + getTargetDir() +FS + testMethodName + ".tar " +  getTargetDir() + FS + WDT_HOME_DIR +
            FS + "logs";
        executeNoVerify(cmd);
    }

    protected static String getProjectRoot() {
        return projectRoot;
    }

    protected static String getTargetDir() {
        return getProjectRoot() + FS + "target";
    }

    protected static void chmodScriptFiles(String... filenames) throws Exception {
        for(String filename : filenames) {
            String cmd = "chmod +x " + filename;
            //executeNoVerify(cmd);
            executeAndVerify(cmd, true);
        }
    }

    protected static void pullOracleDBDockerImage() throws Exception {
        logger.info("Pulling Oracle DB image from OCIIR ...");

        pullDockerImage(ORACLE_DB_IMG, ORACLE_DB_IMG_TAG);
    }

    private static void pullDockerImage(String imagename, String imagetag) throws Exception {

        String cmd = "docker pull " + imagename + ":" + imagetag;
        logger.info("executing command: " + cmd);
        ExecResult result = ExecCommand.exec(cmd, true);
        logger.info("DEBUG: result.stderr=" + result.stderr() );

        // verify the docker image is pulled
        result = ExecCommand.exec("docker images | grep " + imagename  + " | grep " +
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

    protected static void executeNoVerify(String command) throws Exception {
        logger.info("executing command: " + command);
        ExecCommand.exec(command, true);
    }

    protected void verifyResult(ExecResult result, String matchString) throws Exception {
        if(result.exitValue() != 0 || !result.stdout().contains(matchString)) {
            logger.info("DEBUG: result.exitValue=" + result.exitValue());
            logger.info("DEBUG: result.stdout=" + result.stdout());
            System.exit(0);
            throw new Exception("result stdout does not contains the expected string: " + matchString);
        }
    }

    protected static void verifyExitValue(ExecResult result, String command) throws Exception {
        if(result.exitValue() != 0) {
            logger.info(result.stderr());
            throw new Exception("executing the following command failed: " + command);
        }
    }

    protected void verifyErrorMsg(ExecResult result, String errorMsg) throws Exception {
        if(result.exitValue() == 0 || !result.stderr().contains(errorMsg)) {
            logger.info("DEBUG: result stderr: " + result.stderr());
            throw new Exception("test result does not contain the expected error msg: " + errorMsg);
        }
    }

    protected void verifyModelFile(String modelFile) throws Exception {
        String cmd = "ls " + modelFile + " | wc -l";
        logger.info("executing command: " + cmd);
        ExecResult result = ExecCommand.exec(cmd);
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

    protected void logTestBegin(String testMethodName) throws Exception {
        logger.info("=======================================");
        logger.info("BEGIN test " + testMethodName + " ...");
    }

    protected void logTestEnd(String testMethodName) throws Exception {
        logger.info("SUCCESS - " + testMethodName);
        logger.info("=======================================");
    }

    protected static String getResourcePath() {
        return getProjectRoot() + FS + "src" + FS + "test" + FS + "resources";
    }

    protected static String getGeneratedResourcePath() {
        return getTargetDir() + FS + "resources";
    }

    protected static ExecResult buildSampleArchive() throws Exception {
        logger.info("Building WDT archive ...");
        String command = "sh " + getResourcePath() + FS + "build-archive.sh";
        return executeAndVerify(command, true);
    }

    protected static String getSampleArchiveFile() throws Exception {
        return getGeneratedResourcePath() + FS + SAMPLE_ARCHIVE_FILE;
    }

    protected static String getSampleModelFile(String suffix) throws Exception {
        return getResourcePath() + FS + SAMPLE_MODEL_FILE_PREFIX + suffix + ".yaml";
    }

    protected static String getInstallerTargetDir() throws Exception {
        return getProjectRoot() + FS + ".." + FS + "installer" + FS + "target";
    }

    protected static String getSampleVariableFile() throws Exception {
        return getResourcePath() + FS + SAMPLE_VARIABLE_FILE;
    }

    protected static void createDBContainer() throws Exception {
        logger.info("Creating an Oracle db docker container ...");
        String command = "docker rm -f " + DB_CONTAINER_NAME;
        ExecCommand.exec(command);
        command = "docker run -d --name " + DB_CONTAINER_NAME + " --env=\"DB_PDB=InfraPDB1\"" +
                " --env=\"DB_DOMAIN=us.oracle.com\" --env=\"DB_BUNDLE=basic\" " + ORACLE_DB_IMG + ":" +
                ORACLE_DB_IMG_TAG;
        ExecCommand.exec(command);

        // wait for the db is ready
        command = "docker ps | grep " + DB_CONTAINER_NAME;
        checkCmdInLoop(command, "healthy");
    }

    protected static void replaceStringInFile(String filename, String originalString, String newString)
            throws Exception {
        Path path = Paths.get(filename);

        String content = new String(Files.readAllBytes(path));
        content = content.replaceAll(originalString, newString);
        Files.write(path, content.getBytes());
    }

    protected String getDBContainerIP() throws Exception {
        String getDBContainerIP = "docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' " +
                DB_CONTAINER_NAME;
        String dbhost = ExecCommand.exec(getDBContainerIP).stdout().trim();
        logger.info("DEBUG: DB_HOST=" + dbhost);
        return dbhost;
    }

    protected void verifyModelFileContents(String modelFileName, List<String> textToFind) throws Exception {
        BufferedReader model = inputYaml(modelFileName);
        List<String> checkList = new ArrayList(textToFind);
        while (model.ready()) {
            String nextLine = model.readLine();
            if (nextLine != null) {
                for (String textLine : textToFind) {
                    if (nextLine.indexOf(textLine) >=0 ) {
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

    private static ExecResult executeAndVerify(String command, boolean isRedirectToOut) throws Exception {
        logger.info("Executing command: " + command);
        ExecResult result = ExecCommand.exec(command, isRedirectToOut);
        verifyExitValue(result, command);
        logger.info(result.stdout());
        return result;
    }

    private static void checkCmdInLoop(String cmd, String matchStr)
            throws Exception {
        int i = 0;
        while (i < maxIterations) {
            ExecResult result = ExecCommand.exec(cmd);

            // pod might not have been created or if created loop till condition
            if (result.exitValue() != 0
                    || (result.exitValue() == 0 && !result.stdout().contains(matchStr))) {
                logger.info("Output for " + cmd + "\n" + result.stdout() + "\n " + result.stderr());
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
                logger.info("get the expected String " + matchStr);
                break;
            }
        }
    }
}
