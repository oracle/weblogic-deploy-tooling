/*
 * Copyright (c) 2017, 2019, Oracle and/or its affiliates. All rights reserved.
 * Licensed under the Universal Permissive License v 1.0 as shown at http://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.aliases;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Properties;

import org.junit.Test;
import org.python.core.PyDictionary;
import org.python.core.PyObject;
import org.python.core.PyString;
import org.python.core.PyTuple;

import static org.junit.Assert.*;

public class TypeUtilsTest {
    @Test
    public void convertToType() throws Exception {
        assertEquals("Integer conversion failed", 123, TypeUtils.convertToType("integer", "123"));
        assertEquals("Long conversion failed", 123L, TypeUtils.convertToType( "long", "123"));
        assertEquals("Double conversion failed", 123.45D, TypeUtils.convertToType( "double", "123.45"));
        assertEquals("Boolean conversion failed", "true", TypeUtils.convertToType( "boolean", "true"));
        assertEquals("Boolean conversion failed", "false", TypeUtils.convertToType( "boolean", 0));

        assertEquals("String conversion failed", "222", TypeUtils.convertToType( "string", 222));
        assertEquals("Password conversion failed", "abcdef", TypeUtils.convertToType( "password", "abcdef"));
        assertEquals("String conversion failed", "222", TypeUtils.convertToType( "string", "222".toCharArray()));

        String[] strings = {"one", "two", "three"};
        assertEquals("List conversion failed",
            Arrays.asList(strings),
            TypeUtils.convertToType( "list", "one, two, three"));
    }

    @Test(expected = AliasException.class)
    public void convertToTypeInvalidStringType() throws Exception {
        TypeUtils.convertToType( "fancy", "123" );
    }

    @Test(expected = AliasException.class)
    public void convertToTypeInvalidPrimitiveType() throws Exception {
        TypeUtils.convertToType( int.class, "123" );
    }

    @Test
    public void convertToTypeNullTest() throws Exception {
        assertEquals("String null conversion failed", null, TypeUtils.convertToType( String.class, null ));;
        assertEquals("Character null conversion failed", null, TypeUtils.convertToType( Character.class, "" ));;
    }

    @Test
    public void convertToPyObjectTest() throws Exception {
        String value = "abcdefg";
        PyObject expect = TypeUtils.convertToPyObject(value);
        assertEquals(expect, new PyString("abcdefg"));
    }

    @Test
    public void convertToTypeDictionaryTest() throws Exception {
        Properties properties = new Properties();
        properties.put("foo", "bar");
        properties.put("bar", "foo");
        PyDictionary actual = TypeUtils.convertPropertiesToDictionary(properties, true);
        assertEquals(actual.__len__(), 2);
        for (Object obj : actual.items()) {
            PyTuple po = (PyTuple) obj;
            String key =  po.__finditem__(0).toString();
            String value = po.__finditem__(1).toString();
            if (key.equals("foo")) {
                assertEquals(value, "bar");
            } else {
                assertEquals(value, "foo");
            }
        }
    }

    @Test
    public void convertStringToMap() throws Exception {
        String str = "key1=value1,key2=value2, key3=value3,key4=value4";
        String json = "{key1=value1,key2=value2, key3=value3,key4=value4}";
        Map<String, String> expected = new HashMap<>();
        expected.put("key1", "value1");
        expected.put("key2", "value2");
        expected.put("key3", "value3");
        expected.put("key4", "value4");
        assertEquals("String to Map conversion failed", expected, TypeUtils.convertStringToMap(str, ","));
        assertEquals("JSON to Map conversion failed", expected, TypeUtils.convertStringToMap(json, ","));
        assertEquals("String to Map conversion failed", expected, TypeUtils.convertToType(Map.class, str, ","));
        assertEquals("Map to Map conversion failed", expected, TypeUtils.convertToType(Map.class, expected));
    }

    @Test
    public void convertListToArray() throws Exception {
        List<String> list = new ArrayList<>();
        list.add("one");
        list.add("two");
        list.add("three");
        Object result = TypeUtils.convertToType(String[].class, list);
        if ( result == null )
            fail("convertToType returned null for List conversion to String[]");
        assertEquals("List conversion failed", String[].class, result.getClass());

    }

    @Test
    public void convertToList() throws Exception {
        String[] array = { "one", "two", "three" };
        List<String> expected = Arrays.asList(array);
        assertEquals("List from array conversion failed", expected, TypeUtils.convertToType(List.class, array));
        String str = "one, two, three";
        assertEquals("List from string conversion failed", expected, TypeUtils.convertToType(List.class, str));
        String[] empty = {};
        assertEquals("List from empty list conversion failed", null, TypeUtils.convertToType(List.class, empty));
    }

    @Test
    public void convertToProperties() throws Exception {
        String str = "key1=value1;key2=value2";

        Properties expected = new Properties();
        expected.put("key1", "value1");
        expected.put("key2", "value2");
        assertEquals("Properties from String failed", expected, TypeUtils.convertToType(Properties.class, str, ";"));

        Map<String, String> map = new HashMap<>();
        map.put("key1", "value1");
        map.put("key2", "value2");
        assertEquals("Properties from Map failed", expected, TypeUtils.convertToType(Properties.class, map, ";"));

    }
}
