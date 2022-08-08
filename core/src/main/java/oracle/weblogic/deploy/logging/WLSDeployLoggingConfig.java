/*
 * Copyright (c) 2017, 2022, Oracle Corporation and/or its affiliates.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.logging;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.InputStream;
import java.io.IOException;
import java.text.MessageFormat;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;
import java.util.Properties;
import java.util.Set;
import java.util.logging.Level;
import java.util.logging.LogManager;

import oracle.weblogic.deploy.util.FileUtils;
import oracle.weblogic.deploy.util.StringUtils;

/**
 * The logging config class that configures the wlsdeploy tool logging.
 */
public class WLSDeployLoggingConfig {
    private static final String DEFAULT_PROGRAM_NAME = "unknown-test";
    public static final String WLSDEPLOY_LOGGER_NAME = "wlsdeploy";
    private static final List<String> WLSDEPLOY_ROOT_LOGGERS =
        Collections.singletonList(WLSDEPLOY_LOGGER_NAME);
    private static final String DEFAULT_LOG_CONFIG_FILE_NAME = "logging.properties";
    private static final String LOG_NAME_PATTERN = "%s%s%s.log";

    private static final String HANDLERS_PROP = "handlers";
    private static final String CONFIG_PROP = "config";

    private static final String WLSDEPLOY_STDOUT_CONSOLE_HANDLER =
        "oracle.weblogic.deploy.logging.StdoutHandler";
    private static final String WLSDEPLOY_STDERR_CONSOLE_HANDLER =
        "oracle.weblogic.deploy.logging.StderrHandler";
    static final String WLSDEPLOY_SUMMARY_HANDLER = "oracle.weblogic.deploy.logging.SummaryHandler";
    static final String WLSDEPLOY_SUMMARY_STDOUT_HANDLER =
        "oracle.weblogic.deploy.logging.WLSDeploySummaryStdoutHandler";
    private static final String FILE_HANDLER = "java.util.logging.FileHandler";
    private static final List<String> DEFAULT_HANDLERS = new ArrayList<>(Arrays.asList(
        WLSDEPLOY_STDOUT_CONSOLE_HANDLER,
        WLSDEPLOY_STDERR_CONSOLE_HANDLER,
        WLSDEPLOY_SUMMARY_HANDLER,
        FILE_HANDLER
    ));

    private static final String HANDLER_LEVEL_PROP = ".level";
    private static final String HANDLER_FILTER_PROP = ".filter";
    private static final String HANDLER_FORMATTER_PROP = ".formatter";
    private static final String HANDLER_PATTERN_PROP = ".pattern";
    private static final String HANDLER_LIMIT_PROP = ".limit";
    private static final String HANDLER_COUNT_PROP = ".count";
    private static final String HANDLER_APPEND_PROP = ".append";
    private static final String HANDLER_SIZE_PROP = ".size";

    private static final String LOGGER_LEVEL_PROP = HANDLER_LEVEL_PROP;
    private static final String CONSOLE_FORMATTER_PROP = ConsoleFormatter.class.getName();
    private static final String STDOUT_FILTER_PROP = StdoutFilter.class.getName();
    private static final String STDERR_FILTER_PROP = StderrFilter.class.getName();

    private static final String DEFAULT_FILE_HANDLER_LEVEL = Level.ALL.toString();
    private static final String DEFAULT_STDOUT_HANDLER_LEVEL = Level.INFO.toString();
    private static final String DEFAULT_STDERR_HANDLER_LEVEL = Level.INFO.toString();

    private static final String DEFAULT_WLSDEPLOY_ROOT_LOGGER_LEVEL = Level.INFO.toString();
    private static final String DEFAULT_FILE_HANDLER_LIMIT = "0";
    private static final String DEFAULT_FILE_HANDLER_COUNT = "1";
    private static final String DEFAULT_FILE_HANDLER_APPEND = "false";
    private static final String DEFAULT_DEBUG_TO_STDOUT = "false";

    private static final String LOG_FORMATTER = WLSDeployLogFormatter.class.getName();

    /***
     * The exit code for logging configuration problems.
     */
    public static final int ERROR_EXIT_CODE = 2;

    /**
     * The environment variable name set by the shell script to specify the name of
     * the application.  This is used only to make the error messages during log
     * initialization friendlier.
     */
    public static final String WLSDEPLOY_PROGRAM_NAME_ENV_VARIABLE = "WLSDEPLOY_PROGRAM_NAME";

    /**
     * The environment variable name used to specify the logging.properties file to configure
     * the logging levels.  If not set, the default name is logging.properties in the current
     * working directory of the program.
     */
    public static final String WLSDEPLOY_LOG_PROPERTIES_ENV_VARIABLE = "WLSDEPLOY_LOG_PROPERTIES";

    /**
     * The environment variable name used to specify the location where the program's log file
     * should be written.
     */
    public static final String WLSDEPLOY_LOGS_DIRECTORY_ENV_VARIABLE = "WLSDEPLOY_LOG_DIRECTORY";

    /**
     * The environment variable name used to specify a comma separated list of handlers to add
     * to the tool parent logger (WLSDEPLOY_LOGGER_NAME). The handler name is the handler class name.
     */
    public static final String WLSDEPLOY_LOG_HANDLERS_ENV_VARIABLE = "WLSDEPLOY_LOG_HANDLERS";

    /**
     * Java System property to change the ConsoleHandler configuration to log
     * all levels of message to the console.  The default is false, which will
     * set the ConsoleHandler level to INFO.
     */
    public static final String WLSDEPLOY_DEBUG_TO_STDOUT_PROP = WLSDEPLOY_LOGGER_NAME + ".debugToStdout";

    private static File loggingDirectory;
    private static File loggingPropertiesFile;

    private String logFileName;

    /**
     * The constructor.
     */
    public WLSDeployLoggingConfig() {
        String programName = System.getenv(WLSDEPLOY_PROGRAM_NAME_ENV_VARIABLE);
        if (StringUtils.isEmpty(programName)) {
            programName = DEFAULT_PROGRAM_NAME;
        }

        File loggingConfigFile;
        String loggingConfigFileName = System.getenv(WLSDEPLOY_LOG_PROPERTIES_ENV_VARIABLE);
        if (!StringUtils.isEmpty(loggingConfigFileName)) {
            loggingConfigFile = new File(loggingConfigFileName);
        } else {
            loggingConfigFile = new File(new File(System.getProperty("user.dir")), DEFAULT_LOG_CONFIG_FILE_NAME);
        }

        if (!loggingConfigFile.exists()) {
            String message = MessageFormat.format("Unable to find {0} file so skipping logging configuration",
                loggingConfigFile.getAbsolutePath());
            System.err.println(message);
            System.exit(ERROR_EXIT_CODE);
        }
        setLoggingPropertiesFile(loggingConfigFile);

        try (InputStream logPropertiesStream = processLoggingPropertiesFile(programName, loggingConfigFile)) {
            LogManager.getLogManager().readConfiguration(logPropertiesStream);
        } catch (IOException ioe) {
            String message = MessageFormat.format("Failed to process {0}: {1}", loggingConfigFile.getAbsolutePath(),
                ioe.getMessage());
            System.err.println(message);
            ioe.printStackTrace(System.err);
            System.exit(ERROR_EXIT_CODE);
        }
        PlatformLogger logger = WLSDeployLogFactory.getLogger(WLSDEPLOY_LOGGER_NAME);   // make sure that this is the first logger
    }

    /**
     * Get the logging directory.
     *
     * @return the logging directory
     */
    public static synchronized File getLoggingDirectory() {
        return new File(loggingDirectory.getAbsolutePath());
    }

    /**
     * Log the logging directory path
     *
     */
    public static void logLoggingDirectory(String programName) {
      PlatformLogger logger = WLSDeployLogFactory.getLogger(WLSDEPLOY_LOGGER_NAME);
      logger.info("WLSDPLY-01755", programName, loggingDirectory.getAbsolutePath());
    }

    /**
     * Get the logging.properties file.
     *
     * @return the logging.properties file
     */
    @SuppressWarnings("unused")
    public static synchronized File getLoggingPropertiesFile() {
        return new File(loggingPropertiesFile.getAbsolutePath());
    }

    ///////////////////////////////////////////////////////////////////////////
    // Private helper methods                                                //
    ///////////////////////////////////////////////////////////////////////////

    private InputStream processLoggingPropertiesFile(String programName, File logPropsFile) throws IOException {
        Properties logProps = new Properties();

        try (FileInputStream fis = new FileInputStream(logPropsFile)) {
            logProps.load(fis);
        }
        augmentLoggingProperties(programName, logProps);

        // Now, the logging properties object should be ready to pass to
        // the LogManager so let's get an InputStream that contains it...
        //
        byte[] result;
        try (ByteArrayOutputStream baos = new ByteArrayOutputStream()) {
            logProps.store(baos, null);
            result = baos.toByteArray();
        }
        return new ByteArrayInputStream(result);
    }

    private void augmentLoggingProperties(String programName, Properties logProps) {
        List<String> handlers = updateHandlers(processLoggingPropertiesFileContents(logProps), logProps);

        // At this point, we should have a properties object with any
        // handler configuration we care about removed, so we can safely
        // add our configuration.
        //
        for (String handler : DEFAULT_HANDLERS) {
            if (handlers.contains(handler)) {
                configureHandler(programName, handler, logProps);
            }
        }
        ensureRootLoggerLevelIsSet(logProps);

        // Uncomment to debug log properties that will be passed to the LogManager
        // LoggingUtils.printLogProperties(logProps, "Final log properties :  ");
    }

    private List<String> processLoggingPropertiesFileContents(Properties logProps) {
        Set<String> keys = logProps.stringPropertyNames();
        List<String> handlers = null;
        for (String key : keys) {
            if (HANDLERS_PROP.equals(key)) {
                String val = logProps.getProperty(key);
                handlers = new ArrayList<>(Arrays.asList(StringUtils.splitCommaSeparatedList(val)));
            } else if (isFilteredHandlerProperty(key, logProps) || CONFIG_PROP.equals(key)) {
                logProps.remove(key);
            }
        }
        return handlers;
    }

    private List<String> updateHandlers(List<String> inputHandlers, Properties logProps) {
        List<String> handlers = inputHandlers;
        String handlersEnvVar = System.getenv(WLSDEPLOY_LOG_HANDLERS_ENV_VARIABLE);
        if (handlersEnvVar != null) {
            handlers = new ArrayList<>(Arrays.asList(StringUtils.splitCommaSeparatedList(handlersEnvVar)));
        }

        // If the handlers were not explicitly listed in the logging.properties file,
        // add the default handlers to the list.
        //
        if (handlers == null){
            handlers = DEFAULT_HANDLERS;
        } else {
            // The SummaryStdoutHandler cannot be in the registered handlers list or
            // duplicate messages will be logged to stdout.
            //
            handlers.remove(WLSDEPLOY_SUMMARY_STDOUT_HANDLER);

            // The SummaryHandler is required to collect warning and error messages for
            // validation so make sure it is in the list.
            //
            if (!handlers.contains(WLSDEPLOY_SUMMARY_HANDLER)) {
                handlers.add(WLSDEPLOY_SUMMARY_HANDLER);
                // If the user omitted the SummaryHandler from the list, we will set its
                // level to OFF so that its output will not be written to stdout.
                //
                logProps.setProperty(WLSDEPLOY_SUMMARY_HANDLER + HANDLER_LEVEL_PROP, Level.OFF.toString());
            }
        }
        String handlersListString = StringUtils.getCommaSeparatedListString(handlers);
        logProps.setProperty(HANDLERS_PROP, handlersListString);
        return handlers;
    }

    private void configureHandler(String programName, String handler, Properties logProps) {
        switch(handler) {
            case WLSDEPLOY_STDOUT_CONSOLE_HANDLER:
                configureStdoutConsoleHandler(logProps);
                break;

            case WLSDEPLOY_STDERR_CONSOLE_HANDLER:
                configureStderrConsoleHandler(logProps);
                break;

            case WLSDEPLOY_SUMMARY_HANDLER:
                SummaryHandler.addHandlerProperties(logProps);
                break;

            case FILE_HANDLER:
                logFileName = configureFileHandler(programName, logProps);
                break;

            default:
                String message = MessageFormat.format("{0} failed to configure unrecognized log handler {1}",
                    programName, handler);
                System.err.println(message);
                System.exit(ERROR_EXIT_CODE);
        }
    }

    private void ensureRootLoggerLevelIsSet(Properties logProps) {
        for (String loggerName : WLSDEPLOY_ROOT_LOGGERS) {
            String loggerLevelProp = loggerName + LOGGER_LEVEL_PROP;
            if (!logProps.containsKey(loggerLevelProp)) {
                logProps.setProperty(loggerLevelProp, DEFAULT_WLSDEPLOY_ROOT_LOGGER_LEVEL);
            }
        }
    }

    private static boolean isFilteredHandlerProperty(String key, Properties logProps) {
        boolean result = false;
        for (String handler : DEFAULT_HANDLERS) {
            if (key.startsWith(handler)) {
                result = !key.equals(handler + LOGGER_LEVEL_PROP) || !"OFF".equals(logProps.getProperty(key));

                // Allow the user to override the SummaryHandler's size property.
                //
                if (result && key.equals(WLSDEPLOY_SUMMARY_HANDLER + HANDLER_SIZE_PROP)) {
                    result = false;
                }
            }
        }
        return result;
    }

    private static String configureFileHandler(String programName, Properties logProps) {
        File logDir = findLoggingDirectory(programName);
        String pattern = String.format(LOG_NAME_PATTERN, logDir.getAbsolutePath(), File.separator, programName);
        logProps.setProperty(FILE_HANDLER + HANDLER_PATTERN_PROP, pattern);
        logProps.setProperty(FILE_HANDLER + HANDLER_FORMATTER_PROP, LOG_FORMATTER);
        logProps.setProperty(FILE_HANDLER + HANDLER_LEVEL_PROP, DEFAULT_FILE_HANDLER_LEVEL);
        logProps.setProperty(FILE_HANDLER + HANDLER_LIMIT_PROP, DEFAULT_FILE_HANDLER_LIMIT);
        logProps.setProperty(FILE_HANDLER + HANDLER_COUNT_PROP, DEFAULT_FILE_HANDLER_COUNT);
        logProps.setProperty(FILE_HANDLER + HANDLER_APPEND_PROP, DEFAULT_FILE_HANDLER_APPEND);
        return pattern;
    }

    private static void configureStdoutConsoleHandler(Properties logProps) {
        String stdoutHandlerLevel = WLSDEPLOY_STDOUT_CONSOLE_HANDLER + HANDLER_LEVEL_PROP;

        // If the log properties already has the level set, don't bother changing it since
        // currently, the only way this happens is if the value is OFF.
        //
        if (logProps.getProperty(stdoutHandlerLevel) == null) {
            String debugToStdoutString = System.getProperty(WLSDEPLOY_DEBUG_TO_STDOUT_PROP, DEFAULT_DEBUG_TO_STDOUT);
            if (Boolean.parseBoolean(debugToStdoutString)) {
                logProps.setProperty(stdoutHandlerLevel, Level.ALL.toString());
            } else {
                logProps.setProperty(stdoutHandlerLevel, DEFAULT_STDOUT_HANDLER_LEVEL);
            }
        }
        logProps.setProperty(WLSDEPLOY_STDOUT_CONSOLE_HANDLER + HANDLER_FORMATTER_PROP, CONSOLE_FORMATTER_PROP);
        logProps.setProperty(WLSDEPLOY_STDOUT_CONSOLE_HANDLER + HANDLER_FILTER_PROP, STDOUT_FILTER_PROP);
    }

    private static void configureStderrConsoleHandler(Properties logProps) {
        String stderrHandlerLevel = WLSDEPLOY_STDERR_CONSOLE_HANDLER + HANDLER_LEVEL_PROP;

        // If the log properties already has the level set, don't bother changing it since
        // currently, the only way this happens is if the value is OFF.
        //
        if (logProps.getProperty(stderrHandlerLevel) == null) {
            logProps.setProperty(stderrHandlerLevel, DEFAULT_STDERR_HANDLER_LEVEL);
        }
        logProps.setProperty(WLSDEPLOY_STDERR_CONSOLE_HANDLER + HANDLER_FORMATTER_PROP, CONSOLE_FORMATTER_PROP);
        logProps.setProperty(WLSDEPLOY_STDERR_CONSOLE_HANDLER + HANDLER_FILTER_PROP, STDERR_FILTER_PROP);
    }

    private static File findLoggingDirectory(String programName) {
        File logDir = checkLogDirectoryEnvironmentVariable();

        if (logDir == null) {
            logDir = checkCurrentDirectoryForLogging();
        }
        if (logDir == null) {
            logDir = checkTempDirectoryForLogging(programName);
        }

        // If we get to this point and haven't found a suitable log directory, fail.
        if (logDir == null) {
            String message =
                MessageFormat.format("{0} was unable to find a writable location for its logs", programName);
            System.err.println(message);
            System.exit(ERROR_EXIT_CODE);
        }
        setLoggingDir(logDir);
        return logDir;
    }

    private static File checkLogDirectoryEnvironmentVariable() {
        String logLocation = System.getenv(WLSDEPLOY_LOGS_DIRECTORY_ENV_VARIABLE);
        File logDir = null;
        if (!StringUtils.isEmpty(logLocation)) {
            File tmpLogDir = new File(logLocation).getAbsoluteFile();
            if ((tmpLogDir.exists() && tmpLogDir.canWrite()) || (tmpLogDir.mkdirs() && tmpLogDir.canWrite())) {
                logDir = tmpLogDir;
            }
        }
        return logDir;
    }

    private static File checkCurrentDirectoryForLogging() {
        File logDir = null;
        File currentDirectory = new File(System.getProperty("user.dir", "")).getAbsoluteFile();
        if (currentDirectory.canWrite()) {
            File tmpLogDir = new File(currentDirectory, "logs");
            if ((tmpLogDir.exists() && tmpLogDir.canWrite()) || (tmpLogDir.mkdirs() && tmpLogDir.canWrite())) {
                logDir = tmpLogDir;
            }
        }
        return logDir;
    }

    private static File checkTempDirectoryForLogging(String programName) {
        File logDir = null;

        File tmpDir = new File(System.getProperty("java.io.tmpdir")).getAbsoluteFile();
        if (tmpDir.canWrite()) {
            try {
                File parentDir = tmpDir.getCanonicalFile();
                logDir = FileUtils.createTempDirectory(parentDir, "wdt-logs");
            } catch (IOException ioe) {
                String message = MessageFormat.format("{0} failed to create temporary logs directory in {1}: {2}",
                    programName, tmpDir.getAbsolutePath(), ioe.getMessage());
                System.err.println(message);
                System.exit(ERROR_EXIT_CODE);
            }
        }
        return logDir;
    }

    private static synchronized void setLoggingDir(File logDir) {
        if (loggingDirectory == null) {
            loggingDirectory = logDir;
        }
    }

    private static synchronized void setLoggingPropertiesFile(File logPropsFile) {
        if (loggingPropertiesFile == null) {
            loggingPropertiesFile = logPropsFile;
        }
    }
}
