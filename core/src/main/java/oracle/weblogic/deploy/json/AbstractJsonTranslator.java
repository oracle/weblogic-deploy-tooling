/*
 * Copyright (c) 2017, 2022, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.json;

import java.io.IOException;
import java.io.InputStream;
import java.util.ArrayDeque;
import java.util.Deque;

import oracle.weblogic.deploy.exception.ExceptionHelper;
import oracle.weblogic.deploy.logging.PlatformLogger;
import oracle.weblogic.deploy.util.PyOrderedDict;
import oracle.weblogic.deploy.util.PyRealBoolean;
import oracle.weblogic.deploy.util.StringUtils;

import org.antlr.v4.runtime.CharStream;
import org.antlr.v4.runtime.CharStreams;
import org.antlr.v4.runtime.CommonTokenStream;
import org.antlr.v4.runtime.atn.PredictionMode;
import org.antlr.v4.runtime.misc.ParseCancellationException;
import org.antlr.v4.runtime.tree.ParseTree;
import org.antlr.v4.runtime.tree.ParseTreeWalker;
import org.python.core.Py;
import org.python.core.PyDictionary;
import org.python.core.PyFloat;
import org.python.core.PyList;
import org.python.core.PyLong;
import org.python.core.PyObject;
import org.python.core.PyString;
import org.python.core.PyUnicode;

/**
 * This class does the heavy-lifting of walking the parse tree and performing the conversion into a Python dictionary.
 */
public abstract class AbstractJsonTranslator extends JSONBaseListener {

    private PyDictionary fileDict;
    private Deque<PyDictionary> currentDict;
    private Deque<PyList> currentArray;
    private Deque<String> currentPairName;
    private Deque<ValueType> currentValueType;
    private PyObject currentScalarValue;
    @SuppressWarnings("WeakerAccess")
    protected boolean useOrderedDict;
    @SuppressWarnings("WeakerAccess")
    protected boolean useUnicode;

    /**
     * This method triggers parsing of the JSON and conversion into the Python dictionary.
     *
     * @return the python dictionary corresponding to the JSON input
     * @throws JsonException if an error occurs while reading the input
     */
    public abstract PyDictionary parse() throws JsonException;

    /**
     * {@inheritDoc}
     */
    @Override
    public void enterJson(JSONParser.JsonContext ctx) {
        if (useOrderedDict) {
            fileDict = new PyOrderedDict();
        } else {
            fileDict = new PyDictionary();
        }
        currentDict = new ArrayDeque<>();
        currentArray = new ArrayDeque<>();
        currentPairName = new ArrayDeque<>();
        currentValueType = new ArrayDeque<>();
        currentScalarValue = Py.None;
    }

    /**
     * {@inheritDoc}
     */
    @Override
    public void enterPair(JSONParser.PairContext ctx) {
        String name = resolveEscapeSequences(StringUtils.stripQuotes(ctx.STRING().getText()));
        currentPairName.push(name);
    }

    /**
     * {@inheritDoc}
     */
    @Override
    public void exitPair(JSONParser.PairContext ctx) {
        String name = currentPairName.pop();
        ValueType valueType = currentValueType.pop();
        PyDictionary container;
        PyObject value;
        switch(valueType) {
            case OBJECT:
                value = currentDict.pop();
                container = currentDict.peek();
                break;

            case ARRAY:
                container = currentDict.peek();
                value = currentArray.pop();
                break;

            case SCALAR:
                container = currentDict.peek();
                value = currentScalarValue;
                currentScalarValue = Py.None;
                break;

            default:
                container = currentDict.peek();
                getLogger().severe("WLSDPLY-18027", name, valueType);
                value = Py.None;
        }
        container.__setitem__(this.getPythonString(name), value);
    }

    /**
     * {@inheritDoc}
     */
    @Override
    public void enterJsonObject(JSONParser.JsonObjectContext ctx) {
        final String METHOD = "enterJsonObject";
        if (currentPairName.isEmpty()) {
            // This should only happen for the outermost object that the file defines.
            //
            currentDict.push(fileDict);
            currentValueType.push(ValueType.OBJECT);
            return;
        }

        PyDictionary newObjectDict;
        if (useOrderedDict) {
            newObjectDict = new PyOrderedDict();
        } else {
            newObjectDict = new PyDictionary();
        }

        String name = currentPairName.peek();
        PyDictionary nextDict = currentDict.peek();
        if (name != null && nextDict != null && nextDict.has_key(this.getPythonString(name))) {
            String message = ExceptionHelper.getMessage("WLSDPLY-18028", name);
            ParseCancellationException ex =
                new ParseCancellationException(message);
            getLogger().throwing(getClassName(), METHOD, ex);
            throw ex;
        }
        currentDict.push(newObjectDict);
        currentValueType.push(ValueType.OBJECT);
    }

    /**
     * {@inheritDoc}
     */
    @Override
    public void exitJsonObject(JSONParser.JsonObjectContext ctx) {
        // This method also gets called at the very end of the file so we need to
        // guard against this condition and do nothing...
        //
        if (currentPairName.isEmpty()) {
            return;
        }
        addToArrayIfNeeded();
    }

    /**
     * {@inheritDoc}
     */
    @Override
    public void enterJsonArray(JSONParser.JsonArrayContext ctx) {
        PyList list = new PyList();
        currentArray.push(list);
        currentValueType.push(ValueType.ARRAY);
    }

    /**
     * {@inheritDoc}
     */
    @Override
    public void exitJsonArray(JSONParser.JsonArrayContext ctx) {
        addToArrayIfNeeded();
    }

    /**
     * {@inheritDoc}
     */
    @Override
    public void enterJsonString(JSONParser.JsonStringContext ctx) {
        String cleanString = resolveEscapeSequences(StringUtils.stripQuotes(ctx.STRING().getText()));
        currentScalarValue = this.getPythonString(cleanString);
        currentValueType.push(ValueType.SCALAR);
    }

    /**
     * {@inheritDoc}
     */
    @Override
    public void exitJsonString(JSONParser.JsonStringContext ctx) {
        addToArrayIfNeeded();
    }

    /**
     * {@inheritDoc}
     */
    @Override
    public void enterJsonNumber(JSONParser.JsonNumberContext ctx) {
        String numberText = ctx.NUMBER().getText();
        PyObject value;
        if (!StringUtils.isEmpty(numberText)) {
            if (numberText.indexOf('.') < 0) {
                long longValue = 0;
                try {
                    longValue = Long.parseLong(numberText);
                } catch (NumberFormatException nfe) {
                    getLogger().warning("WLSDPLY-18024", nfe, numberText, nfe.getLocalizedMessage());
                }
                value = new PyLong(longValue);
            } else {
                double doubleValue = 0.0;
                try {
                    doubleValue = Double.parseDouble(numberText);
                } catch (NumberFormatException nfe) {
                    getLogger().warning("WLSDPLY-18025", nfe, numberText, nfe.getLocalizedMessage());
                }
                value = new PyFloat(doubleValue);
            }
        } else {
            getLogger().warning("WLSDPLY-18026");
            value = new PyLong(0L);
        }
        currentScalarValue = value;
        currentValueType.push(ValueType.SCALAR);
    }

    /**
     * {@inheritDoc}
     */
    @Override
    public void exitJsonNumber(JSONParser.JsonNumberContext ctx) {
        addToArrayIfNeeded();
    }

    /**
     * {@inheritDoc}
     */
    @Override
    public void enterJsonTrue(JSONParser.JsonTrueContext ctx) {
        currentScalarValue = new PyRealBoolean(true);
        currentValueType.push(ValueType.SCALAR);
    }

    /**
     * {@inheritDoc}
     */
    @Override
    public void exitJsonTrue(JSONParser.JsonTrueContext ctx) {
        addToArrayIfNeeded();
    }

    /**
     * {@inheritDoc}
     */
    @Override
    public void enterJsonFalse(JSONParser.JsonFalseContext ctx) {
        currentScalarValue = new PyRealBoolean(false);
        currentValueType.push(ValueType.SCALAR);
    }

    /**
     * {@inheritDoc}
     */
    @Override
    public void exitJsonFalse(JSONParser.JsonFalseContext ctx) {
        addToArrayIfNeeded();
    }

    /**
     * {@inheritDoc}
     */
    @Override
    public void enterJsonNull(JSONParser.JsonNullContext ctx) {
        currentScalarValue = Py.None;
        currentValueType.push(ValueType.SCALAR);
    }

    /**
     * {@inheritDoc}
     */
    @Override
    public void exitJsonNull(JSONParser.JsonNullContext ctx) {
        addToArrayIfNeeded();
    }

    protected abstract String getClassName();
    protected abstract PlatformLogger getLogger();

    @SuppressWarnings("WeakerAccess")
    protected PyDictionary parseInternal(String jsonFileName, InputStream jsonStream) throws JsonException {
        final String METHOD = "parseInternal";

        PyDictionary result = null;
        if (jsonStream != null) {
            JsonErrorListener errorListener = new JsonErrorListener(jsonFileName, false);
            try {
                CharStream input = CharStreams.fromStream(jsonStream);
                JSONLexer lexer = new JSONLexer(input);
                lexer.removeErrorListeners();
                lexer.addErrorListener(errorListener);

                CommonTokenStream tokens = new CommonTokenStream(lexer);
                JSONParser parser = new JSONParser(tokens);

                parser.removeErrorListeners();
                parser.addErrorListener(errorListener);
                parser.getInterpreter().setPredictionMode(PredictionMode.LL_EXACT_AMBIG_DETECTION);

                ParseTree tree = parser.json();
                ParseTreeWalker walker = new ParseTreeWalker();
                walker.walk(this, tree);
            } catch (IOException ioe) {
                JsonException ex =
                    new JsonException("WLSDPLY-18007", ioe, "JSON", jsonFileName, ioe.getLocalizedMessage());
                getLogger().throwing(getClassName(), METHOD, ex);
                throw ex;
            }

            int errorCount = errorListener.getErrorCount();
            if (errorCount > 0) {
                JsonException je = new JsonException("WLSDPLY-18017", "JSON", errorCount, jsonFileName);
                getLogger().throwing(getClassName(), METHOD, je);
                throw je;
            }
            result = fileDict;
        }
        return result;
    }

    @SuppressWarnings("unchecked")
    private void addToArrayIfNeeded() {
        ValueType myValueType = currentValueType.pop();
        ValueType containerValueType = currentValueType.peek();
        if (containerValueType == ValueType.ARRAY) {
            PyList container;
            switch(myValueType) {
                case OBJECT:
                    PyDictionary myDict = currentDict.pop();
                    container = currentArray.peek();
                    container.pyadd(myDict);
                    break;

                case ARRAY:
                    PyList myList = currentArray.pop();
                    container = currentArray.peek();
                    container.pyadd(myList);
                    break;

                case SCALAR:
                    container = currentArray.peek();
                    container.pyadd(currentScalarValue);
                    currentScalarValue = Py.None;
                    break;
            }
        } else {
            currentValueType.push(myValueType);
        }
    }

    private PyObject getPythonString(String text) {
        if (this.useUnicode) {
            return new PyUnicode(text);
        } else {
            return new PyString(text);
        }
    }

    private static String resolveEscapeSequences(String text) {
        String result = text;
        if (!StringUtils.isEmpty(text)) {
            result = text.replace("\\\"", "\"");    // \" -> "
            result = result.replace("\\\\", "\\");  // \\ -> \
            result = result.replace("\\b", "\b");   // \b -> backspace
            result = result.replace("\\f", "\f");   // \f -> form feed
            result = result.replace("\\n", "\n");   // \n -> new line
            result = result.replace("\\r", "\r");   // \r -> carriage return
            result = result.replace("\\t", "\t");   // \t -> tab
            result = result.replace("\\/", "/");    // \/ -> /
        }
        return result;
    }

    /**
     * Internal enum used to keep track of the types being processed.
     */
    private enum ValueType {
        OBJECT,
        ARRAY,
        SCALAR
    }
}
