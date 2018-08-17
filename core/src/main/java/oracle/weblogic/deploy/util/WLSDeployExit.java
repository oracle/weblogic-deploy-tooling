/*
 * Copyright (c) 2018, Oracle and/or its affiliates. All rights reserved.
 * The Universal Permissive License (UPL), Version 1.0
 */
package oracle.weblogic.deploy.util;

import oracle.weblogic.deploy.logging.*;

import java.util.*;
import java.util.logging.Handler;
import java.util.logging.Level;
import java.util.logging.LogManager;
import java.util.logging.Logger;

/**
 * Perform any Log and Clean up action prior to exiting the tool.
 */
public class WLSDeployExit {

    private static final String CLASS = WLSDeployExit.class.getName();
    private static final PlatformLogger LOGGER = WLSDeployLogFactory.getLogger("wlsdeploy.util");

    public static void initiate(String name, boolean online) {
        LOGGER.log(Level.ALL, "{0} tool started", name);
    }

    public static void exit(int error_code, boolean online) {
        String METHOD = "exit";
        LOGGER.entering(CLASS, METHOD, online);
        log_cleanup(online);
        LOGGER.exiting(CLASS, METHOD);
    }

    private static void exit(int error_code) {
        // might want to validate the exit code first
        System.exit(error_code);
    }

    private static void log_cleanup(boolean online) {
        String METHOD = "log_cleanup";
        LOGGER.entering(CLASS, METHOD, online);
        LogManager manager = LogManager.getLogManager();
        Enumeration<String> e = manager.getLoggerNames();
        Set<Handler> handlerSet = new HashSet<>();
        while (e.hasMoreElements()) {
            String loggerName = e.nextElement();
            if (loggerName.startsWith(WLSDeployLoggingConfig.WLSDEPLOY_LOGGER_NAME)) {
                Logger logger = manager.getLogger(loggerName);
                handlerSet.addAll(callLoggerHandlers(logger, online));
            }
        }
        for (Handler handler : handlerSet) {
            LOGGER.fine("Calling Handler {0} for log cleanup and end", handler.getClass());
            ((WLSDeployLogEndHandler) handler).logEnd(online);
        }
        LOGGER.exiting(CLASS, METHOD);
    }

    private static Set<Handler> callLoggerHandlers(Logger logger, boolean online) {
        Set<Handler> handlerSet = new HashSet<>();
        for (Handler handler : logger.getHandlers()) {
            if (WLSDeployLogEndHandler.class.isAssignableFrom(handler.getClass())) {
                handlerSet.add(handler);
            }
        }
        if (logger.getUseParentHandlers() && logger.getParent() != null) {
            handlerSet.addAll(callLoggerHandlers(logger.getParent(), online));
        }
        return handlerSet;
    }

}