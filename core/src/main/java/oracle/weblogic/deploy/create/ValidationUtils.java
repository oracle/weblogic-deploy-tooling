/*
 * Copyright (c) 2023, Oracle Corporation and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.create;

import java.io.File;

import oracle.weblogic.deploy.logging.PlatformLogger;
import oracle.weblogic.deploy.logging.WLSDeployLogFactory;
import oracle.weblogic.deploy.util.FileUtils;
import oracle.weblogic.deploy.util.StringUtils;

public class ValidationUtils {
    private static final String CLASS = ValidationUtils.class.getName();
    private static final PlatformLogger LOGGER = WLSDeployLogFactory.getLogger("wlsdeploy.create");

    private ValidationUtils() {
        // hide the constructor for this utility class
    }

    public static File validateExistingDirectory(String directoryName, String directoryTypeName)
        throws CreateException {
        final String METHOD = "validateExistingDirectory";

        LOGGER.entering(CLASS, METHOD, directoryName, directoryTypeName);
        File result;
        try {
            result = FileUtils.validateExistingDirectory(directoryName);
        } catch (IllegalArgumentException iae) {
            CreateException ce = new CreateException("WLSDPLY-12004", iae, CLASS, directoryTypeName,
                directoryName, iae.getLocalizedMessage());
            LOGGER.throwing(CLASS, METHOD, ce);
            throw ce;
        }
        LOGGER.exiting(CLASS, METHOD, result);
        return result;
    }

    public static File validateExistingExecutableFile(String executableFileName, String executableTypeName)
        throws CreateException {
        validateNonEmptyString(executableFileName, executableTypeName);
        return validateExistingExecutableFile(new File(executableFileName), executableTypeName);
    }

    public static File validateExistingExecutableFile(File executable, String executableTypeName)
        throws CreateException {
        final String METHOD = "validateExistingExecutableFile";

        LOGGER.entering(CLASS, METHOD, executable, executableTypeName);
        File tmp;
        try {
            tmp = FileUtils.validateExistingFile(executable.getAbsolutePath());
        } catch (IllegalArgumentException iae) {
            CreateException ce = new CreateException("WLSDPLY-12008", iae, CLASS, executableTypeName,
                executable.getAbsolutePath(), iae.getLocalizedMessage());
            LOGGER.throwing(CLASS, METHOD, ce);
            throw ce;
        }
        if (!tmp.canExecute()) {
            CreateException ce =
                new CreateException("WLSDPLY-12009", CLASS, executableTypeName, executable.getAbsolutePath());
            LOGGER.throwing(CLASS, METHOD, ce);
            throw ce;
        }
        LOGGER.exiting(CLASS, METHOD, tmp);
        return tmp;
    }

    public static String validateNonEmptyString(String value, String valueTypeName) throws CreateException {
        final String METHOD = "validateNonEmptyString";

        LOGGER.entering(CLASS, METHOD, value, valueTypeName);
        if (StringUtils.isEmpty(value)) {
            CreateException ce = new CreateException("WLSDPLY-12011", CLASS, valueTypeName);
            LOGGER.throwing(CLASS, METHOD, ce);
            throw ce;
        }
        return value;
    }
}
