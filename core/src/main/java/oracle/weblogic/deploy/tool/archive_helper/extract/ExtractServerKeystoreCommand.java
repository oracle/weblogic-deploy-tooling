/*
 * Copyright (c) 2023, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.tool.archive_helper.extract;

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
    name = "serverKeystore",
    header = "Extract server keystore from the archive file.",
    description = "%nCommand-line options:"
)
public class ExtractServerKeystoreCommand extends ExtractTypeCommandBase {
    private static final String CLASS = ExtractServerKeystoreCommand.class.getName();
    private static final PlatformLogger LOGGER = WLSDeployLogFactory.getLogger(LOGGER_NAME);
    private static final String TYPE = "server keystore";
    private static final String ERROR_KEY = "WLSDPLY-30053";

    @Option(
        names = {"-server_name"},
        description = "Name of the server used to segregate the keystores in the archive file",
        required = true
    )
    private String serverName;

    @Option(
        names = {"-name"},
        description = "Name of the server keystore to be extracted from the archive file",
        required = true
    )
    private String name;


    @Override
    public CommandResponse call() throws Exception {
        final String METHOD = "call";
        LOGGER.entering(CLASS, METHOD);

        CommandResponse response;
        try {
            initializeOptions();

            this.archive.extractServerKeystore(this.serverName, this.name, this.targetDirectory);
            response = new CommandResponse(ExitCode.OK, "WLSDPLY-30052", TYPE, this.name, this.serverName,
                this.archiveFilePath, this.targetDirectory.getPath());
        } catch (ArchiveHelperException ex) {
            LOGGER.severe(ERROR_KEY, ex, TYPE, this.name, this.serverName, this.archiveFilePath,
                this.targetDirectory.getPath(), ex.getLocalizedMessage());
            response = new CommandResponse(ex.getExitCode(), ERROR_KEY, TYPE, this.name, this.serverName,
                this.archiveFilePath, this.targetDirectory.getPath(), ex.getLocalizedMessage());
        } catch (WLSDeployArchiveIOException | IllegalArgumentException ex) {
            LOGGER.severe(ERROR_KEY, ex, TYPE, this.name, this.serverName, this.archiveFilePath,
                this.targetDirectory.getPath(), ex.getLocalizedMessage());
            response = new CommandResponse(ExitCode.ERROR, ERROR_KEY, TYPE, this.name, this.serverName,
                this.archiveFilePath, this.targetDirectory.getPath(), ex.getLocalizedMessage());
        }

        LOGGER.exiting(CLASS, METHOD, response);
        return response;
    }
}
