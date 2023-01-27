/*
 * Copyright (c) 2023, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.tool.archive_helper.list;

import oracle.weblogic.deploy.logging.PlatformLogger;
import oracle.weblogic.deploy.logging.WLSDeployLogFactory;
import oracle.weblogic.deploy.tool.archive_helper.CommandResponse;

import picocli.CommandLine.Command;
import picocli.CommandLine.Option;

import static oracle.weblogic.deploy.tool.ArchiveHelper.LOGGER_NAME;
import static oracle.weblogic.deploy.util.WLSDeployArchive.ArchiveEntryType.APPLICATION;

@Command(
    name = "application",
    header = "List application entries in the archive file.",
    description = "%nCommand-line options:",
    footer = "%nNote: If using an Application Installation Directory, " +
        "please see the archiveHelper list structuredApplication command.%n",
    sortOptions = false
)
public class ListApplicationCommand extends ListTypeCommandBase {
    private static final String CLASS = ListApplicationCommand.class.getName();
    private static final PlatformLogger LOGGER = WLSDeployLogFactory.getLogger(LOGGER_NAME);

    @Option(
        names = { "-name" },
        paramLabel = "<name>",
        description = "Name of the application to list"
    )
    private String name;

    @Override
    public CommandResponse call() throws Exception {
        final String METHOD = "call";
        LOGGER.entering(CLASS, METHOD);

        CommandResponse response = listType(APPLICATION, "application", name);

        LOGGER.exiting(CLASS, METHOD, response);
        return response;
    }
}
