/*
 * Copyright (c) 2022, Oracle Corporation and/or its affiliates.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.util;

import org.junit.jupiter.api.Test;

import oracle.weblogic.deploy.util.WLSBeanHelp;

public class WLSBeanHelpTest {

    @Test
    void testPrettyHTML() {
        String EOL = System.getProperty("line.separator");
        String input = ""
          + "<p>Paragraph</p>"
          + "<p>This paragraph is expected to wrap because it is long.</p>"
          + "<p>text highlighting bullets:</p>"
          + "<ol><li><b>bold</b></li>"
          + "<li><i>italic</i></li>"
          + "<li><code>code</code></li></ol>"
          + "<p>symbol bullets:<p>"
          + "<ul><li>&lt;angle brackets&gt;</li>"
          + "<li>ampersand=&amp;</li>"
          + "<li>quote=&quot;</li>"
          + "<li>at_symbol=&#35;</li>"
          + "<li>backslash=&#92;</li>"
          + "<li>This line is expected to wrap because it is long.</li></ul>";

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

        String output = WLSBeanHelp.prettyHTML(input, 20);
        String message = ""
          + "--- error in bean help HTML pretty print test..." + EOL
          + "--- input:" + EOL + input + EOL
          + "--- expected output:" + EOL + expect
          + "--- actual output:" + EOL + output
          + "---" + EOL;

        if (!output.equals(expect)) throw new AssertionError(message);
    }
}
