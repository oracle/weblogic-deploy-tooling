/*
 * Copyright (c) 2021, 2022, Oracle Corporation and/or its affiliates.
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
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import javax.xml.XMLConstants;
import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;
import javax.xml.parsers.ParserConfigurationException;
import javax.xml.xpath.XPath;
import javax.xml.xpath.XPathConstants;
import javax.xml.xpath.XPathExpressionException;
import javax.xml.xpath.XPathFactory;

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
    private static final String PSU_DESCRIPTION_REGEX_OLD =
        "^WebLogic Server (\\d+(\\.\\d+){3,5}) PSU Patch.*$";
    private static final String PSU_DESCRIPTION_REGEX_NEW =
        "^WLS PATCH SET UPDATE (\\d+(\\.\\d+){3,5})(\\(ID:(\\d+)\\.\\d+\\))?$";
    private static final Pattern PSU_DESCRIPTION_PATTERN_OLD = Pattern.compile(PSU_DESCRIPTION_REGEX_OLD);
    private static final Pattern PSU_DESCRIPTION_PATTERN_NEW = Pattern.compile(PSU_DESCRIPTION_REGEX_NEW);

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
     * Look at the description for the PSU wording.  There are three known formats:
     *
     * - WLS PATCH SET UPDATE <version>.<PSU>
     * - WLS PATCH SET UPDATE <version>.0(ID:<PSU>.<number>)
     * - WebLogic Server <version>.<PSU> PSU Patch for BUG<number> <full date and time>
     *
     * The second format contains the PSU number in the first part of the ID.  In at least one
     * case, the PSU number has a 4 digit year so the extractPsu() method is using this methodology
     * to compute the PSU in this case.
     *
     * The third format was used for early 12.1.2/12.1.3 PSUs.
     */
    public String getPSU() {
        // find the names in the directory first
        if (!(new File(patchesHome)).exists()) {
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
                String psu = null;
                Matcher matcher = PSU_DESCRIPTION_PATTERN_NEW.matcher(descrip);
                if (matcher.matches()) {
                    psu = extractNewPsu(matcher);
                } else {
                    matcher = PSU_DESCRIPTION_PATTERN_OLD.matcher(descrip);
                    if (matcher.matches()) {
                        psu = extractOldPsu(matcher);
                    }
                }

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

    // Only for unit testing
    String extractNewPsu(String description) {
        String psu = null;
        if (description != null) {
            Matcher matcher = PSU_DESCRIPTION_PATTERN_NEW.matcher(description);
            if (matcher.matches()) {
                psu = extractNewPsu(matcher);
            }
        }
        return psu;
    }

    private String extractNewPsu(Matcher matcher) {
        LOGGER.entering(matcher.group(0));

        String psu = null;
        int groupCount = matcher.groupCount();
        if (groupCount == 4) {
            String idGroup = matcher.group(4);
            if (idGroup == null) {
                psu = matcher.group(2).substring(1);
            } else {
                switch (idGroup.length()) {
                    case 6:
                        psu = idGroup;
                        break;

                    // PSU 12.2.1.3.0.190522 has the ID 20190522 so parse off the extra digits...
                    case 8:
                        psu = idGroup.substring(2);
                        break;

                    default:
                        LOGGER.warning("WLSDPLY-01052", idGroup, idGroup.length(), matcher.group(0));
                        break;
                }
            }
        } else {
            LOGGER.warning("WLSDPLY-01051", groupCount, matcher.group(0));
        }

        LOGGER.exiting(psu);
        return psu;
    }

    // Only for unit testing
    String extractOldPsu(String description) {
        String psu = null;
        if (description != null) {
            Matcher matcher = PSU_DESCRIPTION_PATTERN_OLD.matcher(description);
            if (matcher.matches()) {
                psu = extractOldPsu(matcher);
            }
        }
        return psu;
    }

    private String extractOldPsu(Matcher matcher) {
        LOGGER.entering(matcher.group(0));

        String psu = null;
        int groupCount = matcher.groupCount();
        if (groupCount == 2) {
            psu = matcher.group(2).substring(1);
        } else {
            LOGGER.warning("WLSDPLY-01051", groupCount, matcher.group(0));
        }

        LOGGER.exiting(psu);
        return psu;
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
        } catch (IOException ieo) {
            LOGGER.info("Unable to locate the patch files at {0}", patchesHome);
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
