/*
 * Copyright (c) 2022, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.util;

import org.python.core.Py;
import org.python.core.PyObject;
import org.python.core.PyString;

/**
 * A boolean value that can be passed to and from parsers, and converted to other types.
 * The PyBoolean type doesn't exist before Jython 2.7, so this allows
 * boolean values to be distinguished from other types.
 */
public class PyRealBoolean extends PyObject {
    private final boolean isTrue;

    public PyRealBoolean(boolean isTrue) {
        this.isTrue = isTrue;
    }

    public boolean getValue() {
        return isTrue;
    }

    // support Python copy.deepcopy()
    public PyRealBoolean __deepcopy__(PyObject memo) {
        return new PyRealBoolean(isTrue);
    }

    @Override
    // for Python equality checks like abc == xyz
    public PyObject __eq__(PyObject ob_other) {
        return equals(ob_other) ? Py.One : Py.Zero;
    }

    @Override
    // for Python inequality checks like abc != xyz
    public PyObject __ne__(PyObject ob_other) {
        return equals(ob_other) ? Py.Zero : Py.One;
    }

    @Override
    // for Python string conversion, like str(abc)
    public PyString __str__() {
        return new PyString(toString());
    }

    @Override
    // for Python boolean check, such as bool(abc), or if abc...
    public boolean __nonzero__() {
        return isTrue;
    }

    @Override
    public boolean equals(Object other) {
        if(other instanceof PyRealBoolean) {
            return isTrue == ((PyRealBoolean) other).isTrue;
        }
        return false;
    }

    @Override
    public String toString() {
        return String.valueOf(isTrue);
    }
}
