/*
 * Copyright (c) 2017, 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.json;

import java.io.IOException;
import java.io.InputStream;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Deque;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import oracle.weblogic.deploy.exception.ExceptionHelper;
import oracle.weblogic.deploy.logging.PlatformLogger;
import oracle.weblogic.deploy.util.StringUtils;

import org.antlr.v4.runtime.CharStream;
import org.antlr.v4.runtime.CharStreams;
import org.antlr.v4.runtime.CommonTokenStream;
import org.antlr.v4.runtime.atn.PredictionMode;
import org.antlr.v4.runtime.misc.ParseCancellationException;
import org.antlr.v4.runtime.tree.ParseTree;
import org.antlr.v4.runtime.tree.ParseTreeWalker;

/**
 * This class does the heavy-lifting of walking the parse tree and performing the conversion into a Java map.
 */
public abstract class AbstractJavaJsonTranslator extends JSONBaseListener {

    private Map<String, Object> fileDict;
    private Deque<Map<String, Object>> currentDict;
    private Deque<List<Object>> currentArray;
    private Deque<String> currentPairName;
    private Deque<ValueType> currentValueType;
    private Object currentScalarValue;
    protected boolean useOrderedDict;

    /**
     * This method triggers parsing of the JSON and conversion into the Java map.
     *
     * @return the Java map corresponding to the JSON input
     * @throws JsonException if an error occurs while reading the input
     */
    public abstract Map<String, Object> parse() throws JsonException;

    /**
     * {@inheritDoc}
     */
    @Override
    public void enterJson(JSONParser.JsonContext ctx) {
        if (useOrderedDict) {
            fileDict = new LinkedHashMap<>();
        } else {
            fileDict = new HashMap<>();
        }
        currentDict = new ArrayDeque<>();
        currentArray = new ArrayDeque<>();
        currentPairName = new ArrayDeque<>();
        currentValueType = new ArrayDeque<>();
        currentScalarValue = null;
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
        Map<String, Object> container;
        Object value;
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
                currentScalarValue = null;
                break;

            default:
                container = currentDict.peek();
                getLogger().severe("WLSDPLY-18029", name, valueType);
                value = null;
        }
        container.put(name, value);
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

        Map<String, Object> newObjectDict;
        if (useOrderedDict) {
            newObjectDict = new LinkedHashMap<>();
        } else {
            newObjectDict = new HashMap<>();
        }

        String name = currentPairName.peek();
        Map<String, Object> nextDict = currentDict.peek();
        if (name != null && nextDict != null && nextDict.containsKey(name)) {
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
        List<Object> list = new ArrayList<>();
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
        currentScalarValue = cleanString;
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
        Object value;
        if (!StringUtils.isEmpty(numberText)) {
            if (numberText.indexOf('.') < 0) {
                long longValue = 0;
                try {
                    longValue = Long.parseLong(numberText);
                } catch (NumberFormatException nfe) {
                    getLogger().warning("WLSDPLY-18024", nfe, numberText, nfe.getLocalizedMessage());
                }
                value = longValue;
            } else {
                double doubleValue = 0.0;
                try {
                    doubleValue = Double.parseDouble(numberText);
                } catch (NumberFormatException nfe) {
                    getLogger().warning("WLSDPLY-18025", nfe, numberText, nfe.getLocalizedMessage());
                }
                value = doubleValue;
            }
        } else {
            getLogger().warning("WLSDPLY-18026");
            value = 0L;
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
        currentScalarValue = Boolean.TRUE;
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
        currentScalarValue = Boolean.FALSE;
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
        currentScalarValue = null;
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

    protected Map<String, Object> parseInternal(String jsonFileName, InputStream jsonStream) throws JsonException {
        final String METHOD = "parseInternal";

        Map<String, Object> result = null;
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

    private void addToArrayIfNeeded() {
        ValueType myValueType = currentValueType.pop();
        ValueType containerValueType = currentValueType.peek();
        if (containerValueType == ValueType.ARRAY) {
            List<Object> container;
            switch(myValueType) {
                case OBJECT:
                    Map<String, Object> myDict = currentDict.pop();
                    container = currentArray.peek();
                    container.add(myDict);
                    break;

                case ARRAY:
                    List<Object> myList = currentArray.pop();
                    container = currentArray.peek();
                    container.add(myList);
                    break;

                case SCALAR:
                    container = currentArray.peek();
                    container.add(currentScalarValue);
                    currentScalarValue = null;
                    break;
            }
        } else {
            currentValueType.push(myValueType);
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
