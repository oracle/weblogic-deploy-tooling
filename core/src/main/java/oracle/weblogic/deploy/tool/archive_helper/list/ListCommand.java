/*
 * Copyright (c) 2023, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.tool.archive_helper.list;

import picocli.CommandLine.Command;
import picocli.CommandLine.Option;

@Command(
    name = "list",
    header = "List contents of the archive file.",
    description = "%nCommand-line options:",
    commandListHeading = "%nSubcommands:%n",
    subcommands = {
        ListAllCommand.class,
        ListApplicationCommand.class,
        ListClasspathLibraryCommand.class,
        ListCoherenceCommand.class,
        ListCustomCommand.class,
        ListDatabaseWalletCommand.class,
        ListDomainBinScriptCommand.class,
        ListDomainLibraryCommand.class,
        ListFileStoreCommand.class,
        ListJMSForeignServerCommand.class,
        ListMIMEMappingCommand.class,
        ListNodeManagerKeystoreCommand.class,
        ListOPSSWalletCommand.class,
        ListRCUWalletCommand.class,
        ListSaml2InitializationDataCommand.class,
        ListScriptCommand.class,
        ListServerKeystoreCommand.class,
        ListSharedLibraryCommand.class,
        ListStructuredApplicationCommand.class,
        ListWebLogicRemoteConsoleExtensionCommand.class,
        ListXACMLPolicyCommand.class,
        ListXACMLRoleCommand.class
    }
)
public class ListCommand {
    @Option(
        names = { "-help" },
        description = "Get help for the archiveHelper list command",
        usageHelp = true
    )
    private boolean helpRequested = false;
}
