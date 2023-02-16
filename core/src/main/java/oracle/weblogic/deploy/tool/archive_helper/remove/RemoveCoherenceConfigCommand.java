/*
 * Copyright (c) 2023, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.tool.archive_helper.remove;

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
    header = "Remove Coherence config file from the archive file.",
    description = "%nCommand-line options:"
)
public class RemoveCoherenceConfigCommand extends RemoveTypeCommandBase {
    private static final String CLASS = RemoveCoherenceConfigCommand.class.getName();
    private static final PlatformLogger LOGGER = WLSDeployLogFactory.getLogger(LOGGER_NAME);
    private static final String TYPE = "Coherence config file";

    @Option(
        names = {"-cluster_name"},
        description = "Name of the Coherence cluster used to segregate the config files in the archive file",
        required = true
    )
    private String clusterName;

    @Option(
        names = {"-name"},
        description = "Name of the Coherence config file to be removed from the archive file",
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

            int entriesRemoved;
            if (this.force) {
                entriesRemoved = this.archive.removeCoherenceConfigFile(this.clusterName, this.name, true);
            } else {
                entriesRemoved = this.archive.removeCoherenceConfigFile(this.clusterName, this.name);
            }
            response = new CommandResponse(ExitCode.OK, "WLSDPLY-30032", TYPE, this.clusterName, this.name,
                entriesRemoved, this.archiveFilePath);
        } catch (ArchiveHelperException ex) {
            LOGGER.severe("WLSDPLY-30033", ex, this.clusterName, this.name, this.archiveFilePath,
                ex.getLocalizedMessage());
            response = new CommandResponse(ex.getExitCode(), "WLSDPLY-30033", this.clusterName,
                this.name, this.archiveFilePath, ex.getLocalizedMessage());
        } catch (WLSDeployArchiveIOException | IllegalArgumentException ex) {
            LOGGER.severe("WLSDPLY-30034", ex, this.clusterName, this.name, this.force,
                this.archiveFilePath, ex.getLocalizedMessage());
            response = new CommandResponse(ExitCode.ERROR, "WLSDPLY-30034", this.clusterName, this.name,
                this.force, this.archiveFilePath, ex.getLocalizedMessage());
        }

        LOGGER.exiting(CLASS, METHOD, response);
        return response;
    }
}
