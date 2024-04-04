// Copyright (c) 2023, Oracle and/or its affiliates.
// Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.

package oracle.weblogic.deploy.crdschema;

import java.io.File;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

/**
 * Creates a schema for use in WDT to validate the verrazzano section of the model.
 * The source schema files are read from GitHub repositories.
 * The resulting files target/wko/*-v#.json belong in WDT directory:
 * core/src/main/resources/oracle/weblogic/deploy/crd .
 */
public class VzSchemaGenerator extends SchemaGenerator {

  private static final String VZ_SOURCE_URL = "https://raw.githubusercontent.com/verrazzano/verrazzano";
  private static final String VZ_SOURCE_TAG = "master";  // this could also be a specific tag, such as "v3.4.3"
  private static final String OAM_CRD_PATH = "platform-operator/thirdparty/charts/oam-kubernetes-runtime/crds";
  private static final String VZ_CRD_PATH = "platform-operator/helm_config/charts/verrazzano-application-operator/crds";

  // the OAM schema versions that we are using
  private static final String OAM_VERSION_V1 = "v1alpha2";
  // the VZ schema versions that we are using
  private static final String VZ_VERSION_V1 = "v1alpha1";

  private static final String OAM_SCHEMA_PREFIX = "core.oam.";
  private static final String APPLICATION_SCHEMA_NAME = "core.oam.dev_applicationconfigurations.yaml";
  private static final String COMPONENT_SCHEMA_NAME = "core.oam.dev_components.yaml";
  private static final String WLS_WORKLOAD_SCHEMA_NAME = "oam.verrazzano.io_verrazzanoweblogicworkloads.yaml";
  private static final String[] TRAIT_SCHEMA_NAMES = new String[]{
          "oam.verrazzano.io_ingresstraits.yaml",
          "oam.verrazzano.io_loggingtraits.yaml",
          "core.oam.dev_manualscalertraits.yaml",
          "oam.verrazzano.io_metricstraits.yaml"
  };
  private static final String CONFIG_MAP_DEFINITION_KEY = "io.k8s.api.core.v1.ConfigMap";

  private final String oamVersion;
  private final String k8sVersion;
  private final String vzVersion;

  private VzSchemaGenerator(String vzVersion, String oamVersion, String k8sVersion) {
    this.vzVersion = vzVersion;
    this.oamVersion = oamVersion;
    this.k8sVersion = k8sVersion;
  }

  private Map<String, Object> readOamSchema(String schemaName) throws Exception {
    String schemaPath = VZ_SOURCE_URL + "/" + VZ_SOURCE_TAG + "/" + OAM_CRD_PATH + "/" + schemaName;
    return readSchemaVersion(schemaPath, oamVersion);
  }

  private Map<String, Object> readVerrazzanoSchema(String schemaName) throws Exception {
    String schemaPath = VZ_SOURCE_URL + "/" + VZ_SOURCE_TAG + "/" + VZ_CRD_PATH + "/" + schemaName;
    return readSchemaVersion(schemaPath, vzVersion);
  }

  private void writeWdtSchema(Map<String, Object> schema, String filePrefix) throws Exception {
    String fileName = filePrefix + "-" + vzVersion + ".json";
    System.out.println("Writing " + fileName + "...");

    if(REMOVE_DESCRIPTIONS) {
      Map<String, Object> openApiSchema = asMap(schema.get(SCHEMA_ROOT_ELEMENT));
      removeDescriptions(openApiSchema);
    }

    File outputDir = getOutputDirectory();
    File outFile = new File(outputDir, fileName);
    writeSchema(schema, outFile);
  }

  // read and write the Verrazzano application schema.
  // the trait definitions are added as "oneOf" definitions.
  private void createApplicationSchema() throws Exception {
    Map<String, Object> schema = readOamSchema(APPLICATION_SCHEMA_NAME);
    Map<String, Object> traitObject = getObject(schema, SCHEMA_ROOT_ELEMENT, "properties", "spec",
            "properties", "components", "items", "properties", "traits", "items", "properties", "trait");

    List<Map<String, Object>> oneOfs = new ArrayList<>();
    for(String schemaName: TRAIT_SCHEMA_NAMES) {
      boolean isOam = schemaName.startsWith(OAM_SCHEMA_PREFIX);
      Map<String, Object> traitSchema = isOam ? readOamSchema(schemaName) : readVerrazzanoSchema(schemaName);
      traitSchema = asMap(traitSchema.get(SCHEMA_ROOT_ELEMENT));
      oneOfs.add(traitSchema);
    }

    traitObject.put("oneOf", oneOfs);
    writeWdtSchema(schema, "vz-application");
  }

  // insert the k8s definition for WebLogic workload into the Verrazzano component workload.
  private void createWebLogicSchema() throws Exception {
    Map<String, Object> schema = readOamSchema(COMPONENT_SCHEMA_NAME);
    Map<String, Object> workloadObject = getObject(schema, SCHEMA_ROOT_ELEMENT, "properties", "spec",
            "properties", "workload");
    Map<String, Object> weblogicFullSchema = readVerrazzanoSchema(WLS_WORKLOAD_SCHEMA_NAME);
    Map<String, Object> weblogicSchema = asMap(weblogicFullSchema.get(SCHEMA_ROOT_ELEMENT));
    for(String key: weblogicSchema.keySet()) {
      workloadObject.put(key, weblogicSchema.get(key));
    }
    writeWdtSchema(schema, "vz-weblogic");
  }

  // insert the k8s definition for configMap into the Verrazzano component workload.
  private void createConfigmapSchema() throws Exception {
    Map<String, Object> schema = readOamSchema(COMPONENT_SCHEMA_NAME);
    Map<String, Object> workloadObject = getObject(schema, SCHEMA_ROOT_ELEMENT, "properties", "spec",
            "properties", "workload");
    Map<String, Object> configmapSchema = readK8sDefinition(CONFIG_MAP_DEFINITION_KEY, k8sVersion);
    for(String key: configmapSchema.keySet()) {
      workloadObject.put(key, configmapSchema.get(key));
    }
    writeWdtSchema(schema, "vz-configmap");
  }

  public static void generateAllSchemas() throws Exception {
      VzSchemaGenerator generator = new VzSchemaGenerator(VZ_VERSION_V1, OAM_VERSION_V1, K8S_VERSION_V1_13_5);
      generator.createApplicationSchema();
      generator.createWebLogicSchema();
      generator.createConfigmapSchema();
  }
}
