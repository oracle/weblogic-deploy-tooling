/*
 * Copyright (c) 2018, Oracle and/or its affiliates. All rights reserved.
 * The Universal Permissive License (UPL), Version 1.0
 */
package oracle.weblogic.deploy.util;

import oracle.weblogic.deploy.logging.*;

import java.util.Enumeration;
import java.util.logging.Handler;
import java.util.logging.LogManager;

/**
 * Perform any Log and Clean up action prior to exiting the tool.
 */
public class WLSDeployBeforeExitAction {

    private static final String CLASS = WLSDeployBeforeExitAction.class.getName();
    private static final PlatformLogger LOGGER = WLSDeployLogFactory.getLogger("wlsdeploy.util");

    public static void cleanup_and_exit(boolean online) {
        String METHOD = "cleanup_and_exit";
        LOGGER.entering(CLASS, METHOD, online);
        log_cleanup(online);
        LOGGER.exiting(CLASS, METHOD);
    }

    public static void log_cleanup(boolean online) {
        String METHOD = "log_cleanup";
        LOGGER.entering(CLASS, METHOD, online);
        LogManager manager = LogManager.getLogManager();
        Enumeration<String> e = manager.getLoggerNames();
        while (e.hasMoreElements()) {
            String loggerName = e.nextElement();
            if (loggerName.startsWith(WLSDeployLoggingConfig.WLSDEPLOY_LOGGER_NAME)) {
                for (Handler handler : manager.getLogger(loggerName).getHandlers()) {
                    if (WLSDeployLogEndHandler.class.isAssignableFrom(handler.getClass())) {
                        LOGGER.fine("Calling Handler {0} for log cleanup and end", WLSDeployLogEndHandler.class);
                        ((WLSDeployLogEndHandler)handler).logEnd(online);
                    }
                }
            }
        }
        LOGGER.exiting(CLASS, METHOD);
    }

}