/*
 * Copyright (c) 2020, Oracle Corporation and/or its affiliates.  All rights reserved.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.yaml;

import oracle.weblogic.deploy.logging.PlatformLogger;
import oracle.weblogic.deploy.logging.WLSDeployLogFactory;
import oracle.weblogic.deploy.util.FileUtils;
import oracle.weblogic.deploy.util.StringUtils;
import org.antlr.v4.runtime.CharStream;
import org.antlr.v4.runtime.CharStreams;
import org.antlr.v4.runtime.CommonTokenStream;
import org.antlr.v4.runtime.ParserRuleContext;
import org.antlr.v4.runtime.atn.PredictionMode;
import org.antlr.v4.runtime.tree.ParseTree;
import org.antlr.v4.runtime.tree.ParseTreeWalker;
import org.junit.Assert;

import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.text.MessageFormat;
import java.util.*;

/**
 * An implementation of the YAML parser/translator that reads the YAML input from an input stream.
 * A tree of Java objects is created, unlike the WDT parser, which creates a tree of Python objects
 */
public class YamlJavaTranslator extends YamlBaseListener {
    private static final boolean DEBUG = System.getProperty("DEBUG") != null;
    private static final String CLASS = YamlJavaTranslator.class.getName();
    private static final PlatformLogger LOGGER = WLSDeployLogFactory.getLogger("wlsdeploy.yaml");

    private File yamlFile;

    private YamlErrorListener errorListener;

    private Map<String, Object> fileDict;
    private Stack<Map<String, Object>> currentDict;

    private String lastObjectName;
    private List<Object> openObjectList;

    private String[] ruleNames;

    /**
     * Constructor for parsing YAML file into a Java map.
     *
     * @param fileName the name of the existing YAML file to parse
     * @throws IllegalArgumentException if the file name is null or does not point to a valid, existing file.
     */
    @SuppressWarnings("WeakerAccess")
    public YamlJavaTranslator(String fileName) {
        this.yamlFile = FileUtils.validateExistingFile(fileName);
        this.errorListener = new YamlErrorListener(fileName, false);
    }

    /**
     * This method triggers parsing of the file and conversion into the Java map.
     *
     * @return the Java map corresponding to the YAML input file
     * @throws YamlException if an error occurs while reading the input file
     */
    @SuppressWarnings("WeakerAccess")
    public Map<String, Object> parse() throws YamlException {
        final String METHOD = "parse";
        LOGGER.entering(CLASS, METHOD);

        fileDict = new HashMap<>();
        try (FileInputStream fis = new FileInputStream(yamlFile)) {

            CharStream input = CharStreams.fromStream(fis);
            YamlLexer lexer = new YamlLexer(input);

            CommonTokenStream tokens = new CommonTokenStream(lexer);
            YamlParser parser = new YamlParser(tokens);
            ruleNames = parser.getRuleNames();

            parser.removeErrorListeners();
            parser.addErrorListener(errorListener);
            parser.getInterpreter().setPredictionMode(PredictionMode.LL_EXACT_AMBIG_DETECTION);

            ParseTree tree = parser.file();
            ParseTreeWalker walker = new ParseTreeWalker();
            walker.walk(this, tree);

        } catch (IOException ioe) {
            YamlException ex = new YamlException("WLSDPLY-18007", ioe, "YAML", yamlFile.getPath(),
                    ioe.getLocalizedMessage());
            LOGGER.throwing(CLASS, METHOD, ex);
            throw ex;
        }

        LOGGER.exiting(CLASS, METHOD, fileDict);
        return fileDict;
    }

    void checkForParseErrors() {
        int errorCount = errorListener.getErrorCount();
        Assert.assertEquals("Parser error count was " + errorCount, 0, errorCount);
    }

    void ensureStackIsEmpty() {
        Assert.assertTrue("currentDict stack is not empty", currentDict.isEmpty());
    }

    // -------------------------------------------
    // implement YamlBaseListener
    // -------------------------------------------

    @Override
    public void enterFile(YamlParser.FileContext ctx) {
        this.fileDict = new HashMap<>();
        currentDict = new Stack<>();
        currentDict.push(fileDict);
    }

    @Override
    public void enterAssign(YamlParser.AssignContext ctx) {
        String name = getAssignName(ctx);
        Object value = getAssignValue(name, ctx);

        Map<String, Object> container = currentDict.peek();
        container.put(name, value);
    }

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

        List<Object> myList = getOpenObjectList();
        String madeUpName = MessageFormat.format("{0}[{1}]", lastObjectName, myList.size());
        Object value = getScalarValue(madeUpName, valueCtx);
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

    @Override
    public void enterObject(YamlParser.ObjectContext ctx) {
        String name = StringUtils.stripQuotes(ctx.name().getText());
        Map<String, Object> objDict = new HashMap<>();

        Map<String, Object> container = currentDict.peek();
        container.put(name, objDict);
        currentDict.push(objDict);

        // In case this is the name for a list of values, save it off...
        lastObjectName = name;
    }

    @Override
    public void exitObj_block(YamlParser.Obj_blockContext ctx) {
        if (openObjectList != null) {
            // Pop off the dictionary that is created by default for all new objects off the current stack
            currentDict.pop();

            Map<String, Object> container = currentDict.peek();
            container.put(lastObjectName, openObjectList);

            // zero out the open list
            openObjectList = null;
        } else {
            currentDict.pop();
        }
    }

    @Override
    public void exitFile(YamlParser.FileContext ctx) {
        currentDict.pop();
    }

    @Override public void enterEveryRule(ParserRuleContext ctx) {
        if(DEBUG) {
            LOGGER.info("RULE: " + ctx.toString(Arrays.asList(ruleNames))
                    + " " + ctx.getText() + " " + ctx.getStart() + " " + ctx.getChildCount());
        }
    }

    // -------------------------------------------
    // private methods
    // -------------------------------------------

    private String getAssignName(YamlParser.AssignContext ctx) {
        String name = null;
        String text = ctx.name().getText();
        if (!StringUtils.isEmpty(text)) {
            name = StringUtils.stripQuotes(text.trim());
        }
        return name;
    }

    private Object getAssignValue(String name, YamlParser.AssignContext ctx) {
        YamlParser.ValueContext valueCtx = ctx.value();
        Object value;

        if (YamlParser.YamlInlineListValueContext.class.isAssignableFrom(valueCtx.getClass())) {
            YamlParser.YamlInlineListValueContext inlineListCtx =
                    YamlParser.YamlInlineListValueContext.class.cast(valueCtx);
            List<Object> pyObjList = new ArrayList<>();

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
                Object arrayElement = getScalarValue(madeUpName, arrayElementValueContext);
                pyObjList.add(arrayElement);
            }
            value = pyObjList;
        } else {
            value = getScalarValue(name, valueCtx);
        }
        return value;
    }

    private Object getScalarValue(String name, YamlParser.ValueContext valueContext) {
        Object value = null;

        Class<?> valueClazz = valueContext.getClass();
        String text;
        if (YamlParser.YamlNullValueContext.class.isAssignableFrom(valueClazz)) {
            value = null;
        } else if (YamlParser.YamlNameValueContext.class.isAssignableFrom(valueClazz)) {
            YamlParser.YamlNameValueContext nameCtx = YamlParser.YamlNameValueContext.class.cast(valueContext);
            text = nameCtx.NAME().getText();
            if (!StringUtils.isEmpty(text)) {
                value = text.trim();
                value = StringUtils.stripQuotes(value.toString());  // similar to AbstractYamlTranslator
            } else {
                value = null;
            }
        } else if (YamlParser.YamlUnquotedStringValueContext.class.isAssignableFrom(valueClazz)) {
            YamlParser.YamlUnquotedStringValueContext strCtx =
                    YamlParser.YamlUnquotedStringValueContext.class.cast(valueContext);
            text = strCtx.UNQUOTED_STRING().getText();
            if (!StringUtils.isEmpty(text)) {
                value = text.trim();
            } else {
                value = null;
            }
        } else if (YamlParser.YamlQuotedStringValueContext.class.isAssignableFrom(valueClazz)) {
            YamlParser.YamlQuotedStringValueContext strCtx =
                    YamlParser.YamlQuotedStringValueContext.class.cast(valueContext);
            text = strCtx.QUOTED_STRING().getText();
            if (!StringUtils.isEmpty(text)) {
                // trim off any leading/trailing white space
                text = text.trim();
                // trim off the quotes
                value = text.substring(1, text.length() - 1);
            } else {
                value = null;
            }
        } else if (YamlParser.YamlBooleanValueContext.class.isAssignableFrom(valueClazz)) {
            YamlParser.YamlBooleanValueContext boolCtx = YamlParser.YamlBooleanValueContext.class.cast(valueContext);
            text = boolCtx.BOOLEAN().getText();

            String booleanValue = "False";
            if (!StringUtils.isEmpty(text)) {
                text = text.trim();
                if ("true".equalsIgnoreCase(text)) {
                    booleanValue = "True";
                } else if ("false".equalsIgnoreCase(text)) {
                    booleanValue = "False";
                } else {
                    Assert.fail("Boolean value for " + name + " attribute was not true or false (" + text + ")");
                }
            } else {
                Assert.fail("Boolean value for " + name + " attribute was empty");
            }
            value = booleanValue;
        } else if (YamlParser.YamlIntegerValueContext.class.isAssignableFrom(valueClazz)) {
            YamlParser.YamlIntegerValueContext intCtx = YamlParser.YamlIntegerValueContext.class.cast(valueContext);
            text = intCtx.INTEGER().getText();

            int intValue = 0;
            if (!StringUtils.isEmpty(text)) {
                text = text.trim();
                try {
                    intValue = Integer.valueOf(text);
                } catch (NumberFormatException nfe) {
                    Assert.fail(name + " attribute is not an integer: " + nfe.getLocalizedMessage());
                    nfe.printStackTrace();
                }
            } else {
                Assert.fail(name + " attribute value was empty");
            }
            value = intValue;
        } else if (YamlParser.YamlFloatValueContext.class.isAssignableFrom(valueClazz)) {
            YamlParser.YamlFloatValueContext floatCtx = YamlParser.YamlFloatValueContext.class.cast(valueContext);
            text = floatCtx.FLOAT().getText();

            float floatValue = 0;
            if (!StringUtils.isEmpty(text)) {
                text = text.trim();
                try {
                    floatValue = Float.valueOf(text);
                } catch (NumberFormatException nfe) {
                    Assert.fail(name + " attribute is not a float: " + nfe.getLocalizedMessage());
                    nfe.printStackTrace();
                }
            } else {
                Assert.fail(name + " attribute value was empty");
            }
            value = floatValue;
        } else {
            Assert.fail(name + " attribute was an unexpected context type: " + valueClazz.getName());
        }
        return value;
    }

    private synchronized List<Object> getOpenObjectList() {
        if (openObjectList == null) {
            openObjectList = new ArrayList<>();
        }
        return openObjectList;
    }
}
