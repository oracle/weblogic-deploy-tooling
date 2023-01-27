/*
 * Copyright (c) 2023, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.util;

public class ExitCode {
    public static final int OK = 0;
    public static final int WARNING = 1;
    public static final int ERROR = 2;
    public static final int ARG_VALIDATION_ERROR = 98;
    public static final int USAGE_ERROR = 99;
    public static final int HELP = 100;
    public static final int DEPRECATION = 101;
    public static final int RESTART_REQUIRED = 103;
    public static final int CANCEL_CHANGES_IF_RESTART = 104;

    private ExitCode() {
        // hide default constructor
    }
}
