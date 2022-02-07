/*
 * Copyright (c) 2019, 2022, Oracle Corporation and/or its affiliates.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.logging;

import java.util.logging.LogRecord;
import java.util.logging.StreamHandler;

/**
 * This Class extends the StreamHandler to write log records to STDOUT.
 */
@SuppressWarnings("unused")
public class StdoutHandler extends StreamHandler {

    public StdoutHandler() {
        super();
        setOutputStream(System.out);
    }

    @Override
    public synchronized void publish(LogRecord logRecord) {
        super.publish(logRecord);
        flush();
    }

    /**
     * Override <tt>StreamHandler.close</tt> to do a flush but not
     * to close the output stream.  That is, we do <b>not</b>
     * close <tt>System.out</tt>.
     */
    @Override
    public synchronized void close() {
        flush();
    }
}
