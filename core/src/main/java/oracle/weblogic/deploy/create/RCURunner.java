/*
 * Copyright (c) 2017, 2019, Oracle and/or its affiliates. All rights reserved.
 * Licensed under the Universal Permissive License v 1.0 as shown at http://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.create;

import java.io.File;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import oracle.weblogic.deploy.logging.PlatformLogger;
import oracle.weblogic.deploy.logging.WLSDeployLogFactory;
import oracle.weblogic.deploy.util.FileUtils;
import oracle.weblogic.deploy.util.ScriptRunner;
import oracle.weblogic.deploy.util.ScriptRunnerException;
import oracle.weblogic.deploy.util.StringUtils;

import org.python.core.PyDictionary;
import org.python.core.PyString;


/**
 * This class does all the work to drop and recreate the RCU schemas besed on the domain type definition.
 */
public class RCURunner {
    private static final String CLASS = RCURunner.class.getName();
    private static final PlatformLogger LOGGER = WLSDeployLogFactory.getLogger("wlsdeploy.create");
    private static final String MASK = "********";

    private static final boolean WINDOWS = File.separatorChar == '\\';
    private static final String RCU_SCRIPT_NAME = WINDOWS ? "rcu.bat" : "rcu";
    private static final String RCU_DROP_LOG_BASENAME = "rcuDropSchemas";
    private static final String RCU_CREATE_LOG_BASENAME = "rcuCreateSchemas";

    private static final String SILENT_SWITCH = "-silent";
    private static final String DROP_REPO_SWITCH = "-dropRepository";
    private static final String CREATE_REPO_SWITCH = "-createRepository";
    private static final String DB_TYPE_SWITCH = "-databaseType";
    private static final String ORACLE_DB_TYPE = "ORACLE";
    private static final String USER_SAME_PWD_FOR_ALL ="-useSamePasswordForAllSchemaUsers";
    private static final String DB_CONNECT_SWITCH = "-connectString";
    private static final String DB_USER_SWITCH = "-dbUser";
    private static final String DB_USER = "SYS";
    private static final String DB_ROLE_SWITCH = "-dbRole";
    private static final String DB_ROLE = "SYSDBA";
    private static final String SCHEMA_PREFIX_SWITCH = "-schemaPrefix";
    private static final String COMPONENT_SWITCH = "-component";
    private static final String TABLESPACE_SWITCH = "-tablespace";
    private static final String TEMPTABLESPACE_SWITCH = "-tempTablespace";
    private static final String RCU_VARIABLES_SWITCH =  "-variables";
    private static final String READ_STDIN_SWITCH = "-f";
    private static final String USE_SSL_SWITCH = "-useSSL";
    private static final String SERVER_DN_SWITCH = "-serverDN";
    private static final String SSLARGS = "-sslArgs";

    private static final String SERVICE_TABLE_COMPONENT = "STB";
    private static final String WLS_COMPONENT = "WLS";
    private static final String WLS_RUNTIME_COMPONENT = "WLS_RUNTIME";

    private static final Pattern SCHEMA_DOES_NOT_EXIST_PATTERN = Pattern.compile("(ORA-01918|RCU-6013|ORA-12899)");

    private static final int RCU_CREATE_COMMON_ARG_COUNT = 13;

    // +2 for -component STB
    private static final int RCU_DROP_COMMON_ARG_COUNT = RCU_CREATE_COMMON_ARG_COUNT + 2;

    private File oracleHome;
    private File javaHome;
    private String rcuDb;
    private String rcuPrefix;
    private List<String> rcuSchemas;
    private boolean ATP_DB = false;
    private String atpSSlArgs = null;
    private String atpAdminUser = null;
    private String atpDefaultTablespace = null;
    private String atpTemporaryTablespace = null;
    private String rcuVariables = null;

    /**
     * The constructor.
     *
     * @param domainType the domain type
     * @param oracleHome the ORACLE_HOME location
     * @param javaHome   the JAVA_HOME location
     * @param rcuDb      the RCU database connect string
     * @param rcuPrefix  the RCU prefix to use
     * @param rcuSchemas the list of RCU schemas to create (this list should not include STB)
     * @throws CreateException if a parameter validation error occurs
     */
    public RCURunner(String domainType, String oracleHome, String javaHome, String rcuDb, String rcuPrefix,
        List<String> rcuSchemas, String rcuVariables) throws CreateException {

        this.oracleHome = validateExistingDirectory(oracleHome, "ORACLE_HOME");
        this.javaHome = validateExistingDirectory(javaHome, "JAVA_HOME");
        this.rcuDb = validateNonEmptyString(rcuDb, "rcu_db");
        this.rcuPrefix = validateNonEmptyString(rcuPrefix, "rcu_prefix");
        this.rcuSchemas = validateNonEmptyListOfStrings(rcuSchemas, "rcu_schema_list");
        this.rcuVariables = rcuVariables;
//        if (this.rcuSchemas.contains(SERVICE_TABLE_COMPONENT)) {
//            LOGGER.warning("WLSDPLY-12000", CLASS, domainType, SERVICE_TABLE_COMPONENT);
//            this.rcuSchemas.remove(SERVICE_TABLE_COMPONENT);
//        }
    }

    /**
     * The constructor - used only by ATP database
     *
     * @param domainType the domain type
     * @param oracleHome the ORACLE_HOME location
     * @param javaHome   the JAVA_HOME location
     * @throws CreateException if a parameter validation error occurs
     */
    public RCURunner(String domainType, String oracleHome, String javaHome, List<String> rcuSchemas,
        PyDictionary rcuProperties, String rcuVariables)
        throws CreateException {


        String tnsAdmin = rcuProperties.get(new PyString("oracle.net.tns_admin")).toString();
        String keyStorePassword = rcuProperties.get(new PyString("javax.net.ssl.keyStorePassword")).toString();
        String trustStorePassword = rcuProperties.get(new PyString("javax.net.ssl.trustStorePassword")).toString();

        StringBuffer sslArgs = new StringBuffer();
        sslArgs.append("oracle.net.tns_admin=");
        sslArgs.append(tnsAdmin);
        sslArgs.append(",oracle.net.ssl_version=1.2");
        sslArgs.append(",javax.net.ssl.trustStore=");
        sslArgs.append(tnsAdmin + "/truststore.jks");
        sslArgs.append(",javax.net.ssl.trustStoreType=JKS");
        sslArgs.append(",javax.net.ssl.trustStorePassword=");
        sslArgs.append(trustStorePassword);
        sslArgs.append(",javax.net.ssl.keyStore=");
        sslArgs.append(tnsAdmin + "/keystore.jks");
        sslArgs.append(",javax.net.ssl.keyStoreType=JKS");
        sslArgs.append(",javax.net.ssl.keyStorePassword=");
        sslArgs.append(keyStorePassword);
        sslArgs.append(",oracle.jdbc.fanEnabled=false");
        sslArgs.append(",oracle.net.ssl_server_dn_match=true");

        ATP_DB = true;
        atpSSlArgs = sslArgs.toString();

        this.oracleHome = validateExistingDirectory(oracleHome, "ORACLE_HOME");
        this.javaHome = validateExistingDirectory(javaHome, "JAVA_HOME");
        this.rcuDb = "jdbc:oracle:thin:@" + rcuProperties.get(new PyString("tns.alias")).toString();
        this.rcuPrefix = rcuProperties.get(new PyString("rcu_prefix")).toString();
        this.rcuSchemas = validateNonEmptyListOfStrings(rcuSchemas, "rcu_schema_list");
        this.atpAdminUser = rcuProperties.get(new PyString("atp.admin.user")).toString();
        this.atpDefaultTablespace = rcuProperties.get(new PyString("atp.default.tablespace")).toString();
        this.atpTemporaryTablespace = rcuProperties.get(new PyString("atp.temp.tablespace")).toString();
        this.rcuVariables = rcuVariables;

//        if (!this.rcuSchemas.contains(SERVICE_TABLE_COMPONENT)) {
//            LOGGER.warning("WLSDPLY-12000", CLASS, domainType, SERVICE_TABLE_COMPONENT);
//            this.rcuSchemas.add(SERVICE_TABLE_COMPONENT);
//        }
    }


    /**
     * Run RCU to drop and recreate the RCU schemas.
     *
     * @param rcuSysPass    the RCU database SYS password
     * @param rcuSchemaPass the RCU database schema password to use for all RCU schemas
     * @throws CreateException if an error occurs with parameter validation or running RCU
     */
    public void runRcu(String rcuSysPass, String rcuSchemaPass) throws CreateException {
        final String METHOD = "runRcu";

        File rcuBinDir = new File(new File(oracleHome, "oracle_common"), "bin");
        File rcuScript = FileUtils.getCanonicalFile(new File(rcuBinDir, RCU_SCRIPT_NAME));

        validateExistingExecutableFile(rcuScript, RCU_SCRIPT_NAME);
        validateNonEmptyString(rcuSysPass, "rcu_sys_password", true);
        validateNonEmptyString(rcuSchemaPass, "rcu_schema_password", true);

        Map<String, String> dropEnv = getRcuDropEnv();
        String[] scriptArgs = getRcuDropArgs();
        List<String> scriptStdinLines = getRcuDropStdinLines(rcuSysPass, rcuSchemaPass);
        ScriptRunner runner = new ScriptRunner(dropEnv, RCU_DROP_LOG_BASENAME);
        int exitCode;
        try {
            exitCode = runner.executeScript(rcuScript, scriptStdinLines, scriptArgs);
        } catch (ScriptRunnerException sre) {
            CreateException ce = new CreateException("WLSDPLY-12001", sre, CLASS, sre.getLocalizedMessage());
            LOGGER.throwing(CLASS, METHOD, ce);
            throw ce;
        }
        // RCU is stupid and RCU drop exits with exit code 1 if the schemas do not exist...sigh
        //
        if (exitCode != 0 && !isSchemaNotExistError(runner)) {
            CreateException ce = new CreateException("WLSDPLY-12002", CLASS, exitCode, runner.getStdoutFileName());
            LOGGER.throwing(CLASS, METHOD, ce);
            throw ce;
        }

        Map<String, String> createEnv = getRcuCreateEnv();
        scriptArgs = getRcuCreateArgs();
        scriptStdinLines = getRcuCreateStdinLines(rcuSysPass, rcuSchemaPass);
        runner = new ScriptRunner(createEnv, RCU_CREATE_LOG_BASENAME);
        try {
            exitCode = runner.executeScript(rcuScript, scriptStdinLines, scriptArgs);
            if (ATP_DB && exitCode != 0 && isSchemaNotExistError(runner)) {
                exitCode = 0;
            }
        } catch (ScriptRunnerException sre) {
            CreateException ce = new CreateException("WLSDPLY-12003", sre, CLASS, sre.getLocalizedMessage());
            LOGGER.throwing(CLASS, METHOD, ce);
            throw ce;
        }
        if (exitCode != 0) {
            CreateException ce = new CreateException("WLSDPLY-12002", CLASS, exitCode, runner.getStdoutFileName());
            LOGGER.throwing(CLASS, METHOD, ce);
            throw ce;
        }
    }

    ///////////////////////////////////////////////////////////////////////////
    // Private helper methods                                                //
    ///////////////////////////////////////////////////////////////////////////

    private void addATPEnv(Map<String, String> env) {
        if (ATP_DB) {
            env.put("RCU_SSL_MODE", "true");
            env.put("SKIP_CONNECTSTRING_VALIDATION", "true");
            env.put("RCU_SKIP_PRE_REQS", "ALL");
        }
    }


    private Map<String, String> getRcuDropEnv() {
        Map<String, String> env = new HashMap<>(1);
        env.put("JAVA_HOME", this.javaHome.getAbsolutePath());
        addATPEnv(env);
        return env;
    }

    private Map<String, String> getRcuCreateEnv() {
        return getRcuDropEnv();
    }

    private String[] getRcuDropArgs() {
        List<String> dropArgs = new ArrayList<>(RCU_DROP_COMMON_ARG_COUNT + (2 * rcuSchemas.size()));
        dropArgs.add(SILENT_SWITCH);
        dropArgs.add(DROP_REPO_SWITCH);
        dropArgs.add(DB_TYPE_SWITCH);
        dropArgs.add(ORACLE_DB_TYPE);
        dropArgs.add(DB_CONNECT_SWITCH);
        dropArgs.add(rcuDb);

        if (ATP_DB) {
            dropArgs.add(DB_USER_SWITCH);
            dropArgs.add(this.atpAdminUser);
            dropArgs.add(USE_SSL_SWITCH);
            dropArgs.add("true");
            dropArgs.add(SERVER_DN_SWITCH);
            dropArgs.add("CN=ignored");
            dropArgs.add(SSLARGS);
            dropArgs.add(atpSSlArgs);

        } else {
            dropArgs.add(DB_USER_SWITCH);
            dropArgs.add(DB_USER);
            dropArgs.add(DB_ROLE_SWITCH);
            dropArgs.add(DB_ROLE);
        }
        dropArgs.add(SCHEMA_PREFIX_SWITCH);
        dropArgs.add(rcuPrefix);

        for (String rcuSchema : rcuSchemas) {
            dropArgs.add(COMPONENT_SWITCH);
            dropArgs.add(rcuSchema);
        }
        // Add STB to the drop list since it is never specified in the create list...
//        dropArgs.add(COMPONENT_SWITCH);
//        dropArgs.add(SERVICE_TABLE_COMPONENT);

        dropArgs.add(READ_STDIN_SWITCH);

        String[] result = new String[dropArgs.size()];
        return dropArgs.toArray(result);
    }

    private String[] getRcuCreateArgs() {
        List<String> createArgs = new ArrayList<>(RCU_CREATE_COMMON_ARG_COUNT + (2 * rcuSchemas.size()));
        createArgs.add(SILENT_SWITCH);
        createArgs.add(CREATE_REPO_SWITCH);
        createArgs.add(DB_TYPE_SWITCH);
        createArgs.add(ORACLE_DB_TYPE);
        createArgs.add(USER_SAME_PWD_FOR_ALL);
        createArgs.add("true");
        createArgs.add(DB_CONNECT_SWITCH);
        createArgs.add(rcuDb);
        if (ATP_DB) {
            createArgs.add(DB_USER_SWITCH);
            createArgs.add(this.atpAdminUser);
            createArgs.add(USE_SSL_SWITCH);
            createArgs.add("true");
            createArgs.add(SERVER_DN_SWITCH);
            createArgs.add("CN=ignored");
            createArgs.add(SSLARGS);
            createArgs.add(atpSSlArgs);
        } else {
            createArgs.add(DB_USER_SWITCH);
            createArgs.add(DB_USER);
            createArgs.add(DB_ROLE_SWITCH);
            createArgs.add(DB_ROLE);
        }
        createArgs.add(SCHEMA_PREFIX_SWITCH);
        createArgs.add(rcuPrefix);

        for (String rcuSchema : rcuSchemas) {
            createArgs.add(COMPONENT_SWITCH);
            createArgs.add(rcuSchema);
            if (ATP_DB) {
                createArgs.add(TABLESPACE_SWITCH);
                createArgs.add(this.atpDefaultTablespace);
                createArgs.add(TEMPTABLESPACE_SWITCH);
                createArgs.add(this.atpTemporaryTablespace);
            }
        }
        if (rcuVariables != null) {
            createArgs.add(RCU_VARIABLES_SWITCH);
            createArgs.add(this.rcuVariables);
        }
        createArgs.add(READ_STDIN_SWITCH);

        String[] result = new String[createArgs.size()];
        return createArgs.toArray(result);
    }

    private List<String> getRcuDropStdinLines(String rcuSysPass, String rcuSchemaPass) {
        return getRcuStdinLines(RcuOpType.DROP, rcuSysPass, rcuSchemaPass);
    }

    private List<String> getRcuCreateStdinLines(String rcuSysPass, String rcuSchemaPass) {
        return getRcuStdinLines(RcuOpType.CREATE, rcuSysPass, rcuSchemaPass);
    }

    private List<String> getRcuStdinLines(RcuOpType rcuOpType, String rcuSysPass, String rcuSchemaPass) {
        List<String> stdinLines = new ArrayList<>(2);
        stdinLines.add(rcuSysPass);
        stdinLines.add(rcuSchemaPass);

        return stdinLines;
    }

    private int getExtraRcuSchemaPasswordCount(RcuOpType rcuOpType) {
        int result = 0;

        if (!rcuSchemas.contains(SERVICE_TABLE_COMPONENT)) {
            result++;
        }
        if (rcuOpType == RcuOpType.CREATE &&
            rcuSchemas.contains(WLS_COMPONENT) &&
            !rcuSchemas.contains(WLS_RUNTIME_COMPONENT)) {
            result++;
        }
        return result;
    }

    private static boolean isSchemaNotExistError(ScriptRunner runner) {
        List<String> stdoutBuffer = runner.getStdoutBuffer();
        boolean schemaDoesNotExist = false;
        for (String line : stdoutBuffer) {
            Matcher matcher = SCHEMA_DOES_NOT_EXIST_PATTERN.matcher(line);
            if (matcher.find()) {
                schemaDoesNotExist = true;
                break;
            }
        }
        return schemaDoesNotExist;
    }

    private static boolean isValueTooLargeError(ScriptRunner runner) {
        List<String> stdoutBuffer = runner.getStdoutBuffer();
        boolean schemaDoesNotExist = false;
        for (String line : stdoutBuffer) {
            Matcher matcher = SCHEMA_DOES_NOT_EXIST_PATTERN.matcher(line);
            if (matcher.find()) {
                schemaDoesNotExist = true;
                break;
            }
        }
        return schemaDoesNotExist;
    }

    private static File validateExistingDirectory(String directoryName, String directoryTypeName)
        throws CreateException {
        final String METHOD = "validateExistingDirectory";

        LOGGER.entering(CLASS, METHOD, directoryName, directoryTypeName);
        File result;
        try {
            result = FileUtils.validateExistingDirectory(directoryName);
        } catch (IllegalArgumentException iae) {
            CreateException ce = new CreateException("WLSDPLY-12004", iae, CLASS, directoryTypeName,
                directoryName, iae.getLocalizedMessage());
            LOGGER.throwing(CLASS, METHOD, ce);
            throw ce;
        }
        LOGGER.exiting(CLASS, METHOD, result);
        return result;
    }

    private static String validateNonEmptyString(String text, String textTypeName) throws CreateException {
        return validateNonEmptyString(text, textTypeName, false);
    }

    private static String validateNonEmptyString(String text, String textTypeName, boolean mask)
        throws CreateException {
        final String METHOD = "validateNonEmptyString";

        String logText = text;
        if (mask) {
            logText = MASK;
        }
        LOGGER.entering(CLASS, METHOD, logText, textTypeName, mask);

        if (StringUtils.isEmpty(text)) {
            CreateException ce = new CreateException("WLSDPLY-12005", CLASS, textTypeName);
            LOGGER.throwing(CLASS, METHOD, ce);
            throw ce;
        }
        LOGGER.exiting(CLASS, METHOD, logText);
        return text;
    }

    private static List<String> validateNonEmptyListOfStrings(List<String> stringList, String stringListTypeName)
        throws CreateException {
        final String METHOD = "validateNonEmptyListOfStrings";

        LOGGER.entering(CLASS, METHOD, stringList, stringListTypeName);
        if (stringList == null || stringList.isEmpty()) {
            CreateException ce = new CreateException("WLSDPLY-12006", CLASS, stringListTypeName);
            LOGGER.throwing(CLASS, METHOD, ce);
            throw ce;
        }

        for (String element : stringList) {
            if (StringUtils.isEmpty(element)) {
                CreateException ce = new CreateException("WLSDPLY-12007", CLASS, stringListTypeName);
                LOGGER.throwing(CLASS, METHOD, ce);
                throw ce;
            }
        }
        LOGGER.exiting(CLASS, METHOD, stringList);
        return stringList;
    }

    private static void validateExistingExecutableFile(File executable, String executableTypeName)
        throws CreateException {
        final String METHOD = "validateExistingExecutableFile";

        LOGGER.entering(CLASS, METHOD, executable, executableTypeName);
        File tmp;
        try {
            tmp = FileUtils.validateExistingFile(executable.getAbsolutePath());
        } catch (IllegalArgumentException iae) {
            CreateException ce = new CreateException("WLSDPLY-12008", iae, CLASS, executableTypeName,
                executable.getAbsolutePath(), iae.getLocalizedMessage());
            LOGGER.throwing(CLASS, METHOD, ce);
            throw ce;
        }
        if (!tmp.canExecute()) {
            CreateException ce =
                new CreateException("WLSDPLY-12009", CLASS, executableTypeName, executable.getAbsolutePath());
            LOGGER.throwing(CLASS, METHOD, ce);
            throw ce;
        }
        LOGGER.exiting(CLASS, METHOD);
    }

    /**
     * RCU Operation Type enum.
     */
    private enum RcuOpType { DROP, CREATE}
}
