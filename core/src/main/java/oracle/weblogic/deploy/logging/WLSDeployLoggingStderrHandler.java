/*
 * Copyright (c) 2019, Oracle and/or its affiliates. All rights reserved.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.logging;

import java.util.logging.LogRecord;
import java.util.logging.StreamHandler;

/**
 * This Class extends the StreamHandler to write log records to STDERR. The "wlsdeploy" Logger
 * is configured with an instance of this Handler class and an instance of Class @WLSDeployStdoutHandler@
 * to log records to the STDOUT and STDERR output streams.
 * <p>
 * Attach a logger or filter to this Handler to direct log records to the STDERR output stream
 */
public class WLSDeployLoggingStderrHandler extends StreamHandler {

    public WLSDeployLoggingStderrHandler() {
        super();
        setOutputStream(System.err);
    }

    @Override
    public void publish(LogRecord record) {
        super.publish(record);
        flush();
    }

    /**
     * Override <tt>StreamHandler.close</tt> to do a flush but not
     * to close the output stream.  That is, we do <b>not</b>
     * close <tt>System.err</tt>.
     */
    @Override
    public void close() {
        flush();
    }

}