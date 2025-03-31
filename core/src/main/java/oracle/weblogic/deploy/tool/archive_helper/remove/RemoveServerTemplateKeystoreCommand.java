/*
 * Copyright (c) 2025, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.tool.archive_helper.remove;

import oracle.weblogic.deploy.logging.PlatformLogger;
import oracle.weblogic.deploy.logging.WLSDeployLogFactory;
import oracle.weblogic.deploy.tool.archive_helper.ArchiveHelperException;
import oracle.weblogic.deploy.tool.archive_helper.CommandResponse;
import oracle.weblogic.deploy.util.ExitCode;
import oracle.weblogic.deploy.util.WLSDeployArchive;
import oracle.weblogic.deploy.util.WLSDeployArchiveIOException;
import picocli.CommandLine.Command;
import picocli.CommandLine.Option;

import static oracle.weblogic.deploy.tool.ArchiveHelper.LOGGER_NAME;

@Command(
    name = "serverTemplateKeystore",
    header = "Remove server template keystore from the archive file.",
    description = "%nCommand-line options:"
)
public class RemoveServerTemplateKeystoreCommand extends RemoveTypeCommandBase {
    private static final String CLASS = RemoveServerTemplateKeystoreCommand.class.getName();
    private static final PlatformLogger LOGGER = WLSDeployLogFactory.getLogger(LOGGER_NAME);
    private static final String TYPE = "server template keystore";

    @Option(
        names = {"-server_template_name"},
        description = "Name of the server template used to segregate the keystores in the archive file",
        required = true
    )
    private String serverTemplateName;

    @Option(
        names = {"-name"},
        description = "Name of the server template keystore to be removed from the archive file",
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

            WLSDeployArchive.ArchiveEntryType archiveType = WLSDeployArchive.ArchiveEntryType.SERVER_TEMPLATE_KEYSTORE;
            int entriesRemoved;
            if (this.force) {
                entriesRemoved = this.archive.removeSegregatedFile(archiveType, this.serverTemplateName, this.name, true);
            } else {
                entriesRemoved = this.archive.removeSegregatedFile(archiveType, this.serverTemplateName, this.name);
            }
            response = new CommandResponse(ExitCode.OK, "WLSDPLY-30067", TYPE, this.serverTemplateName, this.name,
                entriesRemoved, this.archiveFilePath);
        } catch (ArchiveHelperException ex) {
            LOGGER.severe("WLSDPLY-30068", ex, this.serverTemplateName, this.name, this.archiveFilePath,
                ex.getLocalizedMessage());
            response = new CommandResponse(ex.getExitCode(), "WLSDPLY-30068", this.serverTemplateName,
                this.name, this.archiveFilePath, ex.getLocalizedMessage());
        } catch (WLSDeployArchiveIOException | IllegalArgumentException ex) {
            LOGGER.severe("WLSDPLY-30069", ex, this.serverTemplateName, this.name, this.force,
                this.archiveFilePath, ex.getLocalizedMessage());
            response = new CommandResponse(ExitCode.ERROR, "WLSDPLY-30069", this.serverTemplateName, this.name,
                this.force, this.archiveFilePath, ex.getLocalizedMessage());
        }

        LOGGER.exiting(CLASS, METHOD, response);
        return response;
    }
}
