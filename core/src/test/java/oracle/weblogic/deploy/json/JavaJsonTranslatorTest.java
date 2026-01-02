/*
 * Copyright (c) 2025, 2026, Oracle Corporation and/or its affiliates.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.json;

import oracle.weblogic.deploy.util.FileUtils;
import org.junit.jupiter.api.Test;

import java.io.File;
import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;

public class JavaJsonTranslatorTest {
    private static final File TEST_BASE_DIR = FileUtils.getCanonicalFile(new File(System.getProperty("user.dir")));
    private static final File TEST_JSON_FILE =
        FileUtils.getCanonicalFile(new File(TEST_BASE_DIR, "src/test/resources/json/wktui-operations.json"));

    @Test
    public void testParse() throws Throwable {
        JavaJsonTranslator translator = new JavaJsonTranslator(TEST_JSON_FILE.getAbsolutePath());
        Map<String, Object> result = translator.parse();
        Object operationsObject = result.get("operations");

        List<Map<String, Object>> operationsList = null;
        if (List.class.isAssignableFrom(operationsObject.getClass())) {
            @SuppressWarnings("unchecked")
            List<Map<String, Object>> tmp = (List<Map<String, Object>>) operationsObject;
            operationsList = tmp;
        }
        assertNotNull(operationsList, "operations list should not be null");
        assertEquals(2, operationsList.size(), "operations list should be have 2 elements");

        Map<String, Object> operation = operationsList.get(0);
        String operationType = (String) operation.get("op");
        assertEquals("remove", operationType, "operation type should be remove");
        String operationPath = (String) operation.get("path");
        assertEquals("config/wlsdeploy/custom/DebugScopes.txt", operationPath,
            "operation path should be config/wlsdeploy/custom/DebugScopes.txt");

        operation = operationsList.get(1);
        operationType = (String) operation.get("op");
        assertEquals("add", operationType, "operation type should be add");
        operationPath = (String) operation.get("path");
        assertEquals("config/wlsdeploy/custom/backup_codes.txt", operationPath,
            "operation path should be config/wlsdeploy/custom/backup_codes.txt");
        String operationFilePath = (String) operation.get("filePath");
        assertEquals("/Users/rpatrick/Desktop/backup_codes.txt", operationFilePath,
            "operation filePath should be /Users/rpatrick/Desktop/backup_codes.txt");
    }
}
