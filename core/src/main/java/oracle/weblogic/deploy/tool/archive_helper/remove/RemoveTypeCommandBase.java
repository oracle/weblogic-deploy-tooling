/*
 * Copyright (c) 2023, 2025, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.tool.archive_helper.remove;

import java.util.concurrent.Callable;

import oracle.weblogic.deploy.logging.PlatformLogger;
import oracle.weblogic.deploy.logging.WLSDeployLogFactory;
import oracle.weblogic.deploy.tool.archive_helper.ArchiveHelperException;
import oracle.weblogic.deploy.tool.archive_helper.CommandResponse;
import oracle.weblogic.deploy.util.ExitCode;
import oracle.weblogic.deploy.util.WLSDeployArchive.ArchiveEntryType;
import oracle.weblogic.deploy.util.WLSDeployArchiveIOException;

import static oracle.weblogic.deploy.tool.ArchiveHelper.LOGGER_NAME;

public abstract class RemoveTypeCommandBase extends RemoveOptions implements Callable<CommandResponse> {
    private static final String CLASS = RemoveTypeCommandBase.class.getName();
    private static final PlatformLogger LOGGER = WLSDeployLogFactory.getLogger(LOGGER_NAME);

    /**
     * Remove a non-segregated file or directory from the archive.
     * @param archiveType the archive entry type
     * @param typeName readable type name for logging
     * @param name the name or archive path of entry to be removed
     * @return command response
     */
    public CommandResponse removeType(ArchiveEntryType archiveType, String typeName, String name) {
        final String METHOD = "removeType";
        LOGGER.entering(CLASS, METHOD);

        CommandResponse response;
        try {
            initializeOptions();

            int entriesRemoved;
            if (this.force) {
                entriesRemoved = this.archive.removeItem(archiveType, name, true);
            } else {
                entriesRemoved = this.archive.removeItem(archiveType, name);
            }
            response = new CommandResponse(ExitCode.OK, "WLSDPLY-30026", typeName, name,
                    entriesRemoved, this.archiveFilePath);
        } catch (ArchiveHelperException ex) {
            LOGGER.severe("WLSDPLY-30027", ex, typeName, name, this.archiveFilePath, ex.getLocalizedMessage());
            response = new CommandResponse(ex.getExitCode(), "WLSDPLY-30027", typeName, name,
                    this.archiveFilePath, ex.getLocalizedMessage());
        } catch (WLSDeployArchiveIOException | IllegalArgumentException ex) {
            LOGGER.severe("WLSDPLY-30028", ex, typeName, name, this.force,
                    this.archiveFilePath, ex.getLocalizedMessage());
            response = new CommandResponse(ExitCode.ERROR, "WLSDPLY-30028", typeName, name, this.force,
                    this.archiveFilePath, ex.getLocalizedMessage());
        }

        LOGGER.exiting(CLASS, METHOD, response);
        return response;
    }
}
