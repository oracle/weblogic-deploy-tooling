/*
 * Copyright (c) 2024, Oracle and/or its affiliates.
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
import static oracle.weblogic.deploy.util.WLSDeployArchive.ArchiveEntryType.XACML_ROLE;

@Command(
    name = "xacmlRole",
    header = "List XACML Role Mapper role definition entries in the archive file.",
    description = "%nCommand-line options:"
)
public class ListXACMLRoleCommand extends ListTypeCommandBase {
    private static final String CLASS = ListXACMLRoleCommand.class.getName();
    private static final PlatformLogger LOGGER = WLSDeployLogFactory.getLogger(LOGGER_NAME);

    @Option(
        names = { "-name" },
        paramLabel = "<name>",
        description = "Name of the XACML Role Mapper role definition entry to list"
    )
    private String name;

    @Override
    public CommandResponse call() throws Exception {
        final String METHOD = "call";
        LOGGER.entering(CLASS, METHOD);

        CommandResponse response = listType(XACML_ROLE, "XACML Role Mapper role definition", name);

        LOGGER.exiting(CLASS, METHOD, response);
        return response;
    }
}
