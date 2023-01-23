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
import static oracle.weblogic.deploy.util.WLSDeployArchive.ArchiveEntryType.DOMAIN_LIB;

@Command(
    name = "domainLibrary",
    header = "List domain library entries in the archive file.",
    description = "%nCommand-line options:",
    sortOptions = false
)
public class ListDomainLibraryCommand extends ListTypeCommandBase {
    private static final String CLASS = ListDomainLibraryCommand.class.getName();
    private static final PlatformLogger LOGGER = WLSDeployLogFactory.getLogger(LOGGER_NAME);

    @Option(
        names = { "-name" },
        paramLabel = "<name>",
        description = "Name of the domain library to list"
    )
    private String name;

    @Option(
        names = { "-help" },
        description = "Get help for the archiveHelper list domainLibrary subcommand",
        usageHelp = true
    )
    private boolean helpRequested = false;

    @Override
    public CommandResponse call() throws Exception {
        final String METHOD = "call";
        LOGGER.entering(CLASS, METHOD);

        CommandResponse response = listType(DOMAIN_LIB, "domain library", name);

        LOGGER.exiting(CLASS, METHOD, response);
        return response;
    }
}
