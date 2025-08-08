/*
 * Copyright (c) 2025, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.tool.archive_helper.list;

import oracle.weblogic.deploy.logging.PlatformLogger;
import oracle.weblogic.deploy.logging.WLSDeployLogFactory;
import oracle.weblogic.deploy.tool.archive_helper.CommandResponse;
import picocli.CommandLine.Command;
import picocli.CommandLine.Option;

import static oracle.weblogic.deploy.tool.ArchiveHelper.LOGGER_NAME;
import static oracle.weblogic.deploy.util.WLSDeployArchive.ArchiveEntryType.PLUGIN_DEPLOYMENT;

@Command(
    name = "pluginDeployment",
    header = "List plugin deployment entries in the archive file.",
    description = "%nCommand-line options:"
)
public class ListPluginDeploymentCommand extends ListTypeCommandBase {
    private static final String CLASS = ListPluginDeploymentCommand.class.getName();
    private static final PlatformLogger LOGGER = WLSDeployLogFactory.getLogger(LOGGER_NAME);

    @Option(
        names = { "-name" },
        paramLabel = "<name>",
        description = "Name of the plugin deployment to list"
    )
    private String name;

    @Override
    public CommandResponse call() throws Exception {
        final String METHOD = "call";
        LOGGER.entering(CLASS, METHOD);

        CommandResponse response = listType(PLUGIN_DEPLOYMENT, "plugin deployment", name);

        LOGGER.exiting(CLASS, METHOD, response);
        return response;
    }
}
