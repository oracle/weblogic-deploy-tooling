/*
 * Copyright (c) 2023, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.tool.archive_helper.remove;

import oracle.weblogic.deploy.tool.archive_helper.ArchiveHelperException;
import oracle.weblogic.deploy.tool.archive_helper.CommonOptions;

import picocli.CommandLine.Option;


public class RemoveOptions extends CommonOptions {
    @Option(
        names = {"-force"},
        description = "Force the remove command to succeed even if the item being removed " +
            "does not exist in the archive file"
    )
    protected boolean force;

    protected void initializeOptions() throws ArchiveHelperException {
        super.initializeOptions(false);
    }
}
