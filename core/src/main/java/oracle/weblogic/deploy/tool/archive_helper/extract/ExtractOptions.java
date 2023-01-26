/*
 * Copyright (c) 2023, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.tool.archive_helper.extract;

import java.io.File;

import oracle.weblogic.deploy.logging.PlatformLogger;
import oracle.weblogic.deploy.logging.WLSDeployLogFactory;
import oracle.weblogic.deploy.tool.archive_helper.ArchiveHelperException;
import oracle.weblogic.deploy.tool.archive_helper.CommonOptions;
import oracle.weblogic.deploy.util.ExitCode;
import oracle.weblogic.deploy.util.FileUtils;
import oracle.weblogic.deploy.util.StringUtils;
import picocli.CommandLine.Option;

import static oracle.weblogic.deploy.tool.ArchiveHelper.LOGGER_NAME;

public abstract class ExtractOptions extends CommonOptions {
    private static final String CLASS = ExtractOptions.class.getName();
    private static final PlatformLogger LOGGER = WLSDeployLogFactory.getLogger(LOGGER_NAME);
    @Option(
        names = {"-target"},
        description = "The target directory to which to extract the items from the archive",
        required = true
    )
    protected String targetDirectoryPath;
    protected File targetDirectory;

    protected void initializeOptions() throws ArchiveHelperException {
        super.initializeOptions(true);

        this.targetDirectory = createTargetDirectory();
    }

    private File createTargetDirectory() throws ArchiveHelperException {
        final String METHOD = "createTargetDirectory";
        LOGGER.entering(CLASS, METHOD);

        String fullTargetDirectoryName = FileUtils.getCanonicalPath(this.targetDirectoryPath);
        if (StringUtils.isEmpty(fullTargetDirectoryName)) {
            ArchiveHelperException ex = new ArchiveHelperException(ExitCode.USAGE_ERROR, "WLSDPLY-30043");
            LOGGER.throwing(CLASS, METHOD, ex);
            throw ex;
        }

        File targetDirectoryFile = new File(fullTargetDirectoryName);
        if (!targetDirectoryFile.isDirectory()) {
            ArchiveHelperException ex = new ArchiveHelperException(ExitCode.ARG_VALIDATION_ERROR, "WLSDPLY-30044",
                targetDirectoryFile.getAbsolutePath());
            LOGGER.throwing(CLASS, METHOD, ex);
            throw ex;
        }

        if (!targetDirectoryFile.exists() && !targetDirectoryFile.mkdirs()) {
            ArchiveHelperException ex = new ArchiveHelperException(ExitCode.ARG_VALIDATION_ERROR, "WLSDPLY-30045",
                targetDirectoryFile.getAbsolutePath());
            LOGGER.throwing(CLASS, METHOD, ex);
            throw ex;
        }

        LOGGER.exiting(CLASS, METHOD, targetDirectoryFile);
        return targetDirectoryFile;
    }
}
