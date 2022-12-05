/*
 * Copyright (c) 2017, 2022, Oracle Corporation and/or its affiliates.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.util;

import org.junit.jupiter.api.Test;

import oracle.weblogic.deploy.util.XPathUtil;

import static org.junit.jupiter.api.Assertions.assertEquals;

public class XPathUtilTest {

    @Test
    void testNewPSUExceptionWith8Digits() {
        XPathUtil util = new XPathUtil();
        String tester = new String("WLS PATCH SET UPDATE 12.2.1.3.0(ID:20190522.070630)");
        String expected = new String("190522");
        String actual = util.extractNewPsu(tester);
        assertEquals(expected, actual);
    }

    @Test
    void testNewPSUExceptionWith6Digits() {
        XPathUtil util = new XPathUtil();
        String tester = new String("WLS PATCH SET UPDATE 12.2.1.3.0(ID:191217.1425)");
        String expected = new String("191217");
        String actual = util.extractNewPsu(tester);
        assertEquals(expected, actual);
    }

    void testNewPSUExceptionWithUnknownNumberOfDigits() {
        XPathUtil util = new XPathUtil();
        String tester = new String("WLS PATCH SET UPDATE 12.2.1.3.0(ID:12345.6789)");
        String expected = null;
        String actual = util.extractNewPsu(tester);
        assertEquals(expected, actual);
    }

    @Test
    void testNewPSU() {
        XPathUtil util = new XPathUtil();
        String tester = new String("WLS PATCH SET UPDATE 12.2.1.4.220329");
        String expected = new String("220329");
        String actual = util.extractNewPsu(tester);
        assertEquals(expected, actual);
    }

    @Test
    void testOldPSU() {
        XPathUtil util = new XPathUtil();
        String tester = new String("WebLogic Server 12.1.3.0.2 PSU Patch for BUG19637454 THU NOV 27 10:54:42 IST 2014");
        String expected = new String("2");
        String actual = util.extractOldPsu(tester);
        assertEquals(expected, actual);
    }
}
