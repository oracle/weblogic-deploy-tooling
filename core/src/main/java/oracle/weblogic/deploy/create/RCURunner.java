/*
 * Copyright (c) 2017, 2020, Oracle Corporation and/or its affiliates.  All rights reserved.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
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

import org.python.core.PyClass;
import org.python.core.PyDictionary;
import org.python.core.PyString;


/**
 * This class does all the work to drop and recreate the RCU schemas based on the domain type definition.
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
    private static final String COMPONENT_INFO_LOCATION_SWITCH = "-compInfoXMLLocation";
    private static final String STORAGE_LOCATION_SWITCH = "-storageXMLLocation";

    private static final Pattern SCHEMA_DOES_NOT_EXIST_PATTERN = Pattern.compile("(ORA-01918|RCU-6013|ORA-12899)");

    private final File oracleHome;
    private final File javaHome;
    private final String rcuDb;
    private final String rcuPrefix;
    private final List<String> rcuSchemas;
    private final String rcuVariables;

    private boolean atpDB = false;
    private boolean sslDB = false;
 
    private String atpSSlArgs = null;
    private String atpAdminUser = null;
    private String rcuAdminUser = DB_USER;
    private String atpDefaultTablespace = null;
    private String atpTemporaryTablespace = null;
    private String componentInfoLocation = null;
    private String storageLocation = null;

    /**
     * The private constructor. Callers should use static methods createRunner and createAtpRunner
     * to construct the correct type.
     *
     * @param domainType the domain type
     * @param oracleHome the ORACLE_HOME location
     * @param javaHome   the JAVA_HOME location
     * @param rcuDb      the RCU database connect string
     * @param rcuPrefix  the RCU prefix to use
     * @param rcuSchemas the list of RCU schemas to create (this list should not include STB)
     * @param rcuVariables a comma separated list of key=value variables
     * @throws CreateException if a parameter validation error occurs
     */
    @SuppressWarnings("unused")
    private RCURunner(String domainType, String oracleHome, String javaHome, String rcuDb, String rcuPrefix,
        List<String> rcuSchemas, String rcuVariables) throws CreateException {

        this.oracleHome = validateExistingDirectory(oracleHome, "ORACLE_HOME");
        this.javaHome = validateExistingDirectory(javaHome, "JAVA_HOME");

        // The rcu_db string could be in the long format so quote the argument to prevent the shell
        // from trying to interpret the parens...
        //
        this.rcuDb = quoteStringForCommandLine(rcuDb, "rcu_db");
        this.rcuPrefix = validateNonEmptyString(rcuPrefix, "rcu_prefix");
        this.rcuSchemas = validateNonEmptyListOfStrings(rcuSchemas, "rcu_schema_list");
        this.rcuVariables = rcuVariables;
    }

    /**
     * Build an RCU runner for a standard database.
     *
     * @param domainType the domain type
     * @param oracleHome the ORACLE_HOME location
     * @param javaHome   the JAVA_HOME location
     * @param rcuDb      the RCU database connect string
     * @param rcuPrefix  the RCU prefix to use
     * @param rcuSchemas the list of RCU schemas to create (this list should not include STB)
     * @param rcuVariables a comma separated list of key=value variables
     * @throws CreateException if a parameter validation error occurs
     */
    public static RCURunner createRunner(String domainType, String oracleHome, String javaHome, String rcuDb,
                                         String rcuPrefix, List<String> rcuSchemas,
                                         String rcuVariables) throws CreateException {

        return new RCURunner(domainType, oracleHome, javaHome, rcuDb, rcuPrefix, rcuSchemas, rcuVariables);
    }

    /**
     * Build an RCU runner for an ATP database.
     *
     * @param domainType the domain type
     * @param oracleHome the ORACLE_HOME location
     * @param javaHome   the JAVA_HOME location
     * @param rcuSchemas the list of RCU schemas to create (this list should not include STB)
     * @param rcuVariables a comma separated list of key=value variables
     * @param connectionProperties dictionary of ATP specific arguments
     * @throws CreateException if a parameter validation error occurs
     */
    public static RCURunner createAtpRunner(String domainType, String oracleHome, String javaHome, String rcuDb,
                                            List<String> rcuSchemas, String rcuPrefix, String rcuVariables,
                                            String databaseType, PyDictionary runnerMap,
                                            PyDictionary connectionProperties) throws CreateException {

        RCURunner runner = new RCURunner(domainType, oracleHome, javaHome, rcuDb, rcuPrefix, rcuSchemas, rcuVariables);

        StringBuilder sslArgs = new StringBuilder();

        for (Object connectionProperty: connectionProperties.keys()) {
            if (sslArgs.length() != 0) {
                sslArgs.append(',');
            }
            sslArgs.append(connectionProperty.toString());
            sslArgs.append('=');
            PyDictionary valueObject = (PyDictionary)connectionProperties
                .get(new PyString(connectionProperty.toString()));
            sslArgs.append(valueObject.get(new PyString("Value")));
        }


        addExtraSSLPropertyFromMap(runnerMap, connectionProperties, sslArgs, "javax.net.ssl.keyStorePassword");
        addExtraSSLPropertyFromMap(runnerMap, connectionProperties, sslArgs, "javax.net.ssl.trustStorePassword");


        runner.atpDB = true; // "ATP".equals(databaseType);  // or scan if there are any 'ssl' in properties ?
        runner.atpSSlArgs = sslArgs.toString();

        runner.atpAdminUser = get(runnerMap, "atp.admin.user");
        runner.atpDefaultTablespace = get(runnerMap, "atp.default.tablespace");
        runner.atpTemporaryTablespace = get(runnerMap, "atp.temp.tablespace");

        return runner;
    }

    private static void addExtraSSLPropertyFromMap(PyDictionary runnerMap, PyDictionary connectionProperties,
                                                   StringBuilder sslArgs, String key) {
        if (!connectionProperties.has_key(new PyString(key)) &&
            !get(runnerMap, key).equals("None")) {
            sslArgs.append(",");
            sslArgs.append(key);
            sslArgs.append(get(runnerMap, key));
        }
    }

    /**
     * Build an RCU runner for an SSL database.
     *
     * @param domainType the domain type
     * @param oracleHome the ORACLE_HOME location
     * @param javaHome   the JAVA_HOME location
     * @param rcuDb The URL of the database
     * @param rcuPrefix The prefix used for the tablespaces
     * @param rcuSchemas the list of RCU schemas to create (this list should not include STB)
     * @param rcuVariables a comma separated list of key=value variables
     * @param rcuProperties dictionary of SSL specific arguments
     * @throws CreateException if a parameter validation error occurs
     */
    public static RCURunner createSslRunner(String domainType, String oracleHome, String javaHome, String rcuDb,
                                            String rcuPrefix, List<String> rcuSchemas, String rcuVariables,
                                            PyDictionary rcuProperties) throws CreateException {

        String tnsAdmin = get(rcuProperties, "oracle.net.tns_admin");

        RCURunner runner = new RCURunner(domainType, oracleHome, javaHome, rcuDb, rcuPrefix, rcuSchemas, rcuVariables);
        String trustStorePassword = get(rcuProperties, "javax.net.ssl.trustStorePassword");
        String trustStore = get(rcuProperties, "javax.net.ssl.keyStore");
        String trustStoreType = get(rcuProperties, "javax.net.ssl.keyStoreType");
        String keyStorePassword = get(rcuProperties, "javax.net.ssl.keyStorePassword");
        String keyStore = get(rcuProperties, "javax.net.ssl.keyStore");
        String keyStoreType = get(rcuProperties, "javax.net.ssl.keyStoreType");
        String matchType = get(rcuProperties, "oracle.net.ssl_server_dn_match");
        if (matchType == null || matchType.equals("None"))  {
            matchType = Boolean.FALSE.toString();
        }


        StringBuilder sslArgs = new StringBuilder();
        sslArgs.append("oracle.net.tns_admin=");
        sslArgs.append(tnsAdmin);

        sslArgs.append(",javax.net.ssl.trustStore=");
        sslArgs.append(tnsAdmin + "/" + trustStore);
        sslArgs.append(",javax.net.ssl.trustStoreType=" + trustStoreType);
        // If wallet type is SSO, no password present
        if (trustStorePassword != null && !trustStorePassword.equals("None")) {
            sslArgs.append(",javax.net.ssl.trustStorePassword="+ trustStorePassword);
        }
        sslArgs.append(",javax.net.ssl.keyStore=");
        sslArgs.append(tnsAdmin + "/" + keyStore);
        sslArgs.append(",javax.net.ssl.keyStoreType=" + keyStoreType);
        if (keyStorePassword != null && !keyStorePassword.equals("None")) {
            sslArgs.append(",javax.net.ssl.keyStorePassword="+ keyStorePassword);
        }
        sslArgs.append(",oracle.net.ssl_server_dn_match="+ matchType);

        runner.sslDB = true;
        runner.atpSSlArgs = sslArgs.toString();
        return runner;
    }

    public void setRCUAdminUser(String rcuDBUser) {
        rcuAdminUser = rcuDBUser;
    }

    public String getRCUAdminUser() {
        return rcuAdminUser;
    }

    public void setXmlLocations(String componentInfoLocation, String storageLocation) {
        this.componentInfoLocation = componentInfoLocation;
        this.storageLocation = storageLocation;
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
        String[] scriptArgs = getCommandLineArgs(DROP_REPO_SWITCH);
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
        scriptArgs = getCommandLineArgs(CREATE_REPO_SWITCH);
        scriptStdinLines = getRcuCreateStdinLines(rcuSysPass, rcuSchemaPass);
        runner = new ScriptRunner(createEnv, RCU_CREATE_LOG_BASENAME);
        try {
            exitCode = runner.executeScript(rcuScript, scriptStdinLines, scriptArgs);
            if (atpDB && exitCode != 0 && isSchemaNotExistError(runner)) {
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
        if (atpDB || sslDB) {
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

    /**
     * Build the argument list for the RCU create or drop commands.
     * @param operationSwitch the switch for the RCU operation
     * @return the command-line arguments
     */
    private String[] getCommandLineArgs(String operationSwitch) {
        boolean isCreate = CREATE_REPO_SWITCH.equals(operationSwitch);

        List<String> arguments = new ArrayList<>();
        arguments.add(SILENT_SWITCH);
        arguments.add(operationSwitch);

        if (this.componentInfoLocation != null) {
            arguments.add(COMPONENT_INFO_LOCATION_SWITCH);
            arguments.add(this.componentInfoLocation);
        }

        if (this.storageLocation != null) {
            arguments.add(STORAGE_LOCATION_SWITCH);
            arguments.add(this.storageLocation);
        }

        arguments.add(DB_TYPE_SWITCH);
        arguments.add(ORACLE_DB_TYPE);

        if(isCreate) {
            arguments.add(USER_SAME_PWD_FOR_ALL);
            arguments.add("true");
        }

        arguments.add(DB_CONNECT_SWITCH);
        arguments.add(rcuDb);

        if (atpDB) {
            arguments.add(DB_USER_SWITCH);
            arguments.add(this.atpAdminUser);
            arguments.add(USE_SSL_SWITCH);
            arguments.add("true");
            arguments.add(SERVER_DN_SWITCH);
            arguments.add("CN=ignored");
            arguments.add(SSLARGS);
            arguments.add(atpSSlArgs);
        } else if (sslDB) {
            arguments.add(USE_SSL_SWITCH);
            arguments.add(SSLARGS);
            arguments.add(atpSSlArgs);
            arguments.add(DB_ROLE_SWITCH);
            arguments.add(DB_ROLE);
            arguments.add(DB_USER_SWITCH);
            arguments.add(getRCUAdminUser());
        } else {
            arguments.add(DB_USER_SWITCH);
            arguments.add(getRCUAdminUser());
            arguments.add(DB_ROLE_SWITCH);
            arguments.add(DB_ROLE);
        }

        arguments.add(SCHEMA_PREFIX_SWITCH);
        arguments.add(rcuPrefix);

        for (String rcuSchema : rcuSchemas) {
            arguments.add(COMPONENT_SWITCH);
            arguments.add(rcuSchema);
            if (atpDB && isCreate) {
                arguments.add(TABLESPACE_SWITCH);
                arguments.add(this.atpDefaultTablespace);
                arguments.add(TEMPTABLESPACE_SWITCH);
                arguments.add(this.atpTemporaryTablespace);
            }
        }

        if ((rcuVariables != null) && isCreate) {
            arguments.add(RCU_VARIABLES_SWITCH);
            arguments.add(this.rcuVariables);
        }

        arguments.add(READ_STDIN_SWITCH);

        String[] result = new String[arguments.size()];
        return arguments.toArray(result);
    }

    private List<String> getRcuDropStdinLines(String rcuSysPass, String rcuSchemaPass) {
        return getRcuStdinLines(RcuOpType.DROP, rcuSysPass, rcuSchemaPass);
    }

    private List<String> getRcuCreateStdinLines(String rcuSysPass, String rcuSchemaPass) {
        return getRcuStdinLines(RcuOpType.CREATE, rcuSysPass, rcuSchemaPass);
    }

    @SuppressWarnings("unused")
    private List<String> getRcuStdinLines(RcuOpType rcuOpType, String rcuSysPass, String rcuSchemaPass) {
        List<String> stdinLines = new ArrayList<>(2);
        stdinLines.add(rcuSysPass);
        stdinLines.add(rcuSchemaPass);

        return stdinLines;
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

    private static String quoteStringForCommandLine(String text, String textTypeName) throws CreateException {
        String result = validateNonEmptyString(text, textTypeName);
        return StringUtils.quoteString(result);
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
     * Extract the specified string from the specified python dictionary.
     */
    private static String get(PyDictionary dictionary, String key) {
        return dictionary.get(new PyString(key)).toString();
    }

    /**
     * RCU Operation Type enum.
     */
    private enum RcuOpType { DROP, CREATE}
}

