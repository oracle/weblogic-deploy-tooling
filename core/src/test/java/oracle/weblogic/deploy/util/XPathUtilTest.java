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
    void testPSUWithParen() {
        XPathUtil util = new XPathUtil();
        String tester = new String(".2145)");
        String expected = new String("2145");
        String actual = util.extractPsu(tester);
        assertEquals(expected, actual);
    }

    @Test
    void testPSU() {
        XPathUtil util = new XPathUtil();
        String tester = new String(".2145");
        String expected = new String("2145");
        String actual = util.extractPsu(tester);
        assertEquals(expected, actual);
    }
}
