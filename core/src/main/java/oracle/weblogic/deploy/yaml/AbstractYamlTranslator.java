/*
 * Copyright (c) 2017, 2022, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.yaml;

import java.io.InputStream;
import java.io.Writer;
import java.math.BigDecimal;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

import oracle.weblogic.deploy.logging.PlatformLogger;
import oracle.weblogic.deploy.util.PyOrderedDict;

import oracle.weblogic.deploy.util.PyRealBoolean;
import org.python.core.Py;
import org.python.core.PyDictionary;
import org.python.core.PyFloat;
import org.python.core.PyInteger;
import org.python.core.PyList;
import org.python.core.PyLong;
import org.python.core.PyObject;
import org.python.core.PyString;
import org.python.core.PyUnicode;

import org.yaml.snakeyaml.DumperOptions;
import org.yaml.snakeyaml.LoaderOptions;
import org.yaml.snakeyaml.Yaml;

/**
 * This class does the heavy-lifting of walking the parse tree and performing the conversion into a Python dictionary.
 */
public abstract class AbstractYamlTranslator {

    private final boolean useOrderedDict;
    private final boolean useUnicode;
    private final String fileName;
    private final int codePointsLimit;

    protected abstract PlatformLogger getLogger();
    protected abstract String getClassName();

    // override to return a list of documents as Python dictionaries from the YAML
    public abstract PyList parseDocuments(boolean allowMultiple) throws YamlException;

    // override to write a list of documents as Python dictionaries to the YAML
    public abstract void dumpDocuments(List<?> documents) throws YamlException;

    protected AbstractYamlTranslator(String fileName, boolean useOrderedDict, boolean useUnicode, int codePointsLimit) {
        this.fileName = fileName;
        this.useOrderedDict = useOrderedDict;
        this.useUnicode = useUnicode;
        this.codePointsLimit = codePointsLimit;
    }

    /**
     * This method triggers parsing of the file and conversion into a Python dictionary.
     * If the YAML is empty, a single empty dictionary is returned.
     * If the YAML contains multiple documents, a YamlException is thrown
     *
     * @return the python dictionary corresponding to the YAML input file
     * @throws YamlException if an error occurs while reading the input file
     */
    public PyDictionary parse() throws YamlException {
        PyDictionary result;
        PyList dictionaries = parseDocuments(false);
        if (dictionaries.isEmpty()) {
            result = getNewDictionary();
        } else {
            result = (PyDictionary) dictionaries.get(0);
        }
        return result;
    }

    @SuppressWarnings("WeakerAccess")
    protected PyList parseInternal(InputStream inputStream, boolean allowMultiple) throws YamlException {
        final String METHOD = "parseInternal";

        // there are problems using PyList.add(),
        // so build a java.util.List and construct PyList(javaList).
        List<PyObject> result = new ArrayList<>();
        if (inputStream != null) {
            Yaml parser = new Yaml(this.getDefaultLoaderOptions());

            try {
                Iterable<Object> docsIterable = parser.loadAll(inputStream);
                List<Object> documents = new ArrayList<>();
                for (Object document : docsIterable) {
                    documents.add(document);
                }

                // don't continue with conversion if multiple documents check fails
                if(!allowMultiple && documents.size() > 1) {
                    YamlException pex = new YamlException("WLSDPLY-18101", this.fileName, documents.size());
                    getLogger().throwing(getClassName(), METHOD, pex);
                    throw pex;
                }

                for (Object document : documents) {
                    result.add(convertJavaDataStructureToPython(document));
                }
            } catch (YamlException yex) {
                throw yex;
            } catch (Exception ex) {
                YamlException pex = new YamlException("WLSDPLY-18100", ex, this.fileName, ex.getLocalizedMessage());
                getLogger().throwing(getClassName(), METHOD, pex);
                throw pex;
            }
        }
        return new PyList(result.toArray(new PyObject[0]));
    }

    public void dump(Map<String, Object> data) throws YamlException {
        List<Map<String, Object>> list = new ArrayList<>();
        list.add(data);
        dumpDocuments(list);
    }

    @SuppressWarnings("WeakerAccess")
    protected void dumpInternal(List<?> data, Writer outputWriter) throws YamlException {
        final String METHOD = "dumpInternal";

        if (outputWriter != null) {
            DumperOptions dumperOptions = getDefaultDumperOptions();
            YamlRepresenter representer = new YamlRepresenter(dumperOptions);
            Yaml yaml = new Yaml(representer, dumperOptions);

            try {
                yaml.dumpAll(data.iterator(), outputWriter);
            } catch (Exception ex) {
                YamlException pex = new YamlException("WLSDPLY-18107", ex, this.fileName, ex.getLocalizedMessage());
                getLogger().throwing(getClassName(), METHOD, pex);
                throw pex;
            }
        }
    }

    private LoaderOptions getDefaultLoaderOptions() {
        LoaderOptions result = new LoaderOptions();
        result.setAllowDuplicateKeys(false);
        // Turning on setProcessComments seems to trigger a parsing bug when dealing with
        // tags with no value so leave it off...
        //
        if (this.codePointsLimit > 0) {
            result.setCodePointLimit(this.codePointsLimit);
        } else if (this.codePointsLimit < 0 ){
            getLogger().fine("WLSDPLY-18111", this.codePointsLimit);
        }
        return result;
    }

    private DumperOptions getDefaultDumperOptions() {
        DumperOptions result = new DumperOptions();
        result.setIndent(4);
        result.setIndicatorIndent(2);
        result.setDefaultFlowStyle(DumperOptions.FlowStyle.BLOCK);
        result.setNonPrintableStyle(DumperOptions.NonPrintableStyle.ESCAPE);
        result.setProcessComments(true);
        return result;
    }

    private PyDictionary convertJavaDataStructureToPython(Object object) throws YamlException {
        final String METHOD = "convertJavaDataStructureToPython";

        PyDictionary result;
        if (object != null) {
            if (Map.class.isAssignableFrom(object.getClass())) {
                @SuppressWarnings("unchecked")
                Map<String, Object> map = (Map<String, Object>) object;
                result = convertToPythonDictionary(map);
            } else {
                YamlException pex = new YamlException("WLSDPLY-18103", this.fileName, object.getClass().getName());
                getLogger().throwing(getClassName(), METHOD, pex);
                throw pex;
            }
        } else {
            YamlException pex = new YamlException("WLSDPLY-18104", this.fileName);
            getLogger().throwing(getClassName(), METHOD, pex);
            throw pex;
        }
        return result;
    }

    private PyDictionary convertToPythonDictionary(Map<String, Object> map) throws YamlException {
        PyDictionary result;
        if (map != null) {
            result = getNewDictionary();
            for (Map.Entry<String, Object> entry : map.entrySet()) {
                String key = entry.getKey();
                Object value = entry.getValue();

                PyObject pyKey = convertScalarToPythonObject(key);
                if (value == null) {
                    // snakeyaml sets the value of an empty map node to null.
                    // WDT relies on it being an empty dictionary so set all
                    // nulls to an empty dictionary and hope this doesn't break
                    // anything else...
                    //
                    result.__setitem__(pyKey, getNewDictionary());
                } else if (Map.class.isAssignableFrom(value.getClass())) {
                    @SuppressWarnings("unchecked")
                    Map<String, Object> mapValue = (Map<String, Object>) value;
                    PyDictionary pyValue = convertToPythonDictionary(mapValue);
                    result.__setitem__(pyKey, pyValue);
                } else if (List.class.isAssignableFrom(value.getClass())) {
                    @SuppressWarnings("unchecked")
                    List<Object> listValue = (List<Object>) value;
                    PyList pyValue = convertToPythonList(listValue);
                    result.__setitem__(pyKey, pyValue);
                } else {
                    PyObject pyValue = convertScalarToPythonObject(value);
                    result.__setitem__(pyKey, pyValue);
                }
            }
        } else {
            // This should never happen since we are looking at the object's class prior to dispatching
            // the call to this method so a null object will never get here.  This is just defensive
            // coding...
            //
            getLogger().severe("WLSDPLY-18105", this.fileName);
            result = getNewDictionary();
        }
        return result;
    }

    private PyList convertToPythonList(List<Object> list) throws YamlException {
        PyList result;
        if (list != null) {
            // For whatever reason PyList.pyadd() isn't working here so create a Java List
            // and once if it populated, convert it to a PyList...
            //
            List<PyObject> container = new ArrayList<>();
            for (Object element : list) {
                if (element == null) {
                    container.add(Py.None);
                } else if (Map.class.isAssignableFrom(element.getClass())) {
                    @SuppressWarnings("unchecked")
                    Map<String, Object> mapValue = (Map<String, Object>) element;
                    PyDictionary pyValue = convertToPythonDictionary(mapValue);
                    container.add(pyValue);
                } else if (List.class.isAssignableFrom(element.getClass())) {
                    @SuppressWarnings("unchecked")
                    List<Object> listValue = (List<Object>) element;
                    PyList pyValue = convertToPythonList(listValue);
                    container.add(pyValue);
                } else {
                    PyObject pyValue = convertScalarToPythonObject(element);
                    container.add(pyValue);
                }
            }
            result = new PyList(container.toArray(new PyObject[0]));
        } else {
            // This should never happen since we are looking at the object's class prior to dispatching
            // the call to this method so a null object will never get here.  This is just defensive
            // coding...
            //
            getLogger().severe("WLSDPLY-18106", this.fileName);
            result = new PyList();
        }
        return result;
    }

    private PyObject convertScalarToPythonObject(Object object) throws YamlException {
        final String METHOD = "convertScalarToPythonObject";

        PyObject result = Py.None;
        if (object != null) {
            String classname = object.getClass().getName();
            switch (classname) {
                case "java.lang.String":
                    if (this.useUnicode) {
                        result = new PyUnicode((String) object);
                    } else {
                        result = new PyString((String) object);
                    }
                    break;

                case "java.lang.Boolean":
                    result = new PyRealBoolean((Boolean) object);
                    break;

                case "java.lang.Integer":
                    result = new PyInteger((Integer) object);
                    break;

                case "java.lang.Long":
                    result = new PyLong((Long) object);
                    break;

                case "java.math.BigInteger":
                    result = new PyLong((BigInteger) object);
                    break;

                case "java.lang.Float":
                    result = new PyFloat((Float) object);
                    break;

                case "java.lang.Double":
                    result = new PyFloat((Double) object);
                    break;

                case "java.math.BigDecimal":
                    result = new PyFloat(((BigDecimal) object).doubleValue());
                    break;

                default:
                    YamlException pex = new YamlException("WLSDPLY-18102", this.fileName, classname);
                    getLogger().throwing(getClassName(), METHOD, pex);
                    throw pex;
            }
        }
        return result;
    }

    private PyDictionary getNewDictionary() {
        return useOrderedDict ? new PyOrderedDict() : new PyDictionary();
    }

    private Map<String, Object> replaceNoneInMap(Map<String, Object> map) {
        Map<String, Object> result = null;
        if (map != null && map != Py.None) {
            result = map;
            for (Map.Entry<String, Object> entry : map.entrySet()) {
                Object value = entry.getValue();

                if (value == Py.None) {
                    entry.setValue(null);
                } else if (Map.class.isAssignableFrom(value.getClass())) {
                    @SuppressWarnings("unchecked")
                    Map<String, Object> mapValue = (Map<String, Object>) value;
                    entry.setValue(replaceNoneInMap(mapValue));
                } else if (List.class.isAssignableFrom(value.getClass())) {
                    @SuppressWarnings("unchecked")
                    List<Object> listValue = (List<Object>) value;
                    entry.setValue(replaceNoneInList(listValue));
                }
            }
        }
        return result;
    }

    private List<Object> replaceNoneInList(List<Object> list) {
        List<Object> result = null;
        if (list != null && list != Py.None) {
            result = list;
            for (int i = 0; i < list.size(); i++) {
                Object element = list.get(i);
                if (element == Py.None) {
                    result.set(i, null);
                } else if (Map.class.isAssignableFrom(element.getClass())) {
                    @SuppressWarnings("unchecked")
                    Map<String, Object> mapValue = (Map<String, Object>) element;
                    result.set(i, replaceNoneInMap(mapValue));
                } else if (List.class.isAssignableFrom(element.getClass())) {
                    @SuppressWarnings("unchecked")
                    List<Object> listValue = (List<Object>) element;
                    result.set(i, replaceNoneInList(listValue));
                }
            }
        }
        return result;
    }
}
