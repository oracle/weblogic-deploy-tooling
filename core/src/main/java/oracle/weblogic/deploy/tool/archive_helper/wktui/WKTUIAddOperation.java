/*
 * Copyright (c) 2025, 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.tool.archive_helper.wktui;

public class WKTUIAddOperation extends WKTUIOperation {
    protected final String filePath;

    WKTUIAddOperation(String operationName, String path, String filePath) {
        super(operationName, path);
        this.filePath = filePath;
    }

    public String getFilePath() {
        return filePath;
    }
}
