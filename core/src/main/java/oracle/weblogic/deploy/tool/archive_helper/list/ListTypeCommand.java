package oracle.weblogic.deploy.tool.archive_helper.list;

import java.util.List;
import java.util.concurrent.Callable;

import oracle.weblogic.deploy.logging.PlatformLogger;
import oracle.weblogic.deploy.logging.WLSDeployLogFactory;
import oracle.weblogic.deploy.tool.archive_helper.ArchiveHelperException;
import oracle.weblogic.deploy.tool.archive_helper.CommandResponse;
import oracle.weblogic.deploy.util.ExitCode;
import oracle.weblogic.deploy.util.StringUtils;
import oracle.weblogic.deploy.util.WLSDeployArchive;
import oracle.weblogic.deploy.util.WLSDeployArchiveIOException;

import static oracle.weblogic.deploy.util.WLSDeployArchive.ArchiveEntryType.APPLICATIONS;

public abstract class ListTypeCommand extends ListOptions implements Callable<CommandResponse> {
    private static final String CLASS = ListTypeCommand.class.getName();
    private static final PlatformLogger LOGGER =
        WLSDeployLogFactory.getLogger("wlsdeploy.tool.archive-helper");

    public CommandResponse listApplications() {
        final String METHOD = "listApplications";
        LOGGER.entering(CLASS, METHOD);

        CommandResponse response;
        try {
            initializeOptions();

            List<String> archiveEntries;
            if (StringUtils.isEmpty(this.name)) {
                archiveEntries = this.archive.getArchiveEntries(APPLICATIONS);
            } else {
                archiveEntries = this.archive.getArchiveEntries(APPLICATIONS, this.name);
            }
            response = new CommandResponse(ExitCode.OK);
            response.addMessages(archiveEntries);
        } catch (ArchiveHelperException ex) {
            LOGGER.severe(ex.getLocalizedMessage(), ex);
            response = new CommandResponse(ex.getExitCode(), ex.getLocalizedMessage());
        } catch (WLSDeployArchiveIOException ex) {
            LOGGER.severe("WLSDPLY-30003", ex, ex.getLocalizedMessage());
            response = new CommandResponse(ExitCode.ERROR, "WLSDPLY-30003", ex.getLocalizedMessage());
        }

        LOGGER.exiting(CLASS, METHOD, response);
        return response;
    }
}
