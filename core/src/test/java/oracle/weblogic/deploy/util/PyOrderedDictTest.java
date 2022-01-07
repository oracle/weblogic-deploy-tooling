/*
 * Copyright (c) 2017, 2022, Oracle Corporation and/or its affiliates.  All rights reserved.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.util;

import org.junit.jupiter.api.Test;
import org.python.core.PyDictionary;
import org.python.core.PyInteger;
import org.python.core.PyList;
import org.python.core.PyObject;
import org.python.core.PyString;
import org.python.core.PyTuple;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

public class PyOrderedDictTest {
    @Test
    void testIsInstance() {
        PyOrderedDict myOrderedDict = new PyOrderedDict();
        boolean result = (myOrderedDict instanceof PyDictionary);
        assertTrue(result, "isinstance(myOrderedDict, dict) returns true");
    }

    @Test
    void testSetItem() {
        PyOrderedDict myOrderedDict = new PyOrderedDict();

        myOrderedDict.__setitem__("nba_player", new PyString("Steph Curry"));
        myOrderedDict.__setitem__("nba_mvp_count", new PyInteger(1));
        myOrderedDict.__setitem__("is_retired", new PyInteger(0));
        PyObject[] years = new PyObject[3];
        years[0] = new PyString("2015");
        years[1] = new PyString("2016");
        years[2] = new PyString("2017");
        myOrderedDict.__setitem__("nba_finals_years", new PyList(years));

        PyObject key = new PyString("nba_mvp_count");
        PyObject value = myOrderedDict.get(key);

        assertEquals(((PyInteger)value).getValue(), 1, "myOrderedDict.get(key) returned PyInteger(1)");
    }

    @Test
    void testKeyOrdering() {
        PyOrderedDict myOrderedDict = new PyOrderedDict();

        myOrderedDict.__setitem__("one", new PyInteger(1));
        myOrderedDict.__setitem__("two", new PyInteger(2));
        myOrderedDict.__setitem__("five", new PyInteger(5));
        myOrderedDict.__setitem__("three", new PyInteger(3));
        myOrderedDict.__setitem__("four", new PyInteger(4));

        PyObject[] keys = new PyObject[myOrderedDict.__len__()];
        keys[0] = new PyString("one");
        keys[1] = new PyString("two");
        keys[2] = new PyString("five");
        keys[3] = new PyString("three");
        keys[4] = new PyString("four");

        PyList expected = new PyList(keys);

        // A myOrderedDict.keys() needs to return the keys, in the
        // exact order that they were inserted
        PyList myOrderedDictKeys = myOrderedDict.keys();
        for (int i = 0; i < myOrderedDict.__len__(); i++) {
            assertEquals(expected.get(i), myOrderedDictKeys.get(i), "expected.get(" + i + ") == myOrderedDictKeys.get(" + i +")");
        }
    }

    @Test
    void testIteritems() {
        PyOrderedDict myOrderedDict = new PyOrderedDict();

        myOrderedDict.__setitem__("one", new PyInteger(1));
        myOrderedDict.__setitem__("two", new PyInteger(2));
        myOrderedDict.__setitem__("five", new PyInteger(5));
        myOrderedDict.__setitem__("three", new PyInteger(3));
        myOrderedDict.__setitem__("four", new PyInteger(4));

        PyOrderedDict.PyOrderedDictIter pyIterator = (PyOrderedDict.PyOrderedDictIter)myOrderedDict.iteritems();

        while (pyIterator.hasNext()){
            PyTuple tuple = (PyTuple)pyIterator.next();
            PyObject[] entry = tuple.getArray();
        }
    }

    @Test
    void testOrderedDictAsValue() {
        PyOrderedDict myOrderedDict = new PyOrderedDict();
        PyOrderedDict anotherOrderedDict = new PyOrderedDict();
        anotherOrderedDict.__setitem__("nested_key", new PyString("nested_value"));
        myOrderedDict.__setitem__("ordered_dict", anotherOrderedDict);

        PyObject value = myOrderedDict.get(new PyString("ordered_dict"));
    }

    @Test
    void testCopyConstructor() {
        PyOrderedDict myOrderedDict = new PyOrderedDict();

        myOrderedDict.__setitem__("foo", new PyString("bar"));
        PyOrderedDict anotherOrderedDict = new PyOrderedDict(myOrderedDict);
        assertEquals(myOrderedDict.keys(), anotherOrderedDict.keys());
    }

    @Test
    void testUpdate() {
        PyOrderedDict myOrderedDict = new PyOrderedDict();
        myOrderedDict.__setitem__("network_type", new PyString("ETHERNET"));

        PyDictionary anotherDict = new PyDictionary();
        anotherDict.__setitem__("modem_type", new PyString("Motorola MB8600"));

        PyObject[] keys = new PyObject[2];
        keys[0] = new PyString("network_type");
        keys[1] = new PyString("modem_type");

        PyList expected = new PyList(keys);

        myOrderedDict.update(anotherDict);

        PyList myOrderedDictKeys = myOrderedDict.keys();

        assertEquals(myOrderedDictKeys, expected);
    }
}
