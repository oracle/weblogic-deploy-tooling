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
    name = "rcuWallet",
    header = "Remove RCU wallet from the archive file.",
    description = "%nCommand-line options:",
    sortOptions = false
)
public class RemoveRCUWalletCommand extends RemoveTypeCommandBase {
    private static final String CLASS = RemoveRCUWalletCommand.class.getName();
    private static final PlatformLogger LOGGER = WLSDeployLogFactory.getLogger(LOGGER_NAME);

    @Option(
        names = { "-help" },
        description = "Get help for the archiveHelper remove rcuWallet subcommand",
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
                entriesRemoved = this.archive.removeRCUDatabaseWallet(true);
            } else {
                entriesRemoved = this.archive.removeRCUDatabaseWallet();
            }
            response = new CommandResponse(ExitCode.OK, "WLSDPLY-30060", entriesRemoved, this.archiveFilePath);
        } catch (ArchiveHelperException ex) {
            LOGGER.severe("WLSDPLY-30061", ex, this.archiveFilePath, ex.getLocalizedMessage());
            response = new CommandResponse(ex.getExitCode(), "WLSDPLY-30061",
               this.archiveFilePath, ex.getLocalizedMessage());
        } catch (WLSDeployArchiveIOException | IllegalArgumentException ex) {
            LOGGER.severe("WLSDPLY-30062", ex, this.force, this.archiveFilePath, ex.getLocalizedMessage());
            response = new CommandResponse(ExitCode.ERROR, "WLSDPLY-30062",
                this.force, this.archiveFilePath, ex.getLocalizedMessage());
        }

        LOGGER.exiting(CLASS, METHOD, response);
        return response;
    }
}
