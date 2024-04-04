/*
 * Copyright (c) 2017, 2023, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.aliases;

import java.util.logging.Level;

import oracle.weblogic.deploy.logging.PlatformLogger;
import oracle.weblogic.deploy.logging.WLSDeployLogFactory;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

public class VersionUtilsTest {
    private static final PlatformLogger LOGGER = WLSDeployLogFactory.getLogger("wlsdeploy.versions");

    private static final String VERSION_1033 = "10.3.3.0";
    private static final String VERSION_1036 = "10.3.6.0";
    private static final String VERSION_1211 = "12.1.1.0";
    private static final String VERSION_1212 = "12.1.2.0";
    private static final String VERSION_1213 = "12.1.3.0";
    private static final String VERSION_1221 = "12.2.1.0";
    private static final String VERSION_12211 = "12.2.1.1.0";
    private static final String VERSION_12212 = "12.2.1.2.0";
    private static final String VERSION_12213 = "12.2.1.3.0";
    private static final String VERSION_1231 = "12.3.1.0";
    private static final String VERSION_18   = "18.0.1.20180331";

    private static final String RANGE_ALL_VERSIONS = "[10,)";
    private static final String RANGE_1036_AND_NEWER = "[10.3.6,)";
    private static final String RANGE_LESS_THAN_1212 = "[10,12.1.2)";
    private static final String RANGE_BETWEEN_1212_AND_12213 = "(12.1.1,12.2.1.3]";

    private static final String WLS_1213_VERSION_DESCRIPTION =
        "WebLogic Server 12.1.3.0.0  Wed May 21 18:53:34 PDT 2014 1604337";
    private static final String WLS_1213_VERSION_RESULT = "12.1.3.0.0";
    private static final String WLS_12214_VERSION_DESCRIPTION =
        "WebLogic Server 12.2.1.4.0";
    private static final String WLS_12214_VERSION_RESULT = "12.2.1.4.0";

    private static final String PSU_EXCEPTION_8_DIGIT_DESCRIPTION =
        "WLS PATCH SET UPDATE 12.2.1.3.0(ID:20190522.070630)";
    private static final String PSU_EXCEPTION_8_DIGIT_RESULT = "190522";
    private static final String PSU_EXCEPTION_6_DIGIT_DESCRIPTION = "WLS PATCH SET UPDATE 12.2.1.3.0(ID:191217.1425)";
    private static final String PSU_EXCEPTION_6_DIGIT_RESULT = "191217";
    private static final String PSU_EXCEPTION_UNKNOWN_NUM_DIGITS_DESCRIPTION =
        "WLS PATCH SET UPDATE 12.2.1.3.0(ID:12345.6789)";
    private static final String PSU_EXCEPTION_UNKNOWN_NUM_DIGITS_RESULT = null;
    private static final String PSU_NEW_FORMAT_DESCRIPTION  = "WLS PATCH SET UPDATE 12.2.1.4.220329";
    private static final String PSU_NEW_FORMAT_RESULT = "220329";
    private static final String PSU_OLD_FORMAT_DESCRIPTION =
        "WebLogic Server 12.1.3.0.2 PSU Patch for BUG19637454 THU NOV 27 10:54:42 IST 2014";
    private static final String PSU_OLD_FORMAT_RESULT = "2";
    private static final String[] PSU_NEW_FORMAT_LIST = new String[] {
        "33678734;24551257;Thu Jan 13 09:14:57 CST 2022;SOA Bundle Patch 12.2.1.4.211216",
        "32230661;24024338;Thu Jan 13 08:49:21 CST 2022;One-off",
        "33416868;24444013;Thu Jan 13 08:47:29 CST 2022;WLS PATCH SET UPDATE 12.2.1.4.210930",
        "33313802;24409663;Thu Jan 13 08:38:53 CST 2022;ADF BUNDLE PATCH 12.2.1.4.210903",
        "1221411;24406034;Thu Jan 13 08:33:17 CST 2022;Bundle patch for Oracle Coherence Version 12.2.1.4.11",
        "33093748;24325771;Thu Jan 13 08:31:11 CST 2022;One-off",
        "32905339;24240122;Thu Jan 13 08:29:00 CST 2022;OWSM BUNDLE PATCH 12.2.1.4.210520",
        "32880070;24228725;Thu Jan 13 08:26:19 CST 2022;One-off",
        "32784652;24182560;Thu Jan 13 08:11:55 CST 2022;OPSS Bundle Patch 12.2.1.4.210418",
        "30613424;24331010;Thu Jan 13 08:07:07 CST 2022;One-off"
    };
    private static final String PSU_NEW_FORMAT_LIST_RESULT = "210930";

    @BeforeAll
    static void initialize() {
        LOGGER.setLevel(Level.OFF);
    }

    @Test
    public void testClientGreaterThanServer() throws Exception {
        String clientVersion = "0.7.4";
        String serverVersion = "0.7.3";
        assertTrue(VersionUtils.compareVersions(clientVersion, serverVersion) > 0,
            "Expected client " + clientVersion + " to be newer than server " + serverVersion);

        clientVersion = "0.8";
        serverVersion = "0.7.4";
        assertTrue(VersionUtils.compareVersions(clientVersion, serverVersion) > 0,
            "Expected client " + clientVersion + " to be newer than server " + serverVersion);

        clientVersion = "1.2.3";
        serverVersion = "1.2";
        assertTrue(VersionUtils.compareVersions(clientVersion, serverVersion) > 0,
            "Expected client " + clientVersion + " to be newer than server " + serverVersion);

        clientVersion = "1.2.3";
        serverVersion = "1.2.3-SNAPSHOT";
        assertTrue(VersionUtils.compareVersions(clientVersion, serverVersion) > 0,
            "Expected client " + clientVersion + " to be newer than server " + serverVersion);

        clientVersion = "1.2.3-BETA1";
        serverVersion = "1.2.3-ALPHA3";
        assertTrue(VersionUtils.compareVersions(clientVersion, serverVersion) > 0,
            "Expected client " + clientVersion + " to be newer than server " + serverVersion);

        clientVersion = "1.2.3-SNAPSHOT";
        serverVersion = "1.2.2";
        assertTrue(VersionUtils.compareVersions(clientVersion, serverVersion) > 0,
            "Expected client " + clientVersion + " to be newer than server " + serverVersion);
    }

    @Test
    public void testServerGreaterThanClient() throws Exception {
        String clientVersion = "0.7.3";
        String serverVersion = "0.7.4";
        assertTrue(VersionUtils.compareVersions(clientVersion, serverVersion) < 0,
            "Expected server " + serverVersion + " to be newer than client " + clientVersion);

        clientVersion = "0.7.4";
        serverVersion = "1";
        assertTrue(VersionUtils.compareVersions(clientVersion, serverVersion) < 0,
            "Expected server " + serverVersion + " to be newer than client " + clientVersion);

        clientVersion = "1.2";
        serverVersion = "1.2.3";
        assertTrue(VersionUtils.compareVersions(clientVersion, serverVersion) < 0,
            "Expected server " + serverVersion + " to be newer than client " + clientVersion);

        clientVersion = "1.2.3-SNAPSHOT";
        serverVersion = "1.2.3";
        assertTrue(VersionUtils.compareVersions(clientVersion, serverVersion) < 0,
            "Expected server " + serverVersion + " to be newer than client " + clientVersion);

        clientVersion = "1.2.3-ALPHA4";
        serverVersion = "1.2.3-ALPHA5";
        assertTrue(VersionUtils.compareVersions(clientVersion, serverVersion) < 0,
            "Expected server " + serverVersion + " to be newer than client " + clientVersion);

        clientVersion = "1.2.1";
        serverVersion = "1.2.2-SNAPSHOT";
        assertTrue(VersionUtils.compareVersions(clientVersion, serverVersion) < 0,
            "Expected server " + serverVersion + " to be newer than client " + clientVersion);
    }

    @Test
    public void testServerToEqualClient() throws Exception {
        String clientVersion = "0.7.4";
        String serverVersion = "0.7.4";
        assertEquals(0, VersionUtils.compareVersions(clientVersion, serverVersion),
            "Expected server " + serverVersion + " to be the same as client " + clientVersion);

        clientVersion = "1";
        serverVersion = "1";
        assertEquals(0, VersionUtils.compareVersions(clientVersion, serverVersion),
            "Expected server " + serverVersion + " to be the same as client " + clientVersion);

        clientVersion = "1.2.3-ALPHA1";
        serverVersion = "1.2.3-ALPHA1";
        assertEquals(0, VersionUtils.compareVersions(clientVersion, serverVersion),
            "Expected server " + serverVersion + " to be the same as client " + clientVersion);

        clientVersion = "1.2.3.4.5.6.7.8.9";
        serverVersion = "1.2.3.4.5.6.7.8.9";
        assertEquals(0, VersionUtils.compareVersions(clientVersion, serverVersion),
            "Expected server " + serverVersion + " to be the same as client " + clientVersion);

        clientVersion = "0.7.4-SNAPSHOT";
        serverVersion = "0.7.4-SNAPSHOT";
        assertEquals(0, VersionUtils.compareVersions(clientVersion, serverVersion),
            "Expected server " + serverVersion + " to be the same as client " + clientVersion);
    }


    @Test
    public void testVersionsInRangeAll() throws Exception {
        boolean answer = VersionUtils.isVersionInRange(VERSION_1036, RANGE_ALL_VERSIONS);
        assertTrue(answer, "expected " + VERSION_1036 + " to be in range " + RANGE_ALL_VERSIONS);

        answer = VersionUtils.isVersionInRange(VERSION_1211, RANGE_ALL_VERSIONS);
        assertTrue(answer, "expected " + VERSION_1211 + " to be in range " + RANGE_ALL_VERSIONS);

        answer = VersionUtils.isVersionInRange(VERSION_1212, RANGE_ALL_VERSIONS);
        assertTrue(answer, "expected " + VERSION_1212 + " to be in range " + RANGE_ALL_VERSIONS);

        answer = VersionUtils.isVersionInRange(VERSION_1213, RANGE_ALL_VERSIONS);
        assertTrue(answer, "expected " + VERSION_1213 + " to be in range " + RANGE_ALL_VERSIONS);

        answer = VersionUtils.isVersionInRange(VERSION_1221, RANGE_ALL_VERSIONS);
        assertTrue(answer, "expected " + VERSION_1221 + " to be in range " + RANGE_ALL_VERSIONS);

        answer = VersionUtils.isVersionInRange(VERSION_12211, RANGE_ALL_VERSIONS);
        assertTrue(answer, "expected " + VERSION_12211 + " to be in range " + RANGE_ALL_VERSIONS);

        answer = VersionUtils.isVersionInRange(VERSION_12212, RANGE_ALL_VERSIONS);
        assertTrue(answer, "expected " + VERSION_12212 + " to be in range " + RANGE_ALL_VERSIONS);

        answer = VersionUtils.isVersionInRange(VERSION_12213, RANGE_ALL_VERSIONS);
        assertTrue(answer, "expected " + VERSION_12213 + " to be in range " + RANGE_ALL_VERSIONS);

        answer = VersionUtils.isVersionInRange(VERSION_1231, RANGE_ALL_VERSIONS);
        assertTrue(answer, "expected " + VERSION_1231 + " to be in range " + RANGE_ALL_VERSIONS);

        answer = VersionUtils.isVersionInRange(VERSION_18, RANGE_ALL_VERSIONS);
        assertTrue(answer, "expected " + VERSION_18 + " to be in range " + RANGE_ALL_VERSIONS);
    }

    @Test
    public void testVersionsInRange1036AndHigher() throws Exception {
        boolean answer = VersionUtils.isVersionInRange(VERSION_1033, RANGE_1036_AND_NEWER);
        assertFalse(answer, "expected " + VERSION_1033 + " to not be in range " + RANGE_1036_AND_NEWER);

        answer = VersionUtils.isVersionInRange(VERSION_1036, RANGE_1036_AND_NEWER);
        assertTrue(answer, "expected " + VERSION_1036 + " to be in range " + RANGE_1036_AND_NEWER);

        answer = VersionUtils.isVersionInRange(VERSION_1211, RANGE_1036_AND_NEWER);
        assertTrue(answer, "expected " + VERSION_1211 + " to be in range " + RANGE_1036_AND_NEWER);

        answer = VersionUtils.isVersionInRange(VERSION_1212, RANGE_1036_AND_NEWER);
        assertTrue(answer, "expected " + VERSION_1212 + " to be in range " + RANGE_1036_AND_NEWER);

        answer = VersionUtils.isVersionInRange(VERSION_1213, RANGE_1036_AND_NEWER);
        assertTrue(answer, "expected " + VERSION_1213 + " to be in range " + RANGE_1036_AND_NEWER);

        answer = VersionUtils.isVersionInRange(VERSION_1221, RANGE_1036_AND_NEWER);
        assertTrue(answer, "expected " + VERSION_1221 + " to be in range " + RANGE_1036_AND_NEWER);

        answer = VersionUtils.isVersionInRange(VERSION_12211, RANGE_1036_AND_NEWER);
        assertTrue(answer, "expected " + VERSION_12211 + " to be in range " + RANGE_1036_AND_NEWER);

        answer = VersionUtils.isVersionInRange(VERSION_12212, RANGE_1036_AND_NEWER);
        assertTrue(answer, "expected " + VERSION_12212 + " to be in range " + RANGE_1036_AND_NEWER);

        answer = VersionUtils.isVersionInRange(VERSION_12213, RANGE_1036_AND_NEWER);
        assertTrue(answer, "expected " + VERSION_12213 + " to be in range " + RANGE_1036_AND_NEWER);

        answer = VersionUtils.isVersionInRange(VERSION_1231, RANGE_1036_AND_NEWER);
        assertTrue(answer, "expected " + VERSION_1231 + " to be in range " + RANGE_1036_AND_NEWER);

        answer = VersionUtils.isVersionInRange(VERSION_18, RANGE_1036_AND_NEWER);
        assertTrue(answer, "expected " + VERSION_18 + " to be in range " + RANGE_1036_AND_NEWER);
    }

    @Test
    public void testVersionsInRangeLessThan1212() throws Exception {
        boolean answer = VersionUtils.isVersionInRange(VERSION_1036, RANGE_LESS_THAN_1212);
        assertTrue(answer, "expected " + VERSION_1036 + " to be in range " + RANGE_LESS_THAN_1212);

        answer = VersionUtils.isVersionInRange(VERSION_1211, RANGE_LESS_THAN_1212);
        assertTrue(answer, "expected " + VERSION_1211 + " to be in range " + RANGE_LESS_THAN_1212);

        answer = VersionUtils.isVersionInRange(VERSION_1212, RANGE_LESS_THAN_1212);
        assertFalse(answer, "expected " + VERSION_1212 + " to not be in range " + RANGE_LESS_THAN_1212);

        answer = VersionUtils.isVersionInRange(VERSION_1213, RANGE_LESS_THAN_1212);
        assertFalse(answer, "expected " + VERSION_1213 + " to not be in range " + RANGE_LESS_THAN_1212);

        answer = VersionUtils.isVersionInRange(VERSION_1221, RANGE_LESS_THAN_1212);
        assertFalse(answer, "expected " + VERSION_1221 + " to not be in range " + RANGE_LESS_THAN_1212);

        answer = VersionUtils.isVersionInRange(VERSION_12211, RANGE_LESS_THAN_1212);
        assertFalse(answer, "expected " + VERSION_12211 + " to not be in range " + RANGE_LESS_THAN_1212);

        answer = VersionUtils.isVersionInRange(VERSION_12212, RANGE_LESS_THAN_1212);
        assertFalse(answer, "expected " + VERSION_12212 + " to not be in range " + RANGE_LESS_THAN_1212);

        answer = VersionUtils.isVersionInRange(VERSION_12213, RANGE_LESS_THAN_1212);
        assertFalse(answer, "expected " + VERSION_12213 + " to not be in range " + RANGE_LESS_THAN_1212);

        answer = VersionUtils.isVersionInRange(VERSION_1231, RANGE_LESS_THAN_1212);
        assertFalse(answer, "expected " + VERSION_1231 + " to not be in range " + RANGE_LESS_THAN_1212);

        answer = VersionUtils.isVersionInRange(VERSION_18, RANGE_LESS_THAN_1212);
        assertFalse(answer, "expected " + VERSION_18 + " to not be in range " + RANGE_LESS_THAN_1212);
    }

    @Test
    public void testVersionsInRangeBetween1212and12213() throws Exception {
        boolean answer = VersionUtils.isVersionInRange(VERSION_1036, RANGE_BETWEEN_1212_AND_12213);
        assertFalse(answer, "expected " + VERSION_1036 + " to not be in range " + RANGE_BETWEEN_1212_AND_12213);

        answer = VersionUtils.isVersionInRange(VERSION_1211, RANGE_BETWEEN_1212_AND_12213);
        assertFalse(answer, "expected " + VERSION_1211 + " to not be in range " + RANGE_BETWEEN_1212_AND_12213);

        answer = VersionUtils.isVersionInRange(VERSION_1212, RANGE_BETWEEN_1212_AND_12213);
        assertTrue(answer, "expected " + VERSION_1212 + " to be in range " + RANGE_BETWEEN_1212_AND_12213);

        answer = VersionUtils.isVersionInRange(VERSION_1213, RANGE_BETWEEN_1212_AND_12213);
        assertTrue(answer, "expected " + VERSION_1213 + " to be in range " + RANGE_BETWEEN_1212_AND_12213);

        answer = VersionUtils.isVersionInRange(VERSION_1221, RANGE_BETWEEN_1212_AND_12213);
        assertTrue(answer, "expected " + VERSION_1221 + " to be in range " + RANGE_BETWEEN_1212_AND_12213);

        answer = VersionUtils.isVersionInRange(VERSION_12211, RANGE_BETWEEN_1212_AND_12213);
        assertTrue(answer, "expected " + VERSION_12211 + " to be in range " + RANGE_BETWEEN_1212_AND_12213);

        answer = VersionUtils.isVersionInRange(VERSION_12212, RANGE_BETWEEN_1212_AND_12213);
        assertTrue(answer, "expected " + VERSION_12212 + " to be in range " + RANGE_BETWEEN_1212_AND_12213);

        answer = VersionUtils.isVersionInRange(VERSION_12213, RANGE_BETWEEN_1212_AND_12213);
        assertTrue(answer, "expected " + VERSION_12213 + " to be in range " + RANGE_BETWEEN_1212_AND_12213);

        answer = VersionUtils.isVersionInRange(VERSION_1231, RANGE_BETWEEN_1212_AND_12213);
        assertFalse(answer, "expected " + VERSION_1231 + " to not be in range " + RANGE_BETWEEN_1212_AND_12213);

        answer = VersionUtils.isVersionInRange(VERSION_18, RANGE_BETWEEN_1212_AND_12213);
        assertFalse(answer, "expected " + VERSION_18 + " to not be in range " + RANGE_BETWEEN_1212_AND_12213);
    }

    @Test
    public void testDoVersionRangesOverlap() throws Exception {
        // single value range, range2 is not adjacent
        checkVersionRange("[12.1.2]", "[12.1.2,12.1.3)", true);

        // obvious overlaps
        checkVersionRange("[12.1.1,12.1.3)", "[12.1.2,12.1.4)", true);
        checkVersionRange("[12.1.2,12.1.4)", "[12.1.1,12.1.3)", true);

        // ranges are adjacent
        checkVersionRange("[12.1.1,12.1.2]", "(12.1.2,12.1.3)", false);
        checkVersionRange("[12.1.2,12.1.3]", "(12.1.1,12.1.2)", false);

        // both ranges have no upper limit
        checkVersionRange("[12.1.1,)", "[12.1.2,)", true);
        checkVersionRange("[12.1.2,)", "[12.1.1,)", true);

        // range1 has no upper limit, but is above range2
        checkVersionRange("[12.1.2,)", "[12.1.1,12.1.2)", false);

        // range2 has no upper limit, and starts below range 1
        checkVersionRange("[12.1.2,12.1.3)", "[12.1.1,)", true);

        // range2 has no upper limit, but is above range1
        checkVersionRange("[12.1.2,12.1.3)", "[12.1.4,)", false);

        // range2 has no upper limit, but is adjacent to range1
        checkVersionRange("[12.1.2,12.1.3)", "[12.1.3,)", false);

        // range2 has no upper limit, and is not adjacent to range1
        checkVersionRange("[12.1.2,12.1.3]", "[12.1.3,)", true);
    }

    @Test
    void testGetWebLogicVersion1213Description() {
        String actual = VersionUtils.getWebLogicVersion(WLS_1213_VERSION_DESCRIPTION);
        assertEquals(WLS_1213_VERSION_RESULT, actual);
    }

    @Test
    void testGetWebLogicVersion12214Description() {
        String actual = VersionUtils.getWebLogicVersion(WLS_12214_VERSION_DESCRIPTION);
        assertEquals(WLS_12214_VERSION_RESULT, actual);
    }

    @Test
    void testPSUExceptionWith8Digits() {
        String actual = VersionUtils.getPSUVersion(PSU_EXCEPTION_8_DIGIT_DESCRIPTION);
        assertEquals(PSU_EXCEPTION_8_DIGIT_RESULT, actual);
    }

    @Test
    void testPSUExceptionWith6Digits() {
        String actual = VersionUtils.getPSUVersion(PSU_EXCEPTION_6_DIGIT_DESCRIPTION);
        assertEquals(PSU_EXCEPTION_6_DIGIT_RESULT, actual);
    }

    @Test
    void testPSUExceptionWithUnknownNumberOfDigits() {
        String actual = VersionUtils.getPSUVersion(PSU_EXCEPTION_UNKNOWN_NUM_DIGITS_DESCRIPTION);
        assertEquals(PSU_EXCEPTION_UNKNOWN_NUM_DIGITS_RESULT, actual);
    }

    @Test
    void testNewPsuFormat() {
        String actual = VersionUtils.getPSUVersion(PSU_NEW_FORMAT_DESCRIPTION);
        assertEquals(PSU_NEW_FORMAT_RESULT, actual);
    }

    @Test
    void testOldPsuFormat() {
        String actual = VersionUtils.getPSUVersion(PSU_OLD_FORMAT_DESCRIPTION);
        assertEquals(PSU_OLD_FORMAT_RESULT, actual);
    }

    @Test
    void testNewPSUList() {
        String actual = VersionUtils.getPSUVersion(PSU_NEW_FORMAT_LIST);
        assertEquals(PSU_NEW_FORMAT_LIST_RESULT, actual);
    }

    private void checkVersionRange(String range1, String range2, boolean expected) throws VersionException {
        assertEquals(expected, VersionUtils.doVersionRangesOverlap(range1, range2),
                "Expected ranges " + range1 + " and " + range2 + " to have overlap = " + expected);
    }
}
