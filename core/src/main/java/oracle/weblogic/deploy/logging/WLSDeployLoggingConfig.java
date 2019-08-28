/*
 * Copyright (c) 2017, 2019, Oracle and/or its affiliates. All rights reserved.
 * Licensed under the Universal Permissive License v 1.0 as shown at http://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.logging;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.text.MessageFormat;
import java.util.*;
import java.util.logging.Handler;
import java.util.logging.Level;
import java.util.logging.LogManager;

import oracle.weblogic.deploy.util.FileUtils;
import oracle.weblogic.deploy.util.StringUtils;

/**
 * The logging config class for use by wls-deploy and friends.
 */
public class WLSDeployLoggingConfig {
    private static final String DEFAULT_PROGRAM_NAME = "unknown-test";
    private static final List<String> WLSDEPLOY_ROOT_LOGGERS =
        Collections.singletonList("oracle.weblogic.deploy");
    private static final String DEFAULT_LOG_CONFIG_FILE_NAME = "logging.properties";
    private static final String LOG_NAME_PATTERN = "%s.log";

    private static final String HANDLERS_PROP = "handlers";
    private static final String CONFIG_PROP = "config";

    private static final String WLSDEPLOY_CONSOLE_HANDLER =
        "oracle.weblogic.deploy.logging.WLSDeployLoggingConsoleHandler";
    private static final String FILE_HANDLER = "java.util.logging.FileHandler";
    public static final String WLSDEPLOY_LOGGER_NAME = "wlsdeploy";

    private static final String HANDLER_LEVEL_PROP = ".level";
    private static final String HANDLER_FORMATTER_PROP = ".formatter";
    private static final String HANDLER_PATTERN_PROP = ".pattern";
    private static final String HANDLER_LIMIT_PROP = ".limit";
    private static final String HANDLER_COUNT_PROP = ".count";
    private static final String HANDLER_APPEND_PROP = ".append";

    private static final String LOGGER_LEVEL_PROP = HANDLER_LEVEL_PROP;

    private static final String DEFAULT_FILE_HANDLER_LEVEL = Level.ALL.toString();
    private static final String DEFAULT_CONSOLE_HANDLER_LEVEL = Level.INFO.toString();
    private static final String DEFAULT_WLSLCM_ROOT_LOGGER_LEVEL = Level.INFO.toString();

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

        InputStream logPropertiesStream = null;
        try {
            logPropertiesStream = processLoggingPropertiesFile(programName, loggingConfigFile);
            LogManager.getLogManager().readConfiguration(logPropertiesStream);
        } catch (IOException ioe) {
            String message = MessageFormat.format("Failed to process {0}: {1}", loggingConfigFile.getAbsolutePath(),
                ioe.getMessage());
            System.err.println(message);
            ioe.printStackTrace(System.err);
            System.exit(ERROR_EXIT_CODE);
        } finally {
            if (logPropertiesStream != null) {
                try {
                    logPropertiesStream.close();
                } catch (IOException ignore) {
                    // nothing to do...
                }
            }
        }
        PlatformLogger logger = WLSDeployLogFactory.getLogger(WLSDEPLOY_LOGGER_NAME);   // make sure that this is the first logger
        logger.info("The {0} program will write its log to {1}", programName, logFileName);
    }

    public static synchronized File getLoggingDirectory() {
        return new File(loggingDirectory.getAbsolutePath());
    }

    public static synchronized File getLoggingPropertiesFile() {
        return new File(loggingPropertiesFile.getAbsolutePath());
    }

    public static String getConsoleHandler() {
        return WLSDEPLOY_CONSOLE_HANDLER;
    }

    /**
     * To augment the logging properties with custom properties, extend this class and overwrite this method.
     * The method should add applicable properties to the logProps. These properties will be loaded into the LogManager
     * and available to Logger instances. Do not instantiate Loggers in this class as the reload will reset the
     * Loggers.
     *
     * @param programName the name of the tool running, useful for messages.
     * @param logProps property instance to which to add log properties in string format, key=value
     */
    public void customizeLoggingProperties(String programName, Properties logProps) {
       // override to customize
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
        Set<String> keys = logProps.stringPropertyNames();
        List<String> handlers = new ArrayList<>();
        for (String key : keys) {
            if (HANDLERS_PROP.equals(key)) {
                String val = logProps.getProperty(key);
                handlers = Arrays.asList(StringUtils.splitCommaSeparatedList(val));
            } else if (isKeyKnownHandlerProperty(key) || CONFIG_PROP.equals(key)) {
                logProps.remove(key);
            }
        }

        // At this point, we should have a properties object with any
        // handler configuration we care about removed so we can safely
        // add our configuration.
        //
        String consoleHandler = getConsoleHandler();
        if (!handlers.contains(consoleHandler)) {
            handlers.add(consoleHandler);
        }
        if (!handlers.contains(FILE_HANDLER)) {
            handlers.add(FILE_HANDLER);
        }
        String handlersListString = StringUtils.getCommaSeparatedListString(handlers);
        logProps.setProperty(HANDLERS_PROP, handlersListString);

        customizeLoggingProperties(programName, logProps);

        logFileName = configureFileHandler(programName, logProps);
        configureConsoleHandler(logProps);

        for (String loggerName : WLSDEPLOY_ROOT_LOGGERS) {
            String loggerLevelProp = loggerName + LOGGER_LEVEL_PROP;
            if (!logProps.containsKey(loggerLevelProp)) {
                logProps.setProperty(loggerLevelProp, DEFAULT_WLSLCM_ROOT_LOGGER_LEVEL);
            }
        }

    }

    private static boolean isKeyKnownHandlerProperty(String key) {
        String consoleHandler = getConsoleHandler();
        return key.startsWith(consoleHandler) || key.startsWith(FILE_HANDLER);
    }

    private static String configureFileHandler(String programName, Properties logProps) {
        File logDir = findLoggingDirectory(programName);
        String pattern = String.format(logDir.getAbsolutePath() + File.separator +
            LOG_NAME_PATTERN, programName);
        logProps.setProperty(FILE_HANDLER + HANDLER_PATTERN_PROP, pattern);
        logProps.setProperty(FILE_HANDLER + HANDLER_FORMATTER_PROP, LOG_FORMATTER);
        logProps.setProperty(FILE_HANDLER + HANDLER_LEVEL_PROP, DEFAULT_FILE_HANDLER_LEVEL);
        logProps.setProperty(FILE_HANDLER + HANDLER_LIMIT_PROP, DEFAULT_FILE_HANDLER_LIMIT);
        logProps.setProperty(FILE_HANDLER + HANDLER_COUNT_PROP, DEFAULT_FILE_HANDLER_COUNT);
        logProps.setProperty(FILE_HANDLER + HANDLER_APPEND_PROP, DEFAULT_FILE_HANDLER_APPEND);
        return pattern;
    }

    private static void configureConsoleHandler(Properties logProps) {
        String consoleHandler = getConsoleHandler();
        String debugToStdoutString = System.getProperty(WLSDEPLOY_DEBUG_TO_STDOUT_PROP, DEFAULT_DEBUG_TO_STDOUT);
        if (Boolean.parseBoolean(debugToStdoutString)) {
            logProps.setProperty(consoleHandler + HANDLER_LEVEL_PROP, Level.ALL.toString());
        } else {
            logProps.setProperty(consoleHandler + HANDLER_LEVEL_PROP, DEFAULT_CONSOLE_HANDLER_LEVEL);
        }

        logProps.setProperty(consoleHandler + HANDLER_FORMATTER_PROP, LOG_FORMATTER);
    }

    private static File findLoggingDirectory(String programName) {
        String logLocation = System.getenv(WLSDEPLOY_LOGS_DIRECTORY_ENV_VARIABLE);
        File currentDirectory = new File(System.getProperty("user.dir", "")).getAbsoluteFile();
        File tmpDir = new File(System.getProperty("java.io.tmpdir")).getAbsoluteFile();
        File logDir = null;
        boolean found = false;

        if (!StringUtils.isEmpty(logLocation)) {
            logDir = new File(logLocation).getAbsoluteFile();
            if ((logDir.exists() && logDir.canWrite()) || (logDir.mkdirs() && logDir.canWrite())) {
                found = true;
            }
        }

        if (!found && currentDirectory.canWrite()) {
            logDir = new File(currentDirectory, "logs");
            if ((logDir.exists() && logDir.canWrite()) || (logDir.mkdirs() && logDir.canWrite())) {
                found = true;
            }
        }

        if (!found && tmpDir.canWrite()) {
            try {
                File parentDir = tmpDir.getCanonicalFile().getParentFile();
                logDir = FileUtils.createTempDirectory(parentDir, "jcslcm-logs");
                found = true;
            } catch (IOException ioe) {
                String message = MessageFormat.format("{0} failed to create temporary logs directory in {1}: {2}",
                    programName, tmpDir.getAbsolutePath(), ioe.getMessage());
                System.err.println(message);
                System.exit(ERROR_EXIT_CODE);
            }
        }

        // If we get to this point and we haven't found a suitable log directory, fail.
        if (!found) {
            String message =
                MessageFormat.format("{0} was unable to find a writable location for its logs", programName);
            System.err.println(message);
            System.exit(ERROR_EXIT_CODE);
        }
        setLoggingDir(logDir);
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
