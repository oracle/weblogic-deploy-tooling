/*
 * Copyright (c) 2025, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.tool.archive_helper.extract;

import oracle.weblogic.deploy.logging.PlatformLogger;
import oracle.weblogic.deploy.logging.WLSDeployLogFactory;
import oracle.weblogic.deploy.tool.archive_helper.CommandResponse;
import picocli.CommandLine.Command;
import picocli.CommandLine.Option;

import static oracle.weblogic.deploy.tool.ArchiveHelper.LOGGER_NAME;
import static oracle.weblogic.deploy.util.WLSDeployArchive.ArchiveEntryType.PLUGIN_DEPLOYMENT;

@Command(
    name = "pluginDeployment",
    header = "Extract plugin deployment from the archive file.",
    description = "%nCommand-line options:"
)
public class ExtractPluginDeploymentCommand extends ExtractTypeCommandBase {
    private static final String CLASS = ExtractPluginDeploymentCommand.class.getName();
    private static final PlatformLogger LOGGER = WLSDeployLogFactory.getLogger(LOGGER_NAME);
    private static final String TYPE = "plugin deployment";

    @Option(
        names = {"-name"},
        description = "Name of the plugin deployment to be extracted from the archive file",
        required = true
    )
    private String name;


    @Override
    public CommandResponse call() throws Exception {
        final String METHOD = "call";
        LOGGER.entering(CLASS, METHOD);

        CommandResponse response = extractType(PLUGIN_DEPLOYMENT, TYPE, name);

        LOGGER.exiting(CLASS, METHOD, response);
        return response;
    }
}
