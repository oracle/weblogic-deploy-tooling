/*
 * Copyright (c) 2018, 2022, Oracle Corporation and/or its affiliates.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.logging;

import java.util.ArrayList;
import java.util.List;
import java.util.Properties;
import java.util.logging.Formatter;
import java.util.logging.Handler;
import java.util.logging.Level;
import java.util.logging.LogManager;
import java.util.logging.LogRecord;
import java.util.logging.MemoryHandler;

import oracle.weblogic.deploy.util.StringUtils;
import oracle.weblogic.deploy.util.WLSDeployContext;
import oracle.weblogic.deploy.util.WebLogicDeployToolingVersion;

import static oracle.weblogic.deploy.logging.WLSDeployLoggingConfig.WLSDEPLOY_SUMMARY_STDOUT_HANDLER;

/**
 * This class save the log records logged by the tool at Info level or greater. The WLSDeployExit exit method will
 * call this Handler to publish the messages, along with the total of the log records, by Level category.
 *
 * <p>Before the tool exit, if specified by the caller, an activity summary of the saved logs is displayed to the console.
 * A final total of the records logged by the tool for the Level categories indicated above is displayed to the console.
 *
 * @see oracle.weblogic.deploy.util.WLSDeployExit
 */
public class SummaryHandler extends WLSDeployLogEndHandler {
    private static final String CLASS = SummaryHandler.class.getName();
    private static final PlatformLogger LOGGER = WLSDeployLogFactory.getLogger("wlsdeploy.exit");

    private static final String LEVEL_PROPERTY = ".level";
    private static final String TARGET_PROPERTY = ".target";
    private static final String SIZE_PROPERTY = ".size";
    private static final int DEFAULT_MEMORY_BUFFER_SIZE = 3000;
    private static final String DEFAULT_SIZE_PROPERTY_VALUE = Integer.toString(DEFAULT_MEMORY_BUFFER_SIZE);

    private final int bufferSize;
    private WLSDeployContext context;
    private boolean suppressOutput = false;

    private final Handler outputTargetHandler;
    private final List<LevelHandler> handlers = new ArrayList<>();
    private boolean closed = false;

    /**
     * This default constructor is populated with the handler properties loaded by the WLSDeployCustomizeLoggingConfig.
     */
    public SummaryHandler() {
        super();
        this.outputTargetHandler = getOutputTargetHandler();

        this.bufferSize = getMemoryBufferSize(CLASS + SIZE_PROPERTY);

        addLevelHandler(Level.WARNING);
        addLevelHandler(Level.SEVERE);
    }

    /**
     * The WLSDeployLoggingConfig will call this method to add the SummaryHandler properties to the logging.properties
     * files. If the logging.properties already contains the property, the property in this list will be ignored.
     *
     * @return properties to set in logging.properties
     */
    static void addHandlerProperties(Properties logProps) {
        if (!logProps.containsKey(CLASS + LEVEL_PROPERTY)) {
            logProps.setProperty(CLASS + LEVEL_PROPERTY, Level.INFO.getName());
        }
        logProps.setProperty(CLASS + TARGET_PROPERTY, WLSDEPLOY_SUMMARY_STDOUT_HANDLER);

        // If the user has overridden the size property, don't reset it.
        //
        if (!logProps.containsKey(CLASS + SIZE_PROPERTY)) {
            logProps.setProperty(CLASS + SIZE_PROPERTY, DEFAULT_SIZE_PROPERTY_VALUE);
        }
    }

    /**
     * Tally and save the log record if it matches one of the category Level handlers. Once the summary has completed,
     * all further log records will be ignored.
     *
     * @param logRecord to tally and save in handler with matching Level category
     */
    @Override
    public synchronized void publish(LogRecord logRecord) {
        // after close, take yourself out of the mix. The stored up log messages are going to go to the
        // console handler anyway
        if (!closed) {
            for (Handler handler : handlers) {
                handler.publish(logRecord);
            }
        }
    }

    /**
     * {@inheritDoc}
     */
    @Override
    public void flush() {
        outputTargetHandler.flush();
    }

    /**
     * {@inheritDoc}
     */
    @Override
    public void close() throws SecurityException {
        outputTargetHandler.close();
    }

    /**
     * This method is called by the tool to complete the SummaryHandler, and display the recap and total information
     * to the console. The log records are only displayed to the console if the tool was run in online mode.
     * This compensates for wlst writing spurious blank lines to the console during online mode.
     *
     * @param modelContext contextual information about the tool
     */
    @Override
    public synchronized void logEnd(WLSDeployContext modelContext) {
        closed = true;
        final String METHOD = "logEnd";
        LOGGER.entering(modelContext, CLASS, METHOD);
        this.context = modelContext;
        summaryHead(outputTargetHandler);
        for (LevelHandler handler : handlers) {
            handler.push();
        }
        summaryTail(outputTargetHandler);
        LOGGER.exiting(CLASS, METHOD);
    }

    /**
     * Returns the highest level of the messages in the summary.
     * If no messages are found, the level INFO is returned.
     * @return the maximum message level, or Level.INFO if none are found.
     */
    public Level getMaximumMessageLevel() {
        Level maxLevel = Level.INFO;
        for(LevelHandler levelHandler : handlers) {
            if(levelHandler.getTotalRecords() > 0) {
                Level level = levelHandler.getLevel();
                if(level.intValue() > maxLevel.intValue()) {
                    maxLevel = level;
                }
            }
        }
        return maxLevel;
    }

    /**
     * Returns the message count in the summary for the specified level.
     * @return the message count for the specified level.
     */
    public int getMessageCount(Level level) {
        for(LevelHandler levelHandler : handlers) {
            Level handlerLevel = levelHandler.getLevel();
            if(handlerLevel.equals(level)) {
                return levelHandler.getTotalRecords();
            }
        }
        return 0;
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                             Private helper methods                                        //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    private void addLevelHandler(Level level) {
        Handler levelTargetHandler = getLevelHandlerOutputTargetHandler(level);

        LevelHandler levelHandler = new LevelHandler(levelTargetHandler, bufferSize, level);
        levelHandler.setFilter(null);
        levelHandler.setLevel(level);
        handlers.add(levelHandler);
    }

    private Handler getOutputTargetHandler() {
        Handler summaryStdoutHandler = new WLSDeploySummaryStdoutHandler();
        summaryStdoutHandler.setFormatter(new TotalFormatter());
        summaryStdoutHandler.setFilter(null);

        // If the user turns off the SummaryHandler, turn off the SummaryStdoutHandler instead
        //
        LogManager manager = LogManager.getLogManager();
        String levelProperty = manager.getProperty(CLASS + LEVEL_PROPERTY);
        if (Level.OFF.toString().equals(levelProperty)) {
            suppressOutput = true;
            summaryStdoutHandler.setLevel(Level.OFF);
        } else {
            summaryStdoutHandler.setLevel(Level.INFO);
        }
        return summaryStdoutHandler;
    }

    private Handler getLevelHandlerOutputTargetHandler(Level level) {
        Handler handler = new WLSDeploySummaryStdoutHandler();
        handler.setFormatter(new SummaryFormatter(level));
        handler.setFilter(null);
        if (suppressOutput) {
            handler.setLevel(Level.OFF);
        } else {
            handler.setLevel(level);
        }
        return handler;
    }

    private void summaryHead(Handler handler) {
        handler.publish(getLogRecord("WLSDPLY-21003", context.getProgramName(),
            WebLogicDeployToolingVersion.getVersion(), context.getVersion(), context.getWlstMode()));
    }

    private void summaryTail(Handler handler) {
        StringBuilder buffer = new StringBuilder();
        try (java.util.Formatter fmt = new java.util.Formatter(buffer)) {
            for (LevelHandler levelHandler : handlers) {
                if (levelHandler.getTotalRecords() >= 0) {
                    fmt.format("    %1$s : %2$,5d", levelHandler.getLevel().getName(), levelHandler.getTotalRecords());
                }
            }
        }
        handler.publish(getLogRecord("WLSDPLY-21002", buffer));
    }

    private int getMemoryBufferSize(String sizePropertyName) {
        String sizePropertyValue = LogManager.getLogManager().getProperty(sizePropertyName);

        int size = DEFAULT_MEMORY_BUFFER_SIZE;
        if (!StringUtils.isEmpty(sizePropertyValue)) {
            try {
                size = Integer.parseInt(sizePropertyValue);
            } catch (NumberFormatException nfe) {
                // Best effort only...
            }
        }
        return size;
    }

    private LogRecord getLogRecord(String msg, Object... params) {
        LogRecord logRecord = new LogRecord(Level.INFO, msg);
        logRecord.setLoggerName(LOGGER.getName());
        if (params != null && params.length != 0) {
            logRecord.setParameters(params);
        }
        logRecord.setSourceClassName(CLASS);
        logRecord.setSourceMethodName("");
        logRecord.setResourceBundle(LOGGER.getUnderlyingLogger().getResourceBundle());
        return logRecord;
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////
    //                             Private helper classes                                        //
    ///////////////////////////////////////////////////////////////////////////////////////////////

    private class TotalFormatter extends Formatter {
        @Override
        public synchronized String format(LogRecord logRecord) {
            return System.lineSeparator() + formatMessage(logRecord) + System.lineSeparator();
        }
    }

    private class SummaryFormatter extends Formatter {
        private final String msgFormat = "    %1$5d. %2$s: %3$s" + System.lineSeparator();
        private final String internal = System.lineSeparator() + "%s" + System.lineSeparator() + System.lineSeparator();
        private int sequence = 0;
        private final Level level;

        public SummaryFormatter(Level level) {
            this.level = level;
        }

        @Override
        public synchronized String format(LogRecord logRecord) {
            String message = "";
            String msgId = logRecord.getMessage();
            if (msgId.indexOf('{') >= 0) {
                msgId = null;
            }
            String formatted = formatMessage(logRecord);
            if (msgId != null && !msgId.equals(formatted)) {
                // this has a msg id. don't post any that don't have msg id.
                message = String.format(msgFormat, ++sequence, msgId, formatted);
            }
            return message;
        }

        @Override
        public String getHead(Handler handler) {
            return String.format(internal, formatMessage(getLogRecord("WLSDPLY-21000", level.getLocalizedName())));
        }
    }

    private class LevelHandler extends MemoryHandler {
        private int totalRecords;

        LevelHandler(Handler handler, int size, Level level) {
            super(handler, size, Level.OFF);
            setLevel(level);
        }

        @Override
        public synchronized void publish(LogRecord logRecord) {
            if (logRecord.getLevel().equals(getLevel())) {
                ++totalRecords;
                super.publish(logRecord);
            }
        }

        int getTotalRecords() {
            return totalRecords;
        }
    }
}
