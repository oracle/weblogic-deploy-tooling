/*
 * Copyright (c) 2017, 2019, Oracle and/or its affiliates. All rights reserved.
 * Licensed under the Universal Permissive License v 1.0 as shown at http://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.logging;

import java.util.logging.ConsoleHandler;
import java.util.logging.LogRecord;

/**
 * The WLS Deploy Console Handler that prevents stack traces from being output to the console.
 */
public class WLSDeployLoggingConsoleHandler extends ConsoleHandler {

    /**
     * The default constructor.
     */
    public WLSDeployLoggingConsoleHandler() {
        // nothing to do
    }

    @Override
    public void publish(LogRecord record) {
        LogRecord myRecord = cloneRecordWithoutException(record);
        super.publish(myRecord);
    }

    private static LogRecord cloneRecordWithoutException(LogRecord record) {
        LogRecord newRecord = new LogRecord(record.getLevel(), record.getMessage());

        newRecord.setLoggerName(record.getLoggerName());
        newRecord.setMillis(record.getMillis());
        newRecord.setParameters(record.getParameters());
        newRecord.setResourceBundle(record.getResourceBundle());
        newRecord.setResourceBundleName(record.getResourceBundleName());
        newRecord.setSequenceNumber(record.getSequenceNumber());
        newRecord.setSourceClassName(record.getSourceClassName());
        newRecord.setSourceMethodName(record.getSourceMethodName());
        newRecord.setThreadID(record.getThreadID());
        // Skip thrown
        return newRecord;
    }
}
