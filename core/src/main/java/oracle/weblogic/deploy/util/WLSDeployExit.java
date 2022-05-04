/*
 * Copyright (c) 2018, 2022, Oracle Corporation and/or its affiliates.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.util;

import java.util.List;

import oracle.weblogic.deploy.logging.PlatformLogger;
import oracle.weblogic.deploy.logging.WLSDeployLogEndHandler;
import oracle.weblogic.deploy.logging.WLSDeployLogFactory;

/**
 * Perform generic "ready to exit" methods and exit the jvm. This should be used by the base tools
 * to exit instead of System.exit.
 */
public class WLSDeployExit {
    private static final String CLASS = WLSDeployExit.class.getName();
    private static final PlatformLogger LOGGER = WLSDeployLogFactory.getLogger("wlsdeploy.exit");

    private WLSDeployExit() {
        // hide the constructor
    }

    /**
     * Perform any last methods for the tools and exit the JVM.
     *
     * @param deployContext containing contextual information about the tool
     * @param errorCode for exit from the JVM
     */
    public static void exit(WLSDeployContext deployContext, int errorCode) {
        final String METHOD = "exit";
        LOGGER.entering(errorCode, CLASS, METHOD);
        logCleanup(deployContext);
        LOGGER.exiting(CLASS, METHOD);
        exit(errorCode);
    }

    /**
     * Exit the JVM with the provided exit code.
     *
     * @param errorCode for exit from the JVM
     */
    public static void exit(int errorCode) {
        // might want to validate the exit code first
        System.exit(errorCode);
    }

    private static void logCleanup(WLSDeployContext context) {
        final String METHOD = "logCleanup";
        LOGGER.entering(CLASS, METHOD, context);
        List<WLSDeployLogEndHandler> endHandlers = WLSDeployLogEndHandler.getEndHandlers();
        for (WLSDeployLogEndHandler endHandler : endHandlers) {
            endHandler.logEnd(context);
        }
        LOGGER.exiting(CLASS, METHOD);
    }
}
