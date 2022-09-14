package oracle.weblogic.deploy.integration.utils;

/**
 * Class that holds the results of using java to exec a command
 */
public class CommandResult {
  private int exitValue;
  private String stdout;

  public CommandResult(int exitValue, String stdout) {
    this.exitValue = exitValue;
    this.stdout = stdout;
  }

  public int exitValue() {
    return this.exitValue;
  }

  public String stdout() {
    return this.stdout;
  }

}