/*
 * Copyright (c) 2023, Oracle and/or its affiliates.
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
    name = "serverKeystore",
    header = "Remove server keystore from the archive file.",
    description = "%nCommand-line options:",
    sortOptions = false
)
public class RemoveServerKeystoreCommand extends RemoveTypeCommandBase {
    private static final String CLASS = RemoveServerKeystoreCommand.class.getName();
    private static final PlatformLogger LOGGER = WLSDeployLogFactory.getLogger(LOGGER_NAME);
    private static final String TYPE = "server keystore";

    @Option(
        names = {"-server_name"},
        description = "Name of the server used to segregate the keystores in the archive file",
        required = true
    )
    private String serverName;

    @Option(
        names = {"-name"},
        description = "Name of the server keystore to be removed from the archive file",
        required = true
    )
    private String name;

    @Option(
        names = { "-help" },
        description = "Get help for the archiveHelper remove serverKeystore subcommand",
        usageHelp = true
    )
    private boolean helpRequested = false;

    @Override
    public CommandResponse call() throws Exception {
        final String METHOD = "call";
        LOGGER.entering(CLASS, METHOD);

        CommandResponse response;
        try {
            initializeOptions();

            int entriesRemoved;
            if (this.force) {
                entriesRemoved = this.archive.removeServerKeystore(this.serverName, this.name, true);
            } else {
                entriesRemoved = this.archive.removeServerKeystore(this.serverName, this.name);
            }
            response = new CommandResponse(ExitCode.OK, "WLSDPLY-30029", TYPE, this.serverName, this.name,
                entriesRemoved, this.archiveFilePath);
        } catch (ArchiveHelperException ex) {
            LOGGER.severe("WLSDPLY-30030", ex, this.serverName, this.name, this.archiveFilePath,
                ex.getLocalizedMessage());
            response = new CommandResponse(ex.getExitCode(), "WLSDPLY-30030", this.serverName,
                this.name, this.archiveFilePath, ex.getLocalizedMessage());
        } catch (WLSDeployArchiveIOException | IllegalArgumentException ex) {
            LOGGER.severe("WLSDPLY-30031", ex, this.serverName, this.name, this.force,
                this.archiveFilePath, ex.getLocalizedMessage());
            response = new CommandResponse(ExitCode.ERROR, "WLSDPLY-30031", this.serverName, this.name,
                this.force, this.archiveFilePath, ex.getLocalizedMessage());
        }

        LOGGER.exiting(CLASS, METHOD, response);
        return response;
    }
}
