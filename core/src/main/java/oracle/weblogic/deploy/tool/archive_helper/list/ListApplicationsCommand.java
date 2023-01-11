/*
 * Copyright (c) 2023, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.tool.archive_helper.list;

import oracle.weblogic.deploy.logging.PlatformLogger;
import oracle.weblogic.deploy.logging.WLSDeployLogFactory;
import oracle.weblogic.deploy.tool.archive_helper.CommandResponse;
import oracle.weblogic.deploy.tool.archive_helper.HelpVersionProvider;
import picocli.CommandLine.Command;

@Command(
    name = "applications",
    description = "List application entries in the archive file",
    mixinStandardHelpOptions = true,
    versionProvider = HelpVersionProvider.class,
    sortOptions = false
)
public class ListApplicationsCommand extends ListTypeCommand {
    private static final String CLASS = ListApplicationsCommand.class.getName();
    private static final PlatformLogger LOGGER =
        WLSDeployLogFactory.getLogger("wlsdeploy.tool.archive-helper");

    @Override
    public CommandResponse call() throws Exception {
        final String METHOD = "call";
        LOGGER.entering(CLASS, METHOD);

        CommandResponse response = listApplications();

        LOGGER.exiting(CLASS, METHOD, response);
        return response;
    }
}
