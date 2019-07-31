/*
 * Copyright (c) 2017, 2019, Oracle and/or its affiliates. All rights reserved.
 * Licensed under the Universal Permissive License v 1.0 as shown at http://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.yaml;

import java.io.IOException;
import java.io.InputStream;
import java.text.MessageFormat;
import java.util.ArrayDeque;
import java.util.Deque;

import oracle.weblogic.deploy.logging.PlatformLogger;
import oracle.weblogic.deploy.util.PyOrderedDict;
import oracle.weblogic.deploy.util.StringUtils;

import org.antlr.v4.runtime.CharStream;
import org.antlr.v4.runtime.CharStreams;
import org.antlr.v4.runtime.CommonTokenStream;
import org.antlr.v4.runtime.atn.PredictionMode;
import org.antlr.v4.runtime.tree.ParseTree;
import org.antlr.v4.runtime.tree.ParseTreeWalker;
import org.python.core.Py;
import org.python.core.PyDictionary;
import org.python.core.PyFloat;
import org.python.core.PyList;
import org.python.core.PyLong;
import org.python.core.PyObject;
import org.python.core.PyString;

/**
 * This class does the heavy-lifting of walking the parse tree and performing the conversion into a Python dictionary.
 */
public abstract class AbstractYamlTranslator extends YamlBaseListener {

    private PyDictionary fileDict;
    private Deque<PyDictionary> currentDict;

    private String lastObjectName;
    private PyList openObjectList;
    @SuppressWarnings("WeakerAccess")
    protected boolean useOrderedDict;

    /**
     * This method triggers parsing of the YAML and conversion into the Python dictionary.
     *
     * @return the python dictionary corresponding to the YAML input
     * @throws YamlException if an error occurs while reading the input
     */
    public abstract PyDictionary parse() throws YamlException;

    /**
     * {@inheritDoc}
     */
    @Override
    public void enterFile(YamlParser.FileContext ctx) {
        if (useOrderedDict) {
            fileDict = new PyOrderedDict();
        } else {
            fileDict = new PyDictionary();
        }
        currentDict = new ArrayDeque<>();
        currentDict.push(fileDict);
    }

    /**
     * {@inheritDoc}
     */
    @Override
    public void enterAssign(YamlParser.AssignContext ctx) {
        String name = getQuotedStringText(ctx.name().getText());
        PyObject value = getAssignValue(name, ctx);

        PyDictionary container = currentDict.peek();

        // null indicates not parsable, Py.None would be returned for legitimate cases
        if (value != null) {
            container.__setitem__(new PyString(name), value);
        }
    }

    /**
     * {@inheritDoc}
     */
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

        PyList myList = getOpenObjectList();
        String madeUpName = MessageFormat.format("{0}[{1}]", lastObjectName, myList.size());
        PyObject value = getScalarValue(madeUpName, valueCtx);
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

    /**
     * {@inheritDoc}
     */
    @Override
    public void enterObject(YamlParser.ObjectContext ctx) {
        String name = getQuotedStringText(ctx.name().getText());
        PyDictionary objDict;
        if (useOrderedDict) {
            objDict = new PyOrderedDict();
        } else {
            objDict = new PyDictionary();
        }

        PyDictionary container = currentDict.peek();
        container.__setitem__(new PyString(name), objDict);
        currentDict.push(objDict);

        // In case this is the name for a list of values, save it off...
        lastObjectName = name;
    }

    /**
     * {@inheritDoc}
     */
    @Override
    public void exitObj_block(YamlParser.Obj_blockContext ctx) {
        if (openObjectList != null) {
            // Pop off the dictionary that is created by default for all new objects off the current stack
            currentDict.pop();

            PyDictionary container = currentDict.peek();
            container.__setitem__(new PyString(lastObjectName), openObjectList);

            // zero out the open list
            openObjectList = null;
        } else {
            currentDict.pop();
        }
    }

    /**
     * {@inheritDoc}
     */
    @Override
    public void exitFile(YamlParser.FileContext ctx) {
        currentDict.pop();
    }

    protected abstract String getClassName();
    protected abstract PlatformLogger getLogger();

    @SuppressWarnings("WeakerAccess")
    protected PyDictionary parseInternal(String yamlFileName, InputStream yamlStream) throws YamlException {
        final String METHOD = "parseInternal";

        getLogger().entering(getClassName(), METHOD);
        if (yamlStream != null) {
            YamlErrorListener errorListener = new YamlErrorListener(yamlFileName, false);
            try {
                CharStream input = CharStreams.fromStream(yamlStream);
                YamlLexer lexer = new YamlLexer(input);
                CommonTokenStream tokens = new CommonTokenStream(lexer);
                YamlParser parser = new YamlParser(tokens);

                parser.removeErrorListeners();
                parser.addErrorListener(errorListener);
                parser.getInterpreter().setPredictionMode(PredictionMode.LL_EXACT_AMBIG_DETECTION);

                ParseTree tree = parser.file();
                ParseTreeWalker walker = new ParseTreeWalker();
                walker.walk(this, tree);
            } catch (IOException ioe) {
                YamlException ex =
                    new YamlException("WLSDPLY-18007", ioe, "YAML", yamlFileName, ioe.getLocalizedMessage());
                getLogger().throwing(getClassName(), METHOD, ex);
                throw ex;
            }

            int errorCount = errorListener.getErrorCount();
            if (errorCount > 0) {
                YamlException ye = new YamlException("WLSDPLY-18017", "YAML", errorCount, yamlFileName);
                getLogger().throwing(getClassName(), METHOD, ye);
                throw ye;
            }
        }
        getLogger().exiting(getClassName(), METHOD, fileDict);
        return fileDict;
    }

    private PyObject getAssignValue(String name, YamlParser.AssignContext ctx) {
        YamlParser.ValueContext valueCtx = ctx.value();
        PyObject value;

        if (YamlParser.YamlInlineListValueContext.class.isAssignableFrom(valueCtx.getClass())) {
            YamlParser.YamlInlineListValueContext inlineListCtx =
                YamlParser.YamlInlineListValueContext.class.cast(valueCtx);
            PyList pyObjList = new PyList();

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
                PyObject arrayElement = getScalarValue(madeUpName, arrayElementValueContext);
                pyObjList.pyadd(arrayElement);
            }
            value = pyObjList;
        } else {
            value = getScalarValue(name, valueCtx);
        }
        return value;
    }

    private PyObject getScalarValue(String name, YamlParser.ValueContext valueContext) {
        final String METHOD = "getScalarValue";

        getLogger().entering(getClassName(), METHOD, name, valueContext);
        PyObject value = null;

        Class<?> valueClazz = valueContext.getClass();
        String text;
        if (YamlParser.YamlNullValueContext.class.isAssignableFrom(valueClazz)) {
            value = Py.None;
        } else if (YamlParser.YamlNameValueContext.class.isAssignableFrom(valueClazz)) {
            YamlParser.YamlNameValueContext nameCtx = YamlParser.YamlNameValueContext.class.cast(valueContext);
            text = nameCtx.NAME().getText();
            value = getQuotedStringValue(text);
        } else if (YamlParser.YamlQuotedStringValueContext.class.isAssignableFrom(valueClazz)) {
            YamlParser.YamlQuotedStringValueContext strCtx =
                YamlParser.YamlQuotedStringValueContext.class.cast(valueContext);
            text = strCtx.QUOTED_STRING().getText();
            value = getQuotedStringValue(text);
        } else if (YamlParser.YamlUnquotedStringValueContext.class.isAssignableFrom(valueClazz)) {
            YamlParser.YamlUnquotedStringValueContext strCtx =
                YamlParser.YamlUnquotedStringValueContext.class.cast(valueContext);
            text = strCtx.UNQUOTED_STRING().getText();
            value = getUnquotedStringValue(text);
        } else if (YamlParser.YamlBooleanValueContext.class.isAssignableFrom(valueClazz)) {
            YamlParser.YamlBooleanValueContext boolCtx = YamlParser.YamlBooleanValueContext.class.cast(valueContext);
            text = boolCtx.BOOLEAN().getText();
            value = getBooleanValue(name, text);
        } else if (YamlParser.YamlIntegerValueContext.class.isAssignableFrom(valueClazz)) {
            YamlParser.YamlIntegerValueContext intCtx = YamlParser.YamlIntegerValueContext.class.cast(valueContext);
            text = intCtx.INTEGER().getText();
            value = getIntegerValue(name, text);
        } else if (YamlParser.YamlFloatValueContext.class.isAssignableFrom(valueClazz)) {
            YamlParser.YamlFloatValueContext floatCtx = YamlParser.YamlFloatValueContext.class.cast(valueContext);
            text = floatCtx.FLOAT().getText();
            value = getFloatValue(name, text);
        } else {
            getLogger().severe("WLSDPLY-18006", name, valueClazz.getName());
        }
        getLogger().exiting(getClassName(), METHOD, value);
        return value;
    }

    private synchronized PyList getOpenObjectList() {
        if (openObjectList == null) {
            openObjectList = new PyList();
        }
        return openObjectList;
    }

    private PyObject getBooleanValue(String name, String text) {
        String booleanValue = "False";
        if (!StringUtils.isEmpty(text)) {
            text = StringUtils.stripQuotes(text.trim());
            if ("true".equalsIgnoreCase(text)) {
                booleanValue = "True";
            } else if ("false".equalsIgnoreCase(text)) {
                booleanValue = "False";
            } else {
                getLogger().warning("WLSDPLY-18000", name, text);
            }
        } else {
            getLogger().warning("WLSDPLY-18001", name);
        }
        return new PyString(booleanValue);
    }

    private PyObject getIntegerValue(String name, String text) {
        long longValue = 0;
        if (!StringUtils.isEmpty(text)) {
            text = StringUtils.stripQuotes(text.trim());
            try {
                longValue = Long.parseLong(text);
            } catch (NumberFormatException nfe) {
                getLogger().warning("WLSDPLY-18002", nfe, name, text, nfe.getLocalizedMessage());
            }
        } else {
            getLogger().warning("WLSDPLY-18003", name);
        }
        return new PyLong(longValue);
    }

    private PyObject getFloatValue(String name, String text) {
        double doubleValue = 0;
        if (!StringUtils.isEmpty(text)) {
            text = StringUtils.stripQuotes(text.trim());
            try {
                doubleValue = Double.parseDouble(text);
            } catch (NumberFormatException nfe) {
                getLogger().warning("WLSDPLY-18004", nfe, name, text, nfe.getLocalizedMessage());
            }
        } else {
            getLogger().warning("WLSDPLY-18005", name);
        }
        return new PyFloat(doubleValue);
    }

    private static PyObject getQuotedStringValue(String text) {
        String newString = unquoteEmbeddedQuotes(getQuotedStringText(text));

        PyObject value = Py.None;
        if (newString != null) {
            value = new PyString(newString);
        }
        return value;
    }

    private static PyObject getUnquotedStringValue(String text) {
        String newString = unquoteEmbeddedQuotes(getUnquotedStringText(text));

        PyObject value = Py.None;
        if (newString != null) {
            value = new PyString(newString);
        }
        return value;
    }

    private static String getQuotedStringText(String text) {
        String value = getUnquotedStringText(text);
        if (value != null) {
            value = StringUtils.stripQuotes(value);
        }
        return value;
    }

    private static String getUnquotedStringText(String text) {
        String value = null;
        if (!StringUtils.isEmpty(text)) {
            value = text.trim();
        }
        return value;
    }

    private static String unquoteEmbeddedQuotes(String text) {
        String result = text;
        if (!StringUtils.isEmpty(text)) {
            if (text.contains("''")) {
                result = text.replace("''", "'");
            }
            if (text.contains("\"\"")) {
                result = result.replace("\"\"", "\"");
            }
        }
        return result;
    }
}
