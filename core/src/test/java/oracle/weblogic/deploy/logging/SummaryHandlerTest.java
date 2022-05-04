/*
 * Copyright (c) 2022, Oracle Corporation and/or its affiliates.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.logging;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;

public class SummaryHandlerTest {
    @Test
    public void testGetSummaryHandler_ReturnsHandler() {
        SummaryHandler handler = new SummaryHandler();

        WLSDeployLogEndHandler summaryHandler = WLSDeployLogEndHandler.getSummaryHandler();
        assertNotNull(summaryHandler, "SummaryHandler should not be null");
        assertEquals(handler, summaryHandler, "summaryHandler is not the same object");
    }
}
