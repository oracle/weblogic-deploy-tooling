/*
 * Copyright (c) 2025, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.tool.archive_helper.add;

import oracle.weblogic.deploy.logging.PlatformLogger;
import oracle.weblogic.deploy.logging.WLSDeployLogFactory;
import oracle.weblogic.deploy.tool.archive_helper.ArchiveHelperException;
import oracle.weblogic.deploy.tool.archive_helper.CommandResponse;
import oracle.weblogic.deploy.util.ExitCode;
import oracle.weblogic.deploy.util.WLSDeployArchiveIOException;
import picocli.CommandLine.Command;
import picocli.CommandLine.Option;

import java.io.File;

import static oracle.weblogic.deploy.tool.ArchiveHelper.LOGGER_NAME;

@Command(
    name = "serverTemplateKeystore",
    header = "Add a server template keystore to the archive file.",
    description = "%nCommand-line options:"
)
public class AddServerTemplateKeystoreCommand extends AddTypeCommandBase {
    private static final String CLASS = AddServerTemplateKeystoreCommand.class.getName();
    private static final PlatformLogger LOGGER = WLSDeployLogFactory.getLogger(LOGGER_NAME);

    @Option(
        names = {"-source"},
        paramLabel = "<path>",
        description = "File system path to the server template keystore to add",
        required = true
    )
    private String sourcePath;

    @Option(
        names = {"-server_template_name"},
        paramLabel = "<server-template-name>",
        description = "WebLogic Server domain's server template name to use",
        required = true
    )
    private String serverTemplateName;

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
                resultName = this.archive.replaceServerTemplateKeyStoreFile(this.serverTemplateName,
                    sourceFile.getName(), sourceFile.getPath());
            } else {
                resultName = this.archive.addServerTemplateKeyStoreFile(this.serverTemplateName, sourceFile.getPath());
            }
            response = new CommandResponse(ExitCode.OK, resultName);
        } catch (ArchiveHelperException ex) {
            LOGGER.severe("WLSDPLY-30063", ex, this.sourcePath, this.serverTemplateName,
                this.archiveFilePath, ex.getLocalizedMessage());
            response = new CommandResponse(ex.getExitCode(), "WLSDPLY-30063", this.sourcePath,
                this.serverTemplateName, this.archiveFilePath, ex.getLocalizedMessage());
        } catch (WLSDeployArchiveIOException | IllegalArgumentException ex) {
            LOGGER.severe("WLSDPLY-30064", ex, this.sourcePath, this.serverTemplateName,
                this.overwrite, this.archiveFilePath, ex.getLocalizedMessage());
            response = new CommandResponse(ExitCode.ERROR, "WLSDPLY-30064", this.sourcePath,
                this.serverTemplateName, this.overwrite, this.archiveFilePath, ex.getLocalizedMessage());
        }

        LOGGER.exiting(CLASS, METHOD, response);
        return response;
    }
}
