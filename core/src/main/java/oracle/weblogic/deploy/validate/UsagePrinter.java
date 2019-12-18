/*
 * Copyright (c) 2019, Oracle Corporation and/or its affiliates.  All rights reserved.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.validate;

import oracle.weblogic.deploy.util.FileUtils;

import javax.script.ScriptEngine;
import javax.script.ScriptEngineManager;
import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.StringWriter;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 */
public class UsagePrinter {

    private UsagePrinter() {
    }

    private void print_usage(String path) throws Exception {
        String[] parts = path.split(":/", 2);

        if (parts.length != 2) {
            throw new RuntimeException("path must be: <section>:/<folders>");
        }

        // String sectionName = parts[0];
        // System.out.println("Section: " + sectionName);

        String folderPath = parts[1];
        // System.out.println("Path: " + folderPath);

        // need a map to check if folder in section
        // need a structure to do root level, such as topology:/

        String[] folders = folderPath.split("/");
        String topFolder = folders[0];

        Map aliasMap = readAliasMap(topFolder);

        Map pathFolder;
        if(folders.length == 1) {
            pathFolder = aliasMap;
        } else {
            Map folderMap = (Map) aliasMap.get("folders");
            pathFolder = findFolder(folderMap, Arrays.asList(folders).subList(1, folders.length));
        }

        System.out.println("PATH FOLDER: " + path + " | " + pathFolder.get("wlst_type"));

        // dumpTree(aliasMap, "");
    }

    private Map findFolder(Map folderMap, List<String> path) {
        String firstFolder = path.get(0);
        if(folderMap.containsKey(firstFolder)) {
            Map childMap = (Map) folderMap.get(firstFolder);
            if(path.size() == 1) {
                return childMap;
            } else {
                List<String> nextPath = path.subList(1, path.size());
                return findFolder((Map) childMap.get("folders"), nextPath);
            }
        } else {
            System.out.println("The folder " + path + " is invalid");
        }

        return new HashMap();
    }

    private Map readAliasMap(String topFolder) throws Exception {
        String jsonFileName = topFolder + ".json";
        String resource_path = "oracle/weblogic/deploy/aliases/category_modules/" + jsonFileName;

        InputStream stream = FileUtils.getResourceAsStream(resource_path);

        // remove line feeds to use javascript JSON.parse() with string.
        // use this pre-nashorn method call for compatibility with Java 7.

        String json;
        try(StringWriter writer = new StringWriter()) {
            try(BufferedReader reader = new BufferedReader(new InputStreamReader(stream))) {
                String line;
                while((line = reader.readLine()) != null) {
                    writer.write(line + " ");
                }
            }

            json = writer.toString();
        }

        // escape any apostrophe characters for JavaScript call
        json = json.replaceAll("'", "\\\\'");

        // System.out.println("JAVA VERSION: " + System.getProperty("java.version"));
        // System.out.println("JSON: " + json);

        ScriptEngineManager sem = new ScriptEngineManager();
        ScriptEngine engine = sem.getEngineByName("javascript");

        String script = "JSON.parse('" + json + "')";
        Object result = engine.eval(script);

        // System.out.println("RESULT: " + result + " " + result.getClass());

        return (Map) result;
    }

    private void dumpTree(Map map, String indent) {
        for(Object key: map.keySet()) {
            Object value = map.get(key);
            if(value instanceof Map) {
                System.out.println(indent + key + ":");
                String childIndent = indent + "  ";
                dumpTree((Map) value, childIndent);
            } else {
                System.out.println(indent + key + ": " + value);
            }
        }
    }

    public static void main(String[] args) {
        UsagePrinter printer = new UsagePrinter();

        try {
            printer.print_usage("resources:/JDBCSystemResource");
            printer.print_usage("resources:/JDBCSystemResource/JdbcResource");
            printer.print_usage("resources:/JDBCSystemResource/JdbcResource/JDBCDriverParams/Properties");
            printer.print_usage("resources:/JDBCSystemResource/JdbcResource/BadFolder/Properties");
//            printer.print_usage("resources:/SecurityConfiguration/JdbcResource");
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}
