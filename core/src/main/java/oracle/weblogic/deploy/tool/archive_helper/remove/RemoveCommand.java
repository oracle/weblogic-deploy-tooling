/*
 * Copyright (c) 2023, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.tool.archive_helper.remove;

import picocli.CommandLine.Command;
import picocli.CommandLine.Option;

@Command(
    name = "remove",
    header = "Remove items to the archive file.",
    description = "%nCommand-line options:",
    commandListHeading = "%nSubcommands:%n",
    subcommands = {
        RemoveApplicationCommand.class,
        RemoveApplicationPlanCommand.class,
        RemoveClasspathLibraryCommand.class,
        RemoveCoherenceConfigCommand.class,
        RemoveCoherencePersistenceDirCommand.class,
        RemoveCustomCommand.class,
        RemoveDatabaseWalletCommand.class,
        RemoveDomainBinScriptCommand.class,
        RemoveDomainLibraryCommand.class,
        RemoveFileStoreCommand.class,
        RemoveJMSForeignServerCommand.class,
        RemoveMIMEMappingCommand.class,
        RemoveNodeManagerKeystoreCommand.class,
        RemoveOPSSWalletCommand.class,
        RemoveRCUWalletCommand.class,
        RemoveSaml2InitializationDataCommand.class,
        RemoveScriptCommand.class,
        RemoveServerKeystoreCommand.class,
        RemoveSharedLibraryCommand.class,
        RemoveSharedLibraryPlanCommand.class,
        RemoveStructuredApplicationCommand.class
    }
)
public class RemoveCommand {
    @Option(
        names = { "-help" },
        description = "Get help for the archiveHelper remove command",
        usageHelp = true
    )
    private boolean helpRequested = false;
}
