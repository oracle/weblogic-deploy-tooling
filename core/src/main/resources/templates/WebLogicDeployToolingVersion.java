/*
 * Copyright (c) 2017, 2019, Oracle Corporation and/or its affiliates.  All rights reserved.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.util;

import oracle.weblogic.deploy.logging.PlatformLogger;
import oracle.weblogic.deploy.logging.WLSDeployLogFactory;

/**
 * The utility class that provides the version of the WebLogic Deploy Tooling software.
 */
public final class WebLogicDeployToolingVersion {
    private static final PlatformLogger LOGGER = WLSDeployLogFactory.getLogger("wlsdeploy");

    private static final String WLS_DEPLOY_VERSION = "${project.version}";
    private static final String WLS_DEPLOY_BUILD_REVISION = "${git.branch}.${git.shortRevision}";
    private static final String WLS_DEPLOY_BUILD_TIMESTAMP = "${weblogic.deploy.build.timestamp}";
    private static final String WLS_DEPLOY_FULL_VERSION =
        WLS_DEPLOY_VERSION + ":" + WLS_DEPLOY_BUILD_REVISION + ":" + WLS_DEPLOY_BUILD_TIMESTAMP;

    private WebLogicDeployToolingVersion() {
        // hide the constructor for this utility class
    }

    /**
     * Get the base version of the WebLogic Deploy Tooling software.
     *
     * @return the base version
     */
    public static String getVersion() {
        return WLS_DEPLOY_VERSION;
    }

    /**
     * Get the build revision of the WebLogic Deploy Tooling software..
     *
     * @return the build number in the &lt;branch&gt;.&lt;short-revision-number&gt; format
     */
    public static String getBuildRevision() {
        return WLS_DEPLOY_BUILD_REVISION;
    }

    /**
     * Get the build timestamp of the WebLogic Deploy Tooling software.
     *
     * @return the build timestamp
     */
    public static String getBuildTimestamp() {
        return WLS_DEPLOY_BUILD_TIMESTAMP;
    }

    /**
     * Get the full version of the WebLogic Deploy Tooling software.
     *
     * @return the full version
     */
    public static String getFullVersion() {
        return WLS_DEPLOY_FULL_VERSION;
    }

    /**
     * Utility method to write the WebLogic Deploy Tooling software version to the log file.
     *
     * @param programName - the name of the WebLogic Deploy Tooling program that is running
     */
    public static void logVersionInfo(String programName) {
        LOGGER.info("WLSDPLY-01750", programName, getFullVersion());
    }

    /**
     * Command-line method to print the full version of the WebLogic Deploy Tooling
     * software to standard out.
     *
     * @param args - No arguments are required
     */
    public static void main(String[] args) {
        System.out.println(getFullVersion());
    }
}
