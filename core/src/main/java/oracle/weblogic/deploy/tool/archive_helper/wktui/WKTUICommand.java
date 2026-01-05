/*
 * Copyright (c) 2025, 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.tool.archive_helper.wktui;

import picocli.CommandLine;
import picocli.CommandLine.Command;

@Command(
    name = "wktui",
    header = "Manipulate the contents of the archive file for WKTUI.",
    description = "%nCommand-line options:",
    commandListHeading = "%nSubcommands:%n",
    hidden = true,
    subcommands = {
        WKTUIListCommand.class,
        WKTUIUpdateCommand.class
    }
)
public class WKTUICommand {
    @CommandLine.Option(
        names = { "-help" },
        description = "Get help for the private archiveHelper wktui command",
        usageHelp = true
    )
    private boolean helpRequested = false;
}
