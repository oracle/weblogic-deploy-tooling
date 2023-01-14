/*
 * Copyright (c) 2023, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.tool.archive_helper.add;

import java.io.File;
import java.util.concurrent.Callable;

import oracle.weblogic.deploy.logging.PlatformLogger;
import oracle.weblogic.deploy.logging.WLSDeployLogFactory;
import oracle.weblogic.deploy.tool.archive_helper.ArchiveHelperException;
import oracle.weblogic.deploy.tool.archive_helper.CommandResponse;
import oracle.weblogic.deploy.util.ExitCode;
import oracle.weblogic.deploy.util.FileUtils;

import static oracle.weblogic.deploy.tool.ArchiveHelper.LOGGER_NAME;

public abstract class AddTypeCommandBase extends AddOptions implements Callable<CommandResponse> {
    private static final String CLASS = AddTypeCommandBase.class.getName();
    private static final PlatformLogger LOGGER = WLSDeployLogFactory.getLogger(LOGGER_NAME);

    protected void initializeOptions() throws ArchiveHelperException {
        super.initializeOptions();
    }

    protected File initializeOptions(String sourcePath) throws ArchiveHelperException {
        final String METHOD = "initializeOptions";
        LOGGER.entering(CLASS, METHOD, sourcePath);

        initializeOptions();
        File result = getSourceLocationFile(sourcePath);

        LOGGER.exiting(CLASS, METHOD, result.getAbsolutePath());
        return result;
    }

    private File getSourceLocationFile(String path) throws ArchiveHelperException {
        final String METHOD = "getSourceLocationFile";
        LOGGER.entering(CLASS, METHOD, path);

        File result = FileUtils.getCanonicalFile(path);
        if (!result.exists()) {
            ArchiveHelperException ex =
                new ArchiveHelperException(ExitCode.ARG_VALIDATION_ERROR, "WLSDPLY-30007", path);
            LOGGER.throwing(CLASS, METHOD, ex);
            throw ex;
        }

        LOGGER.exiting(CLASS, METHOD, result.getAbsolutePath());
        return result;
    }
}
