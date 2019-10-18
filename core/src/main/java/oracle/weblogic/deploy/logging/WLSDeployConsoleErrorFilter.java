/*
 * Copyright (c) 2019, Oracle Corporation and/or its affiliates.  All rights reserved.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.logging;

import java.util.logging.Filter;
import java.util.logging.Level;
import java.util.logging.LogRecord;

/**
 * This Class queries the information in the LogRecord to determine if it can be written to the OutputStream
 * associated with Error log record types.
 */
public class WLSDeployConsoleErrorFilter implements Filter {

    @Override
    public boolean isLoggable(LogRecord record) {
        boolean stdErr = false;
        int level = record.getLevel() == null ? 0 : record.getLevel().intValue();
        if (level == Level.WARNING.intValue() || level == Level.SEVERE.intValue()) {
            stdErr = true;
        }
        return stdErr;
    }

}