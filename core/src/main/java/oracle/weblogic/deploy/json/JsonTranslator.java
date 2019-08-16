/*
 * Copyright (c) 2017, 2019, Oracle and/or its affiliates. All rights reserved.
 * Licensed under the Universal Permissive License v 1.0 as shown at http://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.json;

import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;

import oracle.weblogic.deploy.logging.PlatformLogger;
import oracle.weblogic.deploy.logging.WLSDeployLogFactory;
import oracle.weblogic.deploy.util.FileUtils;

import org.python.core.PyDictionary;

/**
 * An implementation of the JSON parser/translator that reads the JSON input from a file.
 */
public class JsonTranslator extends AbstractJsonTranslator {
    private static final String CLASS = JsonTranslator.class.getName();
    private static final PlatformLogger LOGGER = WLSDeployLogFactory.getLogger("wlsdeploy.json");

    private File jsonFile;

    /**
     * Constructor for parsing JSON file into a Python dictionary.
     *
     * @param fileName - the name of the existing JSON file to parse
     * @throws IllegalArgumentException if the file name is null or does not point to a valid, existing file.
     */
    public JsonTranslator(String fileName) {
        this(fileName, false);
    }

    /**
     * Constructor for parsing JSON file into a Python dictionary and control ordering.
     *
     * @param fileName - the name of the existing JSON file to parse
     * @param useOrdering - whether or not to use an ordered dictionary
     * @throws IllegalArgumentException if the file name is null or does not point to a valid, existing file.
     */
    public JsonTranslator(String fileName, boolean useOrdering) {
        this.jsonFile = FileUtils.validateExistingFile(fileName);
        this.useOrderedDict = useOrdering;
    }

    /**
     * This method triggers parsing of the file and conversion into the Python dictionary.
     *
     * @return the python dictionary corresponding to the JSON input file
     * @throws JsonException if an error occurs while reading the input file
     */
    @Override
    public PyDictionary parse() throws JsonException {
        final String METHOD = "parse";

        LOGGER.entering(CLASS, METHOD);
        PyDictionary result;
        try (FileInputStream fis = new FileInputStream(jsonFile)) {
            result = parseInternal(jsonFile.getPath(), fis);
        } catch (IOException ioe) {
            JsonException ex =
                new JsonException("WLSDPLY-18007", ioe, "JSON", jsonFile.getPath(), ioe.getLocalizedMessage());
            LOGGER.throwing(CLASS, METHOD, ex);
            throw ex;
        }
        LOGGER.exiting(CLASS, METHOD);
        return result;
    }

    @Override
    protected String getClassName() {
        return CLASS;
    }

    @Override
    protected PlatformLogger getLogger() {
        return LOGGER;
    }
}
