/*
 * Copyright (c) 2023, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.tool.archive_helper;

import java.io.File;
import java.util.List;

import oracle.weblogic.deploy.logging.PlatformLogger;
import oracle.weblogic.deploy.logging.WLSDeployLogFactory;
import oracle.weblogic.deploy.util.ExitCode;
import oracle.weblogic.deploy.util.FileUtils;
import oracle.weblogic.deploy.util.StringUtils;
import oracle.weblogic.deploy.util.WLSDeployArchive;
import picocli.CommandLine;
import picocli.CommandLine.Option;
import picocli.CommandLine.Spec;
import picocli.CommandLine.Unmatched;

public abstract class CommonOptions {
    private static final String CLASS = CommonOptions.class.getName();
    private static final PlatformLogger LOGGER = WLSDeployLogFactory.getLogger("wlsdeploy.tool.archive-helper");

    @Unmatched
    List<String> unmatchedOptions;

    @Spec
    CommandLine.Model.CommandSpec spec;

    @Option(
        names = { "-archive_file" },
        paramLabel = "<archive_file>",
        required = true,
        description = "Path to the archive file to use."
    )
    protected String archiveFilePath;

    protected WLSDeployArchive archive;

    protected String getArchiveFilePath() {
        return archiveFilePath;
    }

    protected void initializeOptions() throws ArchiveHelperException {
        this.archive = createArchive();
    }

    private WLSDeployArchive createArchive() throws ArchiveHelperException {
        final String METHOD = "createArchive";
        LOGGER.entering(CLASS, METHOD);

        String fullArchiveFileName = FileUtils.getCanonicalPath(getArchiveFilePath());
        if (StringUtils.isEmpty(fullArchiveFileName)) {
            ArchiveHelperException ex = new ArchiveHelperException(ExitCode.USAGE_ERROR, "WLSDPLY-30000");
            LOGGER.throwing(CLASS, METHOD, ex);
            throw ex;
        }

        File fullArchiveFile = new File(fullArchiveFileName);
        if (!fullArchiveFile.exists()) {
            File fullArchiveParentDir = fullArchiveFile.getParentFile();
            if (!fullArchiveParentDir.exists() && !fullArchiveParentDir.mkdirs()) {
                ArchiveHelperException ex = new ArchiveHelperException(ExitCode.ARG_VALIDATION_ERROR, "WLSDPLY-30001",
                    fullArchiveParentDir.getAbsolutePath());
                LOGGER.throwing(CLASS, METHOD, ex);
                throw ex;
            }
        } else if (!fullArchiveFile.isFile()) {
            ArchiveHelperException ex = new ArchiveHelperException(ExitCode.ARG_VALIDATION_ERROR, "WLSDPLY-30002",
                fullArchiveFile.getAbsolutePath());
            LOGGER.throwing(CLASS, METHOD, ex);
            throw ex;
        }

        return new WLSDeployArchive(fullArchiveFileName);
    }
}
