/*
 * Copyright (c) 2023, 2025, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.tool.archive_helper.extract;

import java.util.concurrent.Callable;

import oracle.weblogic.deploy.logging.PlatformLogger;
import oracle.weblogic.deploy.logging.WLSDeployLogFactory;
import oracle.weblogic.deploy.tool.archive_helper.ArchiveHelperException;
import oracle.weblogic.deploy.tool.archive_helper.CommandResponse;
import oracle.weblogic.deploy.util.ExitCode;
import oracle.weblogic.deploy.util.WLSDeployArchive;
import oracle.weblogic.deploy.util.WLSDeployArchiveIOException;

import static oracle.weblogic.deploy.tool.ArchiveHelper.LOGGER_NAME;

public abstract class ExtractTypeCommandBase extends ExtractOptions implements Callable<CommandResponse> {
    private static final String CLASS = ExtractTypeCommandBase.class.getName();
    private static final PlatformLogger LOGGER = WLSDeployLogFactory.getLogger(LOGGER_NAME);
    private static final String ERROR_KEY = "WLSDPLY-30047";

    /**
     * Extract a non-segregated file or directory from the archive.
     * @param archiveType the archive entry type
     * @param typeName readable type name for logging
     * @param name the name or archive path of entry to be extracted
     * @return command response
     */    
    public CommandResponse extractType(WLSDeployArchive.ArchiveEntryType archiveType, String typeName, String name) {
        final String METHOD = "extractType";
        LOGGER.entering(CLASS, METHOD, archiveType, typeName, name);

        CommandResponse response;
        try {
            initializeOptions();

            this.archive.extractItem(archiveType, name, this.targetDirectory);
            response = new CommandResponse(ExitCode.OK, "WLSDPLY-30046", typeName, name,
                    this.archiveFilePath, this.targetDirectory.getPath());
        } catch (ArchiveHelperException ex) {
            LOGGER.severe(ERROR_KEY, ex, typeName, name, this.archiveFilePath,
                    this.targetDirectory.getPath(), ex.getLocalizedMessage());
            response = new CommandResponse(ex.getExitCode(), ERROR_KEY, typeName, name,
                    this.archiveFilePath, this.targetDirectory.getPath(), ex.getLocalizedMessage());
        } catch (WLSDeployArchiveIOException | IllegalArgumentException ex) {
            LOGGER.severe(ERROR_KEY, ex, typeName, name, this.archiveFilePath,
                    this.targetDirectory.getPath(), ex.getLocalizedMessage());
            response = new CommandResponse(ExitCode.ERROR, ERROR_KEY, typeName, name,
                    this.archiveFilePath, this.targetDirectory.getPath(), ex.getLocalizedMessage());
        }

        LOGGER.exiting(CLASS, METHOD, response);
        return response;
    }
}
