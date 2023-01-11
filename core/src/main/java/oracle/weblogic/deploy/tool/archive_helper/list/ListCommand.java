/*
 * Copyright (c) 2023, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.tool.archive_helper.list;

import oracle.weblogic.deploy.tool.archive_helper.HelpVersionProvider;

import picocli.CommandLine.Command;

@Command(
    name = "list",
    description = "List contents of archive file",
    versionProvider = HelpVersionProvider.class,
    commandListHeading = "%nCommands:%n%n",
    subcommands = {
        ListAllCommand.class,
        ListApplicationsCommand.class
    },
    sortOptions = false
)
public class ListCommand {
}
