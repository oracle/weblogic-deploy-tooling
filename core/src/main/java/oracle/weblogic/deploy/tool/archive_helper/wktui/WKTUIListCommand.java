/*
 * Copyright (c) 2025, 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.tool.archive_helper.wktui;

import java.io.IOException;
import java.util.List;
import java.util.concurrent.Callable;

import oracle.weblogic.deploy.logging.PlatformLogger;
import oracle.weblogic.deploy.logging.WLSDeployLogFactory;
import oracle.weblogic.deploy.tool.archive_helper.ArchiveHelperException;
import oracle.weblogic.deploy.tool.archive_helper.CommandResponse;
import oracle.weblogic.deploy.util.ExitCode;
import oracle.weblogic.deploy.util.WLSDeployArchiveIOException;

import picocli.CommandLine.Command;

import static oracle.weblogic.deploy.tool.ArchiveHelper.LOGGER_NAME;

@Command(
        name = "list",
        header = "Write all entries in the archive file to the JSON output file.",
        description = "%nCommand-line options:"
)
public class WKTUIListCommand extends WKTUICommandBase implements Callable<CommandResponse> {
    private static final String CLASS = WKTUIListCommand.class.getName();
    private static final PlatformLogger LOGGER = WLSDeployLogFactory.getLogger(LOGGER_NAME);

    @Override
    public CommandResponse call() throws Exception {
        final String METHOD = "call";
        LOGGER.entering(CLASS, METHOD);

        CommandResponse response;
        try {
            super.initializeOptions(true);

            List<String> files = this.archive.getArchiveEntries();
            List<String> messages = writeOutputJsonFile(files);
            response = new CommandResponse(ExitCode.OK);
            response.addMessages(messages);
        } catch (ArchiveHelperException ex) {
            LOGGER.severe(ex.getLocalizedMessage(), ex);
            response = new CommandResponse(ex.getExitCode(), ex.getLocalizedMessage());
        } catch (WLSDeployArchiveIOException ex) {
            LOGGER.severe("WLSDPLY-30073", ex, this.archiveFilePath, ex.getLocalizedMessage());
            response = new CommandResponse(ExitCode.ERROR, "WLSDPLY-30073", this.archiveFilePath,
                    ex.getLocalizedMessage());
        }
        catch (IOException ex) {
            LOGGER.severe("WLSDPLY-30071", ex, this.archiveFilePath,
                    this.outputJsonFilePath, ex.getLocalizedMessage());
            response = new CommandResponse(ExitCode.ERROR, "WLSDPLY-30071", this.archiveFilePath,
                    this.outputJsonFilePath, ex.getLocalizedMessage());
        }
        LOGGER.exiting(CLASS, METHOD, response);
        return response;
    }
}
