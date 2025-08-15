/*
 * Copyright (c) 2023, 2025, Oracle and/or its affiliates.
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
import oracle.weblogic.deploy.util.WLSDeployArchive.ArchiveEntryType;
import oracle.weblogic.deploy.util.WLSDeployArchiveIOException;

import static oracle.weblogic.deploy.tool.ArchiveHelper.LOGGER_NAME;
import static oracle.weblogic.deploy.util.WLSDeployArchive.ArchiveEntryType.PLUGIN_DEPLOYMENT;

public abstract class AddTypeCommandBase extends AddOptions implements Callable<CommandResponse> {
    private static final String CLASS = AddTypeCommandBase.class.getName();
    private static final PlatformLogger LOGGER = WLSDeployLogFactory.getLogger(LOGGER_NAME);

    protected File initializeOptions(String sourcePath) throws ArchiveHelperException {
        final String METHOD = "initializeOptions";
        LOGGER.entering(CLASS, METHOD, sourcePath);

        initializeOptions();
        File result = getSourceLocationFile(sourcePath);

        LOGGER.exiting(CLASS, METHOD, result.getAbsolutePath());
        return result;
    }

    /**
     * Add a non-segregated file or directory to the archive.
     * @param archiveType the archive entry type
     * @param typeName readable type name for logging
     * @param sourcePath location of the file or directory to be added
     * @return command response
     */
    protected CommandResponse addType(ArchiveEntryType archiveType, String typeName, String sourcePath) {
        final String METHOD = "addType";
        LOGGER.entering(CLASS, archiveType);

        CommandResponse response;
        File sourceFile;
        try {
            sourceFile = initializeOptions(sourcePath);

            String resultName;
            if (this.overwrite) {
                resultName = this.archive.replaceItem(PLUGIN_DEPLOYMENT, sourceFile.getName(), sourceFile.getPath());
            } else {
                resultName = this.archive.addItem(PLUGIN_DEPLOYMENT, sourceFile.getPath());
            }
            response = new CommandResponse(ExitCode.OK, resultName);
        } catch (ArchiveHelperException ex) {
            LOGGER.severe("WLSDPLY-30010", ex, typeName, sourcePath,
                    this.archiveFilePath, ex.getLocalizedMessage());
            response = new CommandResponse(ex.getExitCode(), "WLSDPLY-30010", typeName,
                    sourcePath, this.archiveFilePath, ex.getLocalizedMessage());
        } catch (WLSDeployArchiveIOException | IllegalArgumentException ex) {
            LOGGER.severe("WLSDPLY-30011", ex, typeName, sourcePath,
                    this.overwrite, this.archiveFilePath, ex.getLocalizedMessage());
            response = new CommandResponse(ExitCode.ERROR, "WLSDPLY-30011", typeName,
                    sourcePath, this.overwrite, this.archiveFilePath, ex.getLocalizedMessage());
        }

        LOGGER.exiting(CLASS, METHOD, response);
        return response;
    }

    private File getSourceLocationFile(String path) throws ArchiveHelperException {
        final String METHOD = "getSourceLocationFile";
        LOGGER.entering(CLASS, METHOD, path);

        File result = FileUtils.getCanonicalFile(path);
        if (!result.exists()) {
            ArchiveHelperException ex =
                new ArchiveHelperException(ExitCode.ARG_VALIDATION_ERROR, "WLSDPLY-30009", path);
            LOGGER.throwing(CLASS, METHOD, ex);
            throw ex;
        }

        LOGGER.exiting(CLASS, METHOD, result.getAbsolutePath());
        return result;
    }
}
