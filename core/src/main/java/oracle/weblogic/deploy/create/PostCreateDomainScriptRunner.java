/*
 * Copyright (c) 2023, Oracle Corporation and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.create;

import java.io.File;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import oracle.weblogic.deploy.logging.PlatformLogger;
import oracle.weblogic.deploy.logging.WLSDeployLogFactory;
import oracle.weblogic.deploy.util.FileUtils;
import oracle.weblogic.deploy.util.ScriptRunner;
import oracle.weblogic.deploy.util.ScriptRunnerException;

import static oracle.weblogic.deploy.create.ValidationUtils.validateExistingDirectory;
import static oracle.weblogic.deploy.create.ValidationUtils.validateExistingExecutableFile;
import static oracle.weblogic.deploy.create.ValidationUtils.validateNonEmptyString;

public class PostCreateDomainScriptRunner {
    private static final String CLASS = PostCreateDomainScriptRunner.class.getName();
    private static final PlatformLogger LOGGER = WLSDeployLogFactory.getLogger("wlsdeploy.create");
    private static final List<String> EMPTY_STRING_LIST = Collections.emptyList();

    private final File scriptFile;
    private final File javaHome;
    private final File oracleHome;
    private final File domainHome;
    private final String domainName;
    private Map<String, String> environmentVariables;
    public PostCreateDomainScriptRunner(String scriptFileName, String javaHome, String oracleHome, String domainHome,
                                        String domainName) throws CreateException {
        final String METHOD = "<init>";
        LOGGER.entering(CLASS, METHOD, scriptFileName, javaHome, oracleHome, domainHome, domainName);

        this.scriptFile = validateExistingExecutableFile(scriptFileName, "Post Create Domain Script");
        this.javaHome = validateExistingDirectory(javaHome, "JAVA_HOME");
        this.oracleHome = validateExistingDirectory(oracleHome, "ORACLE_HOME");
        this.domainHome = validateExistingDirectory(domainHome, "DOMAIN_HOME");
        this.domainName = validateNonEmptyString(domainName, "DOMAIN_NAME");

        initializeEnvironment();
        LOGGER.exiting(CLASS, METHOD);
    }

    public void runScript() throws CreateException {
        final String METHOD = "runScript";
        LOGGER.entering(CLASS, METHOD);

        String[] fileComponents = FileUtils.parseFileName(this.scriptFile);
        String logFileBaseName = fileComponents.length > 0 ? fileComponents[0] : "postCreateDomainScript";
        ScriptRunner runner = new ScriptRunner(this.environmentVariables, logFileBaseName);

        int exitCode;
        try {
            exitCode = runner.executeScript(this.scriptFile, EMPTY_STRING_LIST);
        } catch (ScriptRunnerException sre) {
            CreateException ce = new CreateException("WLSDPLY-12001", sre, CLASS, this.scriptFile.getAbsolutePath(),
                sre.getLocalizedMessage());
            LOGGER.throwing(CLASS, METHOD, ce);
            throw ce;
        }

        if (exitCode != 0) {
            CreateException ce = new CreateException("WLSDPLY-12014", this.scriptFile.getAbsolutePath(), exitCode,
                runner.getStdoutFileName());
            LOGGER.throwing(CLASS, METHOD, ce);
            throw ce;
        }

        LOGGER.exiting(CLASS, METHOD, exitCode);
    }

    private void initializeEnvironment() {
        Map<String, String> env = new HashMap<>(System.getenv());
        env.put("JAVA_HOME", this.javaHome.getAbsolutePath());
        env.put("ORACLE_HOME", this.oracleHome.getAbsolutePath());
        env.put("DOMAIN_HOME", this.domainHome.getAbsolutePath());
        env.put("DOMAIN_NAME", this.domainName);
        this.environmentVariables = env;
    }
}
