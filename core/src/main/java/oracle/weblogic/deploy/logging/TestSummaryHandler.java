/*
 * Copyright (c) 2024, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.logging;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.logging.Level;
import java.util.logging.LogRecord;

/**
 * Extend summary handler to collect message IDs for unit tests.
 */
public class TestSummaryHandler extends SummaryHandler {
    private final List<LogRecord> records = new ArrayList<>();

    public int getMessageKeyCount(Level level, String key) {
        int count = 0;
        for(LogRecord record: records) {
            if((record.getLevel() == level) && key.equals(record.getMessage())) {
                count++;
            }
        }
        return count;
    }

    // use to debug unit tests
    public void printDebug() {
        System.out.println();
        for(LogRecord record: records) {
            System.out.println("  " + record.getMessage() + ": " + record.getLevel()
                    + " " + Arrays.asList(record.getParameters()));
        }
        System.out.println();
    }

    @Override
    public synchronized void publish(LogRecord logRecord) {
        records.add(logRecord);
        super.publish(logRecord);
    }
}
