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
import static oracle.weblogic.deploy.util.WLSDeployArchive.ArchiveEntryType.COHERENCE;
@Command(
    name = "coherence",
    header = "List Coherence entries in the archive file.",
    description = "%nCommand-line options:",
    sortOptions = false
)
public class ListCoherenceCommand extends ListTypeCommandBase {
    private static final String CLASS = ListCoherenceCommand.class.getName();
    private static final PlatformLogger LOGGER = WLSDeployLogFactory.getLogger(LOGGER_NAME);

    @Option(
        names = { "-cluster_name" },
        paramLabel = "<cluster-name>",
        description = "Name of the Coherence cluster to list"
    )
    private String clusterName;

    @Override
    public CommandResponse call() throws Exception {
        final String METHOD = "call";
        LOGGER.entering(CLASS, METHOD);

        CommandResponse response = listType(COHERENCE, "Coherence cluster", this.clusterName);

        LOGGER.exiting(CLASS, METHOD, response);
        return response;
    }
}
