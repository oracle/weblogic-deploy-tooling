/*
 * Copyright (c) 2023, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.tool.archive_helper.add;

import oracle.weblogic.deploy.tool.archive_helper.ArchiveHelperException;
import oracle.weblogic.deploy.tool.archive_helper.CommonOptions;

import picocli.CommandLine.Option;

public abstract class AddOptions extends CommonOptions {
    @Option(
        names = {"-overwrite"},
        description = "overwrite the existing entry in the archive file, if any"
    )
    protected boolean overwrite;

    protected void initializeOptions() throws ArchiveHelperException {
        super.initializeOptions(false);
    }
}
