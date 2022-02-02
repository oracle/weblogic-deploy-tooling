/*
 * Copyright (c) 2019, 2022, Oracle Corporation and/or its affiliates.  All rights reserved.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.logging;

import java.util.logging.LogRecord;
import java.util.logging.StreamHandler;

/**
 * This Class extends the StreamHandler to write log records to STDOUT.
 */
public class WLSDeployLoggingStdoutHandler extends StreamHandler {

    public WLSDeployLoggingStdoutHandler() {
        super();
        setOutputStream(System.out);
    }

    @Override
    public void publish(LogRecord record) {
        super.publish(record);
        flush();
    }

    /**
     * Override <tt>StreamHandler.close</tt> to do a flush but not
     * to close the output stream.  That is, we do <b>not</b>
     * close <tt>System.out</tt>.
     */
    @Override
    public void close() {
        flush();
    }
}