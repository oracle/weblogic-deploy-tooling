package oracle.weblogic.deploy.logging;

import java.util.ArrayList;
import java.util.List;
import java.util.Properties;
import java.util.logging.*;


public class SummaryHandler extends MemoryHandler implements WLSDeployLogEndHandler {
    private static final String CLASS = SummaryHandler.class.getName();
    private static final PlatformLogger LOGGER = WLSDeployLogFactory.getLogger("wlsdeploy");
    private static final String LEVEL_PROPERTY = "level";
    private static final String TARGET_PROPERTY = "target";
    private static final String SIZE_PROPERTY = "size";
    private static final int DEFAULT_SIZE = 3000;

    private boolean online = false;
    private int bufferSize;

    private LevelHandler infoMemoryHandler = new NoActionHandler(Level.INFO);
    private LevelHandler warnMemoryHandler = new NoActionHandler(Level.WARNING);
    private LevelHandler errMemoryHandler = new NoActionHandler(Level.SEVERE);
    private LevelHandler[] handlers = {infoMemoryHandler, warnMemoryHandler, errMemoryHandler};
    private boolean closed = false;

    public SummaryHandler() {
        super();
        configure();
        infoMemoryHandler = getLevelHandler(Level.INFO);
        infoMemoryHandler = getLevelHandler(Level.WARNING);
        infoMemoryHandler = getLevelHandler(Level.SEVERE);
    }

    @Override
    public synchronized void publish(LogRecord record) {
        // after close, take yourself out of the mix. The stored up log messages are going to go to the
        // console handler anyway
        if (!closed) {
            infoMemoryHandler.publish(record);
            warnMemoryHandler.publish(record);
            errMemoryHandler.publish(record);
        }
    }

    @Override
    public synchronized void push() {
        String METHOD = "push";
        LOGGER.entering(CLASS, METHOD);
        closed = true;
        List<Integer> counts = new ArrayList<>();
        for (LevelHandler handler : handlers) {
            int count = handler.pushSection();
            if (count >= 0) {
                counts.add(count);
            }
        }
        int size = counts.size();
        String msgNbr = "WLSDPLY-21004";
        if (size == 2) {
            msgNbr = "WLSDPLY-21003";
        } else if (size == 3) {
            msgNbr = "WLSDPLY-21002";
        }
        // got to fix this as this isn't allowed ? check to see if it resolves the msg nbr. Is this going to be 1 arg?
        LOGGER.log(Level.ALL, msgNbr, (Object[])counts.toArray(new Object[size]));
        LOGGER.exiting(CLASS, METHOD);
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
     * @return properties to set in logging.properties
     */
    public static Properties getHandlerProperties() {
        String METHOD = "getHandlerProperties";
        LOGGER.entering(CLASS, METHOD);
        Properties properties = new Properties();
        properties.setProperty(LEVEL_PROPERTY, Level.INFO.getName());
        properties.setProperty(TARGET_PROPERTY, WLSDeployLoggingConsoleHandler.class.getName());
        LOGGER.exiting(CLASS, METHOD, properties);
        return properties;
    }

    private class SummaryFormatter extends Formatter {
        public synchronized String format(LogRecord logRecord) {
            // for now, only format the message in summary - maybe add logger name or other later
            return formatMessage(logRecord);
        }
    }

    private LevelHandler getLevelHandler(Level compareTo) {
        LevelHandler handler;
        if (getLevel().intValue() <= compareTo.intValue()) {
            handler = new LevelHandler(this, bufferSize, Level.ALL);
            setLevel(compareTo);
            setFilter(getFilter());
            setFormatter(new SummaryFormatter());
        } else {
            handler = new NoActionHandler(compareTo);
        }
        return handler;
    }

    private class LevelHandler extends MemoryHandler {

        private int totalRecords;

        LevelHandler(Handler handler, int size, Level level) {
            super(handler, size, Level.ALL);
            setLevel(level);
        }

        LevelHandler(Level level) {
            setLevel(level);
        }

        @Override
        public synchronized void publish(LogRecord record) {
            if (record.getLevel().intValue() == getLevel().intValue()) {
                ++totalRecords;
                super.publish(record);
            }
        }

        public int pushSection() {
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
            LOGGER.log(Level.ALL, "WLSDPLY-2100", getLevel().getName());
        }

        void logEnd() {
            LOGGER.log(Level.ALL, "WLSDPLY-2101", getLevel().getName(), getTotalRecords());
        }
    }

    private class NoActionHandler extends LevelHandler {

        NoActionHandler(Level level) {
            super(level);
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

}