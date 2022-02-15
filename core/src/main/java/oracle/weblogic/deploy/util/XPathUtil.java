/*
 * Copyright (c) 2021, 2022, Oracle Corporation and/or its affiliates.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.util;
import org.w3c.dom.Document;
import org.w3c.dom.Node;
import org.xml.sax.SAXException;

import javax.xml.XMLConstants;
import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;
import javax.xml.parsers.ParserConfigurationException;
import javax.xml.xpath.XPath;
import javax.xml.xpath.XPathConstants;
import javax.xml.xpath.XPathExpressionException;
import javax.xml.xpath.XPathFactory;
import java.io.File;
import java.io.IOException;
import java.nio.file.DirectoryStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.*;

import oracle.weblogic.deploy.logging.PlatformLogger;
import oracle.weblogic.deploy.logging.WLSDeployLogFactory;

/*
 * Parse the xml file at the designated location for the PSU value
 */
public class XPathUtil {
    private static final PlatformLogger LOGGER = WLSDeployLogFactory.getLogger("wlsdeploy.util");
    String  oracle_home;
    String patches_home;
    public XPathUtil(String oracle_home){
        this.oracle_home = oracle_home;
        patches_home = Paths.get(oracle_home, "inventory", "patches").toString();
    }

    public XPathUtil() {
        // for testing only
    }

    private static XPathFactory factory = null;

    private static synchronized XPathFactory factory() {
        if (factory == null) {
            factory = XPathFactory.newInstance();
        }
        return factory;
    }

    /*
     * Get the PSU if one exists at the inventory/patches files. Look at the description
     * for the PSU wording.
     */
    public String getPSU() {
        // find the names in the directory first
        if (!(new File(patches_home)).exists()) {
            LOGGER.info("No patches home at {0}", patches_home);
            return null;
        }
        List<String> patch_files = findPatchFiles();
        List<String> list = new ArrayList<>();
        for (String patch_file : patch_files){
            Document doc = readXmlFile(patch_file);
            String descrip = description(doc, "//@description");
            LOGGER.fine("Description {0}", descrip);
            if (descrip != null && descrip.startsWith("WLS PATCH SET UPDATE")) {
                String psu = extractPsu(descrip);
                list.add(psu);
                Collections.sort(list);
                return list.get(list.size() -1);
            }
        }
        return null;
    }

    public String extractPsu(String descrip) {
        int idx = descrip.lastIndexOf('.') + 1;
        int endIdx = descrip.length() - 1;
        if (descrip.charAt(endIdx) == ')') {
            endIdx--;
        }
        return descrip.substring(idx, endIdx+1);
    }
    /**
     * Locate the patch files in the Oracle home
     * @return list of patch file names.
     */
    public List<String> findPatchFiles() {
        List<String> patch_files = new ArrayList<String>();
        try (DirectoryStream<Path> stream = Files.newDirectoryStream(new File(patches_home).toPath())){
            for (Path path : stream) {
                patch_files.add(path.toString());
            }
        } catch (IOException ieo) {
            LOGGER.info("Unable to locate the patch files at {0}", patches_home);
        }
        return patch_files;
    }

    /**
     * Read the xml file at the indicated path.
     * @param path to the xml file
     * @return Document from the parsed xml file
     */
    public Document readXmlFile(String path) {
        DocumentBuilderFactory dbf = DocumentBuilderFactory.newInstance();
        try {
            dbf.setXIncludeAware(false);
            dbf.setExpandEntityReferences(false);
            dbf.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
            dbf.setAttribute(XMLConstants.ACCESS_EXTERNAL_DTD, "");
            dbf.setAttribute(XMLConstants.ACCESS_EXTERNAL_SCHEMA, "");
            dbf.setFeature(XMLConstants.FEATURE_SECURE_PROCESSING, true);
        } catch (ParserConfigurationException pce) {
            LOGGER.warning("Unable to set feature in DocumentBuilderFactory : {0}");
        }

        Document doc = null;
        try {
            // parse XML file
            DocumentBuilder db = dbf.newDocumentBuilder();

            doc = db.parse(new File(path));

        } catch (ParserConfigurationException | SAXException | IOException ioe) {
            LOGGER.info("Unable to parse the xml file {0}", path);
        }
        return doc;
    }

    /**
     * Apply the expression against the Node and return a String.
     * @param node parsed xml file Node to search
     * @param expression to evaluate on the Node
     * @return the String value if located in the Node
     */
    private String description(Node node, String expression) {
        XPath xpath = factory().newXPath();
        try {
            return (String) xpath.evaluate(expression, node, XPathConstants.STRING);
        } catch (XPathExpressionException xpe) {
            LOGGER.info("Unable to apply the expression {0}", expression);
        }
        return null;
    }
}
