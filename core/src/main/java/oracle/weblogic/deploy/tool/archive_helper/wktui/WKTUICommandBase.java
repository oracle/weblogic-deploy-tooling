/*
 * Copyright (c) 2025, 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.tool.archive_helper.wktui;

import java.io.FileWriter;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

import oracle.weblogic.deploy.exception.ExceptionHelper;
import oracle.weblogic.deploy.logging.PlatformLogger;
import oracle.weblogic.deploy.logging.WLSDeployLogFactory;

import static oracle.weblogic.deploy.tool.ArchiveHelper.LOGGER_NAME;

public abstract class WKTUICommandBase extends WKTUICommonOptions {
    private static final String CLASS = WKTUICommandBase.class.getName();
    private static final PlatformLogger LOGGER = WLSDeployLogFactory.getLogger(LOGGER_NAME);
    private static final String JSON_INDENT = "  ";

    protected List<String> writeOutputJsonFile(List<String> files) throws IOException {
        final String METHOD = "writeOutputJsonFile";
        LOGGER.entering(CLASS, METHOD, files);
        List<String> messages = new ArrayList<>();
        try (FileWriter jsonWriter = new FileWriter(this.outputJsonFile, false)) {
            String jsonString = getJsonString(files);
            jsonWriter.write(jsonString, 0, jsonString.length());
        }

        messages.add(ExceptionHelper.getMessage("WLSDPLY-30072", this.archiveFilePath,
                outputJsonFile.getAbsolutePath()));
        return messages;
    }

    protected String getJsonString(List<String> files) {
        int lastFileIdx = files.size() - 1;
        StringBuilder sb = new StringBuilder("{\n");
        sb.append(JSON_INDENT);
        sb.append("\"files\": {\n");
        for (int idx = 0; idx < files.size(); idx++) {
            sb.append(JSON_INDENT);
            sb.append(JSON_INDENT);
            sb.append(getZipEntryJson(files.get(idx)));
            if (idx != lastFileIdx) {
                sb.append(",");
            }
            sb.append("\n");
        }
        sb.append(JSON_INDENT);
        sb.append("}\n");
        sb.append("}");
        return sb.toString();
    }

    protected String getZipEntryJson(String zipPath) {
        boolean isDirectory = zipPath.endsWith("/");
        StringBuilder sb = new StringBuilder();
        sb.append('"');
        sb.append(zipPath);
        sb.append('"');
        sb.append(": { \"directory\": ");
        sb.append(isDirectory);
        sb.append(" }");
        return sb.toString();
    }
}
