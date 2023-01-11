package oracle.weblogic.deploy.tool.archive_helper.list;

import oracle.weblogic.deploy.logging.PlatformLogger;
import oracle.weblogic.deploy.logging.WLSDeployLogFactory;
import oracle.weblogic.deploy.tool.archive_helper.ArchiveHelperException;
import oracle.weblogic.deploy.tool.archive_helper.CommonOptions;
import picocli.CommandLine.Option;

public class ListOptions extends CommonOptions {
    private static final String CLASS = ListOptions.class.getName();
    private static final PlatformLogger LOGGER = WLSDeployLogFactory.getLogger("wlsdeploy.tool.archive-helper");

    @Option(
        names = { "-name" },
        paramLabel = "<name>",
        description = "Name of the object of the specified type to list."
    )
    String name;

    protected void initializeOptions() throws ArchiveHelperException {
        super.initializeOptions();
    }
}
