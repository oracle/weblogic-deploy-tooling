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
    name = "coherenceConfig",
    header = "Add a Coherence config file to the archive file.",
    description = "%nCommand-line options:",
    sortOptions = false
)
public class AddCoherenceConfigCommand extends AddTypeCommandBase {
    private static final String CLASS = AddCoherenceConfigCommand.class.getName();
    private static final PlatformLogger LOGGER = WLSDeployLogFactory.getLogger(LOGGER_NAME);

    @Option(
        names = {"-source"},
        paramLabel = "<path>",
        description = "File system path to the Coherence config to add",
        required = true
    )
    private String sourcePath;

    @Option(
        names = {"-cluster_name"},
        paramLabel = "<cluster-name>",
        description = "Coherence cluster name to use",
        required = true
    )
    protected String clusterName;

    @Option(
        names = { "-help" },
        description = "Get help for the archiveHelper add coherenceConfig subcommand",
        usageHelp = true
    )
    private boolean helpRequested = false;

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
                resultName = this.archive.replaceCoherenceConfigFile(this.clusterName, sourceFile.getName(),
                    sourceFile.getPath());
            } else {
                resultName = this.archive.addCoherenceConfigFile(this.clusterName, sourceFile.getPath());
            }
            response = new CommandResponse(ExitCode.OK, resultName);
        } catch (ArchiveHelperException ex) {
            LOGGER.severe("WLSDPLY-30014", ex, this.sourcePath, this.clusterName,
                this.archiveFilePath, ex.getLocalizedMessage());
            response = new CommandResponse(ex.getExitCode(), "WLSDPLY-30014", this.sourcePath,
                this.clusterName, this.archiveFilePath, ex.getLocalizedMessage());
        } catch (WLSDeployArchiveIOException | IllegalArgumentException ex) {
            LOGGER.severe("WLSDPLY-30015", ex, this.sourcePath, this.clusterName,
                this.overwrite, this.archiveFilePath, ex.getLocalizedMessage());
            response = new CommandResponse(ExitCode.ERROR, "WLSDPLY-30015", this.sourcePath,
                this.clusterName, this.overwrite, this.archiveFilePath, ex.getLocalizedMessage());
        }

        LOGGER.exiting(CLASS, METHOD, response);
        return response;
    }
}
