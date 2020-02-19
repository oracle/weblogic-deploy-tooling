/*
 * Copyright (c) 2017, 2020, Oracle Corporation and/or its affiliates.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.yaml;

import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;

import java.io.File;
import java.util.Arrays;
import java.util.List;
import java.util.Map;

public class YamlParserTest {
    private static final boolean DEBUG = System.getProperty("DEBUG") != null;
    private static final File YAML_FILE = new File("src/test/resources/unit-test.yaml").getAbsoluteFile();

    private static final List<String> PATH_TO_GENERIC1 =
        Arrays.asList("resources", "JDBCSystemResource", "Generic1");
    private static final List<String> PATH_TO_GENERIC1_DRIVER_PARAMS =
        Arrays.asList("resources", "JDBCSystemResource", "Generic1", "JdbcResource", "JDBCDriverParams");
    private static final List<String> PATH_TO_GENERIC1_DATASOURCE_PARAMS =
        Arrays.asList("resources", "JDBCSystemResource", "Generic1", "JdbcResource", "JDBCDataSourceParams");
    private static final List<String> PATH_TO_GENERIC2_DRIVER_PARAMS =
        Arrays.asList("resources", "JDBCSystemResource", "Generic2", "JdbcResource", "JDBCDriverParams");
    private static final List<String> PATH_TO_GENERIC2_DATASOURCE_PARAMS =
        Arrays.asList("resources", "JDBCSystemResource", "Generic2", "JdbcResource", "JDBCDataSourceParams");
    private static final List<String> PATH_TO_GENERIC2_CONN_POOL_PARAMS =
        Arrays.asList("resources", "JDBCSystemResource", "Generic2", "JdbcResource", "JDBCConnectionPoolParams");
    private static final List<String> PATH_TO_LISTEN_APP =
        Arrays.asList("appDeployments", "Application", "get-listen-address-app");
    private static final List<String> PATH_TO_MYCLUSTER =
        Arrays.asList("topology", "Cluster", "mycluster");
    private static final List<String> PATH_TO_ADMINSERVER =
        Arrays.asList("topology", "Server", "AdminServer");
    private static final List<String> PATH_TO_S1 =
        Arrays.asList("topology", "Server", "s1");
    private static final List<String> PATH_TO_S2 =
        Arrays.asList("topology", "Server", "s2");

    private static final List<String> EXPECTED_TOP_LEVEL_KEYS =
        Arrays.asList("domainInfo", "topology", "resources", "appDeployments");
    private static final String EXPECTED_GENERIC1_URL =
        "jdbc:oracle:thin:@(DESCRIPTION=(ADDRESS_LIST=(ADDRESS=(PROTOCOL=TCP)(HOST=slc05til.us.oracle.com)" +
            "(PORT=1521)))(CONNECT_DATA=(SERVICE_NAME=orcl.us.oracle.com)))";
    private static final String EXPECTED_GENERIC2_URL = "jdbc:oracle:thin:@//den00chv.us.oracle.com:1521/PDBORCL";
    private static final String EXPECTED_LISTEN_APP_SOURCE_PATH = "wlsdeploy/apps/get-listen-address-app.war";

    private static final int EXPECTED_GENERIC2_MAX_CAPACITY = 15;
    private static final String EXPECTED_GENERIC2_TEST_TABLE_NAME = "SQL ISVALID";
    private static final String EXPECTED_GENERIC2_TEST_CONNS_ON_RESERVE = "True";

    private static final List<String> EXPECTED_GENERIC1_JNDI_NAMES = Arrays.asList("jdbc/generic1", "jdbc/special1");
    private static final List<String> EXPECTED_GENERIC2_JNDI_NAMES = Arrays.asList("jdbc/generic2", "jdbc/special2");
    private static final List<String> EXPECTED_GENERIC1_TARGETS = Arrays.asList("mycluster", "AdminServer");

    private static final String EXPECTED_ADMIN_SERVER_LISTEN_ADDRESS = "127.0.0.1";
    private static final int EXPECTED_ADMIN_SERVER_LISTEN_PORT = 7001;

    private static final String EXPECTED_S1_LISTEN_ADDRESS = "127.0.0.1";
    private static final int EXPECTED_S1_LISTEN_PORT = 8001;
    private static final String EXPECTED_S1_CLUSTER = "mycluster";

    private static final String EXPECTED_S2_LISTEN_ADDRESS = "127.0.0.1";
    private static final int EXPECTED_S2_LISTEN_PORT = 8101;
    private static final String EXPECTED_S2_CLUSTER = "mycluster";

    private YamlJavaTranslator translator;
    private Map<String, Object> fileDict;

    @Before
    public void init() throws Exception {
        this.translator = new YamlJavaTranslator(YAML_FILE.getPath());
        fileDict = translator.parse();

        if (DEBUG) {
            System.err.println("fileDict = " + fileDict.toString());
        }
    }

    @Test
    public void ensureStackIsEmpty() throws Exception {
        translator.checkForParseErrors();
        translator.ensureStackIsEmpty();
    }

    @Test
    public void testTopLevelFolders() throws Exception {
        translator.checkForParseErrors();

        for (String key : fileDict.keySet()) {
            Assert.assertTrue("Unexpected key (" + key + ") in fileDict", EXPECTED_TOP_LEVEL_KEYS.contains(key));
        }
    }

    @Test
    public void testSingleQuotedStrings() throws Exception {
        translator.checkForParseErrors();

        Map<String, Object> map = fileDict;
        for (String key : PATH_TO_GENERIC1_DRIVER_PARAMS) {
            map = getMap(map, key);
            Assert.assertNotNull("Generic1 path key (" + key +") not found", map);
        }
        String url = (String)map.get("URL");
        Assert.assertNotNull("Generic1 URL not found", url);
        Assert.assertEquals("Generic1 URL does not match expected value of " + EXPECTED_GENERIC1_URL,
            EXPECTED_GENERIC1_URL, url );

        map = fileDict;
        for (String key : PATH_TO_GENERIC2_DRIVER_PARAMS) {
            map = getMap(map, key);
            Assert.assertNotNull("Generic2 path key (" + key +") not found", map);
        }
        url = (String)map.get("URL");
        Assert.assertNotNull("Generic2 URL not found", url);
        Assert.assertEquals("Generic2 URL does not match expected value of " + EXPECTED_GENERIC2_URL,
            EXPECTED_GENERIC2_URL, url );

        map = fileDict;
        for (String key : PATH_TO_LISTEN_APP) {
            map = getMap(map, key);
            Assert.assertNotNull("get-listen-address-app path key (" + key +") not found", map);
        }
        String sourcePath = (String)map.get("SourcePath");
        Assert.assertNotNull("get-listen-address-app SourcePath not found", url);
        Assert.assertEquals("get-listen-address-app SourcePath does not match expected value of " +
                EXPECTED_LISTEN_APP_SOURCE_PATH, EXPECTED_LISTEN_APP_SOURCE_PATH, sourcePath);
    }

    @Test
    public void testEndOfLineComments() throws Exception {
        translator.checkForParseErrors();

        Map<String, Object> map = fileDict;
        for (String key : PATH_TO_GENERIC2_CONN_POOL_PARAMS) {
            map = getMap(map, key);
            Assert.assertNotNull("Generic2 path key (" + key +") not found", map);
        }
        String testConnectionsOnReserve = (String)map.get("TestConnectionsOnReserve");
        Assert.assertNotNull("Generic2 TestConnectionsOnReserve not found", testConnectionsOnReserve);
        Assert.assertEquals("Generic2 TestConnectionsOnReserve does not match expected value of " +
                EXPECTED_GENERIC2_TEST_CONNS_ON_RESERVE, EXPECTED_GENERIC2_TEST_CONNS_ON_RESERVE,
            testConnectionsOnReserve);

        Integer maxCapacity = (Integer)map.get("MaxCapacity");
        Assert.assertNotNull("Generic2 MaxCapacity not found", maxCapacity);
        Assert.assertEquals("Generic2 MaxCapacity does not match expected value of " + EXPECTED_GENERIC2_MAX_CAPACITY,
            (long)EXPECTED_GENERIC2_MAX_CAPACITY, (long)maxCapacity);

    }

    @Test
    public void testUnquotedStringWithWhitespace() throws Exception {
        translator.checkForParseErrors();

        Map<String, Object> map = fileDict;
        for (String key : PATH_TO_GENERIC2_CONN_POOL_PARAMS) {
            map = getMap(map, key);
            Assert.assertNotNull("Generic2 path key (" + key +") not found", map);
        }
        String testTableName = (String)map.get("TestTableName");
        Assert.assertNotNull("Generic2 TestTableName not found", testTableName);
        Assert.assertEquals("Generic2 TestTableName does not match expected value of " +
                EXPECTED_GENERIC2_TEST_TABLE_NAME, EXPECTED_GENERIC2_TEST_TABLE_NAME, testTableName);
    }

    @Test
    public void testInlineSingleLineList() throws Exception {
        translator.checkForParseErrors();

        Map<String, Object> map = fileDict;
        for (String key : PATH_TO_GENERIC1_DATASOURCE_PARAMS) {
            map = getMap(map, key);
            Assert.assertNotNull("Generic1 path key (" + key +") not found", map);
        }

        @SuppressWarnings("unchecked")
        List<String> jndiNames = (List<String>)map.get("JNDIName");

        Assert.assertNotNull("Generic1 JNDIName list was null", jndiNames);
        Assert.assertEquals("Generic1 JNDINames list was not the expected length", 2, jndiNames.size());
        for (String name : EXPECTED_GENERIC1_JNDI_NAMES) {
            Assert.assertTrue(name + " not found in Generic1 JNDIName list", jndiNames.contains(name));
        }
    }

    @Test
    public void testInlineMultiLineList() throws Exception {
        translator.checkForParseErrors();

        Map<String, Object> map = fileDict;
        for (String key : PATH_TO_GENERIC2_DATASOURCE_PARAMS) {
            map = getMap(map, key);
            Assert.assertNotNull("Generic2 path key (" + key +") not found", map);
        }

        @SuppressWarnings("unchecked")
        List<String> jndiNames = (List<String>)map.get("JNDIName");

        Assert.assertNotNull("Generic2 JNDIName list was null", jndiNames);
        Assert.assertEquals("Generic2 JNDINames list was not the expected length", 2, jndiNames.size());
        for (String name : EXPECTED_GENERIC2_JNDI_NAMES) {
            Assert.assertTrue(name + " not found in Generic2 JNDIName list", jndiNames.contains(name));
        }
    }

    @Test
    public void testYamlStyleList() throws Exception {
        translator.checkForParseErrors();

        Map<String, Object> map = fileDict;
        for (String key : PATH_TO_GENERIC1) {
            map = getMap(map, key);
            Assert.assertNotNull("Generic1 path key (" + key +") not found", map);
        }

        @SuppressWarnings("unchecked")
        List<String> targets = (List<String>)map.get("Target");

        Assert.assertNotNull("Generic1 Target list was null", targets);
        Assert.assertEquals("Generic1 Target list was not the expected length", 2, targets.size());
        for (String name : EXPECTED_GENERIC1_TARGETS) {
            Assert.assertTrue(name + " not found in Generic1 Target list", targets.contains(name));
        }
    }

    @Test
    public void testEmptyObject() throws Exception {
        translator.checkForParseErrors();

        Map<String, Object> map = fileDict;
        for (String key : PATH_TO_MYCLUSTER) {
            map = getMap(map, key);
            Assert.assertNotNull("mycluster path key (" + key +") not found", map);
        }
        Assert.assertEquals("mycluster map should be empty", 0, map.size());

        // Check the next object for accuracy...
        //
        map = fileDict;
        for (String key : PATH_TO_ADMINSERVER) {
            map = getMap(map, key);
            Assert.assertNotNull("AdminServer path key (" + key +") not found", map);
        }

        String listenAddress = (String)map.get("ListenAddress");
        int listenPort = (int)map.get("ListenPort");

        Assert.assertNotNull("AdminServer ListenAddress should not be null", listenAddress);
        Assert.assertEquals("AdminServer ListenAddress not correct",
            EXPECTED_ADMIN_SERVER_LISTEN_ADDRESS, listenAddress);
        Assert.assertEquals("AdminServer ListenPort not correct", EXPECTED_ADMIN_SERVER_LISTEN_PORT, listenPort);

        map = fileDict;
        for (String key : PATH_TO_S1) {
            map = getMap(map, key);
            Assert.assertNotNull("S1 path key (" + key +") not found", map);
        }

        String s1ListenAddress = (String)map.get("ListenAddress");
        int s1ListenPort = (int)map.get("ListenPort");
        String cluster = (String)map.get("Cluster");

        Assert.assertNotNull("S1 ListenAddress should not be null", s1ListenAddress);
        Assert.assertEquals("S1 ListenAddress not correct", EXPECTED_S1_LISTEN_ADDRESS, s1ListenAddress);
        Assert.assertEquals("S1 ListenPort not correct", EXPECTED_S1_LISTEN_PORT, s1ListenPort);
        Assert.assertNotNull("S1 Cluster should not be null", cluster);
        Assert.assertEquals("S1 Cluster not correct", EXPECTED_S1_CLUSTER, cluster);

        map = fileDict;
        for (String key : PATH_TO_S2) {
            map = getMap(map, key);
            Assert.assertNotNull("S2 path key (" + key +") not found", map);
        }

        String s2ListenAddress = (String)map.get("ListenAddress");
        int s2ListenPort = (int)map.get("ListenPort");
        String s2Cluster = (String)map.get("Cluster");

        Assert.assertNotNull("S2 ListenAddress should not be null", s2ListenAddress);
        Assert.assertEquals("S2 ListenAddress not correct", EXPECTED_S2_LISTEN_ADDRESS, s2ListenAddress);
        Assert.assertEquals("S2 ListenPort not correct", EXPECTED_S2_LISTEN_PORT, s2ListenPort);
        Assert.assertNotNull("S2 Cluster should not be null", s2Cluster);
        Assert.assertEquals("S2 Cluster not correct", EXPECTED_S2_CLUSTER, s2Cluster);
    }

    @Test
    public void testEmptyStringKey() {
        Map<String, Object> topology = getMap(fileDict, "topology");
        Assert.assertNotNull("Failed to get topology from yaml", topology);

        Map<String, Object> servers = getMap(topology, "Server");
        Assert.assertNotNull("Failed to get topology/Server from yaml", servers);

        Map<String, Object> adminServer = getMap(servers, "AdminServer");
        Assert.assertNotNull("Failed to get topology/Server/AdminServer from yaml", adminServer);

        Map<String, Object> log = getMap(adminServer, "Log");
        Assert.assertNotNull("Failed to get Log in AdminServer from yaml", adminServer);

        Map<String, Object> properties = getMap(log, "LoggerSeverityProperties");
        Assert.assertEquals("Size of logging properties", 3, properties.size());
        Assert.assertTrue("Could not find empty string key in properties", properties.containsKey(""));
    }
    ///////////////////////////////////////////////////////////////////////////
    //                            End of tests                               //
    ///////////////////////////////////////////////////////////////////////////

    @SuppressWarnings("unchecked")
    private Map<String, Object> getMap(Map<String, Object> container, String key) {
        return (Map<String, Object>) container.get(key);
    }
}
