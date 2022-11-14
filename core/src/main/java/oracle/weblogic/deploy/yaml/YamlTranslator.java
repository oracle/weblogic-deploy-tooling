/*
 * Copyright (c) 2017, 2022, Oracle Corporation and/or its affiliates.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.yaml;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileWriter;
import java.io.IOException;
import java.util.List;

import oracle.weblogic.deploy.logging.PlatformLogger;
import oracle.weblogic.deploy.logging.WLSDeployLogFactory;
import oracle.weblogic.deploy.util.FileUtils;

import org.python.core.PyList;

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
        this(fileName, false, false, 0);
    }

    /**
     * Constructor for parsing YAML file into a Python dictionary and controlling ordering.
     *
     * @param fileName the name of the existing YAML file to parse
     * @param useOrderedDict whether or not to use an ordered dictionary to maintain the order
     * @throws IllegalArgumentException if the file name is null or does not point to a valid, existing file.
     */
    public YamlTranslator(String fileName, boolean useOrderedDict) {
        super(fileName, useOrderedDict, false, 0);
        this.yamlFile = FileUtils.validateExistingFile(fileName);
    }

    /**
     * Constructor for parsing YAML file into a Python dictionary, controlling ordering, and
     * controlling the maximum file size.
     *
     * @param fileName the name of the existing YAML file to parse
     * @param useOrderedDict whether or not to use an ordered dictionary to maintain the order
     * @param maxCodePoints the maximum number of code points for the input file, or zero to accept the default
     * @throws IllegalArgumentException if the file name is null or does not point to a valid, existing file.
     */
    public YamlTranslator(String fileName, boolean useOrderedDict, int maxCodePoints) {
        super(fileName, useOrderedDict, false, maxCodePoints);
        this.yamlFile = FileUtils.validateExistingFile(fileName);
    }

    /**
     * Constructor for parsing YAML file into a Python dictionary, controlling everything.
     *
     * @param fileName the name of the existing YAML file to parse
     * @param useOrderedDict whether or not to use an ordered dictionary to maintain the order
     * @param useUnicode whether or not to use PyUnicode instead of PyString
     * @param maxCodePoints the maximum number of code points for the input file, or zero to accept the default
     * @throws IllegalArgumentException if the file name is null or does not point to a valid, existing file.
     */
    public YamlTranslator(String fileName, boolean useOrderedDict, boolean useUnicode, int maxCodePoints) {
        super(fileName, useOrderedDict, useUnicode, maxCodePoints);
        this.yamlFile = FileUtils.validateExistingFile(fileName);
    }

    /**
     * Read a list of documents as Python dictionaries from the YAML file.
     *
     * @return a list of documents corresponding to the YAML input
     * @throws YamlException if an error occurs while reading the input
     */
    @Override
    public PyList parseDocuments(boolean allowMultiple) throws YamlException {
        final String METHOD = "parseDocuments";

        LOGGER.entering(CLASS, METHOD);
        PyList result;
        try (FileInputStream fis = new FileInputStream(yamlFile)) {
            result = parseInternal(fis, allowMultiple);
        } catch (IOException ioe) {
            YamlException ex = new YamlException("WLSDPLY-18108", ioe, yamlFile.getPath(), ioe.getLocalizedMessage());
            LOGGER.throwing(CLASS, METHOD, ex);
            throw ex;
        }

        // don't log the model on exit, it may contain passwords
        LOGGER.exiting(CLASS, METHOD);
        return result;
    }

    public void dumpDocuments(List<?> data) throws YamlException {
        final String METHOD = "dumpDocuments";

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
