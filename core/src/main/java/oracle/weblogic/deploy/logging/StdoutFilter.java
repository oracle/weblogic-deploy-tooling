/*
 * Copyright (c) 2019, 2022, Oracle Corporation and/or its affiliates.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.logging;

import java.util.logging.Filter;
import java.util.logging.Level;
import java.util.logging.LogRecord;

/**
 * This Class queries the information in the LogRecord to determine if it can be written to the OutputStream
 * associated with standard console log record types.
 */
public class StdoutFilter implements Filter {
    @Override
    public boolean isLoggable(LogRecord logRecord) {
        boolean stdOut = true;
        int level = logRecord.getLevel() == null ? 0 : logRecord.getLevel().intValue();
        if (level == Level.WARNING.intValue() || level == Level.SEVERE.intValue()) {
            stdOut = false;
        }
        return stdOut;
    }
}
