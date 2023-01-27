/*
 * Copyright (c) 2023, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.tool.archive_helper.add;

import java.io.File;

import oracle.weblogic.deploy.logging.PlatformLogger;
import oracle.weblogic.deploy.logging.WLSDeployLogFactory;
import oracle.weblogic.deploy.tool.archive_helper.ArchiveHelperException;
import oracle.weblogic.deploy.tool.archive_helper.CommandResponse;
import oracle.weblogic.deploy.util.ExitCode;
import oracle.weblogic.deploy.util.WLSDeployArchiveIOException;
import picocli.CommandLine.Command;
import picocli.CommandLine.Option;

import static oracle.weblogic.deploy.tool.ArchiveHelper.LOGGER_NAME;

@Command(
    name = "databaseWallet",
    header = "Add database wallet to the archive file.",
    description = "%nCommand-line options:",
    sortOptions = false
)
public class AddDatabaseWalletCommand extends AddTypeCommandBase {
    private static final String CLASS = AddDatabaseWalletCommand.class.getName();
    private static final PlatformLogger LOGGER = WLSDeployLogFactory.getLogger(LOGGER_NAME);
    private static final String TYPE = "database wallet";

    @Option(
        names = {"-wallet_name"},
        paramLabel = "<wallet-name>",
        description = "Name used to identity this database wallet in the archive",
        required = true
    )
    private String walletName;

    @Option(
        names = {"-source"},
        paramLabel = "<path>",
        description = "File system path to the database wallet to add",
        required = true
    )
    private String sourcePath;

    @Override
    public CommandResponse call() throws Exception {
        final String METHOD = "call";
        LOGGER.entering(CLASS, METHOD);

        CommandResponse response;
        File sourceFile;
        try {
            sourceFile = initializeOptions(this.sourcePath);

            String resultName;
            if (this.overwrite) {
                resultName = this.archive.replaceDatabaseWallet(this.walletName, sourceFile.getPath());
            } else {
                resultName = this.archive.addDatabaseWallet(this.walletName, sourceFile.getPath());
            }
            response = new CommandResponse(ExitCode.OK, resultName);
        } catch (ArchiveHelperException ex) {
            LOGGER.severe("WLSDPLY-30022", ex, TYPE, this.walletName, this.sourcePath,
                this.archiveFilePath, ex.getLocalizedMessage());
            response = new CommandResponse(ex.getExitCode(), "WLSDPLY-30022", TYPE, this.walletName,
                this.sourcePath, this.archiveFilePath, ex.getLocalizedMessage());
        } catch (WLSDeployArchiveIOException | IllegalArgumentException ex) {
            LOGGER.severe("WLSDPLY-30023", ex, TYPE, this.walletName, this.sourcePath,
                this.overwrite, this.archiveFilePath, ex.getLocalizedMessage());
            response = new CommandResponse(ExitCode.ERROR, "WLSDPLY-30023", TYPE, this.walletName,
                this.sourcePath, this.overwrite, this.archiveFilePath, ex.getLocalizedMessage());
        }

        LOGGER.exiting(CLASS, METHOD, response);
        return response;
    }
}
