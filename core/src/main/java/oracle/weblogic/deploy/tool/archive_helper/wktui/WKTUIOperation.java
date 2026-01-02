/*
 * Copyright (c) 2025, 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.tool.archive_helper.wktui;

public abstract class WKTUIOperation {
    protected final String operationName;
    protected final String path;

    WKTUIOperation(String operationName, String path) {
        this.operationName = operationName;
        this.path = path;
    }

    public String getOperationName() {
        return operationName;
    }

    public String getPath() {
        return path;
    }
}
