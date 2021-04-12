package oracle.weblogic.deploy.util;

import org.junit.Test;

import static org.junit.Assert.assertFalse;

public class VersionToolTest {

  @Test
  public void testProductVersionIsSet() {
    String version = oracle.weblogic.deploy.util.WebLogicDeployToolingVersion.getFullVersion();
    assertFalse("WebLogicDeployToolingVersion version is invalid: " + version, version.contains("UNKNOWN"));
    assertFalse("WebLogicDeployToolingVersion version is invalid: " + version, version.contains("git."));
  }
}
