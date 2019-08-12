/*
 * Copyright (c) 2018, 2019, Oracle Corporation and/or its affiliates. All rights reserved.
 * Licensed under the Universal Permissive License v 1.0 as shown at http://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.logging;

import java.util.ArrayList;
import java.util.List;
import java.util.Properties;
import java.util.logging.ConsoleHandler;
import java.util.logging.Formatter;
import java.util.logging.Handler;
import java.util.logging.Level;
import java.util.logging.LogManager;
import java.util.logging.LogRecord;
import java.util.logging.MemoryHandler;

import oracle.weblogic.deploy.util.WLSDeployContext;
import oracle.weblogic.deploy.util.WLSDeployExit;
import oracle.weblogic.deploy.util.WebLogicDeployToolingVersion;


/**
 * This class save the log records logged by the tool at Info level or greater. The WLSDeployExit exit method will
 * call this Handler to publish the messages, along with the total of the log records, by Level category.
 *
 * The WLSDeployCustomizeLoggingConfig adds the properties from this class' getHandlerProperties() to the
 * log manager logger properties and adds the handler to the root WLSDEPLOY Logger. See the class for information
 * on how to inject this handler into the wlsdeploy root logger.
 *
 * Before the tool exit, if specified by the caller, an activity summary of the saved logs is displayed to the console.
 * A final total of the records logged by the tool for the Level categories indicated above is displayed to the console.
 *
 * @see WLSDeployCustomizeLoggingConfig
 * @see oracle.weblogic.deploy.util.WLSDeployExit
 */
public class SummaryHandler extends Handler implements WLSDeployLogEndHandler {
    private static final String CLASS = SummaryHandler.class.getName();
    private static final String LEVEL_PROPERTY = "level";
    private static final String TARGET_PROPERTY = "target";
    private static final String FORMATTER_PROPERTY = "formatter";
    private static final String SIZE_PROPERTY = "size";
    private static final int DEFAULT_SIZE = 3000;

    private PlatformLogger LOGGER = WLSDeployLogFactory.getLogger("wlsdeploy.exit");
    private int bufferSize;
    private WLSDeployContext context;

    private Handler topTarget;
    private List<LevelHandler> handlers = new ArrayList<>();
    private boolean closed = false;

    /**
     * This default constructor is populated with the handler properties loaded by the WLSDeployCustomizeLoggingConfig.
     */
    public SummaryHandler() {
        super();
        configure();

        LOGGER.setLevel(Level.INFO);
        addLevelHandler(Level.WARNING);
        addLevelHandler(Level.SEVERE);
    }

    /**
     * Tally and save the log record if it matches one of the category Level handlers. Once the summary has completed,
     * all further log records will be ignored.
     *
     * @param record to tally and save in handler with matching Level category
     */
    @Override
    public synchronized void publish(LogRecord record) {
        // after close, take yourself out of the mix. The stored up log messages are going to go to the
        // console handler anyway
        if (!closed) {
            for (Handler handler : handlers) {
                handler.publish(record);
            }
        }
    }

    @Override
    public void flush() {
        topTarget.flush();
    }

    @Override
    public void close() throws SecurityException {
        topTarget.close();
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
        String METHOD = "push";
        LOGGER.entering(modelContext, CLASS, METHOD);
        this.context = modelContext;
        summaryHead(topTarget);
        for (LevelHandler handler : handlers) {
            handler.push();
        }
        summaryTail(topTarget);
        LOGGER.exiting(CLASS, METHOD);
    }

    /**
     * The WLSDeployLoggingConfig will call this method to add to the logging.properties files.
     * If the logging.properties already contains the property, the property in this list will be ignored.
     *
     * @return properties to set in logging.properties
     */
    public static Properties getHandlerProperties() {
        Properties properties = new Properties();
        properties.setProperty(LEVEL_PROPERTY, Level.INFO.getName());
        properties.setProperty(TARGET_PROPERTY, WLSDeployLoggingConsoleHandler.class.getName());
        properties.setProperty(FORMATTER_PROPERTY, WLSDeployLogFormatter.class.getName());
        return properties;
    }

    private void addLevelHandler(Level level) {
        LevelHandler handler;
        Handler levelTarget = getConsoleHandler();
        levelTarget.setFormatter(new SummaryFormatter(level));
        handler = new LevelHandler(levelTarget, bufferSize, level);
        handler.setLevel(level);
        handler.setFilter(getFilter());
        handlers.add(handler);
    }

    void summaryHead(Handler handler) {
        handler.publish(getLogRecord("WLSDPLY-21003", context.getProgramName(),
                WebLogicDeployToolingVersion.getVersion(), context.getVersion(), context.getWlstMode()));
    }

    void summaryTail(Handler handler) {
        StringBuffer buffer = new StringBuffer();
        java.util.Formatter fmt = new java.util.Formatter(buffer);
        for (LevelHandler levelHandler : handlers) {
            if (levelHandler.getTotalRecords() >= 0) {
                fmt.format("    %1$s : %2$,5d", levelHandler.getLevel().getName(), levelHandler.getTotalRecords());
            }
        }
        handler.publish(getLogRecord("WLSDPLY-21002", buffer));
    }

    private class TotalFormatter extends Formatter {

        @Override
        public synchronized String format(LogRecord record) {
            return System.lineSeparator() + formatMessage(record) + System.lineSeparator();
        }

    }

    private class SummaryFormatter extends Formatter {

        private final String MSG_FORMAT = "    %1$5d. %2$s: %3$s" + System.lineSeparator();
        private final String INTERNAL = System.lineSeparator() + "%s" + System.lineSeparator() + System.lineSeparator();
        private int sequence = 0;
        private Level level;

        public SummaryFormatter(Level level) {
            this.level = level;
        }

        @Override
        public synchronized String format(LogRecord record) {
            String message = "";
            String msgId = record.getMessage();
            if (msgId.indexOf('{') >= 0) {
                msgId = null;
            }
            String formatted = formatMessage(record);
            if (msgId != null && !msgId.equals(formatted)) {
                // this has a msg id. don't post any that don't have msg id.
                message = String.format(MSG_FORMAT, ++sequence, msgId, formatted);
            }
            return message;
        }

        @Override
        public String getHead(Handler handler) {
            return String.format(INTERNAL, formatMessage(getLogRecord("WLSDPLY-21000", level.getLocalizedName())));
        }
    }

    private class LevelHandler extends MemoryHandler {

        private int totalRecords;

        LevelHandler(Handler handler, int size, Level level) {
            super(handler, size, Level.OFF);
            setLevel(level);
        }

        @Override
        public synchronized void publish(LogRecord record) {
            if (record.getLevel().intValue() == getLevel().intValue()) {
                ++totalRecords;
                super.publish(record);
            }
        }

        int getTotalRecords() {
            return totalRecords;
        }

    }

    private void configure() {
        LogManager manager = LogManager.getLogManager();
        topTarget = getConsoleHandler();
        topTarget.setFormatter(new TotalFormatter());
        bufferSize = getSize(manager.getProperty(getClass().getName() + "." + SIZE_PROPERTY));
    }

    private int getSize(String propSize) {
        Integer handlerSize;
        try {
            handlerSize = new Integer(propSize);
        } catch (NumberFormatException nfe) {
            handlerSize = DEFAULT_SIZE;
        }
        return handlerSize;
    }

    private ConsoleHandler getConsoleHandler() {
        ConsoleHandler handler = null;
        try {
            handler = (ConsoleHandler) Class.forName(WLSDeployLoggingConfig.getConsoleHandler()).newInstance();
        } catch (ClassNotFoundException | IllegalAccessException cne) {
            System.out.println("Class not found " + WLSDeployLoggingConfig.getConsoleHandler());
        } catch (InstantiationException ie) {
            handler = new ConsoleHandler();
        }
        return handler;
    }


    private LogRecord getLogRecord(String msg, Object... params) {
        LogRecord record = new LogRecord(Level.INFO, msg);
        record.setLoggerName(LOGGER.getName());
        if (params != null && params.length != 0) {
            record.setParameters(params);
        }
        record.setSourceClassName(CLASS);
        record.setSourceMethodName("");
        record.setResourceBundle(LOGGER.getUnderlyingLogger().getResourceBundle());
        return record;
    }

}