/*
 * Copyright (c) 2017, 2022, Oracle Corporation and/or its affiliates.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.logging;

import java.util.ArrayList;
import java.util.Enumeration;
import java.util.List;
import java.util.logging.Level;
import java.util.logging.LogManager;
import java.util.logging.LogRecord;
import java.util.logging.Logger;

/**
 * A standalone version of the platform logger.
 */
public class PlatformLogger {
    private static final String CLASS = PlatformLogger.class.getName();

    private final Logger logger;

    /**
     * Creates a PlatformLogger wrapping around an API Logger; normally this should be done using the
     * PlatformLoggerFactory only.
     *
     * @param logger the Java Util Logger to use
     */
    public PlatformLogger(Logger logger) {
        this.logger = logger;
    }

    /**
     * Sets the level at which the underlying Logger operates. This should not be
     * called in the general case; levels should be set via OOB configuration
     * (a configuration file exposed by the logging implementation, management
     * API, etc).
     *
     * @param newLevel the new logging level
     */
    public void setLevel(Level newLevel) {
        logger.setLevel(newLevel);
    }

    /**
     * Logs a message at the CONFIG level.
     *
     * @param msg the message
     */
    public void config(String msg) {
        if (isConfigEnabled()) {
            CallerDetails details = inferCaller();
            logger.logp(Level.CONFIG, details.clazz, details.method, msg);
        }
    }

    /**
     * Logs a message which requires parameters at the CONFIG level.
     *
     * @param msg the message
     * @param params the objects to use to fill in the message
     */
    public void config(String msg, Object... params) {
        if (isConfigEnabled()) {
            CallerDetails details = inferCaller();
            logger.logp(Level.CONFIG, details.clazz, details.method, msg, params);
        }
    }

    /**
     * Logs a method entry. The calling class and method names will be inferred.
     */
    public void entering() {
        if (isFinerEnabled()) {
            CallerDetails details = inferCaller();
            logger.entering(details.clazz, details.method);
        }
    }

    /**
     * Logs a method entry, with a list of arguments of interest. The calling class and method
     * names will be inferred.
     * Warning: Depending on the nature of the arguments, it may be required to cast those of type
     * String to Object, to ensure that this variant is called as expected, instead of one of those
     * referenced below.
     *
     * @param params the parameters passed to the method
     * @see #entering(String, String)
     * @see #entering(String, String, Object...)
     */
    public void entering(Object... params) {
        if (isFinerEnabled()) {
            CallerDetails details = inferCaller();
            logger.entering(details.clazz, details.method, params);
        }
    }

    /**
     * Logs a method entry.
     *
     * @param sourceClass the class being entered
     * @param sourceMethod the method being entered
     */
    public void entering(String sourceClass, String sourceMethod) {
        logger.entering(sourceClass, sourceMethod);
    }

    /**
     * Logs a method entry, with a list of arguments of interest. Replaces the Logger equivalents taking a single
     * param or an Object array, and is backward-compatible with them.
     *
     * @param sourceClass the class being entered
     * @param sourceMethod the method being entered
     * @param params the parameters passed to the method
     * @see Logger#entering(String, String, Object[])
     */
    public void entering(String sourceClass, String sourceMethod, Object... params) {
        logger.entering(sourceClass, sourceMethod, params);
    }

    /**
     * Logs a method exit. The calling class and method names will be inferred.
     */
    public void exiting() {
        if (isFinerEnabled()) {
            CallerDetails details = inferCaller();
            logger.exiting(details.clazz, details.method);
        }
    }

    /**
     * Logs a method exit, with a result object. The calling class and method names will be
     * inferred.
     *
     * @param result the return value of the method being exited
     */
    public void exiting(Object result) {
        if (isFinerEnabled()) {
            CallerDetails details = inferCaller();
            logger.exiting(details.clazz, details.method, result);
        }
    }

    /**
     * Logs a method exit.
     *
     * @param sourceClass the class being exited
     * @param sourceMethod the method being exited
     */
    public void exiting(String sourceClass, String sourceMethod) {
        logger.exiting(sourceClass, sourceMethod);
    }

    /**
     * Logs a method exit, with a result object.
     *
     * @param sourceClass the class being exited
     * @param sourceMethod the method being exited
     * @param result the return value of the method being exited
     */
    public void exiting(String sourceClass, String sourceMethod, Object result) {
        logger.exiting(sourceClass, sourceMethod, result);
    }

    /**
     * Logs a message at the FINE level.
     *
     * @param msg the message
     */
    public void fine(String msg) {
        if (isFineEnabled()) {
            CallerDetails details = inferCaller();
            logger.logp(Level.FINE, details.clazz, details.method, msg);
        }
    }

    /**
     * Logs a message which requires parameters at the FINE level.
     *
     * @param msg the message
     * @param params the objects to use to fill in the message details
     */
    public void fine(String msg, Object... params) {
        if (isFineEnabled()) {
            CallerDetails details = inferCaller();
            logger.logp(Level.FINE, details.clazz, details.method, msg, params);
        }
    }

    /**
     * Logs a message which requires parameters at the FINE level.
     *
     * @param msg    the message to log
     * @param error  the exception to log
     * @param params the objects to use to fill in the message details
     */
    public void fine(String msg, Throwable error, Object... params) {
        if (isFineEnabled()) {
            CallerDetails details = inferCaller();
            logger.log( getLogRecord( Level.FINE, details, msg, error, params ) );
        }
    }

    /**
     * Logs a message at the FINER level.
     *
     * @param msg the message
     */
    public void finer(String msg) {
        if (isFinerEnabled()) {
            CallerDetails details = inferCaller();
            logger.logp(Level.FINER, details.clazz, details.method, msg);
        }
    }

    /**
     * Logs a message which requires parameters at the FINER level.
     *
     * @param msg the message
     * @param params the objects to use to fill in the message details
     */
    public void finer(String msg, Object... params) {
        if (isFinerEnabled()) {
            CallerDetails details = inferCaller();
            logger.logp(Level.FINER, details.clazz, details.method, msg, params);
        }
    }

    /**
     * Logs a message at the FINEST level.
     *
     * @param msg the message
     */
    public void finest(String msg) {
        if (isFinestEnabled()) {
            CallerDetails details = inferCaller();
            logger.logp(Level.FINEST, details.clazz, details.method, msg);
        }
    }

    /**
     * Logs a message which requires parameters at the FINEST level.
     *
     * @param msg the message
     * @param params the objects to use to fill in the message details
     */
    public void finest(String msg, Object... params) {
        if (isFinestEnabled()) {
            CallerDetails details = inferCaller();
            logger.logp(Level.FINEST, details.clazz, details.method, msg, params);
        }
    }

    /**
     * Returns the level at which the underlying logger operates.
     *
     * @return the current logging level for this logger
     */
    public Level getLevel() {
        return logger.getLevel();
    }

    /**
     * Returns the name of the underlying logger.
     *
     * @return the name of the logger
     */
    public String getName() {
        return logger.getName();
    }

    /**
     * Returns the underlying logger. This should only be used when component code calls others' code, and that code
     * requires that we provide it with a Logger.
     *
     * @return the underlying java.util.Logger object
     */
    public Logger getUnderlyingLogger() {
        return logger;
    }

    /**
     * Logs a message at the INFO level.
     *
     * @param msg the message
     */
    public void info(String msg) {
        CallerDetails details = inferCaller();
        logger.logp(Level.INFO, details.clazz, details.method, msg);
    }

    /**
     * Logs a message which requires parameters at the INFO level.
     *
     * @param msg the message
     * @param params the objects to use to fill in the message details
     */
    public void info(String msg, Object... params) {
        CallerDetails details = inferCaller();
        logger.logp(Level.INFO, details.clazz, details.method, msg, params);
    }

    /**
     * Checks if a message at CONFIG level would actually be logged.
     *
     * @return whether or not the CONFIG level is enabled
     */
    public boolean isConfigEnabled() {
        return logger.isLoggable(Level.CONFIG);
    }

    /**
     * Checks if a message at FINE level would actually be logged.
     *
     * @return whether or not the FINE level is enabled
     */
    public boolean isFineEnabled() {
        return logger.isLoggable(Level.FINE);
    }

    /**
     * Checks if a message at FINER level would actually be logged.
     *
     * @return whether or not the FINER level is enabled
     */
    public boolean isFinerEnabled() {
        return logger.isLoggable(Level.FINER);
    }

    /**
     * Checks if a message at FINEST level would actually be logged.
     *
     * @return whether or not the FINEST level is enabled
     */
    public boolean isFinestEnabled() {
        return logger.isLoggable(Level.FINEST);
    }

    /**
     * Checks if a message at INFO level would actually be logged.
     *
     * @return whether or not the INFO level is enabled
     */
    @SuppressWarnings("unused")
    public boolean isInfoEnabled() {
        return logger.isLoggable(Level.INFO);
    }

    /**
     * Checks if a message at the provided level would actually be logged.
     *
     * @param level the logging level to check
     * @return whether or not the specified logging level is enabled
     */
    public boolean isLoggable(Level level) {
        return logger.isLoggable(level);
    }

    /**
     * Checks if a message at SEVERE level would actually be logged.
     *
     * @return whether or not the SEVERE level is enabled
     */
    public boolean isSevereEnabled() {
        return logger.isLoggable(Level.SEVERE);
    }

    /**
     * Checks if a message at WARNING level would actually be logged.
     *
     * @return whether or not the WARNING level is enabled
     */
    @SuppressWarnings("unused")
    public boolean isWarningEnabled() {
        return logger.isLoggable(Level.WARNING);
    }

    /**
     * Logs a message at the requested level. Normally, one of the level-specific
     * methods should be used instead.
     *
     * @param level the severity of the log message
     * @param msg   the message to log
     */
    public void log(Level level, String msg) {
        if (isLoggable(level)) {
            CallerDetails details = inferCaller();
            logger.logp(level, details.clazz, details.method, msg);
        }
    }

    /**
     * Logs a message which requires parameters. This replaces the Logger equivalents taking a single param or an Object
     * array, and is backward-compatible with them. Calling the per-Level methods is preferred, but this is present for
     * completeness.
     *
     * @param level  the severity of the log message
     * @param msg    the message to log
     * @param params the objects to use to fill in the message details
     * @see Logger#log(java.util.logging.Level, String, Object[])
     */
    public void log(Level level, String msg, Object... params) {
        if (isLoggable(level)) {
            CallerDetails details = inferCaller();
            logger.logp(level, details.clazz, details.method, msg, params);
        }
    }

    /**
     * Logs a message which accompanies a Throwable. Calling equivalent per-Level method is preferred, but this is
     * present for completeness.
     *
     * @param level  the severity of the log message
     * @param msg    the message to log
     * @param thrown the exception to log
     */
    public void log(Level level, String msg, Throwable thrown) {
        if (isLoggable(level)) {
            CallerDetails details = inferCaller();
            logger.logp(level, details.clazz, details.method, msg, thrown);
        }
    }

    /**
     * Logs a message at the SEVERE level.
     *
     * @param msg    the message to log
     */
    public void severe(String msg) {
        CallerDetails details = inferCaller();
        logger.logp(Level.SEVERE, details.clazz, details.method, msg);
    }

    /**
     * Logs a message which requires parameters at the SEVERE level.
     *
     * @param msg    the message to log
     * @param params the objects to use to fill in the message details
     */
    public void severe(String msg, Object... params) {
        CallerDetails details = inferCaller();
        logger.logp(Level.SEVERE, details.clazz, details.method, msg, params);
    }

    /**
     * Logs a message which requires parameters at the SEVERE level.
     *
     * @param msg    the message to log
     * @param error  the exception to log
     * @param params the objects to use to fill in the message details
     */
    public void severe(String msg, Throwable error, Object... params) {
        CallerDetails details = inferCaller();
        logger.log(getLogRecord(Level.SEVERE, details, msg, error, params));
    }

    /**
     * Logs a message which accompanies a Throwable at the SEVERE level.
     *
     * @param msg    the message to log
     * @param thrown the exception to log
     */
    public void severe(String msg, Throwable thrown) {
        CallerDetails details = inferCaller();
        logger.logp(Level.SEVERE, details.clazz, details.method, msg, thrown);
    }

    /**
     * Logs that an exception will be thrown.  The calling class and method names will be inferred.
     *
     * @param pending the exception being thrown
     */
    public void throwing(Throwable pending) {
        if (isFinerEnabled()) {
            CallerDetails details = inferCaller();
            logger.throwing(details.clazz, details.method, pending);
        }
    }

    /**
     * Logs that an exception will be thrown.
     *
     * @param sourceClass  the class throwing the exception
     * @param sourceMethod the method throwing the exception
     * @param pending      the exception being thrown
     */
    public void throwing(String sourceClass, String sourceMethod, Throwable pending) {
        logger.throwing(sourceClass, sourceMethod, pending);
    }

    /**
     * Logs a message at the WARNING level.
     *
     * @param msg    the message to log
     */
    public void warning(String msg) {
        CallerDetails details = inferCaller();
        logger.logp(Level.WARNING, details.clazz, details.method, msg);
    }

    /**
     * Logs a message which requires parameters at the WARNING level.
     *
     * @param msg    the message to log
     * @param params the objects to use to fill in the message details
     */
    public void warning(String msg, Object... params) {
        CallerDetails details = inferCaller();
        logger.logp(Level.WARNING, details.clazz, details.method, msg, params);
    }

    /**
     * Logs a message which requires parameters and has an exception at the WARNING level.
     *
     * @param msg    the message to log
     * @param error  the exception to log
     * @param params the objects to use to fill in the message details
     */
    public void warning(String msg, Throwable error, Object... params) {
        CallerDetails details = inferCaller();
        logger.log(getLogRecord(Level.WARNING, details, msg, error, params));
    }

    /**
     * Logs a message which accompanies a Throwable at the WARNING level.
     *
     * @param msg    the message to log
     * @param thrown the exception to log
     */
    public void warning(String msg, Throwable thrown) {
        CallerDetails details = inferCaller();
        logger.logp(Level.WARNING, details.clazz, details.method, msg, thrown);
    }

    /**
     * Return a list of the current loggers.
     *
     * @return List of Logger from the Log Manager
     */
    @SuppressWarnings("unused")
    public static List<Logger> getLoggers() {
        LogManager manager = LogManager.getLogManager();
        Enumeration<String> e = manager.getLoggerNames();
        List<Logger> topList = new ArrayList<>();
        while (e.hasMoreElements()) {
            String loggerName = e.nextElement();
            Logger logger = manager.getLogger(loggerName);
            if(logger != null) {
                topList.add(logger);
            }
        }
        return topList;
    }

    /**
     * Obtains caller details, class name and method, to be provided to the actual Logger. This
     * code is adapted from ODLLogRecord, which should yield consistency in reporting using
     * PlatformLogger versus a raw (ODL) Logger. JDK Logger does something similar but utilizes
     * native methods directly.
     */
    CallerDetails inferCaller() {
        CallerDetails details = new CallerDetails();
        Throwable t = new Throwable();
        StackTraceElement[] stack = t.getStackTrace();

        // Walk the stack until we hit a frame outside this class
        int i = 0;
        while (i < stack.length) {
            StackTraceElement frame = stack[i];
            String cname = frame.getClassName();
            if (!cname.equals(CLASS)) {
                details.clazz = cname;
                details.method = frame.getMethodName();
                break;
            }
            i++;
        }

        return details;
    }

    private LogRecord getLogRecord(Level level, CallerDetails details, String msg, Throwable error, Object... params) {
        LogRecord logRecord = new LogRecord(level, msg);
        logRecord.setLoggerName(this.getName());
        logRecord.setMillis(System.currentTimeMillis());
        if (params != null && params.length != 0) {
            logRecord.setParameters(params);
        }
        logRecord.setResourceBundle(logger.getResourceBundle());
        logRecord.setSourceClassName(details.clazz);
        logRecord.setSourceMethodName(details.method);
        logRecord.setThreadID((int)Thread.currentThread().getId());
        logRecord.setThrown(error);
        return logRecord;
    }

    /**
     * Holds caller details obtained by inference.
     */
    private static class CallerDetails {
        String clazz;
        String method;
    }
}
