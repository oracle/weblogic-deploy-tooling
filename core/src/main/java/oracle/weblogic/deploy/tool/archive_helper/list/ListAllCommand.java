/*
 * Copyright (c) 2023, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.tool.archive_helper.list;

import java.util.List;
import java.util.concurrent.Callable;

import oracle.weblogic.deploy.logging.PlatformLogger;
import oracle.weblogic.deploy.logging.WLSDeployLogFactory;
import oracle.weblogic.deploy.tool.archive_helper.ArchiveHelperException;
import oracle.weblogic.deploy.tool.archive_helper.CommandResponse;
import oracle.weblogic.deploy.tool.archive_helper.CommonOptions;
import oracle.weblogic.deploy.util.ExitCode;
import oracle.weblogic.deploy.util.WLSDeployArchiveIOException;

import picocli.CommandLine.Command;
import picocli.CommandLine.Option;

import static oracle.weblogic.deploy.tool.ArchiveHelper.LOGGER_NAME;

@Command(
    name = "all",
    description = "List all entries in the archive file",
    sortOptions = false
)
public class ListAllCommand extends CommonOptions implements Callable<CommandResponse> {
    private static final String CLASS = ListAllCommand.class.getName();
    private static final PlatformLogger LOGGER = WLSDeployLogFactory.getLogger(LOGGER_NAME);

    @Option(
        names = { "-help" },
        description = "Get help for the archiveHelper list all subcommand",
        usageHelp = true
    )
    private boolean helpRequested = false;

    @Override
    public CommandResponse call() throws Exception {
        final String METHOD = "call";
        LOGGER.entering(CLASS, METHOD);

        CommandResponse response;
        try {
            super.initializeOptions(true);

            List<String> archiveEntries = this.archive.getArchiveEntries();
            response = new CommandResponse(ExitCode.OK);
            response.addMessages(archiveEntries);
        } catch (ArchiveHelperException ex) {
            LOGGER.severe(ex.getLocalizedMessage(), ex);
            response = new CommandResponse(ex.getExitCode(), ex.getLocalizedMessage());
        } catch (WLSDeployArchiveIOException ex) {
            LOGGER.severe("WLSDPLY-30004", ex, ex.getLocalizedMessage());
            response = new CommandResponse(ExitCode.ERROR, "WLSDPLY-30004", this.archiveFilePath,
                ex.getLocalizedMessage());
        }
        return response;
    }
}
