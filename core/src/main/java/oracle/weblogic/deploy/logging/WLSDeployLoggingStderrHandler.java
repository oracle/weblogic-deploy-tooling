/*
 * Copyright (c) 2019, Oracle and/or its affiliates. All rights reserved.
 * Licensed under the Universal Permissive License v 1.0 as shown at http://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.logging;

import java.util.logging.LogRecord;
import java.util.logging.StreamHandler;

/**
 * This Class extends the ConsoleHandler to write log records to STDERR. By default, the ConsoleHandler
 * logs records to STDERR. Add this Class to the log properties along with the @WLSDeployStdoutHandler@
 * to write records to both the STDOUT and STDERR. Use a Level or Filter class to select which log records
 * are written to one of the Console output streams.
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