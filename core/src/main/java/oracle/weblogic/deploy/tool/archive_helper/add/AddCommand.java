/*
 * Copyright (c) 2023, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.tool.archive_helper.add;

import picocli.CommandLine.Command;
import picocli.CommandLine.Option;

@Command(
    name = "add",
    description = "%nAdd items to the archive file:",
    commandListHeading = "%nSubcommands:%n%n",
    subcommands = {
        AddApplicationCommand.class,
        AddApplicationPlanCommand.class,
        AddClasspathLibraryCommand.class,
        AddCoherenceConfigCommand.class,
        AddCoherencePersistenceDirCommand.class,
        AddCustomCommand.class,
        AddDatabaseWalletCommand.class,
        AddDomainBinScriptCommand.class,
        AddDomainLibraryCommand.class,
        AddFileStoreCommand.class,
        AddJMSForeignServerCommand.class,
        AddMIMEMappingCommand.class,
        AddNodeManagerKeystoreCommand.class,
        AddOPSSWalletCommand.class,
        AddRCUWalletCommand.class,
        AddScriptCommand.class,
        AddServerKeystoreCommand.class,
        AddSharedLibraryCommand.class,
        AddSharedLibraryPlanCommand.class,
        AddStructuredApplicationCommand.class,
    },
    sortOptions = false
)
public class AddCommand {
    @Option(
        names = { "-help" },
        description = "Get help for the archiveHelper add command",
        usageHelp = true
    )
    private boolean helpRequested = false;
}
