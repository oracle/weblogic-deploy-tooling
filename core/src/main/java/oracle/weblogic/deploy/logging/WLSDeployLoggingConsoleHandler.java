/*
 * Copyright (c) 2017, 2019, Oracle and/or its affiliates. All rights reserved.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.logging;

import java.util.logging.ConsoleHandler;
import java.util.logging.LogRecord;

/**
 * The WLS Deploy Console Handler that prevents stack traces from being output to the console.
 *
 * @deprecated  As of release 1.2.1, moved the code into Formatter {@link WLSDeployConsoleFormatter}
 */
@Deprecated
public class WLSDeployLoggingConsoleHandler extends ConsoleHandler {

    /**
     * The default constructor.
     */
    public WLSDeployLoggingConsoleHandler() {
        // nothing to do
    }

    @Override
    @Deprecated
    public void publish(LogRecord record) {
        LogRecord myRecord = LoggingUtils.cloneRecordWithoutException(record);
        super.publish(myRecord);
    }

}
