/*
 * Copyright (c) 2017, 2019, Oracle and/or its affiliates. All rights reserved.
 * Licensed under the Universal Permissive License v 1.0 as shown at http://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.yaml;

import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;

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
        this.yamlFile = FileUtils.validateExistingFile(fileName);
        this.useOrderedDict = useOrderedDict;
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
            result = parseInternal(yamlFile.getPath(), fis);
        } catch (IOException ioe) {
            YamlException ex = new YamlException("WLSDPLY-18007", ioe, "YAML", yamlFile.getPath(),
                ioe.getLocalizedMessage());
            LOGGER.throwing(CLASS, METHOD, ex);
            throw ex;
        }
        LOGGER.exiting(CLASS, METHOD, result);
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
