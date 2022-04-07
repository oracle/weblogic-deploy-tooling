/*
 * Copyright (c) 2017, 2022, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.util;

import java.io.IOException;
import java.io.ObjectInputStream;
import java.util.ArrayList;
import java.util.Collection;
import java.util.Iterator;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

import oracle.weblogic.deploy.exception.ExceptionHelper;
import oracle.weblogic.deploy.logging.PlatformLogger;
import oracle.weblogic.deploy.logging.WLSDeployLogFactory;

import org.python.core.Py;
import org.python.core.PyDictionary;
import org.python.core.PyIterator;
import org.python.core.PyList;
import org.python.core.PyObject;
import org.python.core.PyString;
import org.python.core.PyTuple;
import org.python.core.PyType;
import org.python.core.ThreadState;

/**
 * A basic implementation of a Python dictionary that preserves order.
 */
public final class PyOrderedDict extends PyDictionary implements Iterable<PyObject> {
    private static final long serialVersionUID = 1L;

    private static final PlatformLogger LOGGER = WLSDeployLogFactory.getLogger("wlsdeploy.util");

    private final LinkedHashMap<PyObject, PyObject> linkedHashMap;

    private final transient CommentMap commentMap = new CommentMap();

    /**
     * The no-args constructor.
     */
    public PyOrderedDict() {
        super(PyType.fromClass(PyOrderedDict.class));
        this.linkedHashMap = new LinkedHashMap<>();
    }

    /**
     * The copy constructor.
     *
     * @param other the object to copy
     */
    public PyOrderedDict(PyOrderedDict other) {
        this();
        super.update(other);
        update(other);
    }

    /**
     * Creates a new PyOrderedDict from a list of keys with the values all set to null.
     * This method hides the PyDictionary fromkeys() static method that does the same thing
     * except that it returns a PyDictionary object.
     *
     * @param keys the keys
     * @return the new PyOrderedDict with the specified keys and null values
     */
    @SuppressWarnings("unused")
    public static PyObject fromkeys(PyObject keys) {
        return fromkeys(keys, null);
    }

    /**
     * Creates a new PyOrderedDict from a list of keys with the values all set to the specified value.
     * This method hides the PyDictionary fromkeys() static method that does the same thing
     * except that it returns a PyDictionary object.
     *
     * @param keys the keys
     * @param value the default value for all keys
     * @return the new PyOrderedDict with the specified keys and their default value
     */
    public static PyObject fromkeys(PyObject keys, PyObject value) {
        return dictFromKeys(PyType.fromClass(PyOrderedDict.class), keys, value);
    }

    /*
     * The following methods are delegated to the PyDictionary superclass:
     *
     * public int hashCode()
     * public boolean isSequenceType()
     */

    /**
     * {@inheritDoc}
     */
    @Override
    public int __cmp__(PyObject obOther) {
        int result = 0;

        PyOrderedDict other = null;
        if (obOther == null || obOther.getType() != getType()) {
            return -2;
        } else {
            other = (PyOrderedDict) obOther;
            int an = this.linkedHashMap.size();
            int bn = other.linkedHashMap.size();
            if (an < bn) {
                return -1;
            } else if (an > bn) {
                return 1;
            }
        }

        PyList akeys = keys();
        PyList bkeys = other.keys();

        akeys.sort();
        bkeys.sort();

        for (int i = 0; i < other.linkedHashMap.size(); i++) {
            PyObject akey = akeys.pyget(i);
            PyObject bkey = bkeys.pyget(i);
            int c = akey._cmp(bkey);
            if (c != 0) {
                result = c;
            } else {
                PyObject avalue = __finditem__(akey);
                PyObject bvalue = other.__finditem__(bkey);
                if (avalue == null && bvalue == null) {
                    continue;
                } else if (avalue == null || bvalue == null) {
                    result = -3;
                } else {
                    c = avalue._cmp(bvalue);
                    if (c != 0) {
                        result = c;
                    }
                }
            }
            if (result != 0) {
                break;
            }
        }
        return result;
    }

    /**
     * {@inheritDoc}
     */
    @Override
    public boolean __contains__(PyObject key) {
        return this.has_key(key);
    }

    /**
     * The internal method that the copy.deepcopy() implementation looks for
     * to perform a deepcopy on non-built-in types.  Note that this implementation
     * has limitations in that it only knows how to deepcopy a limited set of types
     * (NoneType, int, long, float, str, list, dict, and PyOrderedDict).  Any other
     * types encountered will log an error and return the original object without
     * copying.  Support for new types can be added in the switch statement in
     * the internal doDeepCopy() method.
     *
     * @param memo the memo dictionary that keeps track of the new versions of the original objects
     * @return a new deepcopy of this PyOrderedDictionary
     */
    @SuppressWarnings("WeakerAccess")
    public PyOrderedDict __deepcopy__(PyObject memo){
        // memo is actually a Python dict object, so go ahead and cast it
        PyDictionary memoDict;
        if (PyDictionary.class.isAssignableFrom(memo.getClass())) {
            memoDict = PyDictionary.class.cast(memo);
        } else {
            String message = ExceptionHelper.getMessage("WLSDPLY-01250", memo.getClass().getName(),
                    PyDictionary.class.getName());
            throw Py.TypeError(message);
        }
        PyOrderedDict newPyOrderedDict = new PyOrderedDict();

        // Use value returned from Py.idstr(this) as the key for the entry
        // we add to memo dictionary, which was passed to us by reference.
        // Doing this avoids excessive copying, when the object itself is
        // referenced from one of it's attributes.
        memoDict.__setitem__(new PyString(Py.idstr(this)), newPyOrderedDict);

        for (Map.Entry<PyObject, PyObject> entry : linkedHashMap.entrySet()) {
            PyObject newKey = doDeepCopy(entry.getKey(), memo);
            PyObject newValue = doDeepCopy(entry.getValue(), memo);
            newPyOrderedDict.__setitem__(newKey, newValue);
        }
        return newPyOrderedDict;
    }

    /**
     * {@inheritDoc}
     */
    @Override
    public void __delitem__(PyObject key) {
        synchronized (this.linkedHashMap){
            PyObject ret = this.linkedHashMap.remove(key);
            if (ret == null) {
                throw Py.KeyError(key.toString());
            }
        }
        super.__delitem__(key);
    }

    /**
     * {@inheritDoc}
     */
    @Override
    public PyObject __eq__(PyObject obOther) {
        if (obOther.getType() != getType()) {
            return null;
        }

        PyObject result = Py.One;
        PyOrderedDict other = (PyOrderedDict)obOther;
        int an = this.linkedHashMap.size();
        int bn = other.linkedHashMap.size();
        if (an != bn) {
            result = Py.Zero;
        } else {
            PyList akeys = keys();
            for (int i = 0; i < an; i++) {
                PyObject akey = akeys.pyget(i);
                PyObject bvalue = other.__finditem__(akey);
                if (bvalue == null) {
                    result = Py.Zero;
                } else {
                    PyObject avalue = __finditem__(akey);
                    if (!avalue._eq(bvalue).__nonzero__()) {
                        result = Py.Zero;
                    }
                }
                if (result == Py.Zero) {
                    break;
                }
            }
        }
        return result;
    }

    /**
     * {@inheritDoc}
     */
    @Override
    public PyObject __finditem__(PyObject key) {
        return this.get(key);
    }

    /**
     * {@inheritDoc}
     */
    @Override
    public PyObject __iter__(){
        return new PyOrderedDictIter(this, this.linkedHashMap.keySet(), PyOrderedDictIter.KEYS);
    }

    /**
     * {@inheritDoc}
     */
    @Override
    public int __len__() {
        return this.linkedHashMap.size();
    }

    /**
     * {@inheritDoc}
     */
    @Override
    public boolean __nonzero__() {
        return this.linkedHashMap.size() != 0;
    }

    /**
     * {@inheritDoc}
     */
    @Override
    public void __setitem__(PyObject key, PyObject value) {
        synchronized (this.linkedHashMap) {
            this.linkedHashMap.put(key, value);
        }
        // do not access protected field directly.
        // 2.7 version does not have table variable.
        // Neither version has synchronization on the table.
        super.__setitem__(key, value);
    }

    /**
     * {@inheritDoc}
     */
    @Override
    public void clear() {
        this.linkedHashMap.clear();
        super.clear();
    }

    /**
     * {@inheritDoc}
     */
    @Override
    public PyOrderedDict copy() {
        PyOrderedDict newPyOrderedDict = new PyOrderedDict();
        newPyOrderedDict.doUpdate(this);
        return newPyOrderedDict;
    }

    /**
     * {@inheritDoc}
     */
    @Override
    public PyObject get(PyObject key) {
        return this.get(key, Py.None);
    }

    /**
     * {@inheritDoc}
     */
    @Override
    public PyObject get(PyObject key, PyObject defaultObject) {
        // Cannot use getOrDefault() as this is a Java 8 method and
        // the project is attempting to be compatible with Java 7...
        PyObject result = defaultObject;
        if (linkedHashMap.containsKey(key)) {
            result = linkedHashMap.get(key);
        }
        return result;
    }

    /**
     * {@inheritDoc}
     */
    @Override
    public boolean has_key(PyObject key) {
        return this.linkedHashMap.containsKey(key);
    }

    /**
     * {@inheritDoc}
     */
    @Override
    public PyList items() {
        Set<Map.Entry<PyObject, PyObject>> entries = this.linkedHashMap.entrySet();
        List<PyObject> l = new ArrayList<>(entries.size());
        for (Map.Entry<PyObject, PyObject> entry: entries) {
            l.add(new PyTuple(new PyObject[] { entry.getKey(), entry.getValue() }));
        }
        return new PyList(l.toArray(new PyObject[0]));
    }

    /**
     * {@inheritDoc}
     */
    @Override
    public Iterator<PyObject> iterator(){
        return new PyOrderedDictIter(this, this.linkedHashMap.keySet(), PyOrderedDictIter.ITEMS);
    }

    /**
     * {@inheritDoc}
     */
    @Override
    public PyObject iterkeys() {
        return new PyOrderedDictIter(this, this.linkedHashMap.keySet(), PyOrderedDictIter.KEYS);
    }

    /**
     * {@inheritDoc}
     */
    @Override
    public PyObject itervalues() {
        return new PyOrderedDictIter(this, this.linkedHashMap.keySet(), PyOrderedDictIter.VALUES);
    }

    /**
     * {@inheritDoc}
     */
    @Override
    public PyObject iteritems() {
        return new PyOrderedDictIter(this, this.linkedHashMap.keySet(), PyOrderedDictIter.ITEMS);
    }

    /**
     * {@inheritDoc}
     */
    @Override
    public PyList keys() {
        Set<PyObject> keys = this.linkedHashMap.keySet();
        List<PyObject> v = new ArrayList<>(keys.size());
        v.addAll(keys);
        return new PyList(v.toArray(new PyObject[0]));
    }

    /**
     * {@inheritDoc}
     */
    @Override
    public PyObject pop(PyObject key) {
        return this.pop(key, null);
    }

    /**
     * {@inheritDoc}
     */
    @Override
    public PyObject pop(PyObject key, PyObject defaultValue) {
        if (!this.__contains__(key)) {
            return defaultValue;
        }
        PyObject val = this.get(key);
        this.__delitem__(key);
        return val;
    }

    /**
     * {@inheritDoc}
     */
    @Override
    public String toString(){
        ThreadState ts = Py.getThreadState();
        if (!ts.enterRepr(this)) {
            return "{...}";
        }

        Set<Map.Entry<PyObject, PyObject>> entries = this.linkedHashMap.entrySet();
        StringBuilder buf = new StringBuilder("{");
        for (Map.Entry<PyObject, PyObject> entry: entries) {
            buf.append((entry.getKey()).__repr__());
            buf.append(": ");
            buf.append((entry.getValue()).__repr__());
            buf.append(", ");
        }
        if(buf.length() > 1){
            buf.delete(buf.length() - 2, buf.length());
        }
        buf.append('}');

        ts.exitRepr(this);
        return buf.toString();
    }

    /**
     * {@inheritDoc}
     */
    @Override
    public void update(PyObject od) {
        if (od instanceof PyDictionary) {
            doUpdate((PyDictionary)od);
        } else {
            doUpdate(od, od.invoke("keys"));
        }
    }

    /**
     * {@inheritDoc}
     * This method is not supported, as it is not portable between versions of Jython.
     * Jython 2.1 returns PyList, Jython 2.7 returns a Collection.
     * WDT code should use getValues() to get ordered values.
     */
    @Override
    public PyList values() {
        String message = ExceptionHelper.getMessage("WLSDPLY-01252");
        throw new UnsupportedOperationException(message);
    }

    /**
     * Because return type for values() is different between Jython 2.1 and Jython 2.7,
     * WDT code should call this variant to get a list of values.
     * @return an ordered list of values
     */
    public PyList getValues() {
        Collection<PyObject> values = this.linkedHashMap.values();
        List<PyObject> v = new ArrayList<>(values.size());
        v.addAll(values);
        return new PyList(v.toArray(new PyObject[0]));
    }

    public CommentMap getCommentMap() {
        return commentMap;
    }

    public void addComment(String key, String comment) {
        commentMap.addComment(key, comment);
    }

    /**
     * {@inheritDoc}
     */
    @Override
    public boolean equals(Object other) {
        boolean result;
        if (this == other) {
            result = true;
        } else if (other == null || this.getClass() != other.getClass()) {
            result = false;
        } else {
            result = super.equals(other);
            if (result) {
                PyOrderedDict otherDict = (PyOrderedDict) other;
                result = this.linkedHashMap.equals(otherDict.linkedHashMap) &&
                    this.commentMap.equals(otherDict.commentMap);
            }
        }
        return result;
    }

    /**
     * {@inheritDoc}
     */
    @Override
    public int hashCode() {
        return super.hashCode() >> 8 + this.linkedHashMap.hashCode() >> 4 + this.commentMap.hashCode();
    }

    // private methods

    private static PyObject dictFromKeys(PyType type, PyObject keys, PyObject value) {
        if (value == null) {
            value = Py.None;
        }
        PyObject d = type.__call__();
        PyIterator iter = (PyIterator)keys.__iter__();
        for (PyObject o = iter.__iternext__();o != null;o = iter.__iternext__()) {
            d.__setitem__(o, value);
        }
        return d;
    }

    private void doUpdate(PyDictionary od) {
        PyList pylist = od.items();

        for (int i = 0; i < pylist.size(); i++) {
            PyTuple tuple = (PyTuple) pylist.get(i);
            this.__setitem__(Py.java2py(tuple.get(0)), Py.java2py(tuple.get(1)));
            super.__setitem__(Py.java2py(tuple.get(0)), Py.java2py(tuple.get(1)));
        }
    }

    private void doUpdate(PyObject d,PyObject keys) {
        PyObject iter = keys.__iter__();
        for (PyObject key; (key = iter.__iternext__()) != null;) {
            __setitem__(key, d.__getitem__(key));
        }
    }

    private static PyObject doDeepCopy(PyObject orig, PyObject memo) {
        PyObject result;
        PyType origType = orig.getType();

        String typeName = origType.fastGetName();
        switch(typeName) {
            case "bool":
            case "float":
            case "int":
            case "long":
            case "NoneType":
            case "str":
            case "unicode":
            case "PyRealBoolean":
            case "oracle.weblogic.deploy.util.PyRealBoolean":
                result = orig;
                break;

            case "list":
                result = deepCopyList(orig, memo);
                break;

            case "dict":
                result = deepCopyDict(orig, memo);
                break;

            case "PyOrderedDict":
            case "oracle.weblogic.deploy.util.PyOrderedDict":
                // Jython 2.7 uses qualified class name
                PyOrderedDict origOrderedDict = PyOrderedDict.class.cast(orig);
                result = origOrderedDict.__deepcopy__(memo);
                break;

            default:
                LOGGER.severe("WLSDPLY-01251", typeName);
                result = orig;
        }
        return Py.java2py(result);
    }

    private static PyList deepCopyList(PyObject orig, PyObject memo) {
        PyList origList = PyList.class.cast(orig);
        PyDictionary memoDict = PyDictionary.class.cast(memo);

        PyList newList = new PyList();
        memoDict.__setitem__(new PyString(Py.idstr(orig)), newList);
        for (int i = 0; i < origList.size(); i++) {
            PyObject origMember = origList.pyget(i);
            PyObject newMember = doDeepCopy(origMember, memo);
            newList.pyadd(newMember);
        }
        return newList;
    }

    private static PyDictionary deepCopyDict(PyObject orig, PyObject memo) {
        PyDictionary origDict = PyDictionary.class.cast(orig);
        PyDictionary memoDict = PyDictionary.class.cast(memo);

        PyDictionary newDict = new PyDictionary();
        memoDict.__setitem__(new PyString(Py.idstr(orig)), newDict);

        PyObject iter = origDict.keys().__iter__();
        for (PyObject key; (key = iter.__iternext__()) != null;) {
            PyObject newKey = doDeepCopy(key, memo);
            PyObject newValue = doDeepCopy(origDict.__getitem__(key), memo);
            newDict.__setitem__(newKey, newValue);
        }
        return newDict;
    }

    /**
     * Iterator class for PyOrderedDict class.
     */
    static final class PyOrderedDictIter extends PyIterator implements Iterator<PyObject> {
        private static final long serialVersionUID = 1L;

        private static final int KEYS = 0;
        private static final int VALUES = 1;
        private static final int ITEMS = 2;

        private final PyObject orderedDict;
        private final Set<PyObject> dictKeys;
        private final int type;
        private transient Iterator<PyObject> iter;

        private PyOrderedDictIter(PyObject orderedDict, Set<PyObject> dictKeys, int type) {
            this.orderedDict = orderedDict;
            this.dictKeys = new LinkedHashSet<>(dictKeys);
            this.type = type;
            this.iter = dictKeys.iterator();
        }

        /**
         * {@inheritDoc}
         */
        @Override
        public PyObject __iternext__() {
            return next();
        }

        /**
         * {@inheritDoc}
         */
        @Override
        public boolean hasNext(){
            return this.iter.hasNext();
        }

        /**
         * {@inheritDoc}
         */
        @Override
        public PyObject next() {
            PyObject result = null;
            if (hasNext()) {
                PyObject key = this.iter.next();
                switch (type) {
                    case VALUES:
                        result = orderedDict.__finditem__(key);
                        break;

                    case ITEMS:
                        result = new PyTuple(new PyObject[] { key, orderedDict.__finditem__(key) });
                        break;

                    default: // KEYS
                        result = key;
                        break;
                }
            }
            return result;
        }

        @SuppressWarnings("unused")
        private void readObject(ObjectInputStream in) throws IOException, ClassNotFoundException {
            in.defaultReadObject();
            iter = dictKeys.iterator();
        }

        /**
         * {@inheritDoc}
         */
        @Override
        public void remove() {
            throw new UnsupportedOperationException();
        }

        @Override
        public boolean equals(Object other) {
            boolean result;
            if (this == other) {
                result = true;
            } else if (other == null || this.getClass() != other.getClass()) {
                result = false;
            } else {
                result = super.equals(other);
                if (result) {
                    PyOrderedDictIter otherIter = (PyOrderedDictIter) other;
                    result = this.orderedDict.equals(otherIter.orderedDict) &&
                        this.dictKeys.equals(otherIter.dictKeys) &&
                        this.type == otherIter.type &&
                        this.iter.equals(otherIter.iter);
                }
            }
            return result;
        }

        @Override
        public int hashCode() {
            return super.hashCode() >> 16 + this.orderedDict.hashCode() >> 12 +
                this.dictKeys.hashCode() >> 8 + this.iter.hashCode() >> 4 +
                Integer.valueOf(this.type).hashCode();
        }
    }
}
