/*
 * Copyright (c) 2017, 2022, Oracle Corporation and/or its affiliates.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.logging;

import java.io.PrintWriter;
import java.io.StringWriter;
import java.text.MessageFormat;
import java.util.Date;
import java.util.logging.Formatter;
import java.util.logging.LogRecord;
import java.util.regex.Pattern;

/**
 * The log formatting class.
 */
public class WLSDeployLogFormatter extends Formatter {
    private static final String CATALOG_KEY_PATTERN_STRING = "^[A-Z]{3,10}?-[0-9]{3,5}$";
    private static final Pattern CATALOG_KEY_PATTERN = Pattern.compile(CATALOG_KEY_PATTERN_STRING);

    private static final String DATE_FORMAT_STRING = "####<{0,date} {0,time}>";
    private static final String LINE_SEPARATOR = System.getProperty("line.separator");

    private final Object[] args;
    private final MessageFormat formatter;
    private final Date date;

    /**
     * The constructor.
     */
    public WLSDeployLogFormatter() {
        this.date = new Date();
        this.args = new Object[1];
        this.formatter = new MessageFormat(DATE_FORMAT_STRING);
    }

    /**
     * Formats the log record.
     *
     * @param logRecord the log record
     * @return the formatted log record
     */
    @Override
    public synchronized String format(LogRecord logRecord) {
        StringBuilder sb = new StringBuilder();

        date.setTime(logRecord.getMillis());
        args[0] = date;

        StringBuffer text = new StringBuffer();
        formatter.format(args, text, null);
        sb.append(text);

        // Level
        sb.append(" <");
        sb.append(logRecord.getLevel().getLocalizedName());
        sb.append('>');

        // Class name
        sb.append(" <");
        String source = logRecord.getSourceClassName();
        if (source != null) {
            sb.append(source.substring(source.lastIndexOf('.') + 1));
        } else {
            sb.append(logRecord.getLoggerName());
        }
        sb.append('>');

        // Method name
        sb.append(" <");
        if (logRecord.getSourceMethodName() != null) {
            sb.append(logRecord.getSourceMethodName());
        }
        sb.append('>');

        String messageKey = logRecord.getMessage();
        String message = formatMessage(logRecord);

        if (messageKey != null) {
            sb.append(" <");
            if (CATALOG_KEY_PATTERN.matcher(messageKey).matches()) {
                sb.append(messageKey);
            }
            sb.append('>');
        }
        sb.append(" <");
        sb.append(message);
        if (logRecord.getThrown() != null) {
            StringWriter sw = new StringWriter();
            PrintWriter pw = new PrintWriter(sw);
            logRecord.getThrown().printStackTrace(pw);
            pw.close();
            sb.append(LINE_SEPARATOR);
            sb.append(sw);
            sb.append(LINE_SEPARATOR);
        }
        sb.append('>');
        sb.append(LINE_SEPARATOR);
        return sb.toString();
    }
}
