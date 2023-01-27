/*
 * Copyright (c) 2023, Oracle and/or its affiliates.
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

import static oracle.weblogic.deploy.tool.ArchiveHelper.LOGGER_NAME;

@Command(
    name = "coherencePersistenceDir",
    header = "Add a Coherence persistence directory to the archive file.",
    description = "%nCommand-line options:",
    sortOptions = false
)
public class AddCoherencePersistenceDirCommand extends AddTypeCommandBase {
    private static final String CLASS = AddCoherencePersistenceDirCommand.class.getName();
    private static final PlatformLogger LOGGER = WLSDeployLogFactory.getLogger(LOGGER_NAME);

    @Option(
        names = {"-cluster_name"},
        paramLabel = "<cluster-name>",
        description = "Coherence cluster name to use",
        required = true
    )
    protected String clusterName;

    @Option(
        names = {"-type"},
        paramLabel = "<directory-type>",
        description = "The Coherence persistence directory type to add",
        required = true
    )
    private String directoryType;

    @Option(
        names = { "-help" },
        description = "Get help for the archiveHelper add coherencePersistenceDir subcommand",
        usageHelp = true
    )
    private boolean helpRequested = false;

    @Override
    public CommandResponse call() throws Exception {
        final String METHOD = "call";
        LOGGER.entering(CLASS, METHOD);

        CommandResponse response;
        try {
            initializeOptions();

            String resultName;
            if (this.overwrite) {
                resultName = this.archive.replaceCoherencePersistenceDirectory(this.clusterName, this.directoryType);
            } else {
                resultName = this.archive.addCoherencePersistenceDirectory(this.clusterName, this.directoryType);
            }
            response = new CommandResponse(ExitCode.OK, resultName);
        } catch (ArchiveHelperException ex) {
            LOGGER.severe("WLSDPLY-30016", ex, this.directoryType, this.clusterName,
                this.archiveFilePath, ex.getLocalizedMessage());
            response = new CommandResponse(ex.getExitCode(), "WLSDPLY-30016", this.directoryType,
                this.clusterName, this.archiveFilePath, ex.getLocalizedMessage());
        } catch (WLSDeployArchiveIOException | IllegalArgumentException ex) {
            LOGGER.severe("WLSDPLY-30017", ex, this.directoryType, this.clusterName,
                this.overwrite, this.archiveFilePath, ex.getLocalizedMessage());
            response = new CommandResponse(ExitCode.ERROR, "WLSDPLY-30017", this.directoryType,
                this.clusterName, this.overwrite, this.archiveFilePath, ex.getLocalizedMessage());
        }

        LOGGER.exiting(CLASS, METHOD, response);
        return response;
    }
}
