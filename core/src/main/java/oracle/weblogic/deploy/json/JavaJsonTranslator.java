/*
 * Copyright (c) 2017, 2026, Oracle Corporation and/or its affiliates.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.json;

import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.util.Map;

import oracle.weblogic.deploy.logging.PlatformLogger;
import oracle.weblogic.deploy.logging.WLSDeployLogFactory;
import oracle.weblogic.deploy.util.FileUtils;

import org.antlr.v4.runtime.misc.ParseCancellationException;

/**
 * An implementation of the JSON parser/translator that reads the JSON input from a file.
 */
public class JavaJsonTranslator extends AbstractJavaJsonTranslator {
    private static final String CLASS = JavaJsonTranslator.class.getName();
    private static final PlatformLogger LOGGER = WLSDeployLogFactory.getLogger("wlsdeploy.json");

    private final File jsonFile;

    /**
     * Constructor for parsing JSON file into a Java map.
     *
     * @param fileName - the name of the existing JSON file to parse
     * @throws IllegalArgumentException if the file name is null or does not point to a valid, existing file.
     */
    public JavaJsonTranslator(String fileName) {
        this(fileName, false);
    }

    /**
     * Constructor for parsing JSON file into a Java map and control ordering.
     *
     * @param fileName - the name of the existing JSON file to parse
     * @param useOrdering - whether to use an ordered map
     * @throws IllegalArgumentException if the file name is null or does not point to a valid, existing file.
     */
    public JavaJsonTranslator(String fileName, boolean useOrdering) {
        this.jsonFile = FileUtils.validateExistingFile(fileName);
        this.useOrderedDict = useOrdering;
    }

    /**
     * This method triggers parsing of the file and conversion into the Java map.
     *
     * @return the Java map corresponding to the JSON input file
     * @throws JsonException if an error occurs while reading the input file
     */
    @Override
    public Map<String, Object> parse() throws JsonException {
        final String METHOD = "parse";

        LOGGER.entering(CLASS, METHOD);
        Map<String, Object> result;
        try (FileInputStream fis = new FileInputStream(jsonFile)) {
            result = parseInternal(jsonFile.getPath(), fis);
        } catch (IOException | ParseCancellationException ioe) {
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
