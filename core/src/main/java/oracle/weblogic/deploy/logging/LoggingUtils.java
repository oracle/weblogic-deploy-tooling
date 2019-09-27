/*
 * Copyright (c) 2019, Oracle and/or its affiliates. All rights reserved.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.logging;

import java.text.MessageFormat;
import java.util.Properties;
import java.util.logging.Handler;
import java.util.logging.LogRecord;

import static oracle.weblogic.deploy.logging.WLSDeployLoggingConfig.ERROR_EXIT_CODE;

public class LoggingUtils {

    public static <T extends Handler> Class<T> getHandlerClass(String handlerName) {
        Class<T> handler = null;
        try {
            Class<?> checkClass = Class.forName(handlerName);
            handler = (Class<T>)checkClass.asSubclass(Class.forName(handlerName));
        } catch(ClassNotFoundException | ClassCastException cnf) {
            exitWithError(
                    MessageFormat.format("Unable to find handler class {0} so skipping logging configuration",
                    handlerName));
        }
        return handler;
    }

    public static <T extends Handler> T getHandlerInstance(Class<T> handlerClass) {
        T handler = null;
        try {
            handler =  handlerClass.newInstance();
         } catch (InstantiationException | IllegalAccessException e){
            exitWithError(MessageFormat.format("Unable to instantiate Handler for Class {0}", handlerClass));
        }
        return handler;
    }

    public static <T extends Handler> T getHandlerInstance(String handlerClassName) {
        return getHandlerInstance(LoggingUtils.<T>getHandlerClass(handlerClassName));
    }

    public static void exitWithError(String message) {
        System.err.println(message);
        System.exit(ERROR_EXIT_CODE);
    }

    public static LogRecord cloneRecordWithoutException(LogRecord record) {
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

    public static void printLogProperties(Properties logProps, String prefix) {
        if (logProps != null) {
            for (String propName : logProps.stringPropertyNames()) {
                System.err.println(prefix + propName + '=' + logProps.getProperty(propName));
            }
        }
    }

}