/*
 * Copyright (c) 2017, 2025, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.create;

import java.io.File;
import java.util.ArrayList;
import java.util.Arrays;
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
import org.python.core.PyObject;
import org.python.core.PyString;

import static oracle.weblogic.deploy.create.ValidationUtils.validateExistingDirectory;
import static oracle.weblogic.deploy.create.ValidationUtils.validateExistingExecutableFile;


/**
 * This class does all the work to drop and recreate the RCU schemas based on the domain type definition.
 */
public class RCURunner {
    public static final String ORACLE_DB_TYPE = "ORACLE";
    public static final String EBR_DB_TYPE = "EBR";
    public static final String SQLSERVER_DB_TYPE = "SQLSERVER";
    public static final String DB2_DB_TYPE = "IBMDB2";
    public static final String MYSQL_DB_TYPE = "MYSQL";

    public static final String ORACLE_ATP_DB_TYPE = "ATP";
    public static final String ORACLE_SSL_DB_TYPE = "SSL";

    public static final String TABLESPACE_SWITCH = "-tablespace";
    public static final String TEMP_TABLESPACE_SWITCH = "-tempTablespace";
    public static final String VARIABLES_SWITCH =  "-variables";
    public static final String COMPONENT_INFO_LOCATION_SWITCH = "-compInfoXMLLocation";
    public static final String STORAGE_LOCATION_SWITCH = "-storageXMLLocation";
    public static final String EDITION_SWITCH = "-edition";
    public static final String UNICODE_SUPPORT = "-unicodeSupport";

    // Any args passed to the constructor in the extraRcuArgsMap will be used
    // for both dropRepository and createRepository unless added to this list.
    //
    public static final List<String> CREATE_ONLY_EXTRA_RCU_ARGS =
        Arrays.asList(TABLESPACE_SWITCH, TEMP_TABLESPACE_SWITCH);

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
    private static final String USER_SAME_PWD_FOR_ALL ="-useSamePasswordForAllSchemaUsers";
    private static final String DB_CONNECT_SWITCH = "-connectString";
    private static final String DB_USER_SWITCH = "-dbUser";
    private static final String DB_ROLE_SWITCH = "-dbRole";
    private static final String SCHEMA_PREFIX_SWITCH = "-schemaPrefix";
    private static final String COMPONENT_SWITCH = "-component";
    private static final String READ_STDIN_SWITCH = "-f";
    private static final String USE_SSL_SWITCH = "-useSSL";
    private static final String SERVER_DN_SWITCH = "-serverDN";
    private static final String SSLARGS = "-sslArgs";

    private static final Pattern SCHEMA_DOES_NOT_EXIST_PATTERN = Pattern.compile("(ORA-01918|RCU-6013[^0-9])");
    private static final Pattern SCHEMA_ALREADY_EXISTS_PATTERN = Pattern.compile("RCU-6016[^0-9]");

    private final File oracleHome;
    private final File javaHome;
    private final String databaseType;
    private final String connectString;
    private final String schemaPrefix;
    private final String dbUser;
    private final String dbRole;
    private final List<String> componentsList;
    private final PyDictionary extraRcuArgsMap;
    private final PyDictionary sslArgsProperties;
    private final boolean sslDB;
    private final boolean atpDB;

    /**
     * The constructor.
     *
     * @param oracleHome        the ORACLE_HOME location
     * @param javaHome          the JAVA_HOME location
     * @param databaseType      the databaseType argument for RCU (ORACLE|SQLSERVER|IBMDB2|MYSQL|EBR)
     * @param connectString     the database connect string
     * @param schemaPrefix      the schema prefix
     * @param dbUser            the database administrator user name
     * @param dbRole            the database administrator role
     * @param componentsList    the list of RCU schemas
     * @param extraRcuArgsMap   any extra RCU arguments map
     * @param sslArgsProperties the SSL-related arguments map
     * @throws CreateException  if a parameter validation error occurs
     */
    public RCURunner(String oracleHome, String javaHome, String databaseType, String oracleDatabaseConnectionType,
                     String connectString, String schemaPrefix, String dbUser, String dbRole,
                     List<String> componentsList, PyDictionary extraRcuArgsMap, PyDictionary sslArgsProperties)
        throws CreateException {

        this.oracleHome = validateExistingDirectory(oracleHome, "ORACLE_HOME");
        this.javaHome = validateExistingDirectory(javaHome, "JAVA_HOME");

        this.databaseType = validateNonEmptyString(databaseType, "rcu_database_type");
        this.sslDB = ORACLE_SSL_DB_TYPE.equals(oracleDatabaseConnectionType);
        this.atpDB = ORACLE_ATP_DB_TYPE.equals(oracleDatabaseConnectionType);

        // The rcu_db_conn_string could be in the long format so quote the argument
        // to prevent the shell from trying to interpret the parens...
        //
        this.connectString = quoteStringForCommandLine(connectString, "rcu_db_conn_string");

        this.schemaPrefix = validateNonEmptyString(schemaPrefix, "rcu_prefix");
        this.dbUser = validateNonEmptyString(dbUser, "rcu_admin_user");
        this.dbRole = dbRole;
        this.componentsList = validateNonEmptyListOfStrings(componentsList, "rcu_schema_list");
        this.extraRcuArgsMap = extraRcuArgsMap;
        this.sslArgsProperties = sslArgsProperties;
    }

    /**
     * Run RCU to drop and recreate the RCU schemas.
     *
     * @param rcuSysPass    the RCU database SYS password
     * @param rcuSchemaPass the RCU database schema password to use for all RCU schemas
     * @throws CreateException if an error occurs with parameter validation or running RCU
     */
    public void runRcu(String rcuSysPass, String rcuSchemaPass, boolean disableRcuDropSchema) throws CreateException {
        final String METHOD = "runRcu";

        File rcuBinDir = new File(new File(oracleHome, "oracle_common"), "bin");
        File rcuScript = FileUtils.getCanonicalFile(new File(rcuBinDir, RCU_SCRIPT_NAME));

        validateExistingExecutableFile(rcuScript, RCU_SCRIPT_NAME);
        validateNonEmptyString(rcuSysPass, "rcu_admin_password", true);
        validateNonEmptyString(rcuSchemaPass, "rcu_schema_password", true);

        if (!disableRcuDropSchema) {
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
        }

        Map<String, String> createEnv = getRcuCreateEnv();
        String[] scriptArgs = getCommandLineArgs(CREATE_REPO_SWITCH);
        List<String> scriptStdinLines = getRcuCreateStdinLines(rcuSysPass, rcuSchemaPass);
        ScriptRunner runner = new ScriptRunner(createEnv, RCU_CREATE_LOG_BASENAME);
        int exitCode;
        try {
            exitCode = runner.executeScript(rcuScript, scriptStdinLines, scriptArgs);
        } catch (ScriptRunnerException sre) {
            CreateException ce = new CreateException("WLSDPLY-12003", sre, CLASS, sre.getLocalizedMessage());
            LOGGER.throwing(CLASS, METHOD, ce);
            throw ce;
        }
        if (exitCode != 0) {
            if (disableRcuDropSchema && isSchemaAlreadyExistsError(runner)) {
                CreateException ce = new CreateException("WLSDPLY-12010", CLASS, schemaPrefix, runner.getStdoutFileName());
                LOGGER.throwing(CLASS, METHOD, ce);
                throw ce;
            } else {
                CreateException ce = new CreateException("WLSDPLY-12002", CLASS, exitCode, runner.getStdoutFileName());
                LOGGER.throwing(CLASS, METHOD, ce);
                throw ce;
            }
        }
    }

    ///////////////////////////////////////////////////////////////////////////
    // Private helper methods                                                //
    ///////////////////////////////////////////////////////////////////////////

    private boolean isOracleDatabase() {
        return ORACLE_DB_TYPE.equals(this.databaseType) || EBR_DB_TYPE.equals(this.databaseType);
    }

    private Map<String, String> getRcuDropEnv() {
        Map<String, String> env = new HashMap<>(1);
        env.put("JAVA_HOME", this.javaHome.getAbsolutePath());
        addOracleDatabaseSSLEnv(env);
        return env;
    }

    private Map<String, String> getRcuCreateEnv() {
        return getRcuDropEnv();
    }

    private void addOracleDatabaseSSLEnv(Map<String, String> env) {
        if (isOracleDatabase()) {
            if (atpDB || sslDB) {
                env.put("RCU_SSL_MODE", "true");
                env.put("SKIP_CONNECTSTRING_VALIDATION", "true");
                env.put("RCU_SKIP_PRE_REQS", "ALL");
            }
        }
    }

    private String getSSLArgs() {
        String result = null;
        if (this.sslArgsProperties != null) {
            StringBuilder sslArgs = new StringBuilder();

            for (Object connectionProperty : this.sslArgsProperties.keys()) {
                if (sslArgs.length() > 0) {
                    sslArgs.append(',');
                }
                String key = connectionProperty.toString();
                String value = get(this.sslArgsProperties, key);
                if (!StringUtils.isEmpty(value)) {
                    sslArgs.append(key);
                    sslArgs.append('=');
                    sslArgs.append(value);
                }
            }
            if (sslArgs.length() > 0) {
                result = sslArgs.toString();
            }
        }
        return result;
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

        arguments.add(DB_TYPE_SWITCH);
        arguments.add(this.databaseType);

        if (isCreate) {
            arguments.add(USER_SAME_PWD_FOR_ALL);
            arguments.add("true");
        }

        arguments.add(DB_CONNECT_SWITCH);
        arguments.add(this.connectString);
        arguments.add(DB_USER_SWITCH);
        arguments.add(this.dbUser);
        if (this.dbRole != null) {
            arguments.add(DB_ROLE_SWITCH);
            arguments.add(this.dbRole);
        }

        if (this.atpDB || this.sslDB) {
            arguments.add(USE_SSL_SWITCH);
            arguments.add(SSLARGS);
            arguments.add(getSSLArgs());
        }

        if (atpDB) {
            arguments.add(SERVER_DN_SWITCH);
            arguments.add("CN=ignored");
        }

        arguments.add(SCHEMA_PREFIX_SWITCH);
        arguments.add(schemaPrefix);

        String tablespace = isCreate ? get(this.extraRcuArgsMap, TABLESPACE_SWITCH) : null;
        String tempTablespace = isCreate ? get(this.extraRcuArgsMap, TEMP_TABLESPACE_SWITCH) : null;
        List<String> extraArgsAlreadyProcessed =
            new ArrayList<>(Arrays.asList(TABLESPACE_SWITCH, TEMP_TABLESPACE_SWITCH));
        for (String rcuSchema : componentsList) {
            arguments.add(COMPONENT_SWITCH);
            arguments.add(rcuSchema);
            if (isCreate) {
                if (!StringUtils.isEmpty(tablespace)) {
                    arguments.add(TABLESPACE_SWITCH);
                    arguments.add(tablespace);
                }
                if (!StringUtils.isEmpty(tempTablespace)) {
                    arguments.add(TEMP_TABLESPACE_SWITCH);
                    arguments.add(tempTablespace);
                }
            }
        }

        if (this.extraRcuArgsMap != null) {
            for (Object rcuArgsKeyObject : this.extraRcuArgsMap.keys()) {
                String key = rcuArgsKeyObject.toString();
                if (extraArgsAlreadyProcessed.contains(key)) {
                    continue;
                } else if (!isCreate && CREATE_ONLY_EXTRA_RCU_ARGS.contains(key)) {
                    continue;
                }

                String value = get(this.extraRcuArgsMap, key);
                if (!StringUtils.isEmpty(value)) {
                    arguments.add(key);
                    arguments.add(value);
                }
            }
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

    private static boolean isSchemaAlreadyExistsError(ScriptRunner runner) {
        List<String> stdoutBuffer = runner.getStdoutBuffer();
        boolean schemaAlreadyExists = false;
        for (String line : stdoutBuffer) {
            Matcher matcher = SCHEMA_ALREADY_EXISTS_PATTERN.matcher(line);
            if (matcher.find()) {
                schemaAlreadyExists = true;
                break;
            }
        }
        return schemaAlreadyExists;
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

    /**
     * Extract the specified string from the specified python dictionary.
     */
    private static String get(PyDictionary dictionary, String key) {
        String result = null;
        if (dictionary.has_key(new PyString(key))) {
            PyObject value = dictionary.get(new PyString(key));
            if (value != null) {
                result = value.toString();
                if (result.equals("None")) {
                    result = null;
                }
            }
        }
        return result;
    }

    /**
     * RCU Operation Type enum.
     */
    private enum RcuOpType { DROP, CREATE}
}

