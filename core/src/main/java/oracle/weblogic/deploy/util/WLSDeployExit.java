/*
 * Copyright (c) 2018, 2019, Oracle Corporation and/or its affiliates. All rights reserved.
 * Licensed under the Universal Permissive License v 1.0 as shown at http://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.util;

import java.util.ArrayList;
import java.util.LinkedList;
import java.util.List;
import java.util.logging.Handler;
import java.util.logging.Logger;
import java.util.Stack;

import oracle.weblogic.deploy.logging.PlatformLogger;
import oracle.weblogic.deploy.logging.WLSDeployLogEndHandler;
import oracle.weblogic.deploy.logging.WLSDeployLoggingConfig;
import oracle.weblogic.deploy.logging.WLSDeployLogFactory;

/**
 * Perform generic "ready to exit" methods and exit the jvm. This should be used by the base tools
 * to exit instead of System.exit.
 */
public class WLSDeployExit {

    private static final String CLASS = WLSDeployExit.class.getName();
    private static final PlatformLogger LOGGER = WLSDeployLogFactory.getLogger("wlsdeploy.util");

    /**
     * Perform any last methods for the tools and exit the JVM.
     *
     * @param deployContext containing contextual information about the tool
     * @param errorCode for exit from the JVM
     */
    public static void exit(WLSDeployContext deployContext, int errorCode) {
        String METHOD = "exit";
        LOGGER.entering(errorCode, CLASS, METHOD);
        logCleanup(deployContext);
        LOGGER.exiting(CLASS, METHOD);
        exit(errorCode);
    }

    /**
     * Exit the JVM with the provided exit code.
     *
     * @param error_code for exit from the JVM
     */
    public static void exit(int error_code) {
        // might want to validate the exit code first
        System.exit(error_code);
    }

    /**
     * Call any WLSDeployLogEnd Logger handlers so the handlers can perform end actions.
     *
     * @param context that contains contextual information about the tool that is currently running
     */
    public static void logCleanup(WLSDeployContext context) {
        String METHOD = "logCleanup";
        LOGGER.entering(CLASS, METHOD, context);
        Stack<Handler> handlers = reduceList(traverseHandlers(getTopLogList(), new LinkedList<Handler>()));
        while (handlers.size() > 0) {
            logEnd(context, (WLSDeployLogEndHandler)handlers.pop());
        }
        LOGGER.exiting(CLASS, METHOD);
    }

    private static List<Logger> getTopLogList() {
        List<Logger> loggerList = new ArrayList<>();
        for (Logger logger : PlatformLogger.getLoggers()) {
            if (logger.getName().startsWith(WLSDeployLoggingConfig.WLSDEPLOY_LOGGER_NAME)) {
                loggerList.add(logger);
            }
        }
        return loggerList;
    }

    private static synchronized void logEnd(WLSDeployContext context, WLSDeployLogEndHandler handler) {
        handler.logEnd(context);
    }

    private static LinkedList<Handler> traverseHandlers(List<Logger> loggers, LinkedList<Handler> handlerList) {
        List<Logger> parents = new ArrayList<>();
        if (loggers.size() > 0) {
            for (Logger logger : loggers) {
                if (logger.getUseParentHandlers()) {
                    for (Handler handler : logger.getHandlers()) {
                        if (WLSDeployLogEndHandler.class.isAssignableFrom(handler.getClass())) {
                            handlerList.add(handler);
                        }
                        Logger parent = logger.getParent();
                        if (parent != null) {
                            parents.add(parent);
                        }
                    }
                }
            }
            handlerList = traverseHandlers(parents, handlerList);
        }
        return handlerList;
    }

    private static Stack<Handler> reduceList(LinkedList<Handler> handlers) {
        Stack<Handler> reducedList = new Stack<>();
        while (handlers.size() > 0 ){
            Handler bottom = handlers.removeLast();
            if (!reducedList.contains(bottom)) {
                reducedList.add(bottom);
            }
        }
        return reducedList;
    }

}