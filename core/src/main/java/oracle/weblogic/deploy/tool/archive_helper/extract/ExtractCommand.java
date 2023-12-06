/*
 * Copyright (c) 2023, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.tool.archive_helper.extract;

import picocli.CommandLine.Command;
import picocli.CommandLine.Option;

@Command(
    name = "extract",
    header = "Extract items from the archive file.",
    description = "%nCommand-line options:",
    commandListHeading = "%nSubcommands:%n",
    subcommands = {
        ExtractAllCommand.class,
        ExtractApplicationCommand.class,
        ExtractApplicationPlanCommand.class,
        ExtractClasspathLibraryCommand.class,
        ExtractCoherenceConfigCommand.class,
        ExtractCoherencePersistenceDirCommand.class,
        ExtractCustomCommand.class,
        ExtractDatabaseWalletCommand.class,
        ExtractDomainBinScriptCommand.class,
        ExtractDomainLibraryCommand.class,
        ExtractFileStoreCommand.class,
        ExtractJMSForeignServerCommand.class,
        ExtractMIMEMappingCommand.class,
        ExtractNodeManagerKeystoreCommand.class,
        ExtractOPSSWalletCommand.class,
        ExtractRCUWalletCommand.class,
        ExtractSaml2InitializationDataCommand.class,
        ExtractScriptCommand.class,
        ExtractServerKeystoreCommand.class,
        ExtractSharedLibraryCommand.class,
        ExtractSharedLibraryPlanCommand.class,
        ExtractStructuredApplicationCommand.class,
        ExtractWebLogicRemoteConsoleExtensionCommand.class
    }
)
public class ExtractCommand {
    @Option(
        names = { "-help" },
        description = "Get help for the archiveHelper extract command",
        usageHelp = true
    )
    private boolean helpRequested = false;
}
