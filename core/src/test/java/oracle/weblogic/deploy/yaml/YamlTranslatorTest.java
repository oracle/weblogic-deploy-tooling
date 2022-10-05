/*
 * Copyright (c) 2020, 2022, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.yaml;

import java.io.ByteArrayInputStream;
import java.io.File;
import java.io.InputStream;
import java.math.BigInteger;
import java.util.logging.Level;
import java.util.logging.Logger;

import oracle.weblogic.deploy.util.PyOrderedDict;

import oracle.weblogic.deploy.util.PyRealBoolean;
import org.junit.jupiter.api.Test;

import org.python.core.PyDictionary;
import org.python.core.PyFloat;
import org.python.core.PyInteger;
import org.python.core.PyList;
import org.python.core.PyLong;
import org.python.core.PyObject;
import org.python.core.PyString;

import static java.nio.charset.StandardCharsets.UTF_8;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.junit.jupiter.api.Assertions.fail;

public class YamlTranslatorTest {

    @Test
    public void testEmptyModelReturnsPyDictionary() throws Exception {
        File yamlFile = new File("src/test/resources/yaml/empty.yaml").getAbsoluteFile();
        YamlTranslator yamlTranslator = new YamlTranslator(yamlFile.getAbsolutePath(), true);

        PyDictionary actual = yamlTranslator.parse();

        assertNotNull(actual, "empty model file should return dict");
    }

    @Test
    public void testFlatMapScalarTypes() throws Exception {
        File yamlFile = new File("src/test/resources/yaml/flat-map-with-scalars.yaml").getAbsoluteFile();
        YamlTranslator yamlTranslator = new YamlTranslator(yamlFile.getAbsolutePath(), true);

        PyDictionary actual = yamlTranslator.parse();

        assertNotNull(actual, "dict should not be null");

        PyString key = new PyString("field1");
        assertTrue(actual.has_key(key), "field1 should be present");
        PyObject value = actual.__getitem__(key);
        assertEquals(PyString.class, value.getClass(), "field1 should be a string");
        assertEquals("string", value.toString(), "field1 value should be string");

        key = new PyString("field2");
        assertTrue(actual.has_key(key), "field2 should be present");
        value = actual.__getitem__(key);
        assertEquals(PyInteger.class, value.getClass(), "field2 should be an integer");
        assertEquals(123, ((PyInteger)value).getValue(), "field2 value should be 123");

        key = new PyString("field3");
        assertTrue(actual.has_key(key), "field3 should be present");
        value = actual.__getitem__(key);
        assertEquals(PyLong.class, value.getClass(), "field3 should be a long");
        assertEquals(new BigInteger("123456789012345"), ((PyLong)value).getValue(), "field3 value should be 123456789012345");

        key = new PyString("field4");
        assertTrue(actual.has_key(key), "field4 should be present");
        value = actual.__getitem__(key);
        assertEquals(PyFloat.class, value.getClass(), "field4 should be a float");
        assertEquals(123.456, ((PyFloat)value).getValue(), 0.0000000001, "field4 value should be 123.456");

        key = new PyString("field5");
        assertTrue(actual.has_key(key), "field5 should be present");
        value = actual.__getitem__(key);
        assertEquals(PyFloat.class, value.getClass(), "field5 should be a float");
        assertEquals(0.12345678901234567890, ((PyFloat)value).getValue(), 0.0000000001,
            "field5 value should be 0.12345678901234567890");

        key = new PyString("field6");
        assertTrue(actual.has_key(key), "field6 should be present");
        value = actual.__getitem__(key);
        assertEquals(PyRealBoolean.class, value.getClass(), "field6 should be a PyRealBoolean");
        assertEquals(true, ((PyRealBoolean) value).getValue(), "field6 value should be true");

        key = new PyString("field7");
        assertTrue(actual.has_key(key), "field7 should be present");
        value = actual.__getitem__(key);
        assertEquals(PyRealBoolean.class, value.getClass(), "field7 should be a PyRealBoolean");
        assertEquals(true, ((PyRealBoolean) value).getValue(), "field7 value should be true");

        key = new PyString("field8");
        assertTrue(actual.has_key(key), "field8 should be present");
        value = actual.__getitem__(key);
        assertEquals(PyRealBoolean.class, value.getClass(), "field8 should be a PyRealBoolean");
        assertEquals(false, ((PyRealBoolean) value).getValue(), "field8 value should be false");

        key = new PyString("field9");
        assertTrue(actual.has_key(key), "field9 should be present");
        value = actual.__getitem__(key);
        assertEquals(PyRealBoolean.class, value.getClass(), "field9 should be a PyRealBoolean");
        assertEquals(false, ((PyRealBoolean) value).getValue(), "field9 value should be false");

        key = new PyString("field10");
        assertTrue(actual.has_key(key), "field10 should be present");
        value = actual.__getitem__(key);
        assertEquals(PyString.class, value.getClass(), "field10 should be a string");
        assertEquals("string", value.toString(), "field10 value should be string");

        key = new PyString("field11");
        assertTrue(actual.has_key(key), "field11 should be present");
        value = actual.__getitem__(key);
        assertEquals(PyString.class, value.getClass(), "field11 should be a string");
        assertEquals("string", value.toString(), "field11 value should be string");

        key = new PyString("field12");
        assertTrue(actual.has_key(key), "field12 should be present");
        value = actual.__getitem__(key);
        assertEquals(PyString.class, value.getClass(), "field12 should be a string");
        assertEquals("123", value.toString(), "field12 value should be 123");

        key = new PyString("field13");
        assertTrue(actual.has_key(key), "field13 should be present");
        value = actual.__getitem__(key);
        assertEquals(PyString.class, value.getClass(), "field13 should be a string");
        assertEquals( "123", value.toString(), "field13 value should be 123");

        key = new PyString("field14");
        assertTrue(actual.has_key(key), "field14 should be present");
        value = actual.__getitem__(key);
        assertEquals(PyString.class, value.getClass(), "field14 should be a string");
        assertEquals("123456789012345", value.toString(), "field14 value should be 123456789012345");

        key = new PyString("field15");
        assertTrue(actual.has_key(key), "field15 should be present");
        value = actual.__getitem__(key);
        assertEquals(PyString.class, value.getClass(), "field15 should be a string");
        assertEquals("123456789012345", value.toString(), "field15 value should be 123456789012345");

        key = new PyString("field16");
        assertTrue(actual.has_key(key), "field16 should be present");
        value = actual.__getitem__(key);
        assertEquals(PyString.class, value.getClass(), "field16 should be a string");
        assertEquals("123.456", value.toString(), "field16 value should be 123.456");

        key = new PyString("field17");
        assertTrue(actual.has_key(key), "field17 should be present");
        value = actual.__getitem__(key);
        assertEquals(PyString.class, value.getClass(), "field17 should be a string");
        assertEquals("123.456", value.toString(), "field17 value should be 123.456");

        key = new PyString("field18");
        assertTrue(actual.has_key(key), "field18 should be present");
        value = actual.__getitem__(key);
        assertEquals(PyString.class, value.getClass(), "field18 should be a string");
        assertEquals("0.12345678901234567890", value.toString(), "field18 value should be 0.12345678901234567890");

        key = new PyString("field19");
        assertTrue(actual.has_key(key), "field19 should be present");
        value = actual.__getitem__(key);
        assertEquals(PyString.class, value.getClass(), "field19 should be a string");
        assertEquals("0.12345678901234567890", value.toString(), "field19 value should be 0.12345678901234567890");

        key = new PyString("field20");
        assertTrue(actual.has_key(key), "field20 should be present");
        value = actual.__getitem__(key);
        assertEquals(PyString.class, value.getClass(), "field20 should be a string");
        assertEquals("true", value.toString(), "field20 value should be true");

        key = new PyString("field21");
        assertTrue(actual.has_key(key), "field21 should be present");
        value = actual.__getitem__(key);
        assertEquals(PyString.class, value.getClass(), "field21 should be a string");
        assertEquals("True", value.toString(), "field21 value should be True");

        key = new PyString("field22");
        assertTrue(actual.has_key(key), "field22 should be present");
        value = actual.__getitem__(key);
        assertEquals(PyString.class, value.getClass(), "field22 should be a string");
        assertEquals("false", value.toString(), "field22 value should be false");

        key = new PyString("field23");
        assertTrue(actual.has_key(key), "field23 should be present");
        value = actual.__getitem__(key);
        assertEquals(PyString.class, value.getClass(), "field23 should be a string");
        assertEquals("False", value.toString(), "field23 value should be False");
    }

    @Test
    public void testNestedDictionaries() throws Exception {
        File yamlFile = new File("src/test/resources/yaml/nested-dict.yaml").getAbsoluteFile();
        YamlTranslator yamlTranslator = new YamlTranslator(yamlFile.getAbsolutePath(), true);

        PyDictionary actual = yamlTranslator.parse();
        assertNotNull(actual, "dict should not be null");

        PyString key = new PyString("level1");
        assertTrue(actual.has_key(key), "level1 should be present");
        PyObject value = actual.__getitem__(key);
        assertNotNull(value, "level1 value should not be null");
        assertEquals(PyOrderedDict.class, value.getClass(), "level1 should be a dict");
        PyDictionary dict = (PyDictionary) value;

        key = new PyString("level2");
        assertTrue(dict.has_key(key), "level2 should be present");
        value = dict.__getitem__(key);
        assertNotNull(value, "level2 value should not be null");
        assertEquals(PyOrderedDict.class, value.getClass(), "level2 should be a dict");
        dict = (PyDictionary) value;

        key = new PyString("level3");
        assertTrue(dict.has_key(key), "level3 should be present");
        value = dict.__getitem__(key);
        assertNotNull(value, "level3 value should not be null");
        assertEquals(PyOrderedDict.class, value.getClass(), "level3 should be a dict");
        dict = (PyDictionary) value;

        key = new PyString("field1");
        assertTrue(dict.has_key(key), "field1 should be present");
        value = dict.__getitem__(key);
        assertNotNull(value, "field1 value should not be null");
        assertEquals(PyString.class, value.getClass(), "field1 should be a string");
        assertEquals("abc", value.toString(), "field1 value should be abc");

        key = new PyString("field2");
        assertTrue(dict.has_key(key), "field2 should be present");
        value = dict.__getitem__(key);
        assertNotNull(value, "field2 value should not be null");
        assertEquals(PyString.class, value.getClass(), "field2 should be a string");
        assertEquals("def", value.toString(), "field2 value should be def");
    }

    @Test
    public void testSecurityConfigModel2() throws Exception {
        File yamlFile = new File("src/test/resources/compare/model-sc2-new.yaml").getAbsoluteFile();
        YamlTranslator yamlTranslator = new YamlTranslator(yamlFile.getAbsolutePath(), true);

        PyDictionary actual = yamlTranslator.parse();
        assertNotNull(actual, "dict should not be null");

        PyString key = new PyString("topology");
        assertTrue(actual.has_key(key), "topology should be present");
        PyObject value = actual.__getitem__(key);
        assertNotNull(value, "topology value should not be null");
        assertEquals(PyOrderedDict.class, value.getClass(), "topology should be a dict");
        PyDictionary dict = (PyDictionary) value;

        key = new PyString("SecurityConfiguration");
        assertTrue(dict.has_key(key), "SecurityConfiguration should be present");
        value = dict.__getitem__(key);
        assertNotNull(value, "SecurityConfiguration value should not be null");
        assertEquals(PyOrderedDict.class, value.getClass(), "SecurityConfiguration should be a dict");
        dict = (PyDictionary) value;

        key = new PyString("Realm");
        assertTrue(dict.has_key(key), "Realm should be present");
        value = dict.__getitem__(key);
        assertNotNull(value, "Realm value should not be null");
        assertEquals(PyOrderedDict.class, value.getClass(), "Realm should be a dict");
        dict = (PyDictionary) value;

        key = new PyString("myrealm");
        assertTrue(dict.has_key(key), "myrealm should be present");
        value = dict.__getitem__(key);
        assertNotNull(value, "myrealm value should not be null");
        assertEquals(PyOrderedDict.class, value.getClass(), "myrealm should be a dict");
        PyDictionary myrealm = (PyDictionary) value;

        key = new PyString("AuthenticationProvider");
        assertTrue(myrealm.has_key(key), "AuthenticationProvider should be present");
        value = myrealm.__getitem__(key);
        assertNotNull(value, "AuthenticationProvider value should not be null");
        assertEquals(PyOrderedDict.class, value.getClass(), "AuthenticationProvider should be a dict");
        PyDictionary authenticationProvider = (PyDictionary) value;

        key = new PyString("MyIdentityAsserterV2");
        assertTrue(authenticationProvider.has_key(key), "MyIdentityAsserterV2 should be present");
        value = authenticationProvider.__getitem__(key);
        assertNotNull(value, "MyIdentityAsserterV2 value should not be null");
        assertEquals(PyOrderedDict.class, value.getClass(), "MyIdentityAsserterV2 should be a dict");
        dict = (PyDictionary) value;

        key = new PyString("org.asserter.MyIdentityAsserterV2");
        assertTrue(dict.has_key(key), "org.asserter.MyIdentityAsserterV2 should be present");
        value = dict.__getitem__(key);
        assertNotNull(value, "org.asserter.MyIdentityAsserterV2 value should not be null");
        assertEquals(PyOrderedDict.class, value.getClass(), "org.asserter.MyIdentityAsserterV2 should be a dict");
        dict = (PyDictionary) value;

        key = new PyString("ExcludedContextPaths");
        assertTrue(dict.has_key(key), "ExcludedContextPaths should be present");
        value = dict.__getitem__(key);
        assertNotNull(value, "ExcludedContextPaths value should not be null");
        assertEquals(PyList.class, value.getClass(), "ExcludedContextPaths should be a list");
        PyList list = (PyList) value;
        PyObject listItem = list.__getitem__(0);
        assertNotNull(listItem, "ExcludedContextPaths first element should not be null");
        assertEquals(PyString.class, listItem.getClass(), "ExcludedContextPaths first element should be a string");
        assertEquals("/soa-infra", listItem.toString(), "ExcludedContextPaths first element value should be /soa-infra");
        listItem = list.__getitem__(1);
        assertNotNull(listItem, "ExcludedContextPaths second element should not be null");
        assertEquals(PyString.class, listItem.getClass(), "ExcludedContextPaths second element should be a string");
        assertEquals("/management", listItem.toString(), "ExcludedContextPaths second element value should be /management");
        listItem = list.__getitem__(2);
        assertNotNull(listItem, "ExcludedContextPaths third element should not be null");
        assertEquals(PyString.class, listItem.getClass(), "ExcludedContextPaths third element should be a string");
        assertEquals("/jolokia", listItem.toString(), "ExcludedContextPaths third element value should be /jolokia");

        key = new PyString("DefaultAuthenticator");
        assertTrue(authenticationProvider.has_key(key), "DefaultAuthenticator should be present");
        value = authenticationProvider.__getitem__(key);
        assertNotNull(value, "DefaultAuthenticator value should not be null");
        assertEquals(PyOrderedDict.class, value.getClass(), "AuthenticationProvider should be a dict");
        dict = (PyDictionary) value;

        key = new PyString("DefaultAuthenticator");
        assertTrue(dict.has_key(key), "DefaultAuthenticator should be present");
        value = dict.__getitem__(key);
        assertNotNull(value, "DefaultAuthenticator value should not be null");
        assertEquals(PyOrderedDict.class, value.getClass(), "AuthenticationProvider should be a dict");
        dict = (PyDictionary) value;

        key = new PyString("ControlFlag");
        assertTrue(dict.has_key(key), "ControlFlag should be present");
        value = dict.__getitem__(key);
        assertNotNull(value, "ControlFlag value should not be null");
        assertEquals(PyString.class, value.getClass(), "ControlFlag should be a string");
        assertEquals("REQUIRED", value.toString(), "ControlFlag value should be REQUIRED");

        key = new PyString("DefaultIdentityAsserter");
        assertTrue(authenticationProvider.has_key(key), "DefaultIdentityAsserter should be present");
        value = authenticationProvider.__getitem__(key);
        assertNotNull(value, "DefaultIdentityAsserter value should not be null");
        assertEquals(PyOrderedDict.class, value.getClass(), "DefaultIdentityAsserter should be a dict");
        dict = (PyDictionary) value;

        key = new PyString("DefaultIdentityAsserter");
        assertTrue(dict.has_key(key), "DefaultIdentityAsserter should be present");
        value = dict.__getitem__(key);
        assertNotNull(value, "DefaultIdentityAsserter value should not be null");
        assertEquals(PyOrderedDict.class, value.getClass(), "DefaultIdentityAsserter should be a dict");
        dict = (PyDictionary) value;

        key = new PyString("DefaultUserNameMapperAttributeType");
        assertTrue(dict.has_key(key), "DefaultUserNameMapperAttributeType should be present");
        value = dict.__getitem__(key);
        assertNotNull(value, "DefaultUserNameMapperAttributeType value should not be null");
        assertEquals(PyString.class, value.getClass(), "DefaultUserNameMapperAttributeType should be a string");
        assertEquals("CN", value.toString(), "DefaultUserNameMapperAttributeType value should be CN");

        key = new PyString("ActiveType");
        assertTrue(dict.has_key(key), "ActiveType should be present");
        value = dict.__getitem__(key);
        assertNotNull(value, "ActiveType value should not be null");
        assertEquals(PyList.class, value.getClass(), "ActiveType should be a list");
        list = (PyList) value;
        listItem = list.__getitem__(0);
        assertNotNull(listItem, "ActiveType first element should not be null");
        assertEquals(PyString.class, listItem.getClass(), "ActiveType first element should be a string");
        assertEquals("AuthenticatedUser", listItem.toString(), "ActiveType first element value should be AuthenticatedUser");
        listItem = list.__getitem__(1);
        assertNotNull(listItem, "ActiveType second element should not be null");
        assertEquals(PyString.class, listItem.getClass(), "ActiveType second element should be a string");
        assertEquals("X.509", listItem.toString(), "ActiveType second element value should be X.509");

        key = new PyString("DefaultUserNameMapperAttributeDelimiter");
        assertTrue(dict.has_key(key), "DefaultUserNameMapperAttributeDelimiter should be present");
        value = dict.__getitem__(key);
        assertNotNull(value, "DefaultUserNameMapperAttributeDelimiter value should not be null");
        assertEquals(PyString.class, value.getClass(), "DefaultUserNameMapperAttributeDelimiter should be a string");
        assertEquals(",", value.toString(), "DefaultUserNameMapperAttributeDelimiter value should be ,");

        key = new PyString("UseDefaultUserNameMapper");
        assertTrue(dict.has_key(key), "UseDefaultUserNameMapper should be present");
        value = dict.__getitem__(key);
        assertNotNull(value, "UseDefaultUserNameMapper value should not be null");
        assertEquals(PyRealBoolean.class, value.getClass(), "UseDefaultUserNameMapper should be a PyRealBoolean");
        assertTrue(((PyRealBoolean) value).getValue(), "UseDefaultUserNameMapper value should be true");

        key = new PyString("PasswordValidator");
        assertTrue(myrealm.has_key(key), "PasswordValidator should be present");
        value = myrealm.__getitem__(key);
        assertNotNull(value, "PasswordValidator value should not be null");
        assertEquals(PyOrderedDict.class, value.getClass(), "PasswordValidator should be a dict");
        dict = (PyDictionary) value;

        key = new PyString("SystemPasswordValidator");
        assertTrue(dict.has_key(key), "SystemPasswordValidator should be present");
        value = dict.__getitem__(key);
        assertNotNull(value, "SystemPasswordValidator value should not be null");
        assertEquals(PyOrderedDict.class, value.getClass(), "SystemPasswordValidator should be a dict");
        dict = (PyDictionary) value;

        key = new PyString("SystemPasswordValidator");
        assertTrue(dict.has_key(key), "SystemPasswordValidator should be present");
        value = dict.__getitem__(key);
        assertNotNull(value, "SystemPasswordValidator value should not be null");
        assertEquals(PyOrderedDict.class, value.getClass(), "SystemPasswordValidator should be a dict");
        dict = (PyDictionary) value;

        key = new PyString("MinAlphabeticCharacters");
        assertTrue(dict.has_key(key), "MinAlphabeticCharacters should be present");
        value = dict.__getitem__(key);
        assertNotNull(value, "MinAlphabeticCharacters value should not be null");
        assertEquals(PyInteger.class, value.getClass(), "MinAlphabeticCharacters should be an integer");
        assertEquals("1", value.toString(), "MinAlphabeticCharacters value should be 1");

        key = new PyString("MinLowercaseCharacters");
        assertTrue(dict.has_key(key), "MinLowercaseCharacters should be present");
        value = dict.__getitem__(key);
        assertNotNull(value, "MinLowercaseCharacters value should not be null");
        assertEquals(PyInteger.class, value.getClass(), "MinLowercaseCharacters should be an integer");
        assertEquals("1", value.toString(), "MinLowercaseCharacters value should be 1");

        key = new PyString("MinNumericCharacters");
        assertTrue(dict.has_key(key), "MinNumericCharacters should be present");
        value = dict.__getitem__(key);
        assertNotNull(value, "MinNumericCharacters value should not be null");
        assertEquals(PyInteger.class, value.getClass(), "MinNumericCharacters should be an integer");
        assertEquals("1", value.toString(), "MinNumericCharacters value should be 1");

        key = new PyString("MaxConsecutiveCharacters");
        assertTrue(dict.has_key(key), "MaxConsecutiveCharacters should be present");
        value = dict.__getitem__(key);
        assertNotNull(value, "MaxConsecutiveCharacters value should not be null");
        assertEquals(PyInteger.class, value.getClass(), "MaxConsecutiveCharacters should be an integer");
        assertEquals("2", value.toString(), "MaxConsecutiveCharacters value should be 2");

        key = new PyString("MinNonAlphanumericCharacters");
        assertTrue(dict.has_key(key), "MinNonAlphanumericCharacters should be present");
        value = dict.__getitem__(key);
        assertNotNull(value, "MinNonAlphanumericCharacters value should not be null");
        assertEquals(PyInteger.class, value.getClass(), "MinNonAlphanumericCharacters should be an integer");
        assertEquals("1", value.toString(), "MinNonAlphanumericCharacters value should be 1");

        key = new PyString("MinUppercaseCharacters");
        assertTrue(dict.has_key(key), "MinUppercaseCharacters should be present");
        value = dict.__getitem__(key);
        assertNotNull(value, "MinUppercaseCharacters value should not be null");
        assertEquals(PyInteger.class, value.getClass(), "MinUppercaseCharacters should be an integer");
        assertEquals("1", value.toString(), "MinUppercaseCharacters value should be 1");

        key = new PyString("RejectEqualOrContainUsername");
        assertTrue(dict.has_key(key), "RejectEqualOrContainUsername should be present");
        value = dict.__getitem__(key);
        assertNotNull(value, "RejectEqualOrContainUsername value should not be null");
        assertEquals(PyRealBoolean.class, value.getClass(), "RejectEqualOrContainUsername should be a PyRealBoolean");
        assertTrue(((PyRealBoolean) value).getValue(), "RejectEqualOrContainUsername value should be true");

        key = new PyString("MinPasswordLength");
        assertTrue(dict.has_key(key), "MinPasswordLength should be present");
        value = dict.__getitem__(key);
        assertNotNull(value, "MinPasswordLength value should not be null");
        assertEquals(PyInteger.class, value.getClass(), "MinPasswordLength should be an integer");
        assertEquals("10", value.toString(), "MinPasswordLength value should be 10");

        key = new PyString("RejectEqualOrContainReverseUsername");
        assertTrue(dict.has_key(key), "RejectEqualOrContainReverseUsername should be present");
        value = dict.__getitem__(key);
        assertNotNull(value, "RejectEqualOrContainReverseUsername value should not be null");
        assertEquals(PyRealBoolean.class, value.getClass(), "RejectEqualOrContainReverseUsername should be a PyRealBoolean");
        assertTrue(((PyRealBoolean) value).getValue(), "RejectEqualOrContainReverseUsername value should be true");
    }

    @Test
    public void testLargeFileIsSuccessful() throws Exception {
        File yamlFile = new File("src/test/resources/yaml/big-model.yaml").getAbsoluteFile();
        YamlTranslator yamlTranslator = new YamlTranslator(yamlFile.getAbsolutePath(), true, 20000000);

        PyDictionary actual = yamlTranslator.parse();

        assertNotNull(actual, "big model file should return dict");
    }

    /**
     * Verify that a lexical error will throw an Exception
     */
    @Test
    public void testLexicalError() {
        // Temporarily disable logging for this test. Intended lexical failure will log a stack trace.
        Logger logger = Logger.getLogger("wlsdeploy.yaml");
        Level originalLevel  = logger.getLevel();
        logger.setLevel(Level.OFF);

        try {
            // YAML causes lexical error:
            // abc:
            //   xyz: - aa-bb
            String text = "abc:\n  xyz: - aa-bb\n";
            InputStream stream = new ByteArrayInputStream(text.getBytes(UTF_8));
            YamlStreamTranslator translator = new YamlStreamTranslator("String", stream);
            System.out.println("translator = " + translator.toString());
            translator.parse();
            fail("Test must raise YamlException when model has a lexical error");

        } catch(YamlException e) {
            // expected result

        } finally {
            logger.setLevel(originalLevel);
        }
    }
}
