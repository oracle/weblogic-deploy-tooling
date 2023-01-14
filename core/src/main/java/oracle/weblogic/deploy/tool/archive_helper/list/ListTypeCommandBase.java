package oracle.weblogic.deploy.tool.archive_helper.list;

import java.util.List;
import java.util.concurrent.Callable;

import oracle.weblogic.deploy.logging.PlatformLogger;
import oracle.weblogic.deploy.logging.WLSDeployLogFactory;
import oracle.weblogic.deploy.tool.archive_helper.ArchiveHelperException;
import oracle.weblogic.deploy.tool.archive_helper.CommandResponse;
import oracle.weblogic.deploy.tool.archive_helper.CommonOptions;
import oracle.weblogic.deploy.util.ExitCode;
import oracle.weblogic.deploy.util.StringUtils;
import oracle.weblogic.deploy.util.WLSDeployArchiveIOException;
import oracle.weblogic.deploy.util.WLSDeployArchive.ArchiveEntryType;

import static oracle.weblogic.deploy.tool.ArchiveHelper.LOGGER_NAME;

public abstract class ListTypeCommandBase extends CommonOptions implements Callable<CommandResponse> {
    private static final String CLASS = ListTypeCommandBase.class.getName();
    private static final PlatformLogger LOGGER = WLSDeployLogFactory.getLogger(LOGGER_NAME);

    protected CommandResponse listType(ArchiveEntryType type, String typeName, String name) {
        final String METHOD = "listType";
        LOGGER.entering(CLASS, METHOD, type, typeName, name);

        boolean hasName = !StringUtils.isEmpty(name);
        CommandResponse response;
        try {
            initializeOptions(true);

            List<String> archiveEntries;
            if (hasName) {
                archiveEntries = this.archive.getArchiveEntries(type, name);
            } else {
                archiveEntries = this.archive.getArchiveEntries(type);
            }
            response = new CommandResponse(ExitCode.OK);
            response.addMessages(archiveEntries);
        } catch (ArchiveHelperException ex) {
            LOGGER.severe(ex.getLocalizedMessage(), ex);
            response = new CommandResponse(ex.getExitCode(), ex.getLocalizedMessage());
        } catch (WLSDeployArchiveIOException ex) {
            if (hasName) {
                LOGGER.severe("WLSDPLY-30005", ex, typeName, name, archiveFilePath, ex.getLocalizedMessage());
                response = new CommandResponse(ExitCode.ERROR, "WLSDPLY-30005", type, name,
                    this.archiveFilePath, ex.getLocalizedMessage());
            } else {
                LOGGER.severe("WLSDPLY-30006", ex, typeName, this.archiveFilePath, ex.getLocalizedMessage());
                response = new CommandResponse(ExitCode.ERROR, "WLSDPLY-30006", type, this.archiveFilePath,
                    ex.getLocalizedMessage());
            }
        }

        LOGGER.exiting(CLASS, METHOD, response);
        return response;
    }
}
