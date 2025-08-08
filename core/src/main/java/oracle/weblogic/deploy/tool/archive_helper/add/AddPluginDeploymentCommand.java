/*
 * Copyright (c) 2025, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.tool.archive_helper.add;

import oracle.weblogic.deploy.logging.PlatformLogger;
import oracle.weblogic.deploy.logging.WLSDeployLogFactory;
import oracle.weblogic.deploy.tool.archive_helper.CommandResponse;
import picocli.CommandLine.Command;
import picocli.CommandLine.Option;

import static oracle.weblogic.deploy.tool.ArchiveHelper.LOGGER_NAME;
import static oracle.weblogic.deploy.util.WLSDeployArchive.ArchiveEntryType.PLUGIN_DEPLOYMENT;

@Command(
    name = "pluginDeployment",
    header = "Add plugin deployment to the archive file.",
    description = "%nCommand-line options:"
)
public class AddPluginDeploymentCommand extends AddTypeCommandBase {
    private static final String CLASS = AddPluginDeploymentCommand.class.getName();
    private static final PlatformLogger LOGGER = WLSDeployLogFactory.getLogger(LOGGER_NAME);
    private static final String TYPE = "plugin deployment";

    @Option(
        names = {"-source"},
        paramLabel = "<path>",
        description = "File system path to the plugin deployment to add",
        required = true
    )
    private String sourcePath;

    @Override
    public CommandResponse call() throws Exception {
        final String METHOD = "call";
        LOGGER.entering(CLASS, METHOD);

        CommandResponse response = addType(PLUGIN_DEPLOYMENT, TYPE, this.sourcePath);
        
        LOGGER.exiting(CLASS, METHOD, response);
        return response;
    }
}
