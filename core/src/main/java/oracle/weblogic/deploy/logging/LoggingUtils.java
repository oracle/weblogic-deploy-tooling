/*
 * Copyright (c) 2019, 2022, Oracle Corporation and/or its affiliates.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.logging;

import java.util.Properties;
import java.util.logging.LogRecord;

/**
 * Utility class with methods used by the logging framework.
 */
public class LoggingUtils {

    private LoggingUtils() {
        // hide the constructor
    }

    /**
     * Make a copy of a log record without the exception.
     *
     * @param logRecord the log record to copy
     * @return the cloned log record without the exception
     */
    public static LogRecord cloneRecordWithoutException(LogRecord logRecord) {
        LogRecord newRecord = new LogRecord(logRecord.getLevel(), logRecord.getMessage());

        newRecord.setLoggerName(logRecord.getLoggerName());
        newRecord.setMillis(logRecord.getMillis());
        newRecord.setParameters(logRecord.getParameters());
        newRecord.setResourceBundle(logRecord.getResourceBundle());
        newRecord.setResourceBundleName(logRecord.getResourceBundleName());
        newRecord.setSequenceNumber(logRecord.getSequenceNumber());
        newRecord.setSourceClassName(logRecord.getSourceClassName());
        newRecord.setSourceMethodName(logRecord.getSourceMethodName());
        newRecord.setThreadID(logRecord.getThreadID());
        // Skip thrown
        return newRecord;
    }

    public static void printLogProperties(Properties logProps, String prefix) {
        if (logProps != null) {
            for (String propName : logProps.stringPropertyNames()) {
                System.err.println(prefix + propName + '=' + logProps.getProperty(propName));
            }
        }
    }
}
