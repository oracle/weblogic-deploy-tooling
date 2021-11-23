/*
 * Copyright (c) 2020, Oracle Corporation and/or its affiliates.
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

import org.junit.jupiter.api.Test;

import org.python.core.PyDictionary;
import org.python.core.PyFloat;
import org.python.core.PyInteger;
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
        assertEquals(PyString.class, value.getClass(), "field6 should be a string");
        assertEquals("true", value.toString(), "field6 value should be true");

        key = new PyString("field7");
        assertTrue(actual.has_key(key), "field7 should be present");
        value = actual.__getitem__(key);
        assertEquals(PyString.class, value.getClass(), "field7 should be a string");
        assertEquals("true", value.toString(), "field7 value should be true");

        key = new PyString("field8");
        assertTrue(actual.has_key(key), "field8 should be present");
        value = actual.__getitem__(key);
        assertEquals(PyString.class, value.getClass(), "field8 should be a string");
        assertEquals("false", value.toString(), "field8 value should be false");

        key = new PyString("field9");
        assertTrue(actual.has_key(key), "field9 should be present");
        value = actual.__getitem__(key);
        assertEquals(PyString.class, value.getClass(), "field9 should be a string");
        assertEquals("false", value.toString(), "field9 value should be false");

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
