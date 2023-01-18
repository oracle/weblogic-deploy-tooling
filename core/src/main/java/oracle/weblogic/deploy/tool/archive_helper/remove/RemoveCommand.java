/*
 * Copyright (c) 2023, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.tool.archive_helper.remove;

import picocli.CommandLine.Command;
import picocli.CommandLine.Option;

@Command(
    name = "remove",
    description = "%nRemove items to the archive file:",
    commandListHeading = "%nSubcommands:%n%n",
    subcommands = {
    },
    sortOptions = false
)
public class RemoveCommand {
    @Option(
        names = { "-help" },
        description = "Get help for the archiveHelper remove command",
        usageHelp = true
    )
    private boolean helpRequested = false;
}
