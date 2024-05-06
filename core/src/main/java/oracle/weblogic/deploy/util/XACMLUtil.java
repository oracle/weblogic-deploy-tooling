/*
 * Copyright (c) 2024, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.util;

import java.io.IOException;
import java.io.StringReader;
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
import org.xml.sax.InputSource;
import org.xml.sax.SAXException;

public class XACMLUtil {
    private static final String CLASS = XACMLUtil.class.getName();
    private static final PlatformLogger LOGGER = WLSDeployLogFactory.getLogger("wlsdeploy.util");
    private static final String EXPRESSION_XPATH = "//Description/text()";

    private static XPathFactory factory = null;

    private static synchronized XPathFactory factory() {
        if (factory == null) {
            factory = XPathFactory.newInstance();
        }
        return factory;
    }

    private Document xacmlDocument;

    public XACMLUtil(String xacmlText) throws XACMLException {
        this.xacmlDocument = parseXACMLDocument(xacmlText);
    }

    public String getPolicyEntitlementExpression() throws XACMLException {
        final String METHOD = "getPolicyEntitlementExpression";
        LOGGER.entering(CLASS, METHOD);

        String policy = getExpression();

        LOGGER.exiting(CLASS, METHOD, policy);
        return policy;
    }

    public String getRoleMappingEntitlementExpression() throws XACMLException {
        final String METHOD = "getRoleMappingEntitlementExpression";
        LOGGER.entering(CLASS, METHOD);

        String roleMappingExpression = getExpression();

        LOGGER.exiting(CLASS, METHOD, roleMappingExpression);
        return roleMappingExpression;
    }

    private String getExpression() throws XACMLException {
        final String METHOD = "getExpression";
        LOGGER.entering(CLASS, METHOD);

        String expression = null;
        XPath xpath = factory().newXPath();
        try {
            expression = (String)xpath.evaluate(EXPRESSION_XPATH, this.xacmlDocument, XPathConstants.STRING);
        } catch (XPathExpressionException e) {
            XACMLException ex = new XACMLException("WLSDPLY-07002", e, EXPRESSION_XPATH, e.getLocalizedMessage());
            LOGGER.throwing(CLASS, METHOD, ex);
            throw ex;
        }

        LOGGER.exiting(CLASS, METHOD, expression);
        return expression;
    }

    private Document parseXACMLDocument(String xacmlText) throws XACMLException {
        final String METHOD = "parseXACMLDocument";
        LOGGER.entering(CLASS, METHOD, xacmlText);

        DocumentBuilder documentBuilder;
        try {
            DocumentBuilderFactory documentBuilderFactory = getDocumentBuilderFactory();
            documentBuilder = documentBuilderFactory.newDocumentBuilder();
        } catch (ParserConfigurationException e) {
            XACMLException ex = new XACMLException("WLSDPLY-07000", e, e.getLocalizedMessage());
            LOGGER.throwing(CLASS, METHOD, ex);
            throw ex;
        }

        Document document;
        try (StringReader reader = new StringReader(xacmlText)) {
            document = documentBuilder.parse(new InputSource(reader));
        } catch (SAXException | IOException e) {
            XACMLException ex = new XACMLException("WLSDPLY-07001", e, e.getLocalizedMessage());
            LOGGER.throwing(CLASS, METHOD, ex);
            throw ex;
        }

        LOGGER.exiting(CLASS, METHOD, document);
        return document;
    }

    private DocumentBuilderFactory getDocumentBuilderFactory() throws ParserConfigurationException {
        final String METHOD = "getDocumentBuilderFactory";
        LOGGER.entering(CLASS, METHOD);

        DocumentBuilderFactory dbf = DocumentBuilderFactory.newInstance();
        dbf.setXIncludeAware(false);
        dbf.setExpandEntityReferences(false);
        dbf.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
        dbf.setAttribute(XMLConstants.ACCESS_EXTERNAL_DTD, "");
        dbf.setAttribute(XMLConstants.ACCESS_EXTERNAL_SCHEMA, "");
        dbf.setFeature(XMLConstants.FEATURE_SECURE_PROCESSING, true);

        LOGGER.exiting(CLASS, METHOD, dbf);
        return dbf;
    }
}
