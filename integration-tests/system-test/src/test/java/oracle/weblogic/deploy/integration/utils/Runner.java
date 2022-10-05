package oracle.weblogic.deploy.integration.utils;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.PrintWriter;
import java.util.Arrays;
import java.util.HashMap;
import java.util.Map;
import java.util.logging.Logger;

import static java.nio.charset.StandardCharsets.UTF_8;

/**
 * Class for executing shell commands from java.
 */
public class Runner {

  private static final Logger logger = Logger.getLogger("integration.tests.runner");

  /**
   * Run the provided shell command, and send stdout to System.out.
   * @param command external command to be executed
   * @return result from running the provided command
   * @throws IOException if process start fails
   * @throws InterruptedException if the wait is interrupted before the process completes
   */
  public static CommandResult run(String command) throws IOException, InterruptedException {
    return run(command, new PrintWriter(System.out));
  }

  /**
   * Run the provided shell command, and send stdout/stderr to the PrintWriter.
   * @param command external command to be executed
   * @param output PrintWriter to receive stdout
   * @return result from running the provided command
   * @throws IOException if process start fails
   * @throws InterruptedException if the wait is interrupted before the process completes
   */
  public static CommandResult run(String command, PrintWriter... output) throws IOException, InterruptedException {
    return run(command, new HashMap<>(), output);
  }

  /**
   * Run the provided shell command, and send stdout/stderr to the PrintWriter.
   * @param command external command to be executed
   * @param environment values to insert into the new process environment
   * @param writers one or more PrintWriter to receive stdout
   * @return result from running the provided command
   * @throws IOException if process start fails
   * @throws InterruptedException if the wait is interrupted before the process completes
   */
  public static CommandResult run(String command, Map<String,String> environment, PrintWriter... writers) throws IOException, InterruptedException {
    Arrays.stream(writers).forEach(writer -> writer.println("Executing shell command: " + command));
    logger.info("Executing shell command: " + command);

    ProcessBuilder pb = new ProcessBuilder("/bin/sh", "-c", command);
    Process p = null;

    try {
      Map<String, String> processEnv = pb.environment();
      processEnv.putAll(environment);

      pb.redirectErrorStream(true);
      p = pb.start();

      BufferedReader reader = new BufferedReader(new InputStreamReader(p.getInputStream(), UTF_8));
      StringBuilder processOut = new StringBuilder();
      String line;
      while ((line = reader.readLine()) != null) {
        processOut.append(line).append('\n');
        for (PrintWriter output: writers) {
          output.println(line);
        }
      }

      p.waitFor();
      return new CommandResult(p.exitValue(), processOut.toString());
    } finally {
      if (p != null) {
        p.destroy();
      }
    }
  }
}