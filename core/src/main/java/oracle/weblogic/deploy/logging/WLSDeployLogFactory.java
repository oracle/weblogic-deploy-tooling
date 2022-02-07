/*
 * Copyright (c) 2017, 2022, Oracle Corporation and/or its affiliates.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.logging;

import java.util.HashMap;
import java.util.logging.Logger;

/**
 * The java.util.logging log factory for the WLS Deploy tooling.
 */
public final class WLSDeployLogFactory {
    private static final HashMap<String, PlatformLogger> LOGGERS = new HashMap<>();

    private static final String DEFAULT_RESOURCE_BUNDLE_NAME = "oracle.weblogic.deploy.messages.wlsdeploy_rb";

    // Hide the default constructor.
    //
    private WLSDeployLogFactory() {
        // No constructor for this utility class
    }

    /**
     * Get the logger using the specified logger name and resource bundle name.
     *
     * @param loggerName the logger name
     * @param resourceBundleName the resource bundle name
     * @return the logger
     */
    public static PlatformLogger getLogger(String loggerName, String resourceBundleName) {
        PlatformLogger myLogger = LOGGERS.get(loggerName);

        if (myLogger == null) {
            myLogger = initializeLogger(loggerName, resourceBundleName);
        }
        return myLogger;
    }

    /**
     * Get the logger using the logger name and using the default resource bundle for the WLS Deploy tooling.
     *
     * @param loggerName the logger name
     * @return the logger
     */
    public static PlatformLogger getLogger(String loggerName) {
        PlatformLogger myLogger = LOGGERS.get(loggerName);

        if (myLogger == null) {
            myLogger = initializeLogger(loggerName, DEFAULT_RESOURCE_BUNDLE_NAME);
        }
        return myLogger;
    }

    ////////////////////////////////////////////////////////////////////////////////
    // private helper methods                                                     //
    ////////////////////////////////////////////////////////////////////////////////

    private static synchronized PlatformLogger initializeLogger(String loggerName, String resourceBundleName) {
        // Make sure another thread didn't get here first and create it)
        PlatformLogger myLogger = LOGGERS.get(loggerName);
        if (myLogger == null) {
            myLogger = getComponentLogger(loggerName, resourceBundleName);
            LOGGERS.put(loggerName, myLogger);
        }
        return myLogger;
    }

    private static PlatformLogger getComponentLogger(String name, String resourceBundleName) {
        final Logger logger = Logger.getLogger(name, resourceBundleName);
        return new PlatformLogger(logger);
    }
}
