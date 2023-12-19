/*
 * Copyright (c) 2021, 2023, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.util;

import java.io.File;
import java.io.IOException;
import java.nio.file.DirectoryStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

import javax.xml.XMLConstants;
import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;
import javax.xml.parsers.ParserConfigurationException;
import javax.xml.xpath.XPath;
import javax.xml.xpath.XPathConstants;
import javax.xml.xpath.XPathExpressionException;
import javax.xml.xpath.XPathFactory;

import oracle.weblogic.deploy.aliases.VersionUtils;
import oracle.weblogic.deploy.logging.PlatformLogger;
import oracle.weblogic.deploy.logging.WLSDeployLogFactory;

import org.w3c.dom.Document;
import org.w3c.dom.Node;
import org.xml.sax.SAXException;

/*
 * Parse the xml file at the designated location for the PSU value
 */
public class XPathUtil {
    private static final PlatformLogger LOGGER = WLSDeployLogFactory.getLogger("wlsdeploy.util");
    String oracleHome;
    String patchesHome;
    public XPathUtil(String oracleHome){
        this.oracleHome = oracleHome;
        patchesHome = Paths.get(oracleHome, "inventory", "patches").toString();
    }

    public XPathUtil() {
        // for use by other types of docs
    }

    private static XPathFactory factory = null;

    private static synchronized XPathFactory factory() {
        if (factory == null) {
            factory = XPathFactory.newInstance();
        }
        return factory;
    }

    /*
     * Get the PSU if one exists at the inventory/patches files (only works for WLS installations using OPatch).
     */
    public String getPSU() {
        // find the names in the directory first
        if (StringUtils.isEmpty(oracleHome)) {
            LOGGER.fine("Cannot detect PSU version since Oracle Home is empty");
            return null;
        } else if (!(new File(patchesHome)).exists()) {
            LOGGER.fine("No PSU, patches directory not found at {0}", patchesHome);
            return null;
        }
        List<String> patchFiles = findPatchFiles();
        List<String> list = new ArrayList<>();
        for (String patchFile : patchFiles){
            Document doc = readXmlFile(patchFile);
            String descrip = description(doc, "//@description");
            LOGGER.fine("Description {0}", descrip);
            if (!StringUtils.isEmpty(descrip)) {
                String psu = VersionUtils.getPSUVersion(descrip);
                if (psu != null) {
                    list.add(psu);
                }
            }
        }
        if (!list.isEmpty()) {
            Collections.sort(list);
            return list.get(list.size() - 1);
        }
        return null;
    }

    /**
     * Locate the patch files in the Oracle home
     * @return list of patch file names.
     */
    public List<String> findPatchFiles() {
        List<String> patchFiles = new ArrayList<>();
        try (DirectoryStream<Path> stream = Files.newDirectoryStream(new File(patchesHome).toPath())){
            for (Path path : stream) {
                patchFiles.add(path.toString());
            }
        } catch (IOException ioe) {
            LOGGER.info("WLSDPLY-01053", ioe, patchesHome, ioe.getLocalizedMessage());
        }
        return patchFiles;
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
            LOGGER.warning("WLSDPLY-01054", pce, pce.getLocalizedMessage());
        }

        Document doc = null;
        try {
            // parse XML file
            DocumentBuilder db = dbf.newDocumentBuilder();

            doc = db.parse(new File(path));

        } catch (ParserConfigurationException | SAXException | IOException ioe) {
            LOGGER.info("WLSDPLY-01055", ioe, path, ioe.getLocalizedMessage());
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
            LOGGER.info("WLSDPLY-01056", xpe, expression, xpe.getLocalizedMessage());
        }
        return null;
    }
}
