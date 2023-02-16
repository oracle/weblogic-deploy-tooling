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
import picocli.CommandLine.Option;
import picocli.CommandLine.Unmatched;

import static oracle.weblogic.deploy.tool.ArchiveHelper.LOGGER_NAME;

public abstract class CommonOptions {
    private static final String CLASS = CommonOptions.class.getName();
    private static final PlatformLogger LOGGER = WLSDeployLogFactory.getLogger(LOGGER_NAME);

    @Unmatched
    protected List<String> unmatchedOptions;

    @Option(
          names = { "-help" },
          description = "Get help for the ${COMMAND-FULL-NAME} command",
          usageHelp = true,
          defaultValue = "false"
    )
    @SuppressWarnings("unused")
    private boolean helpRequested;

    @Option(
        names = { "-archive_file" },
        paramLabel = "<archive_file>",
        description = "Path to the archive file to use.",
        required = true
    )
    protected String archiveFilePath;

    protected WLSDeployArchive archive;

    protected String getArchiveFilePath() {
        return archiveFilePath;
    }

    protected void initializeOptions(boolean archiveFileMustAlreadyExist) throws ArchiveHelperException {
        this.archive = createArchive(archiveFileMustAlreadyExist);
    }

    private WLSDeployArchive createArchive(boolean fileMustExist) throws ArchiveHelperException {
        final String METHOD = "createArchive";
        LOGGER.entering(CLASS, METHOD);

        String fullArchiveFileName = FileUtils.getCanonicalPath(getArchiveFilePath());
        if (StringUtils.isEmpty(fullArchiveFileName)) {
            ArchiveHelperException ex = new ArchiveHelperException(ExitCode.USAGE_ERROR, "WLSDPLY-30000");
            LOGGER.throwing(CLASS, METHOD, ex);
            throw ex;
        }

        File fullArchiveFile = new File(fullArchiveFileName);
        if (fileMustExist) {
            if (!fullArchiveFile.isFile()) {
                ArchiveHelperException ex = new ArchiveHelperException(ExitCode.ARG_VALIDATION_ERROR, "WLSDPLY-30001",
                    fullArchiveFile.getAbsolutePath());
                LOGGER.throwing(CLASS, METHOD, ex);
                throw ex;
            }

            if (!fullArchiveFile.exists()) {
                ArchiveHelperException ex = new ArchiveHelperException(ExitCode.ARG_VALIDATION_ERROR, "WLSDPLY-30002",
                    fullArchiveFile.getAbsolutePath());
                LOGGER.throwing(CLASS, METHOD, ex);
                throw ex;
            }
        } else {
            if (!fullArchiveFile.exists()) {
                File fullArchiveParentDir = fullArchiveFile.getParentFile();
                if (!fullArchiveParentDir.exists() && !fullArchiveParentDir.mkdirs()) {
                    ArchiveHelperException ex = new ArchiveHelperException(ExitCode.ARG_VALIDATION_ERROR,
                        "WLSDPLY-30003", fullArchiveParentDir.getAbsolutePath());
                    LOGGER.throwing(CLASS, METHOD, ex);
                    throw ex;
                }
            }
        }

        return new WLSDeployArchive(fullArchiveFileName);
    }
}
