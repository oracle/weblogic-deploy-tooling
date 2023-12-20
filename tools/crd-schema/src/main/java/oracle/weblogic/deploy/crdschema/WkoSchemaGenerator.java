// Copyright (c) 2023, Oracle and/or its affiliates.
// Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.

package oracle.weblogic.deploy.crdschema;

import java.io.File;
import java.util.Arrays;
import java.util.List;
import java.util.Map;

/**
 * Creates schemas for use in WDT to validate the kubernetes section of the model.
 * The source schema files are read from the WKO GitHub repository.
 * The resulting files target/wko/*-v#.json belong in WDT directory:
 * core/src/main/resources/oracle/weblogic/deploy/crd .
 */

public class WkoSchemaGenerator extends SchemaGenerator {

  // contains wko-specific definitions including spec and status
  private static final String OPERATOR_SCHEMA_PATH = "kubernetes/crd";

  // top-level fields in the WKO schema should not be imported from K8S_SCHEMA
  private static final List<String> WKO_SCHEMA_ROOTS = Arrays.asList("spec", "status");

  // the WKO schema versions that we are using, should be in WKO schema files
  private static final String WKO_VERSION_V1 = "v1";
  private static final String WKO_VERSION_V8 = "v8";
  private static final String WKO_VERSION_V9 = "v9";

  private WkoSchemaGenerator() {
  }

  // read the root properties for Deployment from the K8S_SCHEMA file.
  // discard root properties that WKO will override.
  // resolve any internal references in the resulting schema.
  private Map<String, Object> readDeploymentProperties(String kubernetesVersion) throws Exception {
    Map<String, Object> deployDefinition = readK8sDefinition("io.k8s.api.apps.v1.Deployment", kubernetesVersion);
    Map<String, Object> deployProperties = asMap(deployDefinition.get("properties"));

    for(String root: WKO_SCHEMA_ROOTS) {
      deployProperties.remove(root);
    }
    return deployProperties;
  }

  // combine WKO-specific elements and k8s elements in final schema.
  public void createSchema(String crdName, String wkoVersion, String k8sVersion,
                           String schemaPrefix) throws Exception {

    String fileName = schemaPrefix + "-" + wkoVersion + ".json";
    System.out.println("Writing " + fileName + "...");

    // generic k8s properties (metadata, kind, etc.) are in the k8s definition
    Map<String, Object> deploymentProperties = readDeploymentProperties(k8sVersion);

    String schemaPath = WKO_SOURCE_URL + "/" + WKO_SOURCE_TAG + "/" + OPERATOR_SCHEMA_PATH + "/" + crdName;
    Map<String, Object> schema = readSchemaVersion(schemaPath, wkoVersion);
    Map<String, Object> openApiSchema = asMap(schema.get(SCHEMA_ROOT_ELEMENT));
    Map<String, Object> schemaProperties = asMap(openApiSchema.get("properties"));

    // preserve the "kind/enum" value pulled from the versioned schema
    Map<String, Object> kindFolder = getObject(schemaProperties, "kind");
    Object kindEnum = kindFolder.get("enum");
    Map<String, Object> deploymentKind = asMap(deploymentProperties.get("kind"));
    deploymentKind.put("enum", kindEnum);

    // generic k8s properties (metadata, kind, etc.) are in the k8s definition
    schemaProperties.putAll(deploymentProperties);

    if(REMOVE_DESCRIPTIONS) {
     removeDescriptions(openApiSchema);
    }

    File outputDir = getOutputDirectory();
    File outFile = new File(outputDir, fileName);
    writeSchema(schema, outFile);
  }

  public static void generateAllSchemas() throws Exception {
      WkoSchemaGenerator generator = new WkoSchemaGenerator();
      generator.createSchema("domain-crdv8.yaml", WKO_VERSION_V8, K8S_VERSION_V1_9_0, "domain-crd-schema");
      generator.createSchema("domain-crd.yaml", WKO_VERSION_V9, K8S_VERSION_V1_13_5, "domain-crd-schema");
      generator.createSchema("cluster-crd.yaml", WKO_VERSION_V1, K8S_VERSION_V1_13_5, "cluster-crd-schema");
  }
}
