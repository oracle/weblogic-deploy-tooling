/*
 * Copyright (c) 2024, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.tool.archive_helper.remove;

import oracle.weblogic.deploy.logging.PlatformLogger;
import oracle.weblogic.deploy.logging.WLSDeployLogFactory;
import oracle.weblogic.deploy.tool.archive_helper.ArchiveHelperException;
import oracle.weblogic.deploy.tool.archive_helper.CommandResponse;
import oracle.weblogic.deploy.util.ExitCode;
import oracle.weblogic.deploy.util.WLSDeployArchiveIOException;
import picocli.CommandLine.Command;
import picocli.CommandLine.Option;

import static oracle.weblogic.deploy.tool.ArchiveHelper.LOGGER_NAME;

@Command(
    name = "xacmlRole",
    header = "Remove XACML Role Mapper role definition file from the archive file.",
    description = "%nCommand-line options:"
)
public class RemoveXACMLRoleCommand extends RemoveTypeCommandBase {
    private static final String CLASS = RemoveXACMLRoleCommand.class.getName();
    private static final PlatformLogger LOGGER = WLSDeployLogFactory.getLogger(LOGGER_NAME);
    private static final String TYPE = "XACML Role Mapper role definition file";

    @Option(
        names = {"-name"},
        description = "Name of the XACML Role Mapper role definition file to be removed from the archive file",
        required = true
    )
    private String name;

    @Override
    public CommandResponse call() throws Exception {
        final String METHOD = "call";
        LOGGER.entering(CLASS, METHOD);

        CommandResponse response;
        try {
            initializeOptions();

            int entriesRemoved;
            if (this.force) {
                entriesRemoved = this.archive.removeXACMLRoleFile(this.name, true);
            } else {
                entriesRemoved = this.archive.removeXACMLRoleFile(this.name);
            }
            response = new CommandResponse(ExitCode.OK, "WLSDPLY-30026", TYPE, this.name,
                entriesRemoved, this.archiveFilePath);
        } catch (ArchiveHelperException ex) {
            LOGGER.severe("WLSDPLY-30027", ex, TYPE, this.name, this.archiveFilePath, ex.getLocalizedMessage());
            response = new CommandResponse(ex.getExitCode(), "WLSDPLY-30027", TYPE, this.name,
                this.archiveFilePath, ex.getLocalizedMessage());
        } catch (WLSDeployArchiveIOException | IllegalArgumentException ex) {
            LOGGER.severe("WLSDPLY-30028", ex, TYPE, this.name, this.force,
                this.archiveFilePath, ex.getLocalizedMessage());
            response = new CommandResponse(ExitCode.ERROR, "WLSDPLY-30028", TYPE, this.name, this.force,
                this.archiveFilePath, ex.getLocalizedMessage());
        }

        LOGGER.exiting(CLASS, METHOD, response);
        return response;
    }
}
