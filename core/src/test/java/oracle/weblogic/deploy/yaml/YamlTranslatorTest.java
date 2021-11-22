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
import org.junit.Assert;
import org.junit.Test;
import org.python.core.PyDictionary;
import org.python.core.PyFloat;
import org.python.core.PyInteger;
import org.python.core.PyLong;
import org.python.core.PyObject;
import org.python.core.PyString;

import static java.nio.charset.StandardCharsets.UTF_8;

public class YamlTranslatorTest {

    @Test
    public void testFlatMapScalarTypes() throws Exception {
        File yamlFile = new File("src/test/resources/yaml/flat-map-with-scalars.yaml").getAbsoluteFile();
        YamlTranslator yamlTranslator = new YamlTranslator(yamlFile.getAbsolutePath(), true);

        PyDictionary actual = yamlTranslator.parse();

        Assert.assertNotNull("dict should not be null", actual);

        PyString key = new PyString("field1");
        Assert.assertTrue("field1 should be present", actual.has_key(key));
        PyObject value = actual.__getitem__(key);
        Assert.assertEquals("field1 should be a string", PyString.class, value.getClass());
        Assert.assertEquals("field1 value should be string", "string", value.toString());

        key = new PyString("field2");
        Assert.assertTrue("field2 should be present", actual.has_key(key));
        value = actual.__getitem__(key);
        Assert.assertEquals("field2 should be an integer", PyInteger.class, value.getClass());
        Assert.assertEquals("field2 value should be 123", 123,
            ((PyInteger)value).getValue());

        key = new PyString("field3");
        Assert.assertTrue("field3 should be present", actual.has_key(key));
        value = actual.__getitem__(key);
        Assert.assertEquals("field3 should be a long", PyLong.class, value.getClass());
        Assert.assertEquals("field3 value should be 123456789012345",
            new BigInteger("123456789012345"), ((PyLong)value).getValue());

        key = new PyString("field4");
        Assert.assertTrue("field4 should be present", actual.has_key(key));
        value = actual.__getitem__(key);
        Assert.assertEquals("field4 should be a float", PyFloat.class, value.getClass());
        Assert.assertEquals("field4 value should be 123.456",123.456,
            ((PyFloat)value).getValue(), 0.0000000001);

        key = new PyString("field5");
        Assert.assertTrue("field5 should be present", actual.has_key(key));
        value = actual.__getitem__(key);
        Assert.assertEquals("field5 should be a float", PyFloat.class, value.getClass());
        Assert.assertEquals("field5 value should be 0.12345678901234567890",
            0.12345678901234567890, ((PyFloat)value).getValue(), 0.0000000001);

        key = new PyString("field6");
        Assert.assertTrue("field6 should be present", actual.has_key(key));
        value = actual.__getitem__(key);
        Assert.assertEquals("field6 should be a string", PyString.class, value.getClass());
        Assert.assertEquals("field6 value should be true", "true", value.toString());

        key = new PyString("field7");
        Assert.assertTrue("field7 should be present", actual.has_key(key));
        value = actual.__getitem__(key);
        Assert.assertEquals("field7 should be a string", PyString.class, value.getClass());
        Assert.assertEquals("field7 value should be true", "true", value.toString());

        key = new PyString("field8");
        Assert.assertTrue("field8 should be present", actual.has_key(key));
        value = actual.__getitem__(key);
        Assert.assertEquals("field8 should be a string", PyString.class, value.getClass());
        Assert.assertEquals("field8 value should be false", "false", value.toString());

        key = new PyString("field9");
        Assert.assertTrue("field9 should be present", actual.has_key(key));
        value = actual.__getitem__(key);
        Assert.assertEquals("field9 should be a string", PyString.class, value.getClass());
        Assert.assertEquals("field9 value should be false", "false", value.toString());

        key = new PyString("field10");
        Assert.assertTrue("field10 should be present", actual.has_key(key));
        value = actual.__getitem__(key);
        Assert.assertEquals("field10 should be a string", PyString.class, value.getClass());
        Assert.assertEquals("field10 value should be string", "string", value.toString());

        key = new PyString("field11");
        Assert.assertTrue("field11 should be present", actual.has_key(key));
        value = actual.__getitem__(key);
        Assert.assertEquals("field11 should be a string", PyString.class, value.getClass());
        Assert.assertEquals("field11 value should be string", "string", value.toString());

        key = new PyString("field12");
        Assert.assertTrue("field12 should be present", actual.has_key(key));
        value = actual.__getitem__(key);
        Assert.assertEquals("field12 should be a string", PyString.class, value.getClass());
        Assert.assertEquals("field12 value should be 123", "123", value.toString());

        key = new PyString("field13");
        Assert.assertTrue("field13 should be present", actual.has_key(key));
        value = actual.__getitem__(key);
        Assert.assertEquals("field13 should be a string", PyString.class, value.getClass());
        Assert.assertEquals("field13 value should be 123", "123", value.toString());

        key = new PyString("field14");
        Assert.assertTrue("field14 should be present", actual.has_key(key));
        value = actual.__getitem__(key);
        Assert.assertEquals("field14 should be a string", PyString.class, value.getClass());
        Assert.assertEquals("field14 value should be 123456789012345",
            "123456789012345", value.toString());

        key = new PyString("field15");
        Assert.assertTrue("field15 should be present", actual.has_key(key));
        value = actual.__getitem__(key);
        Assert.assertEquals("field15 should be a string", PyString.class, value.getClass());
        Assert.assertEquals("field15 value should be 123456789012345",
            "123456789012345", value.toString());

        key = new PyString("field16");
        Assert.assertTrue("field16 should be present", actual.has_key(key));
        value = actual.__getitem__(key);
        Assert.assertEquals("field16 should be a string", PyString.class, value.getClass());
        Assert.assertEquals("field16 value should be 123.456", "123.456", value.toString());

        key = new PyString("field17");
        Assert.assertTrue("field17 should be present", actual.has_key(key));
        value = actual.__getitem__(key);
        Assert.assertEquals("field17 should be a string", PyString.class, value.getClass());
        Assert.assertEquals("field17 value should be 123.456", "123.456", value.toString());

        key = new PyString("field18");
        Assert.assertTrue("field18 should be present", actual.has_key(key));
        value = actual.__getitem__(key);
        Assert.assertEquals("field18 should be a string", PyString.class, value.getClass());
        Assert.assertEquals("field18 value should be 0.12345678901234567890",
            "0.12345678901234567890", value.toString());

        key = new PyString("field19");
        Assert.assertTrue("field19 should be present", actual.has_key(key));
        value = actual.__getitem__(key);
        Assert.assertEquals("field19 should be a string", PyString.class, value.getClass());
        Assert.assertEquals("field19 value should be 0.12345678901234567890",
            "0.12345678901234567890", value.toString());

        key = new PyString("field20");
        Assert.assertTrue("field20 should be present", actual.has_key(key));
        value = actual.__getitem__(key);
        Assert.assertEquals("field20 should be a string", PyString.class, value.getClass());
        Assert.assertEquals("field20 value should be true", "true", value.toString());

        key = new PyString("field21");
        Assert.assertTrue("field21 should be present", actual.has_key(key));
        value = actual.__getitem__(key);
        Assert.assertEquals("field21 should be a string", PyString.class, value.getClass());
        Assert.assertEquals("field21 value should be True", "True", value.toString());

        key = new PyString("field22");
        Assert.assertTrue("field22 should be present", actual.has_key(key));
        value = actual.__getitem__(key);
        Assert.assertEquals("field22 should be a string", PyString.class, value.getClass());
        Assert.assertEquals("field22 value should be false", "false", value.toString());

        key = new PyString("field23");
        Assert.assertTrue("field23 should be present", actual.has_key(key));
        value = actual.__getitem__(key);
        Assert.assertEquals("field23 should be a string", PyString.class, value.getClass());
        Assert.assertEquals("field23 value should be False", "False", value.toString());
    }

    @Test
    public void testNestedDictionaries() throws Exception {
        File yamlFile = new File("src/test/resources/yaml/nested-dict.yaml").getAbsoluteFile();
        YamlTranslator yamlTranslator = new YamlTranslator(yamlFile.getAbsolutePath(), true);

        PyDictionary actual = yamlTranslator.parse();
        Assert.assertNotNull("dict should not be null", actual);

        PyString key = new PyString("level1");
        Assert.assertTrue("level1 should be present", actual.has_key(key));
        PyObject value = actual.__getitem__(key);
        Assert.assertNotNull("level1 value should not be null", value);
        Assert.assertEquals("level1 should be a dict", PyOrderedDict.class, value.getClass());
        PyDictionary dict = (PyDictionary) value;

        key = new PyString("level2");
        Assert.assertTrue("level2 should be present", dict.has_key(key));
        value = dict.__getitem__(key);
        Assert.assertNotNull("level2 value should not be null", value);
        Assert.assertEquals("level2 should be a dict", PyOrderedDict.class, value.getClass());
        dict = (PyDictionary) value;

        key = new PyString("level3");
        Assert.assertTrue("level3 should be present", dict.has_key(key));
        value = dict.__getitem__(key);
        Assert.assertNotNull("level3 value should not be null", value);
        Assert.assertEquals("level3 should be a dict", PyOrderedDict.class, value.getClass());
        dict = (PyDictionary) value;

        key = new PyString("field1");
        Assert.assertTrue("field1 should be present", dict.has_key(key));
        value = dict.__getitem__(key);
        Assert.assertNotNull("field1 value should not be null", value);
        Assert.assertEquals("field1 should be a string", PyString.class, value.getClass());
        Assert.assertEquals("field1 value should be abc", "abc", value.toString());

        key = new PyString("field2");
        Assert.assertTrue("field2 should be present", dict.has_key(key));
        value = dict.__getitem__(key);
        Assert.assertNotNull("field2 value should not be null", value);
        Assert.assertEquals("field2 should be a string", PyString.class, value.getClass());
        Assert.assertEquals("field2 value should be def", "def", value.toString());
    }

    @Test
    public void testSecurityConfigModel2() throws Exception {
        File yamlFile = new File("src/test/resources/compare/model-sc2-new.yaml").getAbsoluteFile();
        YamlTranslator yamlTranslator = new YamlTranslator(yamlFile.getAbsolutePath(), true);

        PyDictionary actual = yamlTranslator.parse();

        Assert.assertNotNull("dict should not be null", actual);

        PyString key = new PyString("topology");
        Assert.assertTrue("topology should be present", actual.has_key(key));
        PyObject value = actual.__getitem__(key);
        Assert.assertNotNull("topology value should not be null", value);
        Assert.assertEquals("topology should be a dict", PyOrderedDict.class, value.getClass());
        PyDictionary dict = (PyDictionary) value;

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
            translator.parse();
            Assert.fail("Test must raise YamlException when model has a lexical error");

        } catch(YamlException e) {
            // expected result

        } finally {
            logger.setLevel(originalLevel);
        }
    }
}
