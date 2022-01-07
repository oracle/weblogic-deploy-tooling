/*
 * Copyright (c) 2017, 2022, Oracle Corporation and/or its affiliates.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.yaml;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileWriter;
import java.io.IOException;
import java.util.Map;

import oracle.weblogic.deploy.logging.PlatformLogger;
import oracle.weblogic.deploy.logging.WLSDeployLogFactory;
import oracle.weblogic.deploy.util.FileUtils;

import org.python.core.PyDictionary;

/**
 * An implementation of the YAML parser/translator that reads the YAML input from an input stream.
 */
public class YamlTranslator extends AbstractYamlTranslator {
    private static final String CLASS = YamlTranslator.class.getName();
    private static final PlatformLogger LOGGER = WLSDeployLogFactory.getLogger("wlsdeploy.yaml");

    private File yamlFile;

    /**
     * Constructor for parsing YAML file into a Python dictionary.
     *
     * @param fileName the name of the existing YAML file to parse
     * @throws IllegalArgumentException if the file name is null or does not point to a valid, existing file.
     */
    public YamlTranslator(String fileName) {
        this(fileName, false);
    }

    /**
     * Constructor for parsing YAML file into a Python dictionary and controlling ordering.
     *
     * @param fileName the name of the existing YAML file to parse
     * @param useOrderedDict whether or not to use an ordered dictionary to maintain the order
     * @throws IllegalArgumentException if the file name is null or does not point to a valid, existing file.
     */
    public YamlTranslator(String fileName, boolean useOrderedDict) {
        super(fileName, useOrderedDict);
        this.yamlFile = FileUtils.validateExistingFile(fileName);
    }
    /**
     * This method triggers parsing of the file and conversion into the Python dictionary.
     *
     * @return the python dictionary corresponding to the YAML input file
     * @throws YamlException if an error occurs while reading the input file
     */
    @Override
    public PyDictionary parse() throws YamlException {
        final String METHOD = "parse";

        LOGGER.entering(CLASS, METHOD);
        PyDictionary result;
        try (FileInputStream fis = new FileInputStream(yamlFile)) {
            result = parseInternal(fis);
        } catch (IOException ioe) {
            YamlException ex = new YamlException("WLSDPLY-18108", ioe, yamlFile.getPath(), ioe.getLocalizedMessage());
            LOGGER.throwing(CLASS, METHOD, ex);
            throw ex;
        }

        // don't log the model on exit, it may contain passwords
        LOGGER.exiting(CLASS, METHOD);
        return result;
    }

    public void dump(Map<String, Object> data) throws YamlException {
        final String METHOD = "dump";

        // Don't log the data since it is big and could contain credentials.
        LOGGER.entering(CLASS, METHOD);
        try (FileWriter fileWriter = new FileWriter(yamlFile)) {
            dumpInternal(data, fileWriter);
        } catch (IOException ioe) {
            YamlException ex = new YamlException("WLSDPLY-18109", ioe, yamlFile.getPath(), ioe.getLocalizedMessage());
            LOGGER.throwing(CLASS, METHOD, ex);
            throw ex;
        }
        LOGGER.exiting(CLASS, METHOD);
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
