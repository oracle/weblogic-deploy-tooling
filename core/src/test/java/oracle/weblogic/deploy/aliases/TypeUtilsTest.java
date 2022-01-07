/*
 * Copyright (c) 2017, 2022, Oracle Corporation and/or its affiliates.  All rights reserved.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.aliases;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Properties;

import org.junit.jupiter.api.Test;
import org.python.core.PyDictionary;
import org.python.core.PyLong;
import org.python.core.PyObject;
import org.python.core.PyString;
import org.python.core.PyTuple;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertThrows;

public class TypeUtilsTest {
    @Test
    public void convertToType() throws Exception {
        assertEquals(123, TypeUtils.convertToType("integer", "123"), "Integer conversion failed");
        assertEquals(123L, TypeUtils.convertToType( "long", "123"), "Long conversion failed");
        assertEquals(123.45D, TypeUtils.convertToType( "double", "123.45"), "Double conversion failed");
        assertEquals("true", TypeUtils.convertToType( "boolean", "true"), "Boolean conversion failed");
        assertEquals("false", TypeUtils.convertToType( "boolean", 0), "Boolean conversion failed");

        assertEquals("222", TypeUtils.convertToType( "string", 222), "String conversion failed");
        assertEquals("abcdef", TypeUtils.convertToType( "password", "abcdef"), "Password conversion failed");
        assertEquals("222", TypeUtils.convertToType( "string", "222".toCharArray()), "String conversion failed");

        String[] strings = {"one", "two", "three"};
        assertEquals(Arrays.asList(strings), TypeUtils.convertToType( "list", "one, two, three"), "List conversion failed");
    }

    @Test
    public void convertToTypeInvalidStringType() {
        assertThrows(AliasException.class, () -> TypeUtils.convertToType("fancy", "123"));
    }

    @Test
    public void convertToTypeInvalidPrimitiveType() {
        assertThrows(AliasException.class, () -> TypeUtils.convertToType(int.class, "123"));
    }

    @Test
    public void convertInvalidInteger() {
        assertThrows(AliasException.class, () -> TypeUtils.convertToType(Integer.class, "this is a string"));
    }

    @Test
    public void convertToTypeNullTest() throws Exception {
        assertNull(TypeUtils.convertToType(String.class, null), "String null conversion failed");
        assertNull(TypeUtils.convertToType(Character.class, ""), "Character null conversion failed");
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
        assertEquals(expected, TypeUtils.convertStringToMap(str, ","), "String to Map conversion failed");
        assertEquals(expected, TypeUtils.convertStringToMap(json, ","), "JSON to Map conversion failed");
        assertEquals(expected, TypeUtils.convertToType(Map.class, str, ","), "String to Map conversion failed");
        assertEquals(expected, TypeUtils.convertToType(Map.class, expected), "Map to Map conversion failed");
    }

    @Test
    public void convertListToArray() throws Exception {
        List<String> list = new ArrayList<>();
        list.add("one");
        list.add("two");
        list.add("three");
        Object result = TypeUtils.convertToType(String[].class, list);
        assertNotNull(result, "convertToType returned null for List conversion to String[]");
        assertEquals(String[].class, result.getClass(), "List conversion failed");

    }

    @Test
    public void convertToList() throws Exception {
        String[] array = { "one", "two", "three" };
        List<String> expected = Arrays.asList(array);
        assertEquals(expected, TypeUtils.convertToType(List.class, array), "List from array conversion failed");
        String str = "one, two, three";
        assertEquals(expected, TypeUtils.convertToType(List.class, str), "List from string conversion failed");
        String[] empty = {};
        assertNull(TypeUtils.convertToType(List.class, empty), "List from empty list conversion failed");
    }

    @Test
    public void convertToProperties() throws Exception {
        String str = "key1=value1;key2=value2";

        Properties expected = new Properties();
        expected.put("key1", "value1");
        expected.put("key2", "value2");
        assertEquals(expected, TypeUtils.convertToType(Properties.class, str, ";"), "Properties from String failed");

        Map<String, String> map = new HashMap<>();
        map.put("key1", "value1");
        map.put("key2", "value2");
        assertEquals(expected, TypeUtils.convertToType(Properties.class, map, ";"), "Properties from Map failed");

    }

    @Test
    public void convertDictToProperties() throws Exception {
        PyDictionary dict = new PyDictionary();
        // test special processing to remove trailing L from PyLong, such as 25L
        dict.__setitem__("mail.smtp.port", new PyLong(25));
        dict.__setitem__("mail.smtp.host", new PyString("192.168.56.1"));

        Properties result = (Properties) TypeUtils.convertToType(Properties.class, dict);

        Properties expected = new Properties();
        expected.put("mail.smtp.port", "25");
        expected.put("mail.smtp.host", "192.168.56.1");

        assertEquals(expected, result, "Properties from dict failed");
    }
}
