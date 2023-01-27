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
import oracle.weblogic.deploy.util.StringUtils;
import oracle.weblogic.deploy.util.WLSDeployArchiveIOException;
import picocli.CommandLine.Command;
import picocli.CommandLine.Option;

import static oracle.weblogic.deploy.tool.ArchiveHelper.LOGGER_NAME;
import static oracle.weblogic.deploy.util.WLSDeployArchive.ZIP_SEP;

@Command(
    name = "custom",
    header = "Add custom file/directory to the archive file.",
    description = "%nCommand-line options:"
)
public class AddCustomCommand extends AddTypeCommandBase {
    private static final String CLASS = AddCustomCommand.class.getName();
    private static final PlatformLogger LOGGER = WLSDeployLogFactory.getLogger(LOGGER_NAME);
    private static final String TYPE = "custom file or directory";

    @Option(
        names = {"-source"},
        paramLabel = "<file-path>",
        description = "File system path to the custom file or directory to add",
        required = true
    )
    private String sourcePath;

    @Option(
        names = {"-path"},
        paramLabel = "<archive-path>",
        description = "Relative archive path from custom to the parent directory to use to add the file or directory, if any"
    )
    private String archivePath = null;

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
                String archiveReplacementPath = "";
                if (!StringUtils.isEmpty(archivePath)) {
                    archiveReplacementPath = this.archivePath;
                    if (!archiveReplacementPath.endsWith(ZIP_SEP)) {
                        archiveReplacementPath += ZIP_SEP;
                    }
                }
                archiveReplacementPath += sourceFile.getName();
                resultName = this.archive.replaceCustomEntry(archiveReplacementPath, sourceFile.getPath());
            } else {
                resultName = this.archive.addCustomEntry(sourceFile.getPath(), this.archivePath);
            }
            response = new CommandResponse(ExitCode.OK, resultName);
        } catch (ArchiveHelperException ex) {
            LOGGER.severe("WLSDPLY-30010", ex, TYPE, this.sourcePath,
                this.archiveFilePath, ex.getLocalizedMessage());
            response = new CommandResponse(ex.getExitCode(), "WLSDPLY-30010", TYPE,
                this.sourcePath, this.archiveFilePath, ex.getLocalizedMessage());
        } catch (WLSDeployArchiveIOException | IllegalArgumentException ex) {
            LOGGER.severe("WLSDPLY-30011", ex, TYPE, this.sourcePath,
                this.overwrite, this.archiveFilePath, ex.getLocalizedMessage());
            response = new CommandResponse(ExitCode.ERROR, "WLSDPLY-30011", TYPE,
                this.sourcePath, this.overwrite, this.archiveFilePath, ex.getLocalizedMessage());
        }

        LOGGER.exiting(CLASS, METHOD, response);
        return response;
    }
}
