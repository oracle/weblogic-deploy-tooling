/*
 * Copyright (c) 2018, Oracle and/or its affiliates. All rights reserved.
 * The Universal Permissive License (UPL), Version 1.0
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


/**
 * This class save the log records logged by the tool at Info level or greater. The WLSDeployExit exit method will
 * call this Handler to publish the messages, along with the total of the log records, by Level category.
 *
 * The WLSDeployCustomizeLoggingConfig adds the properties from this class' getHandlerProperties() to the
 * log manager logger properties and adds the handler to the root WLSDEPLOY Logger. See the class for information
 * on how to inject this handler into the wlsdeploy root logger.
 *
 * Before the tool exit, if specified by the caller, a recap of the saved logs is displayed to the console.
 * A final total of the records logged by the tool for the Level categories indicated above is displayed to the console.
 *
 * @see WLSDeployCustomizeLoggingConfig
 * @see oracle.weblogic.deploy.util.WLSDeployExit
 */
public class SummaryHandler extends MemoryHandler implements WLSDeployLogEndHandler {
    private static final String CLASS = SummaryHandler.class.getName();
    private static final String LEVEL_PROPERTY = "level";
    private static final String TARGET_PROPERTY = "target";
    private static final String FORMATTER_PROPERTY = "formatter";
    private static final String SIZE_PROPERTY = "size";
    private static final int DEFAULT_SIZE = 3000;
    private static final String LINE_SEPARATION = System.lineSeparator();

    private PlatformLogger LOGGER = WLSDeployLogFactory.getLogger("wlsdeploy.exit");
    private boolean online = false;
    private String toolName;
    private int bufferSize;

    private Handler target;
    private List<LevelHandler> handlers = new ArrayList<>();
    private boolean closed = false;

    /**
     * This default constructor is populated with the handler properties loaded by the WLSDeployCustomizeLoggingConfig.
     */
    public SummaryHandler() {
        super();
        configure();
        target = getConsoleHandler();
        target.setFormatter(new TotalFormatter());
        LOGGER.setLevel(Level.INFO);
        addLevelHandler(Level.INFO);
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

    /**
     * The Summary Handler will publish the recaps and total. The log records are discarded and the total reset.
     */
    @Override
    public synchronized void push() {
        String METHOD = "push";
        LOGGER.entering(CLASS, METHOD);
        closed = true;
        setPushLevel(getLevel());
        StringBuffer buffer = new StringBuffer();
        System.out.println(LINE_SEPARATION);
        target.publish(getLogRecord("WLSDPLY-21003", toolName));
        java.util.Formatter fmt = new java.util.Formatter(buffer);
        for (LevelHandler handler : handlers) {
            int count = handler.pushSection();
            super.push();
            if (count >= 0) {
                fmt.format("    %1$s : %2$,5d", handler.getLevel().getName(), count);
            }
        }

        System.out.println(LINE_SEPARATION);
        target.publish(getLogRecord("WLSDPLY-21002", buffer));
    }

    @Override
    public void flush() {
        super.flush();
    }

    @Override
    public void close() throws SecurityException {
        super.close();
    }

    /**
     * This method is called by the tool to complete the SummaryHandler, and display the recap and total information
     * to the console. The log records are only displayed to the console if the tool was run in online mode.
     * This compensates for wlst writing spurious blank lines to the console during online mode.
     *
     * @param onlineMode if true, a recap of the log records will be displayed
     */
    @Override
    public void logEnd(String toolName, boolean onlineMode) {
        this.toolName = toolName;
        push();
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
        levelTarget.setFormatter(new SummaryFormatter());
        if (getLevel().intValue() <= level.intValue()) {
            handler = new LevelHandler(levelTarget, bufferSize, level);
        } else {
            handler = new NoActionHandler(levelTarget, bufferSize, level);
        }
        handler.setLevel(level);
        handler.setFilter(getFilter());
        handlers.add(handler);
    }

    private class TotalFormatter extends Formatter {
        @Override
        public synchronized String format(LogRecord record) {
            return formatMessage(record) + System.lineSeparator();
        }
    }

    private class SummaryFormatter extends Formatter {

        private final String MSG_FORMAT = "    %1$5d. %2$s: %3$s" + System.lineSeparator();
        private final String INTERNAL = "%s" + System.lineSeparator();
        private int sequence = 0;

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
                if (msgId.startsWith("WLSDPLY-21")) {
                    message = String.format(INTERNAL, formatted);
                } else {
                    message = String.format(MSG_FORMAT, ++sequence, msgId, formatted);
                }
            }
            return message;
        }

        @Override
        public String getHead(Handler handler) {
            return formatMessage(getLogRecord("WLSDPLY-21000", handler.getLevel().getLocalizedName()))
                    + System.lineSeparator();
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

        public synchronized int pushSection() {
            super.push();
            int result = totalRecords;
            totalRecords = 0;
            return result;
        }

        int getTotalRecords() {
            return totalRecords;
        }

        void logStart() {
            if (getTotalRecords() > 0) {
                System.out.println(LINE_SEPARATION);
                target.publish(getLogRecord("WLSDPLY-21000", getLevel().getName()));
                System.out.println(LINE_SEPARATION);
            }
        }

        void logEnd() {
            System.out.println(LINE_SEPARATION);
            target.publish(getLogRecord("WLSDPLY-21001", getLevel().getName(), getTotalRecords()));
        }
    }

    private class NoActionHandler extends LevelHandler {

        NoActionHandler(Handler handler, int size, Level level) {
            super(handler, size, level);
        }


        @Override
        public void publish(LogRecord record) {

        }

        @Override
        public int pushSection() {
            return getTotalRecords();
        }

        @Override
        public void push() {

        }

        @Override
        public void flush() {

        }

        @Override
        public void close() throws SecurityException {

        }

        @Override
        public int getTotalRecords() {
            return -1;
        }

        @Override
        void logStart() {

        }

        @Override
        void logEnd() {

        }
    }

    private void configure() {
        LogManager manager = LogManager.getLogManager();
        String cname = getClass().getName();

        bufferSize = getSize(manager.getProperty(cname + "." + SIZE_PROPERTY));
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