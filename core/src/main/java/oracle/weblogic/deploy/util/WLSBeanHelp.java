/*
 * Copyright (c) 2022, Oracle Corporation and/or its affiliates.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.util;

import java.beans.BeanDescriptor;
import java.beans.BeanInfo;
import java.beans.FeatureDescriptor;
import java.beans.PropertyDescriptor;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.util.ArrayList;
import java.util.Enumeration;
import java.util.HashMap;

/**
 * Helper for getting attribute descriptions from a WL mbean.
 *
 * Includes an undocumented main intended for ad-hoc printing of a particular bean or bean property help.
 */
public class WLSBeanHelp {
  private static final String EOL = System.getProperty("line.separator");

  // useful attribute names found in an mbean property descriptor
  private static final String PD_ATT_DESCRIPTION = "description";
  private static final String PD_ATT_LEGALVALUES = "legalValues";
  private static final String PD_ATT_LEGALMIN    = "legalMin";
  private static final String PD_ATT_LEGALMAX    = "legalMax";
  private static final String PD_ATT_SEE         = "see";

  // hide constructor (only static methods in this class)
  private WLSBeanHelp() {}

  // gets description of given bean or property in "plain text HTML"
  //   - returns "" if not found
  //   - if propName is null, gets description of bean,
  //     else gets description of prop
  //   - yields full help, with newlines,
  //     and margin set to "width"
  //   - if propDefault not null, inline it as "default=" along with
  //     any of the discovered prop limits...
  public static String get(String beanName, String propName, int width, String propDefault) {
    String ds;

    if (propName == null)
      ds = getFeatureDescription(getBeanDescriptor(beanName));
    else
      ds = getFeatureDescription(getPropertyDescriptor(beanName, propName));

    if (ds.length() == 0)
      return "";

    String limits = "";
    if (propName != null) {
      limits = getPropertyLimits(beanName, propName, propDefault);
      if (limits.length() > 0) limits += EOL;
    }

    return limits + prettyHTML(ds, width);
  }

  public static String get(String beanName, int width) {
    return get(beanName, null, width, null);
  }

  // convert basic javadoc HTML to plain text
  // (package visible to enable unit testing)
  static String prettyHTML(String html, int margin) {
    return new PrettyHTML(html, margin).toString();
  }

  private static String getFeatureDescription(FeatureDescriptor fd) {
    if (fd == null) return "";
    Object d = fd.getValue(PD_ATT_DESCRIPTION);
    if (d == null) return ""; // should pretty much never happen
    return d.toString();
  }

  // gets pretty printed default for a given bean prop, legal values, min, or max
  // default is passed in from outside
  // returns "" if not applicable or not found
  private static String getPropertyLimits(String beanName, String propName, String propDefault) {
    StringBuilder ret = new StringBuilder();
    if (propDefault != null) {
      // we report the passed in default from the alias DB instead of using the
      // default obtained from the mbean
      ret.append("Default=").append(propDefault).append(EOL);
    }

    PropertyDescriptor pd = getPropertyDescriptor(beanName, propName);
    if (pd == null) return ret.toString();

    Object lval = pd.getValue(PD_ATT_LEGALVALUES);
    if (lval != null) {
      ret.append("Legal values: ").append(EOL);
      for (String val : legalValues(lval))
        ret.append("   '").append(val.trim()).append("'").append(EOL);
    }

    Object lmin = pd.getValue(PD_ATT_LEGALMIN);
    if (lmin != null)
      ret.append("Min=").append(lmin.toString()).append(EOL);

    Object lmax = pd.getValue(PD_ATT_LEGALMAX);
    if (lmax != null)
      ret.append("Max=").append(lmax.toString()).append(EOL);

    return ret.toString();
  }

  // can return null if not found
  private static PropertyDescriptor getPropertyDescriptor(String beanName, String propName) {
    try {
      BeanInfo info = getBeanInfo(beanName);
      if (info == null) return null;
      for (String pluralize : new String [] { "", "s"}) {
        String pName = propName + pluralize;
        for (PropertyDescriptor pd:info.getPropertyDescriptors()) {
          if (pName.equals(pd.getName())) return pd;
        }
        for (PropertyDescriptor pd:info.getPropertyDescriptors()) {
          if (pName.equalsIgnoreCase(pd.getName())) return pd;
        }
      }
    } catch (Exception ignore) {
      // ignore
    }
    return null;
  }

  // can return null if not found
  private static BeanDescriptor getBeanDescriptor(String beanName) {
    try {
      BeanInfo info = getBeanInfo(beanName);
      if (info == null) return null;
      return info.getBeanDescriptor();
    } catch (Exception ignore) {
      // ignore
    }
    return null;
  }

  private static String legalValuesAsString(Object o) {
    ArrayList<String> arr = legalValues(o);
    StringBuilder ret = new StringBuilder();
    for (int i = 0; i < arr.size(); i++) {
      ret.append(arr.get(i));
      if (i < arr.size() - 1) ret.append(", ");
    }
    return ret.toString();
  }

  // turn legal values property descriptor attribute into array of strings
  private static ArrayList<String> legalValues(Object o) {
    HashMap<String,String> foo = new HashMap<>();
    ArrayList<String> ret = new ArrayList<>();
    try {
      for (Object xx : (Object [])o) {
        String cur = "" + xx;
        if (foo.get(cur) == null) {
          foo.put(cur, "something");
          ret.add(cur);
        }
      }
    } catch (ClassCastException cce) {
      // ignore - legal values is not an array of objects, so we don't know how to handle it...
    }
    return ret;
  }

  // returns BeanInfo for given bean name, or null if not found
  private static BeanInfo getBeanInfo(String beanName)
  {

    try {
      // use reflection to implement the equivalent of:
      //    weblogic management provider ManagementServiceClient getBeanInfoAccess()
      //       getBeanInfoForInterface(beanName, false, null)
      //
      Class<?> mscClass = Class.forName("weblogic.management.provider.ManagementServiceClient");
      Method getBeanInfoAccessMethod = mscClass.getMethod("getBeanInfoAccess");
      Object mscObject = mscClass.getDeclaredConstructor().newInstance();
      Object biaObject = getBeanInfoAccessMethod.invoke(mscObject);
      Class<?> biaClass = Class.forName("weblogic.management.provider.beaninfo.BeanInfoAccess");

      Method getBeanInfoForInterfaceMethod =
        biaClass.getMethod(
          "getBeanInfoForInterface",
          String.class,
          boolean.class,
          String.class
        );

      return (BeanInfo)getBeanInfoForInterfaceMethod.invoke(
               biaObject,
               beanName,
               Boolean.FALSE,
               null
             );
    } catch (Exception ignore) {
      // probably a bean not found InvocationTargetException, but could be a reflection exception
    }
    return null;
  }

  // helper class for converting mbean javadoc HTML to plain text
  private static class PrettyHTML {
    private static final String PGS = "<p>";
    private static final String PGE = "</p>";
    private static final String OLS = "<ol>";
    private static final String OLE = "</ol>";
    private static final String ULS = "<ul>";
    private static final String ULE = "</ul>";
    private static final String LIS = "<li>";
    private static final String LIE = "</li>";
    private static final String CDS = "<code>";
    private static final String CDE = "</code>";
    private static final String BOS = "<b>";
    private static final String BOE = "</b>";
    private static final String ITS = "<i>";
    private static final String ITE = "</i>";
    private static final String QUO = "&quot;";
    private static final String LTH = "&lt;";
    private static final String GTH = "&gt;";
    private static final String AMP = "&amp;";
    private static final String ATS = "&#35;";
    private static final String BCK = "&#92;";

    private StringBuilder sb = new StringBuilder(25);  // output string
    private int col;     // current column within output string
    private int indent;  // current indent within output string
    private int margin;  // right margin to use in output string

    private String html; // input html string to parse
    private int pos;     // current position within html string

    private PrettyHTML(String html, int margin) {
      this.html = html;
      this.margin = margin;

      while (pos < html.length()) {

        if (parseSimpleChars()
            || parseBullets()
            || parseParagraph()) continue; // adjusts pos and returns true on success

        out(html.charAt(pos));

        pos++;
      }
      outln();
    }

    private boolean parseSimpleChars() {
      // code
      if (html.startsWith(CDS, pos)) { pos += CDS.length(); out("'"); return true; }
      if (html.startsWith(CDE, pos)) { pos += CDE.length(); out("'"); return true; }

      // bold
      if (html.startsWith(BOS, pos)) { pos += BOS.length(); out("*"); return true; }
      if (html.startsWith(BOE, pos)) { pos += BOE.length(); out("*"); return true; }

      // italic
      if (html.startsWith(ITS, pos)) { pos += ITS.length(); out("*"); return true; }
      if (html.startsWith(ITE, pos)) { pos += ITE.length(); out("*"); return true; }

      // quote, <, >, &, @, \
      if (html.startsWith(QUO, pos)) { pos += QUO.length(); out("'"); return true; }
      if (html.startsWith(LTH, pos)) { pos += LTH.length(); out("<"); return true; }
      if (html.startsWith(GTH, pos)) { pos += GTH.length(); out(">"); return true; }
      if (html.startsWith(AMP, pos)) { pos += AMP.length(); out("&"); return true; }
      if (html.startsWith(ATS, pos)) { pos += ATS.length(); out("@"); return true; }
      if (html.startsWith(BCK, pos)) { pos += BCK.length(); out("\\"); return true; }

      if (html.charAt(pos) != ' ' && Character.isWhitespace(html.charAt(pos))) { pos++; return true; }
      return false;
    }

    private boolean parseParagraph() {
      if (html.startsWith(PGS, pos)) {
        pos += PGS.length();
        if (indent==0) outln();
        return true;
      }
      if (html.startsWith(PGE, pos)) {
        pos += PGE.length();
        outln();
        return true;
      }
      return false;
    }

    private boolean parseBullets() {
      // lists of bullets

      if (html.startsWith(OLS, pos)) { pos += OLS.length(); outln(); indent++; return true; }
      if (html.startsWith(OLE, pos)) { pos += OLE.length(); outln(); indent--; return true; }

      if (html.startsWith(ULS, pos)) { pos += ULS.length(); outln(); indent++; return true; }
      if (html.startsWith(ULE, pos)) { pos += ULE.length(); outln(); indent--; return true; }

      // a bullet starts with LIS and ends with LIE

      if (html.startsWith(LIS, pos)) {
        pos += LIS.length();
        outlnBullet();
        while (pos < html.length()
               && (html.charAt(pos)==' ' || Character.isWhitespace(html.charAt(pos))))
          pos++;
        return true;
      }

      if (html.startsWith(LIE, pos)) { pos += LIE.length(); outln(); return true; }

      return false;
    }

    private void outlnBullet() {
      sb.append(EOL);
      for (int i = 0; i < indent * 2; i++) sb.append(" ");
      sb.append("* ");
      col = indent * 2 + 2;
    }

    private void outln() {
      sb.append(EOL);
      if (indent > 0) {
        col = indent * 2 + 2;
        for (int i = 0; i < col; i++) sb.append(" ");
      } else  {
        col = 0;
      }
    }

    private void out(String s) {
      sb.append(s);
      col += s.length();
    }

    private void out(char c) {
      sb.append(c);
      col += 1;
      // poor man's word wrap:  we should wrap before we hit the margin
      //                        but it's easier to wrap after...
      if ((c == ' ') && (col > margin)) outln();
    }

    public String toString() {
      return sb.toString();
    }
  }
}
