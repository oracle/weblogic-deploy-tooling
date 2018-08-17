package oracle.weblogic.deploy.logging;

import java.text.MessageFormat;
import java.util.*;
import java.util.logging.*;
import java.util.logging.Formatter;


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
    private int bufferSize;

    private Handler target;
    private List<LevelHandler> handlers = new ArrayList<>();
    private boolean closed = false;

    public SummaryHandler() {
        super();
        configure();
        target = getConsoleHandler();
        LOGGER.setLevel(Level.INFO);
        addLevelHandler(Level.INFO);
        addLevelHandler(Level.WARNING);
        addLevelHandler(Level.SEVERE);
        System.out.println("*** summary handler");
    }

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
    public synchronized void push() {
        System.out.println("i am in push ");
        String METHOD = "push";
        LOGGER.entering(CLASS, METHOD);
        closed = true;
        setPushLevel(getLevel());
        StringBuffer buffer = new StringBuffer();
        java.util.Formatter fmt = new java.util.Formatter(buffer);
        for (LevelHandler handler : handlers) {
            int count = handler.pushSection();
            super.push();
            if (count >= 0) {
                fmt.format("  %1$s : %2$,5d", handler.getLevel().getName(), count);
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

    public void setOnline(boolean isOnline) {
        online = isOnline;
    }

    public boolean isOnline() {
        return online;
    }

    @Override
    public void logEnd(boolean online) {
        setOnline(online);
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
        properties.setProperty(FORMATTER_PROPERTY, SummaryFormatter.class.getName());
        return properties;
    }

    public class SummaryFormatter extends Formatter {
        public synchronized String format(LogRecord logRecord) {
            // for now, only format the message in summary - maybe add logger name or other later
            return formatMessage(logRecord);
        }
    }

    private void addLevelHandler(Level level) {
        LevelHandler handler = null;
        if (getLevel().intValue() <= level.intValue()) {
            handler = new LevelHandler(target, bufferSize, level);
            handler.setLevel(level);
            handler.setFilter(getFilter());
            //handler.setFormatter(new SummaryFormatter());
            handlers.add(handler);
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
            if (isOnline()) {
                logStart();
                super.push();
                logEnd();
            }
            return getTotalRecords();
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