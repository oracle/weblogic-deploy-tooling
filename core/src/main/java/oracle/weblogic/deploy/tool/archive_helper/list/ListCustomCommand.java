/*
 * Copyright (c) 2023, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.tool.archive_helper.list;

import java.util.List;

import oracle.weblogic.deploy.logging.PlatformLogger;
import oracle.weblogic.deploy.logging.WLSDeployLogFactory;
import oracle.weblogic.deploy.tool.archive_helper.ArchiveHelperException;
import oracle.weblogic.deploy.tool.archive_helper.CommandResponse;
import oracle.weblogic.deploy.util.ExitCode;
import oracle.weblogic.deploy.util.StringUtils;
import oracle.weblogic.deploy.util.WLSDeployArchiveIOException;
import picocli.CommandLine.Command;
import picocli.CommandLine.Option;

import static oracle.weblogic.deploy.tool.ArchiveHelper.LOGGER_NAME;
import static oracle.weblogic.deploy.util.WLSDeployArchive.ArchiveEntryType.CUSTOM;

@Command(
    name = "custom",
    header = "List custom directory entries in the archive file.",
    description = "%nCommand-line options:"
)
public class ListCustomCommand extends ListTypeCommandBase {
    private static final String CLASS = ListCustomCommand.class.getName();
    private static final PlatformLogger LOGGER = WLSDeployLogFactory.getLogger(LOGGER_NAME);

    @Option(
        names = { "-name" },
        paramLabel = "<name>",
        description = "Name of the custom directory entry to list"
    )
    private String name;

    @Option(
        names = {"-use_non_replicable_location"},
        description = "List the contents of the wlsdeploy/custom location instead of the default config/wlsdeploy/custom location"
    )
    private boolean useNonReplicableLocation;

    @Override
    public CommandResponse call() throws Exception {
        final String METHOD = "call";
        LOGGER.entering(CLASS, METHOD);

        CommandResponse response;
        boolean hasName = !StringUtils.isEmpty(this.name);
        try {
            initializeOptions(true);

            List<String> archiveEntries;
            if (hasName) {
                archiveEntries = this.archive.listCustomEntries(name, useNonReplicableLocation);
            } else {
                archiveEntries = this.archive.listCustomEntries(useNonReplicableLocation);
            }
            response = new CommandResponse(ExitCode.OK);
            response.addMessages(archiveEntries);
        } catch (ArchiveHelperException ex) {
            LOGGER.severe(ex.getLocalizedMessage(), ex);
            response = new CommandResponse(ex.getExitCode(), ex.getLocalizedMessage());
        } catch (WLSDeployArchiveIOException | IllegalArgumentException ex) {
            if (hasName) {
                LOGGER.severe("WLSDPLY-30005", ex, CUSTOM, name, archiveFilePath, ex.getLocalizedMessage());
                response = new CommandResponse(ExitCode.ERROR, "WLSDPLY-30005", CUSTOM, name,
                    this.archiveFilePath, ex.getLocalizedMessage());
            } else {
                LOGGER.severe("WLSDPLY-30006", ex, CUSTOM, this.archiveFilePath, ex.getLocalizedMessage());
                response = new CommandResponse(ExitCode.ERROR, "WLSDPLY-30006", CUSTOM, this.archiveFilePath,
                    ex.getLocalizedMessage());
            }
        }

        LOGGER.exiting(CLASS, METHOD, response);
        return response;
    }
}
