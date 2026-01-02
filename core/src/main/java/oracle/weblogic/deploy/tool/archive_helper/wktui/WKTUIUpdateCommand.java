package oracle.weblogic.deploy.tool.archive_helper.wktui;

import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
/*
 * Copyright (c) 2025, 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
import java.util.Map;
import java.util.concurrent.Callable;

import oracle.weblogic.deploy.json.JavaJsonTranslator;
import oracle.weblogic.deploy.json.JsonException;
import oracle.weblogic.deploy.logging.PlatformLogger;
import oracle.weblogic.deploy.logging.WLSDeployLogFactory;
import oracle.weblogic.deploy.tool.archive_helper.ArchiveHelperException;
import oracle.weblogic.deploy.tool.archive_helper.CommandResponse;
import oracle.weblogic.deploy.util.ExitCode;
import oracle.weblogic.deploy.util.FileUtils;
import oracle.weblogic.deploy.util.StringUtils;
import oracle.weblogic.deploy.util.WLSDeployArchiveIOException;

import picocli.CommandLine.Command;
import picocli.CommandLine.Option;

import static oracle.weblogic.deploy.tool.ArchiveHelper.LOGGER_NAME;

@Command(
    name = "update",
    header = "Using the input JSON updates file, update the archive file, and write all entries to the JSON output file.",
    description = "%nCommand-line options:"
)
public class WKTUIUpdateCommand extends WKTUICommandBase implements Callable<CommandResponse> {
    private static final String CLASS = WKTUIUpdateCommand.class.getName();
    private static final PlatformLogger LOGGER = WLSDeployLogFactory.getLogger(LOGGER_NAME);

    @Option(
        names = { "-input_json_file" },
        paramLabel = "<input-json-file>",
        description = "File path of the location of the input JSON file containing the operations to perform on the archive file",
        required = true
    )
    private String inputOperationsFilePath;
    private Map<String, Object> operationsMap;

    @Override
    protected void initializeOptions(boolean archiveFileMustAlreadyExist) throws ArchiveHelperException  {
        super.initializeOptions(archiveFileMustAlreadyExist);
        this.operationsMap = getOperationsMap();
    }

    @Override
    public CommandResponse call() throws Exception {
        final String METHOD = "call";
        LOGGER.entering(CLASS, METHOD);

        CommandResponse response;
        try {
            initializeOptions(false);
            List<WKTUIOperation> operationsList = getOperationsList();
            List<String> updatedArchiveEntries = this.archive.wktuiProcessOperations(operationsList);
            List<String> messages = writeOutputJsonFile(updatedArchiveEntries);
            response = new CommandResponse(ExitCode.OK);
            response.addMessages(messages);
        } catch (ArchiveHelperException ex) {
            LOGGER.severe(ex.getLocalizedMessage(), ex);
            response = new CommandResponse(ex.getExitCode(), ex.getLocalizedMessage());
        } catch (WLSDeployArchiveIOException waioe) {
            LOGGER.severe("WLSDPLY-30080", waioe, this.inputOperationsFilePath,
                this.archiveFilePath, waioe.getLocalizedMessage());
            response = new CommandResponse(ExitCode.ERROR,"WLSDPLY-30080",
                this.inputOperationsFilePath, this.archiveFilePath, waioe.getLocalizedMessage());
        } catch (IOException ioe) {
            LOGGER.severe("WLSDPLY-30081", ioe, this.inputOperationsFilePath,
                this.archiveFilePath, ioe.getLocalizedMessage());
            response = new CommandResponse(ExitCode.ERROR, "WLSDPLY-30081", this.inputOperationsFilePath,
                this.archiveFilePath, ioe.getLocalizedMessage());
        }

        LOGGER.exiting(CLASS, METHOD, response);
        return response;
    }

    protected Map<String, Object> getOperationsMap() throws ArchiveHelperException {
        final String METHOD = "getOperationsMap";
        LOGGER.entering(CLASS, METHOD);

        this.inputOperationsFilePath = FileUtils.getCanonicalPath(this.inputOperationsFilePath);
        if (StringUtils.isEmpty(this.inputOperationsFilePath)) {
            ArchiveHelperException ex = new ArchiveHelperException(ExitCode.USAGE_ERROR, "WLSDPLY-30074");
            LOGGER.throwing(CLASS, METHOD, ex);
            throw ex;
        }

        File inputJsonFile = new File(this.inputOperationsFilePath);
        if (!inputJsonFile.isFile()) {
            ArchiveHelperException ex = new ArchiveHelperException(ExitCode.ARG_VALIDATION_ERROR, "WLSDPLY-30075",
                this.inputOperationsFilePath);
            LOGGER.throwing(CLASS, METHOD, ex);
            throw ex;
        }
        if (!inputJsonFile.exists()) {
            ArchiveHelperException ex = new ArchiveHelperException(ExitCode.ARG_VALIDATION_ERROR, "WLSDPLY-30076",
                this.inputOperationsFilePath);
            LOGGER.throwing(CLASS, METHOD, ex);
            throw ex;
        }

        Map<String, Object> wktuiOperationsMap = null;
        try {
            JavaJsonTranslator translator = new JavaJsonTranslator(this.inputOperationsFilePath);
            wktuiOperationsMap = translator.parse();
        } catch (JsonException je) {
            ArchiveHelperException ex = new ArchiveHelperException(ExitCode.ARG_VALIDATION_ERROR, "WLSDPLY-30077", je,
                this.inputOperationsFilePath, je.getLocalizedMessage());
            LOGGER.throwing(CLASS, METHOD, ex);
            throw ex;
        }
        LOGGER.exiting(CLASS, METHOD, wktuiOperationsMap);
        return wktuiOperationsMap;
    }

    protected List<WKTUIOperation> getOperationsList() throws ArchiveHelperException {
        final String METHOD = "getOperationsList";
        LOGGER.entering(CLASS, METHOD);

        Object operationsListObject = operationsMap.get("operations");
        List<Map<String, Object>> operationsList = null;
        if (operationsListObject == null) {
            ArchiveHelperException ex = new ArchiveHelperException(ExitCode.ERROR, "WLSDPLY-30078",
                this.inputOperationsFilePath, "operations");
            LOGGER.throwing(CLASS, METHOD, ex);
            throw ex;
        } else if (List.class.isAssignableFrom(operationsListObject.getClass())) {
            @SuppressWarnings("unchecked")
            List<Map<String, Object>> tmp = (List<Map<String, Object>>) operationsListObject;
            operationsList = tmp;
        } else {
            ArchiveHelperException ex = new ArchiveHelperException(ExitCode.ERROR, "WLSDPLY-30079",
                this.inputOperationsFilePath, "operations", operationsListObject.getClass().getName());
            LOGGER.throwing(CLASS, METHOD, ex);
            throw ex;
        }

        List<WKTUIOperation> wktuiOperationsList = new ArrayList<>();
        for (Map<String, Object> operationsMap : operationsList) {
            String operationType = (String) operationsMap.get("op");
            switch (operationType) {
                case "add":
                    String path = (String) operationsMap.get("path");
                    String filePath = (String) operationsMap.get("filePath");
                    WKTUIAddOperation addOp = new WKTUIAddOperation(operationType, path, filePath);
                    wktuiOperationsList.add(addOp);
                    break;

                case "remove":
                    path = (String) operationsMap.get("path");
                    WKTUIRemoveOperation removeOp = new WKTUIRemoveOperation(operationType, path);
                    wktuiOperationsList.add(removeOp);
                    break;

                default:
                    ArchiveHelperException ex = new ArchiveHelperException(ExitCode.ERROR, "WLSDPLY-30079",
                        this.inputOperationsFilePath, operationType);
                    LOGGER.throwing(CLASS, METHOD, ex);
                    throw ex;
            }
        }

        LOGGER.exiting(CLASS, METHOD, wktuiOperationsList);
        return wktuiOperationsList;
    }
}
