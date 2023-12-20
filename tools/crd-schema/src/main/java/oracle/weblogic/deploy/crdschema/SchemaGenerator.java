// Copyright (c) 2023, Oracle and/or its affiliates.
// Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.

package oracle.weblogic.deploy.crdschema;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.databind.MapperFeature;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.ObjectWriter;
import com.fasterxml.jackson.databind.SerializationFeature;
import com.fasterxml.jackson.databind.json.JsonMapper;
import com.fasterxml.jackson.dataformat.yaml.YAMLFactory;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.io.InputStream;
import java.net.InetSocketAddress;
import java.net.Proxy;
import java.net.SocketAddress;
import java.net.URL;
import java.net.URLConnection;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Creates schemas for use in WDT to validate the CRD-based sections of the model.
 * The source schema files are read from GitHub repositories.
 * The resulting files target/crd/*-v#.json belong in WDT directory:
 * core/src/main/resources/oracle/weblogic/deploy/wko .
 */
public class SchemaGenerator {

  private static final boolean USE_PROXY = true;
  private static final String PROXY_HOST = "www-proxy-hqdc.us.oracle.com";
  private static final int PROXY_PORT = 80;

  // remove extra whitespace from result (set to false for debug)
  protected static final boolean MINIMIZE = true;

  // remove descriptions from result.
  // we leave them in place in WDT 4.0 for modelHelp to display
  protected static final boolean REMOVE_DESCRIPTIONS = false;

  // WKO project is contains k8s definitions
  protected static final String WKO_SOURCE_URL = "https://raw.githubusercontent.com/oracle/weblogic-kubernetes-operator";
  protected static final String WKO_SOURCE_TAG = "main";  // this could also be a specific tag, such as "v3.4.3"

  // contains generic k8s definitions including metadata, apiVersion, etc.
  private static final String K8S_SCHEMA_PATH =
          "json-schema-generator/src/main/resources/oracle/kubernetes/json/caches";

  // local definitions internal to K8S_SCHEMA can be resolved
  private static final String LOCAL_DEFINITION_PREFIX = "#/definitions/";

  protected static final String K8S_VERSION_V1_9_0 = "1.9.0";
  protected static final String K8S_VERSION_V1_13_5 = "1.13.5";

  protected static final String SCHEMA_ROOT_ELEMENT = "openAPIV3Schema";

  protected static Map<String, Object> asMap(Object obj) {
    @SuppressWarnings("unchecked")
    Map<String, Object> map = (Map<String, Object>) obj;
    return map;
  }

  protected static List<Object> asList(Object obj) {
    @SuppressWarnings("unchecked")
    List<Object> list = (List<Object>) obj;
    return list;
  }

  // read a schema from the specified URL, with no alterations
  protected static Map<String, Object> readSchema(String url) throws Exception {
    boolean isYaml = url.endsWith(".yaml");
    JsonFactory factory = isYaml ? new YAMLFactory() : null;
    ObjectMapper objectMapper = new ObjectMapper(factory);

    Proxy proxy = Proxy.NO_PROXY;
    if(USE_PROXY) {
      SocketAddress addr = new InetSocketAddress(PROXY_HOST, PROXY_PORT);
      proxy = new Proxy(Proxy.Type.HTTP, addr);
    }

    URLConnection latestConnection = new URL(url).openConnection(proxy);
    try(InputStream stream  = latestConnection.getInputStream()) {
      return asMap(objectMapper.readValue(stream, Object.class));
    }
  }

  // resolve an INTERNAL reference in K8S_SCHEMA, such as:
  // "$ref": "#/definitions/io.k8s.api.core.v1.PodTemplateSpec" .
  // if the reference is not internal to K8S_SCHEMA, or can't be resolved, return null.
  private static Map<String, Object> resolveReference(String refValue, Map<String, Object> definitions) {
    if (refValue.startsWith(LOCAL_DEFINITION_PREFIX)) {
      refValue = refValue.substring(LOCAL_DEFINITION_PREFIX.length());
      return asMap(definitions.get(refValue));
    }
    return null;
  }

  // resolve references for the specified section in schema, and recurse through its children.
  // child nodes may have been added by resolving references.
  protected static void resolveRefs(Map<String, Object> section, Map<String, Object> definitions) {
    // properties reference will look like:
    //   "properties": {
    //     "<field>": {
    //       "description": "<text>",
    //       "$ref": "#/definitions/io.k8s.api.core.v1.PodTemplateSpec"
    //     },
    //     . . .
    //   }

    Map<String, Object> properties = asMap(section.get("properties"));
    if(properties != null) {
      for(Map.Entry<String, Object> entry: properties.entrySet()) {
        Map<String, Object> details = asMap(entry.getValue());
        String ref = (String) details.get("$ref");
        if (ref != null) {
          Map<String, Object> resolved = resolveReference(ref, definitions);
          if(resolved != null) {
            properties.put(entry.getKey(), resolved);
            details = resolved;
          }
        }
        resolveRefs(details, definitions);
      }
    }

    // items reference will look like:
    //   "items": {
    //     "$ref": "#/definitions/io.k8s.api.extensions.v1beta1.DaemonSet"
    //   },

    Map<String, Object> itemProperties = asMap(section.get("items"));
    if(itemProperties != null) {
      String ref = (String) itemProperties.get("$ref");
      if(ref != null) {
        Map<String, Object> resolved = resolveReference(ref, definitions);
        if(resolved != null) {
          section.put("items", resolved);
          itemProperties = resolved;
        }
      }
      resolveRefs(itemProperties, definitions);
    }
  }

  // get a specific schema version from a versioned schema
  protected static Map<String, Object> readSchemaVersion(String url, String version) throws Exception {
    Map<String, Object> schema = readSchema(url);
    Map<String, Object> spec = asMap(schema.get("spec"));

    String kind = null;
    Map<String, Object> names = asMap(spec.get("names"));
    if(names != null) {
      kind = (String) names.get("kind");
    }

    List<Object> versions = asList(spec.get("versions"));
    for(Object versionObject: versions) {
      Map<String, Object> versionSchema = asMap(versionObject);
      String name = versionSchema.get("name").toString();
      if(name.equals(version)) {
        Map<String, Object> versionedSchema = asMap(versionSchema.get("schema"));

        // if "kind" was in the schema, add its value to "properties/kind/enum" in the versioned schema.
        // this will allow the modelHelp tool to display it as a possible value.
        if(kind != null) {
          Map<String, Object> kindFolder = getObject(versionedSchema, SCHEMA_ROOT_ELEMENT, "properties", "kind");
          if(kindFolder == null) {
            kindFolder = new HashMap<>();
            Map<String, Object> propertiesFolder = getObject(versionedSchema, SCHEMA_ROOT_ELEMENT, "properties");
            propertiesFolder.put("kind", kindFolder);
          }

          if(!kindFolder.containsKey("enum")) {
            kindFolder.put("enum", Collections.singletonList(kind));
          }
        }
        return versionedSchema;
      }
    }

    throw new Exception("Unable to find version " + version + " for schema " + url);
  }

  protected static void removeDescriptions(Map<String, Object> section) {
    section.remove("description");

    Map<String, Object> properties = asMap(section.get("properties"));
    if(properties != null) {
      for(Map.Entry<String, Object> entry: properties.entrySet()) {
        Map<String, Object> details = asMap(entry.getValue());
        removeDescriptions(details);
      }
    }

    Map<String, Object> itemProperties = asMap(section.get("items"));
    if(itemProperties != null) {
      removeDescriptions(itemProperties);
    }
  }

  // read the root properties for Deployment from the K8S_SCHEMA file.
  // resolve any internal references in the resulting schema.
  private Map<String, Object> readK8sDefinitions(String kubernetesVersion) throws Exception {
    String fileName = "kubernetes-" + kubernetesVersion + ".json";
    String url = WKO_SOURCE_URL + "/" + WKO_SOURCE_TAG + "/" + K8S_SCHEMA_PATH + "/" + fileName;
    Map<String, Object> schema = readSchema(url);
    return asMap(schema.get("definitions"));
  }

  protected Map<String, Object> readK8sDefinition(String definitionKey, String version) throws Exception {
    Map<String, Object> definitions = readK8sDefinitions(version);
    Map<String, Object> definition = asMap(definitions.get(definitionKey));
    resolveRefs(definition, definitions);
    return definition;
  }

  protected static void writeSchema(Map<String, Object> schema, File outputFile) throws IOException {
    ObjectMapper mapper = JsonMapper.builder()
            .configure(MapperFeature.SORT_PROPERTIES_ALPHABETICALLY, true)
            .configure(SerializationFeature.ORDER_MAP_ENTRIES_BY_KEYS, true)
            .build();

    ObjectWriter objectWriter = MINIMIZE ? mapper.writer() : mapper.writerWithDefaultPrettyPrinter();
    String json = objectWriter.writeValueAsString(schema);

    try (FileWriter writer = new FileWriter(outputFile)) {
      writer.write(json);
      writer.write(System.lineSeparator());
    }
  }

  protected static File getOutputDirectory() throws Exception {
    // if running from JAR file, output to current directory
    String className = SchemaGenerator.class.getName().replace('.', '/');
    URL classResource = SchemaGenerator.class.getResource("/" + className + ".class");
    if ((classResource != null) && "jar".equals(classResource.getProtocol())) {
      return new File(System.getProperty("user.dir"));
    }

    // write to the Maven target directory
    URL baseUrl = SchemaGenerator.class.getResource("/");
    if(baseUrl == null) {
      throw new Exception("Can't determine resource directory");
    }

    Path targetPath = Paths.get(baseUrl.toURI()).getParent();
    File outputDir = new File(targetPath.toString(), "crd");
    if(!outputDir.isDirectory() && !outputDir.mkdirs()) {
      throw new Exception("Can't create " + outputDir);
    }

    return outputDir;
  }

  protected static Map<String, Object> getObject(Map<String, Object> schema, String... names) {
    Map<String, Object> object = schema;
    for (String name: names) {
      object = asMap(object.get(name));
    }
    return object;
  }

  public static void main(String[] args) {
    try {
      WkoSchemaGenerator.generateAllSchemas();;

      VzSchemaGenerator.generateAllSchemas();;

      System.out.println("Files written to: " + getOutputDirectory());

    } catch(Exception e) {
      System.err.println("Unable to update schemas: " + e.getLocalizedMessage());
      e.printStackTrace();
    }
  }

}
