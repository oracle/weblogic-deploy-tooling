/*
 * Copyright (c) 2023, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.tool.archive_helper;

import oracle.weblogic.deploy.util.WebLogicDeployToolingVersion;

import picocli.CommandLine.IVersionProvider;

public class ArchiveHelperVersionProvider implements IVersionProvider {
    @Override
    public String[] getVersion() {
        return new String[] {
            "WebLogic Deploy Tooling version: " + WebLogicDeployToolingVersion.getVersion(),
            "Build: " + WebLogicDeployToolingVersion.getBuildRevision() + ":" +
                WebLogicDeployToolingVersion.getBuildTimestamp()
        };
    }
}
