package oracle.weblogic.deploy.integration.extensions;

import java.util.concurrent.TimeUnit;
import java.util.logging.Level;
import java.util.logging.Logger;

import org.junit.jupiter.api.extension.AfterTestExecutionCallback;
import org.junit.jupiter.api.extension.BeforeTestExecutionCallback;
import org.junit.jupiter.api.extension.ExtensionContext;

public class TimingExtension implements BeforeTestExecutionCallback, AfterTestExecutionCallback {
  private static final String START_TIME = "start time";

  @Override
  public void beforeTestExecution(ExtensionContext context) {
    getStore(context).put(START_TIME, System.currentTimeMillis());
  }

  @Override
  public void afterTestExecution(ExtensionContext context) {
    long startTime = getStore(context).remove(START_TIME, long.class);
    long duration = System.currentTimeMillis() - startTime;
    long minutes = TimeUnit.MILLISECONDS.toMinutes(duration);
    long seconds = TimeUnit.MILLISECONDS.toSeconds(duration) - TimeUnit.MINUTES.toSeconds(minutes);

    boolean testFailed = context.getExecutionException().isPresent();
    Logger logger = LoggingExtension.getLogger((context.getRequiredTestClass()));
    if (testFailed) {
      logger.log(Level.SEVERE, () -> String.format("========== FAILED test [%s] method=%s: %s min, %s sec  ==========",
          context.getDisplayName(), context.getRequiredTestMethod().getName(), minutes, seconds));
      logger.severe(context.getExecutionException().get().getMessage());
    } else {
      logger.log(Level.INFO, () -> String.format("========== Finished test [%s] method=%s: %s min, %s sec  ==========",
          context.getDisplayName(), context.getRequiredTestMethod().getName(), minutes, seconds));
    }
  }

  private ExtensionContext.Store getStore(ExtensionContext context) {
    return context.getStore(
        ExtensionContext.Namespace.create(context.getRequiredTestClass(), context.getRequiredTestMethod()));
  }
}