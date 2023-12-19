/*
 * Copyright (c) 2019, 2023, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.logging;

import java.util.logging.Formatter;
import java.util.logging.Level;
import java.util.logging.LogManager;
import java.util.logging.LogRecord;

import static oracle.weblogic.deploy.logging.WLSDeployLoggingConfig.HANDLER_LEVEL_PROP;
import static oracle.weblogic.deploy.logging.WLSDeployLoggingConfig.WLSDEPLOY_STDOUT_CONSOLE_HANDLER;

/**
 * This class removes the Exception record from the LogRecord before formatting so that a
 * stack trace will not print to the Console. The WLSDeployLogFormatter is by default called to
 * format the LogRecord into a localized String. To select a different formatter, inject
 * that instance into the set formatter of this Instance.
 */
public class ConsoleFormatter extends Formatter {

    // Default Formatter if another is not injected
    private Formatter formatter = new WLSDeployLogFormatter();
    private boolean suppressExceptions = true;

    public ConsoleFormatter() {
        String stdoutHandlerLevel =
            LogManager.getLogManager().getProperty(WLSDEPLOY_STDOUT_CONSOLE_HANDLER + HANDLER_LEVEL_PROP);
        if (stdoutHandlerLevel != null && stdoutHandlerLevel.equalsIgnoreCase(Level.ALL.toString())) {
            suppressExceptions = false;
        }
    }

    public String format(LogRecord logRecord) {
        LogRecord recordToPublish = logRecord;
        if (suppressExceptions) {
            recordToPublish = LoggingUtils.cloneRecordWithoutException(logRecord);
        }
        return formatter.format(recordToPublish);
    }

    @SuppressWarnings("unused")
    public void setFormatter(Formatter formatter) {
        if (formatter != null) {
            this.formatter = formatter;
        }
    }
}
