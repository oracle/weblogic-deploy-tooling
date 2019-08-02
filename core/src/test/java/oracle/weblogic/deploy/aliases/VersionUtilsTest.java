/*
 * Copyright (c) 2017, 2019, Oracle and/or its affiliates. All rights reserved.
 * Licensed under the Universal Permissive License v 1.0 as shown at http://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.aliases;

import org.junit.Assert;
import org.junit.Test;

public class VersionUtilsTest {
    private static final String VERSION_1033 = "10.3.3.0";
    private static final String VERSION_1034 = "10.3.4.0";
    private static final String VERSION_1035 = "10.3.5.0";
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
    private static final String RANGE_1034_AND_NEWER = "[10.3.4,)";
    private static final String RANGE_LESS_THAN_1212 = "[10,12.1.2)";
    private static final String RANGE_BETWEEN_1212_AND_12213 = "(12.1.1,12.2.1.3]";

    @Test
    public void testClientGreaterThanServer() throws Exception {
        String clientVersion = "0.7.4";
        String serverVersion = "0.7.3";
        Assert.assertTrue("Expected client " + clientVersion + " to be newer than server " + serverVersion,
                          VersionUtils.compareVersions(clientVersion, serverVersion) > 0);

        clientVersion = "0.8";
        serverVersion = "0.7.4";
        Assert.assertTrue("Expected client " + clientVersion + " to be newer than server " + serverVersion,
            VersionUtils.compareVersions(clientVersion, serverVersion) > 0);

        clientVersion = "1.2.3";
        serverVersion = "1.2";
        Assert.assertTrue("Expected client " + clientVersion + " to be newer than server " + serverVersion,
            VersionUtils.compareVersions(clientVersion, serverVersion) > 0);

        clientVersion = "1.2.3";
        serverVersion = "1.2.3-SNAPSHOT";
        Assert.assertTrue("Expected client " + clientVersion + " to be newer than server " + serverVersion,
            VersionUtils.compareVersions(clientVersion, serverVersion) > 0);

        clientVersion = "1.2.3-BETA1";
        serverVersion = "1.2.3-ALPHA3";
        Assert.assertTrue("Expected client " + clientVersion + " to be newer than server " + serverVersion,
            VersionUtils.compareVersions(clientVersion, serverVersion) > 0);

        clientVersion = "1.2.3-SNAPSHOT";
        serverVersion = "1.2.2";
        Assert.assertTrue("Expected client " + clientVersion + " to be newer than server " + serverVersion,
            VersionUtils.compareVersions(clientVersion, serverVersion) > 0);
    }

    @Test
    public void testServerGreaterThanClient() throws Exception {
        String clientVersion = "0.7.3";
        String serverVersion = "0.7.4";
        Assert.assertTrue("Expected server " + serverVersion + " to be newer than client " + clientVersion,
            VersionUtils.compareVersions(clientVersion, serverVersion) < 0);

        clientVersion = "0.7.4";
        serverVersion = "1";
        Assert.assertTrue("Expected server " + serverVersion + " to be newer than client " + clientVersion,
            VersionUtils.compareVersions(clientVersion, serverVersion) < 0);

        clientVersion = "1.2";
        serverVersion = "1.2.3";
        Assert.assertTrue("Expected server " + serverVersion + " to be newer than client " + clientVersion,
            VersionUtils.compareVersions(clientVersion, serverVersion) < 0);

        clientVersion = "1.2.3-SNAPSHOT";
        serverVersion = "1.2.3";
        Assert.assertTrue("Expected server " + serverVersion + " to be newer than client " + clientVersion,
            VersionUtils.compareVersions(clientVersion, serverVersion) < 0);

        clientVersion = "1.2.3-ALPHA4";
        serverVersion = "1.2.3-ALPHA5";
        Assert.assertTrue("Expected server " + serverVersion + " to be newer than client " + clientVersion,
            VersionUtils.compareVersions(clientVersion, serverVersion) < 0);

        clientVersion = "1.2.1";
        serverVersion = "1.2.2-SNAPSHOT";
        Assert.assertTrue("Expected server " + serverVersion + " to be newer than client " + clientVersion,
            VersionUtils.compareVersions(clientVersion, serverVersion) < 0);
    }

    @Test
    public void testServerToEqualClient() throws Exception {
        String clientVersion = "0.7.4";
        String serverVersion = "0.7.4";
        Assert.assertTrue("Expected server " + serverVersion + " to be the same as client " + clientVersion,
            VersionUtils.compareVersions(clientVersion, serverVersion) == 0);

        clientVersion = "1";
        serverVersion = "1";
        Assert.assertTrue("Expected server " + serverVersion + " to be the same as client " + clientVersion,
            VersionUtils.compareVersions(clientVersion, serverVersion) == 0);

        clientVersion = "1.2.3-ALPHA1";
        serverVersion = "1.2.3-ALPHA1";
        Assert.assertTrue("Expected server " + serverVersion + " to be the same as client " + clientVersion,
            VersionUtils.compareVersions(clientVersion, serverVersion) == 0);

        clientVersion = "1.2.3.4.5.6.7.8.9";
        serverVersion = "1.2.3.4.5.6.7.8.9";
        Assert.assertTrue("Expected server " + serverVersion + " to be the same as client " + clientVersion,
            VersionUtils.compareVersions(clientVersion, serverVersion) == 0);

        clientVersion = "0.7.4-SNAPSHOT";
        serverVersion = "0.7.4-SNAPSHOT";
        Assert.assertTrue("Expected server " + serverVersion + " to be the same as client " + clientVersion,
            VersionUtils.compareVersions(clientVersion, serverVersion) == 0);
    }


    @Test
    public void testVersionsInRangeAll() throws Exception {
        boolean answer = VersionUtils.isVersionInRange(VERSION_1033, RANGE_ALL_VERSIONS);
        Assert.assertTrue("expected " + VERSION_1033 + " to be in range " + RANGE_ALL_VERSIONS, answer);

        answer = VersionUtils.isVersionInRange(VERSION_1034, RANGE_ALL_VERSIONS);
        Assert.assertTrue("expected " + VERSION_1034 + " to be in range " + RANGE_ALL_VERSIONS, answer);

        answer = VersionUtils.isVersionInRange(VERSION_1035, RANGE_ALL_VERSIONS);
        Assert.assertTrue("expected " + VERSION_1035 + " to be in range " + RANGE_ALL_VERSIONS, answer);

        answer = VersionUtils.isVersionInRange(VERSION_1036, RANGE_ALL_VERSIONS);
        Assert.assertTrue("expected " + VERSION_1036 + " to be in range " + RANGE_ALL_VERSIONS, answer);

        answer = VersionUtils.isVersionInRange(VERSION_1211, RANGE_ALL_VERSIONS);
        Assert.assertTrue("expected " + VERSION_1211 + " to be in range " + RANGE_ALL_VERSIONS, answer);

        answer = VersionUtils.isVersionInRange(VERSION_1212, RANGE_ALL_VERSIONS);
        Assert.assertTrue("expected " + VERSION_1212 + " to be in range " + RANGE_ALL_VERSIONS, answer);

        answer = VersionUtils.isVersionInRange(VERSION_1213, RANGE_ALL_VERSIONS);
        Assert.assertTrue("expected " + VERSION_1213 + " to be in range " + RANGE_ALL_VERSIONS, answer);

        answer = VersionUtils.isVersionInRange(VERSION_1221, RANGE_ALL_VERSIONS);
        Assert.assertTrue("expected " + VERSION_1221 + " to be in range " + RANGE_ALL_VERSIONS, answer);

        answer = VersionUtils.isVersionInRange(VERSION_12211, RANGE_ALL_VERSIONS);
        Assert.assertTrue("expected " + VERSION_12211 + " to be in range " + RANGE_ALL_VERSIONS, answer);

        answer = VersionUtils.isVersionInRange(VERSION_12212, RANGE_ALL_VERSIONS);
        Assert.assertTrue("expected " + VERSION_12212 + " to be in range " + RANGE_ALL_VERSIONS, answer);

        answer = VersionUtils.isVersionInRange(VERSION_12213, RANGE_ALL_VERSIONS);
        Assert.assertTrue("expected " + VERSION_12213 + " to be in range " + RANGE_ALL_VERSIONS, answer);

        answer = VersionUtils.isVersionInRange(VERSION_1231, RANGE_ALL_VERSIONS);
        Assert.assertTrue("expected " + VERSION_1231 + " to be in range " + RANGE_ALL_VERSIONS, answer);

        answer = VersionUtils.isVersionInRange(VERSION_18, RANGE_ALL_VERSIONS);
        Assert.assertTrue("expected " + VERSION_18 + " to be in range " + RANGE_ALL_VERSIONS, answer);
    }

    @Test
    public void testVersionsInRange1034AndHigher() throws Exception {
        boolean answer = VersionUtils.isVersionInRange(VERSION_1033, RANGE_1034_AND_NEWER);
        Assert.assertFalse("expected " + VERSION_1033 + " to not be in range " + RANGE_1034_AND_NEWER, answer);

        answer = VersionUtils.isVersionInRange(VERSION_1034, RANGE_1034_AND_NEWER);
        Assert.assertTrue("expected " + VERSION_1034 + " to be in range " + RANGE_1034_AND_NEWER, answer);

        answer = VersionUtils.isVersionInRange(VERSION_1035, RANGE_1034_AND_NEWER);
        Assert.assertTrue("expected " + VERSION_1035 + " to be in range " + RANGE_1034_AND_NEWER, answer);

        answer = VersionUtils.isVersionInRange(VERSION_1036, RANGE_1034_AND_NEWER);
        Assert.assertTrue("expected " + VERSION_1036 + " to be in range " + RANGE_1034_AND_NEWER, answer);

        answer = VersionUtils.isVersionInRange(VERSION_1211, RANGE_1034_AND_NEWER);
        Assert.assertTrue("expected " + VERSION_1211 + " to be in range " + RANGE_1034_AND_NEWER, answer);

        answer = VersionUtils.isVersionInRange(VERSION_1212, RANGE_1034_AND_NEWER);
        Assert.assertTrue("expected " + VERSION_1212 + " to be in range " + RANGE_1034_AND_NEWER, answer);

        answer = VersionUtils.isVersionInRange(VERSION_1213, RANGE_1034_AND_NEWER);
        Assert.assertTrue("expected " + VERSION_1213 + " to be in range " + RANGE_1034_AND_NEWER, answer);

        answer = VersionUtils.isVersionInRange(VERSION_1221, RANGE_1034_AND_NEWER);
        Assert.assertTrue("expected " + VERSION_1221 + " to be in range " + RANGE_1034_AND_NEWER, answer);

        answer = VersionUtils.isVersionInRange(VERSION_12211, RANGE_1034_AND_NEWER);
        Assert.assertTrue("expected " + VERSION_12211 + " to be in range " + RANGE_1034_AND_NEWER, answer);

        answer = VersionUtils.isVersionInRange(VERSION_12212, RANGE_1034_AND_NEWER);
        Assert.assertTrue("expected " + VERSION_12212 + " to be in range " + RANGE_1034_AND_NEWER, answer);

        answer = VersionUtils.isVersionInRange(VERSION_12213, RANGE_1034_AND_NEWER);
        Assert.assertTrue("expected " + VERSION_12213 + " to be in range " + RANGE_1034_AND_NEWER, answer);

        answer = VersionUtils.isVersionInRange(VERSION_1231, RANGE_1034_AND_NEWER);
        Assert.assertTrue("expected " + VERSION_1231 + " to be in range " + RANGE_1034_AND_NEWER, answer);

        answer = VersionUtils.isVersionInRange(VERSION_18, RANGE_1034_AND_NEWER);
        Assert.assertTrue("expected " + VERSION_18 + " to be in range " + RANGE_1034_AND_NEWER, answer);
    }

    @Test
    public void testVersionsInRangeLessThan1212() throws Exception {
        boolean answer = VersionUtils.isVersionInRange(VERSION_1033, RANGE_LESS_THAN_1212);
        Assert.assertTrue("expected " + VERSION_1033 + " to be in range " + RANGE_LESS_THAN_1212, answer);

        answer = VersionUtils.isVersionInRange(VERSION_1034, RANGE_LESS_THAN_1212);
        Assert.assertTrue("expected " + VERSION_1034 + " to be in range " + RANGE_LESS_THAN_1212, answer);

        answer = VersionUtils.isVersionInRange(VERSION_1035, RANGE_LESS_THAN_1212);
        Assert.assertTrue("expected " + VERSION_1035 + " to be in range " + RANGE_LESS_THAN_1212, answer);

        answer = VersionUtils.isVersionInRange(VERSION_1036, RANGE_LESS_THAN_1212);
        Assert.assertTrue("expected " + VERSION_1036 + " to be in range " + RANGE_LESS_THAN_1212, answer);

        answer = VersionUtils.isVersionInRange(VERSION_1211, RANGE_LESS_THAN_1212);
        Assert.assertTrue("expected " + VERSION_1211 + " to be in range " + RANGE_LESS_THAN_1212, answer);

        answer = VersionUtils.isVersionInRange(VERSION_1212, RANGE_LESS_THAN_1212);
        Assert.assertFalse("expected " + VERSION_1212 + " to not be in range " + RANGE_LESS_THAN_1212, answer);

        answer = VersionUtils.isVersionInRange(VERSION_1213, RANGE_LESS_THAN_1212);
        Assert.assertFalse("expected " + VERSION_1213 + " to not be in range " + RANGE_LESS_THAN_1212, answer);

        answer = VersionUtils.isVersionInRange(VERSION_1221, RANGE_LESS_THAN_1212);
        Assert.assertFalse("expected " + VERSION_1221 + " to not be in range " + RANGE_LESS_THAN_1212, answer);

        answer = VersionUtils.isVersionInRange(VERSION_12211, RANGE_LESS_THAN_1212);
        Assert.assertFalse("expected " + VERSION_12211 + " to not be in range " + RANGE_LESS_THAN_1212, answer);

        answer = VersionUtils.isVersionInRange(VERSION_12212, RANGE_LESS_THAN_1212);
        Assert.assertFalse("expected " + VERSION_12212 + " to not be in range " + RANGE_LESS_THAN_1212, answer);

        answer = VersionUtils.isVersionInRange(VERSION_12213, RANGE_LESS_THAN_1212);
        Assert.assertFalse("expected " + VERSION_12213 + " to not be in range " + RANGE_LESS_THAN_1212, answer);

        answer = VersionUtils.isVersionInRange(VERSION_1231, RANGE_LESS_THAN_1212);
        Assert.assertFalse("expected " + VERSION_1231 + " to not be in range " + RANGE_LESS_THAN_1212, answer);

        answer = VersionUtils.isVersionInRange(VERSION_18, RANGE_LESS_THAN_1212);
        Assert.assertFalse("expected " + VERSION_18 + " to not be in range " + RANGE_LESS_THAN_1212, answer);
    }

    @Test
    public void testVersionsInRangeBetween1212and12213() throws Exception {
        boolean answer = VersionUtils.isVersionInRange(VERSION_1033, RANGE_BETWEEN_1212_AND_12213);
        Assert.assertFalse("expected " + VERSION_1033 + " to not be in range " + RANGE_BETWEEN_1212_AND_12213, answer);

        answer = VersionUtils.isVersionInRange(VERSION_1034, RANGE_BETWEEN_1212_AND_12213);
        Assert.assertFalse("expected " + VERSION_1034 + " to not be in range " + RANGE_BETWEEN_1212_AND_12213, answer);

        answer = VersionUtils.isVersionInRange(VERSION_1035, RANGE_BETWEEN_1212_AND_12213);
        Assert.assertFalse("expected " + VERSION_1035 + " to not be in range " + RANGE_BETWEEN_1212_AND_12213, answer);

        answer = VersionUtils.isVersionInRange(VERSION_1036, RANGE_BETWEEN_1212_AND_12213);
        Assert.assertFalse("expected " + VERSION_1036 + " to not be in range " + RANGE_BETWEEN_1212_AND_12213, answer);

        answer = VersionUtils.isVersionInRange(VERSION_1211, RANGE_BETWEEN_1212_AND_12213);
        Assert.assertFalse("expected " + VERSION_1211 + " to not be in range " + RANGE_BETWEEN_1212_AND_12213, answer);

        answer = VersionUtils.isVersionInRange(VERSION_1212, RANGE_BETWEEN_1212_AND_12213);
        Assert.assertTrue("expected " + VERSION_1212 + " to be in range " + RANGE_BETWEEN_1212_AND_12213, answer);

        answer = VersionUtils.isVersionInRange(VERSION_1213, RANGE_BETWEEN_1212_AND_12213);
        Assert.assertTrue("expected " + VERSION_1213 + " to be in range " + RANGE_BETWEEN_1212_AND_12213, answer);

        answer = VersionUtils.isVersionInRange(VERSION_1221, RANGE_BETWEEN_1212_AND_12213);
        Assert.assertTrue("expected " + VERSION_1221 + " to be in range " + RANGE_BETWEEN_1212_AND_12213, answer);

        answer = VersionUtils.isVersionInRange(VERSION_12211, RANGE_BETWEEN_1212_AND_12213);
        Assert.assertTrue("expected " + VERSION_12211 + " to be in range " + RANGE_BETWEEN_1212_AND_12213, answer);

        answer = VersionUtils.isVersionInRange(VERSION_12212, RANGE_BETWEEN_1212_AND_12213);
        Assert.assertTrue("expected " + VERSION_12212 + " to be in range " + RANGE_BETWEEN_1212_AND_12213, answer);

        answer = VersionUtils.isVersionInRange(VERSION_12213, RANGE_BETWEEN_1212_AND_12213);
        Assert.assertTrue("expected " + VERSION_12213 + " to be in range " + RANGE_BETWEEN_1212_AND_12213, answer);

        answer = VersionUtils.isVersionInRange(VERSION_1231, RANGE_BETWEEN_1212_AND_12213);
        Assert.assertFalse("expected " + VERSION_1231 + " to not be in range " + RANGE_BETWEEN_1212_AND_12213, answer);

        answer = VersionUtils.isVersionInRange(VERSION_18, RANGE_BETWEEN_1212_AND_12213);
        Assert.assertFalse("expected " + VERSION_18 + " to not be in range " + RANGE_BETWEEN_1212_AND_12213, answer);
    }
}
