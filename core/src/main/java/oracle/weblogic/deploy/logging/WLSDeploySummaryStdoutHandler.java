package oracle.weblogic.deploy.logging;

import java.util.logging.LogRecord;
import java.util.logging.StreamHandler;


public class WLSDeploySummaryStdoutHandler extends StreamHandler {

    public WLSDeploySummaryStdoutHandler() {
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
