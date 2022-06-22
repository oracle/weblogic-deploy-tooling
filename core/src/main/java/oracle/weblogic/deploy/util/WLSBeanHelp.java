/*
 * Copyright (c) 2022, Oracle Corporation and/or its affiliates.  
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */

package oracle.weblogic.deploy.util;

import java.beans.BeanDescriptor;
import java.beans.BeanInfo;
import java.beans.FeatureDescriptor;
import java.beans.PropertyDescriptor;
import java.io.ByteArrayOutputStream;
import java.io.PrintStream;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.nio.charset.StandardCharsets;
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

  // gets description of given bean or property in "plain text HTML"
  //   - returns "" if not found
  //   - if propName is null, gets description of bean,
  //     else gets description of prop
  //   - in abbreviate mode, truncates to a single line of
  //     maximum "width-3" or the first "." 
  //     (whichever comes first), and appends "..." if truncated
  //   - in !abbreviate mode, yields full help, with newlines, 
  //     and margin set to "width"
  //   - if propDefault not null, inline it as "default=" along with
  //     any of the discovered prop limits...
  public static String get(
    String beanName,
    String propName,
    boolean abbreviate,
    int width,
    String propDefault
  ) {
    String ds;

    if (propName == null)
      ds = getFeatureDescription(getBeanDescriptor(beanName));
    else
      ds = getFeatureDescription(getPropertyDescriptor(beanName, propName));

    if (ds.length() == 0)
      return "";

    if (abbreviate)
      return " - " + prettyHTMLAbbrev(ds, width); 

    String limits = "";
    if (propName != null) {
      limits = getPropertyLimits(beanName, propName, propDefault);
      if (limits.length() > 0) limits += EOL;
    }

    return limits + prettyHTML(ds, width);
  }

  public static String get(
    String beanName,
    boolean abbreviate,
    int width
  ) {
    return get(beanName, null, abbreviate, width, null);
  }

  private static String getFeatureDescription(
    FeatureDescriptor fd
  ) {
    if (fd == null) return "";
    Object d = fd.getValue("description");
    if (d == null) return ""; // should pretty much never happen
    return d.toString();
  }

  // gets pretty printed default for a given bean prop, legal values, min, or max
  // default is passed in from outside
  // returns "" if not applicable or not found
  private static String getPropertyLimits(
    String beanName,
    String propName,
    String propDefault
  ) {
    String ret = "";
    if (propDefault != null) {
      // we report the passed in default from the alias DB instead of using the 
      // default obtained from the mbean
      ret += "Default=" + propDefault + EOL;
    }

    PropertyDescriptor pd = getPropertyDescriptor(beanName, propName);
    if (pd == null) return ret;

    Object lval = pd.getValue("legalValues");
    if (lval != null) {
      ret += "Legal values: " + EOL;
      for (String val : legalValues(lval))
        ret += "   '" + val.trim() + "'" + EOL;
    }

    Object lmin = pd.getValue("legalMin");
    if (lmin != null) ret += "Min=" + lmin.toString() + EOL;

    Object lmax = pd.getValue("legalMax");
    if (lmax != null) ret += "Max=" + lmax.toString() + EOL;
    return ret;
  }

  // can return null if not found
  private static PropertyDescriptor getPropertyDescriptor(
    String beanName,
    String propName
  ) {
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
    } catch (Throwable ignore) {}
    return null;
  }

  // can return null if not found
  private static BeanDescriptor getBeanDescriptor(
    String beanName
  ) {
    try {
      BeanInfo info = getBeanInfo(beanName);
      if (info == null) return null;
      return info.getBeanDescriptor();
    } catch (Throwable ignore) {}
    return null;
  }

  private static boolean printAttributeHelp(String beanName, String propName, int margin) {
    try {
      BeanInfo info = getBeanInfo(beanName);

      if (info == null)
        throw new RuntimeException("Error:  Bean '" + beanName + "' not found.");

      for (PropertyDescriptor pd:info.getPropertyDescriptors()) {
        if (propName.equals(pd.getName())) {
          println("Bean = " + beanName);
          println("");
          printPropertyDescriptor(pd, margin);
          return true;
        }
      }

      println("Error: Prop '" + propName + "' not found in bean '" + beanName + "'.");
    } catch (Throwable th) {
      println("Error: " + th.getMessage());
    }
    return false;
  }

  static void print(String s) {
    System.out.print(s);
  }

  static void println(String s) {
    System.out.println(s);
  }

  static void printPropertyDescriptor(PropertyDescriptor o, int margin) {
    println("\nPROPERTY\n");
    println("  name=" + o.getName());

    if (!o.getName().equals(o.getDisplayName()))
      println("  display name=" + o.getDisplayName());

    if (!o.getName().equals(o.getShortDescription()))
      println("  short description=" + o.getShortDescription());

    println("  property type=" + o.getPropertyType());
    println("  hidden=" + o.isHidden());

    for (Enumeration<String> en = o.attributeNames();
      en.hasMoreElements();) {
      String s = en.nextElement();
      Object v = o.getValue(s);
      if (s.equals("description")) continue;
      if (s.equals("legalValues")) v = legalValuesAsString(v);
      if (s.equals("see")) v = legalValuesAsString(v);
      println("  " + s + "=" + v);
    }

    println("  " + "description" + "=");
    println(prettyHTML(o.getValue("description").toString(), margin));
    println("");
  }

  public static String prettyHTML(String html, int margin) {
    return new PrettyHTML(html, margin).toString();
  }

  public static String prettyHTMLAbbrev(String html, int width) {
    return new PrettyHTML(html, 1000000).abbrevString(width);
  }

  public static void prettyHTMLTest() {
    String input = ""
      + "<p>Paragraph</p>"
      + "<p>This paragraph is expected to wrap because it is long.</p>"
      + "<p>text highlighting bullets:</p>"
      + "<ol>"
      + "<li><b>bold</b></li>"
      + "<li><i>italic</i></li>"
      + "<li><code>code</code></li>"
      + "</ol>"
      + "<p>symbol bullets:<p>"
      + "<ul>"
      + "<li>&lt;angle brackets&gt;</li>"
      + "<li>ampersand=&amp;</li>"
      + "<li>quote=&quot;</li>"
      + "<li>at_symbol=&#35;</li>"
      + "<li>backslash=&#92;</li>"
      + "<li>This line is expected to wrap because it is long.</li>"
      + "</ul>";
    
    String expect = ""
      + "" + EOL
      + "Paragraph" + EOL
      + "" + EOL
      + "This paragraph is expected " + EOL
      + "to wrap because it is " + EOL
      + "long." + EOL
      + "" + EOL
      + "text highlighting bullets:" + EOL
      + "" + EOL
      + "" + EOL
      + "  * *bold*" + EOL
      + "    " + EOL
      + "  * *italic*" + EOL
      + "    " + EOL
      + "  * 'code'" + EOL
      + "    " + EOL
      + "    " + EOL
      + "symbol bullets:" + EOL
      + "" + EOL
      + "" + EOL
      + "  * <angle brackets>" + EOL
      + "    " + EOL
      + "  * ampersand=&" + EOL
      + "    " + EOL
      + "  * quote='" + EOL
      + "    " + EOL
      + "  * at_symbol=@" + EOL
      + "    " + EOL
      + "  * backslash=\\" + EOL
      + "    " + EOL
      + "  * This line is expected " + EOL
      + "    to wrap because it " + EOL
      + "    is long." + EOL
      + "    " + EOL
      + "    " + EOL;

    String output = prettyHTML(input, 20);
    String message = ""
      + "--- error in bean help HTML pretty print test..." + EOL
      + "--- input:" + EOL + input + EOL
      + "--- expected output:" + EOL + expect
      + "--- actual output:" + EOL + output
      + "---" + EOL;

    if (!output.equals(expect)) throw new RuntimeException(message);
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
    private static final String LT_ = "&lt;";
    private static final String GT_ = "&gt;";
    private static final String AMP = "&amp;";
    private static final String AT_ = "&#35;";
    private static final String BCK = "&#92;";

    private int col;
    private int indent;
    private int margin;
    private StringBuffer sb = new StringBuffer(25);

    PrettyHTML(String s, int margin) {
      this.margin = margin;

      for (int i = 0; i < s.length(); i++) {
        // paragraph mark
        if      (s.startsWith(PGS, i)) { i += PGS.length()-1; if (indent==0) outln(); }
        else if (s.startsWith(PGE, i)) { i += PGE.length()-1; outln(); }
 
        // list of bullets 
        else if (s.startsWith(OLS, i)) { i += OLS.length()-1; outln(); indent++; }
        else if (s.startsWith(OLE, i)) { i += OLE.length()-1; outln(); indent--; }
 
        // list of bullets 
        else if (s.startsWith(ULS, i)) { i += ULS.length()-1; outln(); indent++; }
        else if (s.startsWith(ULE, i)) { i += ULE.length()-1; outln(); indent--; }
 
        // bullet 
        else if (s.startsWith(LIS, i)) { i += LIS.length()-1; 
                                         outln_bullet(); 
                                         while (i + 1 < s.length()
                                                && (s.charAt(i + 1) == ' '
                                                    || Character.isWhitespace(s.charAt(i + 1))))
                                           i++;
                                       } 
        else if (s.startsWith(LIE, i)) { i += LIE.length()-1; outln(); }
 
        // code 
        else if (s.startsWith(CDS, i)) { i += CDS.length()-1; out("'"); }
        else if (s.startsWith(CDE, i)) { i += CDE.length()-1; out("'"); }

        // bold
        else if (s.startsWith(BOS, i)) { i += BOS.length()-1; out("*"); }
        else if (s.startsWith(BOE, i)) { i += BOE.length()-1; out("*"); }

        // italic
        else if (s.startsWith(ITS, i)) { i += ITS.length()-1; out("*"); }
        else if (s.startsWith(ITE, i)) { i += ITE.length()-1; out("*"); }

        // quote, <, >, &, @, \
        else if (s.startsWith(QUO, i)) { i += QUO.length()-1; out("'"); }
        else if (s.startsWith(LT_, i)) { i += LT_.length()-1; out("<"); }
        else if (s.startsWith(GT_, i)) { i += GT_.length()-1; out(">"); }
        else if (s.startsWith(AMP, i)) { i += AMP.length()-1; out("&"); }
        else if (s.startsWith(AT_, i)) { i += AT_.length()-1; out("@"); }
        else if (s.startsWith(BCK, i)) { i += BCK.length()-1; out("\\"); }
 
        else if (s.charAt(i) != ' ' && Character.isWhitespace(s.charAt(i))) { i++; }

        else out(s.charAt(i));
      }
      outln();
    }

    private void outln_bullet() {
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
      col+=1; 
      // poor man's word wrap:  we should wrap before we hit the margin
      //                        but it's easier to wrap after...
      if ((c == ' ') && (col > margin)) outln(); 
    }

    // string up to len "len" stripped of all new-lines and extra white-space.
    // if string contains "." less then len, then string is truncated to the "."
    // if string is truncated, then last three chars are replaced with "..."
    String abbrevString(int len) {
      len = Math.max(4, len);
      String s = toString().trim().replace(EOL, " ");
      s.replaceAll(" *", " ");
      if (s.length() == 0) return "";
      String retS = s.substring(0, Math.min(s.length(), len - 3));
      retS.trim();
      if (retS.indexOf('.') > 0) {
        retS = s.substring(0, retS.indexOf('.') + 1);
        if (retS.length() < s.length())
          retS += ".."; 
      } else {
        if (retS.length() < s.length())
          retS += "..."; 
      }
      return retS;
    }

    public String toString() {
      return sb.toString();
    }
  }

  static String legalValuesAsString(Object o) {
    ArrayList<String> arr = legalValues(o);
    String ret = "";
    for (int i = 0; i < arr.size(); i++) {
      ret += arr.get(i);
      if (i < arr.size() - 1) ret += ", ";
    }
    return ret;
  }

  static ArrayList<String> legalValues(Object o) {
    HashMap<String,String> foo = new HashMap<String,String>();
    ArrayList<String> ret = new ArrayList<String>();
    try {
      for (Object xx : (Object [])o) {
        String cur = "" + xx;
        if (foo.get(cur) == null) {
          foo.put(cur, "something");
          ret.add(cur);
        }
      }
    } catch (ClassCastException cce) {}
    return ret;
  }

  // returns BeanInfo for given bean name, or null if not found
  private static BeanInfo getBeanInfo(String beanName)
  {
    /* we use reflection to implement the equivalent of:
       try {
         return weblogic.management.provider
                .ManagementServiceClient
                .getBeanInfoAccess()
                .getBeanInfoForInterface(beanName, false, null);
       } catch (Throwable th) {
         return null;
       }
    */
    try {
      Class mscClass = 
        Class.forName("weblogic.management.provider.ManagementServiceClient");

      Method getBeanInfoAccessMethod =
        mscClass.getMethod(
          "getBeanInfoAccess",
          new Class[] { }
        );

      // Deprecated Object mscObject = mscClass.newInstance();
      Object mscObject = mscClass.getDeclaredConstructor().newInstance();

      Object biaObject =
        getBeanInfoAccessMethod.invoke(mscObject, new Object[] {});

      Class biaClass =
        Class.forName("weblogic.management.provider.beaninfo.BeanInfoAccess");

      Method getBeanInfoForInterfaceMethod =
        biaClass.getMethod(
          "getBeanInfoForInterface",
          new Class[] { String.class, boolean.class, String.class}
        );

      return (BeanInfo)getBeanInfoForInterfaceMethod.invoke(
               biaObject,
               new Object[] { beanName, Boolean.FALSE, null } 
             );
    } catch (InvocationTargetException ite) {
      // probably bean not found
      // Throwable target = ite.getTargetException();
      // target.printStackTrace(); 
    } catch (Throwable th) {
      // probably a reflection error of some kind
      // th.printStackTrace();  
    }
    return null;
  }

  private static void mainHelp() {
    println("Usage:");
    println("  Ensure weblogic.jar is in CLASSPATH.");
    println("  java -cp \"$CLASSPATH:./core/target/classes\" oracle.weblogic.deploy.util.WLSBeanHelp -bean weblogic.j2ee.descriptor.wl.UniformDistributedTopicBean -prop ForwardingPolicy -margin 60");
    println("  java -cp \"$CLASSPATH:./core/target/classes\" oracle.weblogic.deploy.util.WLSBeanHelp -bean weblogic.j2ee.descriptor.wl.UniformDistributedTopicBean -margin 60");
  }

  // undocumented main to ad hoc retrieve help for a particular bean or bean prop
  public static void main(String [] argv) {
    String beanName = "BeanNotSpecified";
    String propName = null;
    int margin = 60;

    if (argv.length == 0) {
      mainHelp();
      System.exit(1);
    }

    for (int i = 0; i < argv.length; i++) {
      String arg = argv[i];
      try {
        if (arg.equals("-bean")) { 
          beanName = argv[i+1]; i++; 
        }
        else if (arg.equals("-prop")) {
          propName = argv[i+1]; i++;
        }
        else if (arg.equals("-margin")) {
          margin = Integer.parseInt(argv[i+1]); i++;
        }
        else {
          println("Error: Unrecognized parameter '" + arg +"'.");
          mainHelp();
          System.exit(1);
        }
      } catch (ArrayIndexOutOfBoundsException a) {
        println("Error: Expected argument after parameter: " + arg);
        mainHelp();
        System.exit(1);
      }
    }

    if (getBeanInfo(beanName) == null) {
      println("Error: Bean '" + beanName + "' not found.");
    }

    if (propName == null) {
      println("*** Abbreviated bean help for bean '" + beanName + "':");
      println(get(beanName, null, true, margin, null));
      println("*** Full bean help for bean '" + beanName + "':");
      println(get(beanName, null, false, margin, null));
      println("***");
    } else {
      println("*** Abbreviated property help for property '" + beanName + "/" + propName + "':");
      println(get(beanName, propName, true, margin, null));
      println("*** Full property help for property '" + beanName + "/" + propName + "':");
      println(get(beanName, propName, false, margin, null));
      println("*** Raw property help for property '" + beanName + "/" + propName + "':");
      printAttributeHelp(beanName, propName, margin);
      println("***");
    }

    prettyHTMLTest(); // tests HTML pretty printing - emits runtime exception on failure
  }
}
