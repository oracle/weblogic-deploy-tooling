/*
 * Copyright (c) 2025, 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.tool.archive_helper.wktui;

import java.io.File;

import oracle.weblogic.deploy.logging.PlatformLogger;
import oracle.weblogic.deploy.logging.WLSDeployLogFactory;
import oracle.weblogic.deploy.tool.archive_helper.ArchiveHelperException;
import oracle.weblogic.deploy.tool.archive_helper.CommonOptions;

import oracle.weblogic.deploy.util.ExitCode;
import oracle.weblogic.deploy.util.FileUtils;
import picocli.CommandLine.Option;

import static oracle.weblogic.deploy.tool.ArchiveHelper.LOGGER_NAME;

public abstract class WKTUICommonOptions extends CommonOptions {
    private static final String CLASS = WKTUICommonOptions.class.getName();
    private static final PlatformLogger LOGGER = WLSDeployLogFactory.getLogger(LOGGER_NAME);

    @Option(
        names = { "-output_json_file" },
        paramLabel = "<output-json-file>",
        description = "File path of the location to write the output JSON file",
        required = true
    )
    protected String outputJsonFilePath;

    protected File outputJsonFile;

    protected void initializeOptions(boolean archiveFileMustAlreadyExist) throws ArchiveHelperException {
        final String METHOD = "initializeOptions";
        LOGGER.entering(CLASS, METHOD);

        super.initializeOptions(archiveFileMustAlreadyExist);
        this.outputJsonFile = getJsonOutputFile(this.outputJsonFilePath);

        LOGGER.exiting(CLASS, METHOD);
    }

    private File getJsonOutputFile(String path) throws ArchiveHelperException {
        final String METHOD = "getJsonOutputFile";
        LOGGER.entering(CLASS, METHOD, path);

        File result = FileUtils.getCanonicalFile(path);
        File parentDir = result.getParentFile();
        if (!parentDir.exists()) {
            ArchiveHelperException ex = new ArchiveHelperException(ExitCode.ARG_VALIDATION_ERROR, "WLSDPLY-30070",
                    path, parentDir.getAbsolutePath());
            LOGGER.throwing(CLASS, METHOD, ex);
            throw ex;
        }

        LOGGER.exiting(CLASS, METHOD, result.getAbsolutePath());
        return result;
    }
}
