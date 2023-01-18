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
import static oracle.weblogic.deploy.util.WLSDeployArchive.ArchiveEntryType.JMS_FOREIGN_SERVER;

@Command(
    name = "jmsForeignServer",
    description = "%nList JMS foreign server binding entries in the archive file:",
    sortOptions = false
)
public class ListJMSForeignServerCommand extends ListTypeCommandBase {
    private static final String CLASS = ListJMSForeignServerCommand.class.getName();
    private static final PlatformLogger LOGGER = WLSDeployLogFactory.getLogger(LOGGER_NAME);

    @Option(
        names = { "-foreign_server_name" },
        paramLabel = "<jms-foreign-server-name>",
        description = "WebLogic JMS Foreign Server name",
        required = true
    )
    private String jmsForeignServerName;

    @Option(
        names = { "-name" },
        paramLabel = "<name>",
        description = "Name of the JMS foreign server binding to list"
    )
    private String name;

    @Option(
        names = { "-help" },
        description = "Get help for the archiveHelper list jmsForeignServer subcommand",
        usageHelp = true
    )
    private boolean helpRequested = false;

    @Override
    public CommandResponse call() throws Exception {
        final String METHOD = "call";
        LOGGER.entering(CLASS, METHOD);

        CommandResponse response = listType(JMS_FOREIGN_SERVER, "JMS foreign server binding",
            this.jmsForeignServerName, this.name);

        LOGGER.exiting(CLASS, METHOD, response);
        return response;
    }
}
