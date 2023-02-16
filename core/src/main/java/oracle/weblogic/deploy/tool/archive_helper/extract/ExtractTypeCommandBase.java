/*
 * Copyright (c) 2023, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.tool.archive_helper.extract;

import java.util.concurrent.Callable;

import oracle.weblogic.deploy.tool.archive_helper.CommandResponse;

public abstract class ExtractTypeCommandBase extends ExtractOptions implements Callable<CommandResponse> {
}
