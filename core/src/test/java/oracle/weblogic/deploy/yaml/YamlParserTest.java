/*
 * Copyright (c) 2017, 2019, Oracle and/or its affiliates. All rights reserved.
 * Licensed under the Universal Permissive License v 1.0 as shown at http://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.yaml;

import java.io.File;
import java.io.FileInputStream;
import java.text.MessageFormat;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Stack;

import oracle.weblogic.deploy.util.StringUtils;

import org.antlr.v4.runtime.CharStream;
import org.antlr.v4.runtime.CharStreams;
import org.antlr.v4.runtime.CommonTokenStream;
import org.antlr.v4.runtime.atn.PredictionMode;
import org.antlr.v4.runtime.tree.ParseTree;
import org.antlr.v4.runtime.tree.ParseTreeWalker;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;

public class YamlParserTest extends YamlBaseListener {
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

    private Map<String, Object> fileDict;
    private Stack<Map<String, Object>> currentDict;

    private String lastObjectName;
    private List<Object> openObjectList;

    private YamlErrorListener errorListener = new YamlErrorListener(YAML_FILE.getPath(), false);

    @Before
    public void init() throws Exception {
        try (FileInputStream fis = new FileInputStream(YAML_FILE)) {
            CharStream input = CharStreams.fromStream(fis);
            YamlLexer lexer = new YamlLexer(input);
            CommonTokenStream tokens = new CommonTokenStream(lexer);
            YamlParser parser = new YamlParser(tokens);

            parser.removeErrorListeners();
            parser.addErrorListener(errorListener);
            parser.getInterpreter().setPredictionMode(PredictionMode.LL_EXACT_AMBIG_DETECTION);

            ParseTree tree = parser.file();
            ParseTreeWalker walker = new ParseTreeWalker();
            walker.walk(this, tree);
        }
        if (DEBUG) {
            System.out.println("fileDict = " + fileDict.toString());
        }
    }

    @Test
    public void ensureStackIsEmpty() throws Exception {
        checkForParseErrors();

        Assert.assertTrue("currentDict stack is not empty", currentDict.isEmpty());
    }

    @Test
    public void testTopLevelFolders() throws Exception {
        checkForParseErrors();

        for (String key : fileDict.keySet()) {
            Assert.assertTrue("Unexpected key (" + key + ") in fileDict", EXPECTED_TOP_LEVEL_KEYS.contains(key));
        }
    }

    @Test
    public void testSingleQuotedStrings() throws Exception {
        checkForParseErrors();

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
        checkForParseErrors();

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
        checkForParseErrors();

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
        checkForParseErrors();

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
        checkForParseErrors();

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
        checkForParseErrors();

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
        checkForParseErrors();

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

        @SuppressWarnings("unchecked")
        String listenAddress = (String)map.get("ListenAddress");
        @SuppressWarnings("unchecked")
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

        @SuppressWarnings("unchecked")
        String s1ListenAddress = (String)map.get("ListenAddress");
        @SuppressWarnings("unchecked")
        int s1ListenPort = (int)map.get("ListenPort");
        @SuppressWarnings("unchecked")
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

        @SuppressWarnings("unchecked")
        String s2ListenAddress = (String)map.get("ListenAddress");
        @SuppressWarnings("unchecked")
        int s2ListenPort = (int)map.get("ListenPort");
        @SuppressWarnings("unchecked")
        String s2Cluster = (String)map.get("Cluster");

        Assert.assertNotNull("S2 ListenAddress should not be null", s2ListenAddress);
        Assert.assertEquals("S2 ListenAddress not correct", EXPECTED_S2_LISTEN_ADDRESS, s2ListenAddress);
        Assert.assertEquals("S2 ListenPort not correct", EXPECTED_S2_LISTEN_PORT, s2ListenPort);
        Assert.assertNotNull("S2 Cluster should not be null", s2Cluster);
        Assert.assertEquals("S2 Cluster not correct", EXPECTED_S2_CLUSTER, s2Cluster);
    }

    ///////////////////////////////////////////////////////////////////////////
    //                            End of tests                               //
    ///////////////////////////////////////////////////////////////////////////

    @Override
    public void enterFile(YamlParser.FileContext ctx) {
        this.fileDict = new HashMap<>();
        currentDict = new Stack<>();
        currentDict.push(fileDict);
    }

    @Override
    public void enterAssign(YamlParser.AssignContext ctx) {
        String name = getAssignName(ctx);
        Object value = getAssignValue(name, ctx);

        Map<String, Object> container = currentDict.peek();
        container.put(name, value);
    }

    @Override
    public void enterYamlListItemAssign(YamlParser.YamlListItemAssignContext ctx) {
        YamlParser.AssignContext assignCtx = ctx.assign();

        // The only type of list item we treat differently is a list of values.
        enterAssign(assignCtx);
    }

    /**
     * {@inheritDoc}
     */
    @Override
    public void enterYamlListItemValue(YamlParser.YamlListItemValueContext ctx) {
        YamlParser.ValueContext valueCtx = ctx.value();

        List<Object> myList = getOpenObjectList();
        String madeUpName = MessageFormat.format("{0}[{1}]", lastObjectName, myList.size());
        Object value = getScalarValue(madeUpName, valueCtx);
        myList.add(value);
    }

    /**
     * {@inheritDoc}
     */
    @Override
    public void enterYamlListItemObject(YamlParser.YamlListItemObjectContext ctx) {
        YamlParser.ObjectContext objCtx = ctx.object();

        // The only type of list item we treat differently is a list of values.
        enterObject(objCtx);
    }

    @Override
    public void enterObject(YamlParser.ObjectContext ctx) {
        String name = StringUtils.stripQuotes(ctx.name().getText());
        Map<String, Object> objDict = new HashMap<>();

        Map<String, Object> container = currentDict.peek();
        container.put(name, objDict);
        currentDict.push(objDict);

        // In case this is the name for a list of values, save it off...
        lastObjectName = name;
    }

    @Override
    public void exitObj_block(YamlParser.Obj_blockContext ctx) {
        if (openObjectList != null) {
            // Pop off the dictionary that is created by default for all new objects off the current stack
            currentDict.pop();

            Map<String, Object> container = currentDict.peek();
            container.put(lastObjectName, openObjectList);

            // zero out the open list
            openObjectList = null;
        } else {
            currentDict.pop();
        }
    }

    @Override
    public void exitFile(YamlParser.FileContext ctx) {
        currentDict.pop();
    }


    private String getAssignName(YamlParser.AssignContext ctx) {
        String name = null;
        String text = ctx.name().getText();
        if (!StringUtils.isEmpty(text)) {
            name = StringUtils.stripQuotes(text.trim());
        }
        return name;
    }

    private Object getAssignValue(String name, YamlParser.AssignContext ctx) {
        YamlParser.ValueContext valueCtx = ctx.value();
        Object value;

        if (YamlParser.YamlInlineListValueContext.class.isAssignableFrom(valueCtx.getClass())) {
            YamlParser.YamlInlineListValueContext inlineListCtx =
                YamlParser.YamlInlineListValueContext.class.cast(valueCtx);
            List<Object> pyObjList = new ArrayList<>();

            YamlParser.Inline_listContext listCtx = inlineListCtx.inline_list();
            for (int i = 0; i < listCtx.getChildCount(); i++) {
                ParseTree obj = listCtx.getChild(i);
                // This code is not handling arrays of objects or arrays of arrays since we do not need it
                // for our use case.  If we encounter it, we will log an error and return None.
                // We really should do something better if Antlr has a more graceful way to handle it...
                //
                if (!YamlParser.Inline_list_itemContext.class.isAssignableFrom(obj.getClass())) {
                    continue;
                }
                YamlParser.Inline_list_itemContext liCtx = YamlParser.Inline_list_itemContext.class.cast(obj);
                YamlParser.ValueContext arrayElementValueContext = liCtx.value();
                String madeUpName = MessageFormat.format("{0}[{1}]", name, pyObjList.size());
                Object arrayElement = getScalarValue(madeUpName, arrayElementValueContext);
                pyObjList.add(arrayElement);
            }
            value = pyObjList;
        } else {
            value = getScalarValue(name, valueCtx);
        }
        return value;
    }

    private Object getScalarValue(String name, YamlParser.ValueContext valueContext) {
        Object value = null;

        Class<?> valueClazz = valueContext.getClass();
        String text;
        if (YamlParser.YamlNullValueContext.class.isAssignableFrom(valueClazz)) {
            value = null;
        } else if (YamlParser.YamlNameValueContext.class.isAssignableFrom(valueClazz)) {
            YamlParser.YamlNameValueContext nameCtx = YamlParser.YamlNameValueContext.class.cast(valueContext);
            text = nameCtx.NAME().getText();
            if (!StringUtils.isEmpty(text)) {
                value = text.trim();
                value = StringUtils.stripQuotes(value.toString());  // similar to AbstractYamlTranslator
            } else {
                value = null;
            }
        } else if (YamlParser.YamlUnquotedStringValueContext.class.isAssignableFrom(valueClazz)) {
            YamlParser.YamlUnquotedStringValueContext strCtx =
                YamlParser.YamlUnquotedStringValueContext.class.cast(valueContext);
            text = strCtx.UNQUOTED_STRING().getText();
            if (!StringUtils.isEmpty(text)) {
                value = text.trim();
            } else {
                value = null;
            }
        } else if (YamlParser.YamlQuotedStringValueContext.class.isAssignableFrom(valueClazz)) {
            YamlParser.YamlQuotedStringValueContext strCtx =
                YamlParser.YamlQuotedStringValueContext.class.cast(valueContext);
            text = strCtx.QUOTED_STRING().getText();
            if (!StringUtils.isEmpty(text)) {
                // trim off any leading/trailing white space
                text = text.trim();
                // trim off the quotes
                value = text.substring(1, text.length() - 1);
            } else {
                value = null;
            }
        } else if (YamlParser.YamlBooleanValueContext.class.isAssignableFrom(valueClazz)) {
            YamlParser.YamlBooleanValueContext boolCtx = YamlParser.YamlBooleanValueContext.class.cast(valueContext);
            text = boolCtx.BOOLEAN().getText();

            String booleanValue = "False";
            if (!StringUtils.isEmpty(text)) {
                text = text.trim();
                if ("true".equalsIgnoreCase(text)) {
                    booleanValue = "True";
                } else if ("false".equalsIgnoreCase(text)) {
                    booleanValue = "False";
                } else {
                    Assert.fail("Boolean value for " + name + " attribute was not true or false (" + text + ")");
                }
            } else {
                Assert.fail("Boolean value for " + name + " attribute was empty");
            }
            value = booleanValue;
        } else if (YamlParser.YamlIntegerValueContext.class.isAssignableFrom(valueClazz)) {
            YamlParser.YamlIntegerValueContext intCtx = YamlParser.YamlIntegerValueContext.class.cast(valueContext);
            text = intCtx.INTEGER().getText();

            int intValue = 0;
            if (!StringUtils.isEmpty(text)) {
                text = text.trim();
                try {
                    intValue = Integer.valueOf(text);
                } catch (NumberFormatException nfe) {
                    Assert.fail(name + " attribute is not an integer: " + nfe.getLocalizedMessage());
                    nfe.printStackTrace();
                }
            } else {
                Assert.fail(name + " attribute value was empty");
            }
            value = intValue;
        } else if (YamlParser.YamlFloatValueContext.class.isAssignableFrom(valueClazz)) {
            YamlParser.YamlFloatValueContext floatCtx = YamlParser.YamlFloatValueContext.class.cast(valueContext);
            text = floatCtx.FLOAT().getText();

            float floatValue = 0;
            if (!StringUtils.isEmpty(text)) {
                text = text.trim();
                try {
                    floatValue = Float.valueOf(text);
                } catch (NumberFormatException nfe) {
                    Assert.fail(name + " attribute is not a float: " + nfe.getLocalizedMessage());
                    nfe.printStackTrace();
                }
            } else {
                Assert.fail(name + " attribute value was empty");
            }
            value = floatValue;
        } else {
            Assert.fail(name + " attribute was an unexpected context type: " + valueClazz.getName());
        }
        return value;
    }

    private synchronized List<Object> getOpenObjectList() {
        if (openObjectList == null) {
            openObjectList = new ArrayList<>();
        }
        return openObjectList;
    }

    @SuppressWarnings("unchecked")
    private Map<String, Object> getMap(Map<String, Object> container, String key) {
        return (Map<String, Object>) container.get(key);
    }

    private void checkForParseErrors() throws Exception {
        int errorCount = errorListener.getErrorCount();
        Assert.assertEquals("Parser error count was " + errorCount, 0, errorCount);
    }
}
