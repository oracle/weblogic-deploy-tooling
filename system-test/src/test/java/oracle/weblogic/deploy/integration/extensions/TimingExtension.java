package oracle.weblogic.deploy.integration.extensions;

import java.util.concurrent.TimeUnit;

import oracle.weblogic.deploy.logging.PlatformLogger;
import oracle.weblogic.deploy.logging.WLSDeployLogFactory;
import org.junit.jupiter.api.extension.AfterTestExecutionCallback;
import org.junit.jupiter.api.extension.BeforeTestExecutionCallback;
import org.junit.jupiter.api.extension.ExtensionContext;

public class TimingExtension implements BeforeTestExecutionCallback, AfterTestExecutionCallback {
  private static final String START_TIME = "start time";

  @Override
  public void beforeTestExecution(ExtensionContext context) throws Exception {
    getStore(context).put(START_TIME, System.currentTimeMillis());
  }

  @Override
  public void afterTestExecution(ExtensionContext context) throws Exception {
    long startTime = getStore(context).remove(START_TIME, long.class);
    long duration = System.currentTimeMillis() - startTime;
    long minutes = TimeUnit.MILLISECONDS.toMinutes(duration);
    long seconds = TimeUnit.MILLISECONDS.toSeconds(duration) - TimeUnit.MINUTES.toSeconds(minutes);

    LoggingExtension.getLogger((context.getRequiredTestClass()))
        .info("========== Test duration [{0}] method={1}: {2} min, {3} sec ==========",
            context.getDisplayName(),
            context.getRequiredTestMethod().getName(),
            minutes, seconds);
  }

  private ExtensionContext.Store getStore(ExtensionContext context) {
    return context.getStore(
        ExtensionContext.Namespace.create(context.getRequiredTestClass(), context.getRequiredTestMethod()));
  }
}