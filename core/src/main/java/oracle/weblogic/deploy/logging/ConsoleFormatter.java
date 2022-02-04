/*
 * Copyright (c) 2019, 2022, Oracle Corporation and/or its affiliates.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.logging;

import java.util.logging.Formatter;
import java.util.logging.LogRecord;

/**
 * This class removes the Exception record from the LogRecord before formatting so that a
 * stack trace will not print to the Console. The WLSDeployLogFormatter is by default called to
 * format the LogRecord into a localized String. To select a different formatter, inject
 * that instance into the set formatter of this Instance.
 */
public class ConsoleFormatter extends Formatter {

    // Default Formatter if another is not injected
    private Formatter formatter = new WLSDeployLogFormatter();

    public String format(LogRecord logRecord) {
        LogRecord cloned = LoggingUtils.cloneRecordWithoutException(logRecord);
        return formatter.format(cloned);
    }

    @SuppressWarnings("unused")
    public void setFormatter(Formatter formatter) {
        if (formatter != null) {
            this.formatter = formatter;
        }
    }
}
