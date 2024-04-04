/*
 * Copyright (c) 2018, 2023, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.util;

/**
 * Context information from the tool model context for use in java programs without introducing jython
 */
public class WLSDeployContext {

    public enum WLSTMode {

        OFFLINE("offline"), ONLINE("online");

        private String value;

        private WLSTMode(String value) {
            this.value = value;
        }

        @Override
        public String toString() {
            return value;
        }

    }

    private String version;
    private WLSTMode wlstMode;
    private String programName;
    private boolean isRemote;
    private String remoteVersion;

    /**
     * The context members are encapsulated within this instance through the constructor.
     *
     * @param programName name of the currently running tool
     * @param version     version of oracle home in use by the tool
     * @param wlstMode    mode online or offline how tool is attached to wlst
     */
    public WLSDeployContext(String programName, String version, WLSTMode wlstMode) {
        this.programName = programName;
        this.version = version;
        this.wlstMode = wlstMode;
        this.isRemote = false;
        this.remoteVersion = null;
    }

    /**
     * The context members are encapsulated within this instance through the constructor.
     *
     * @param programName   name of the currently running tool
     * @param version       version of oracle home in use by the tool
     * @param wlstMode      mode online or offline how tool is attached to wlst
     * @param isRemote      whether WDT was run using -remote or with -ssh_host
     * @param remoteVersion the version of the server if it is running remotely
     */
    public WLSDeployContext(String programName, String version, WLSTMode wlstMode, boolean isRemote, String remoteVersion) {
        this.programName = programName;
        this.version = version;
        this.wlstMode = wlstMode;
        this.isRemote = isRemote;
        this.remoteVersion = remoteVersion;
    }

    /**
     * Get the tool name.
     *
     * @return tool program name
     */
    public String getProgramName() {
        return programName;
    }

    /**
     * Return the oracle version for tool.
     *
     * @return version of weblogic
     */
    public String getVersion() {
        return version;
    }

    /**
     * Get the type of connection to wlst.
     *
     * @return offline or online
     */
    public WLSTMode getWlstMode() {
        return wlstMode;
    }

    /**
     * Whether the server is running remotely.
     *
     * @return true if the server is remote, false otherwise
     */
    public boolean isRemote() {
        return isRemote;
    }

    /**
     * Get the remote WebLogic Server version.
     *
     * @return remote WebLogic Server version or null
     */
    public String getRemoteVersion() {
        return remoteVersion;
    }
}