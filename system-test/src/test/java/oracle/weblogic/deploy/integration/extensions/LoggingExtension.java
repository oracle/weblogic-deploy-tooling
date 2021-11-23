package oracle.weblogic.deploy.integration.extensions;

import java.util.List;

import oracle.weblogic.deploy.integration.annotations.Logger;
import oracle.weblogic.deploy.logging.PlatformLogger;
import org.junit.jupiter.api.extension.AfterTestExecutionCallback;
import org.junit.jupiter.api.extension.BeforeTestExecutionCallback;
import org.junit.jupiter.api.extension.ExtensionContext;
import org.junit.platform.commons.support.AnnotationSupport;

public class LoggingExtension implements BeforeTestExecutionCallback, AfterTestExecutionCallback {

  @Override
  public void beforeTestExecution(ExtensionContext context) throws Exception {
    getLogger(context.getRequiredTestClass())
        .info("========== Starting test [{0}] method={1} ==========",
            context.getDisplayName(),
            context.getRequiredTestMethod().getName());
  }


  @Override
  public void afterTestExecution(ExtensionContext context) throws Exception {
    boolean testFailed = context.getExecutionException().isPresent();
    PlatformLogger logger = getLogger((context.getRequiredTestClass()));
    if (testFailed) {
      logger.severe("========== FAILED test [{0}] method={1} ==========",
          context.getDisplayName(), context.getRequiredTestMethod().getName());
      logger.severe(context.getExecutionException().get().getMessage());
    } else {
      logger.info("========== Finished test [{0}] method={1} ==========",
          context.getDisplayName(), context.getRequiredTestMethod().getName());
    }
  }


  /**
   * Return the declared logger from the test class by finding the annotated logger with @Logger.
   * @param testClass JUnit5 test class
   * @return LoggingFacade instance from the test class
   */
  public static PlatformLogger getLogger(Class<?> testClass) {
    List<PlatformLogger> loggers = AnnotationSupport
        .findAnnotatedFieldValues(testClass, Logger.class, PlatformLogger.class);
    if (loggers == null || loggers.isEmpty()) {
      throw new IllegalStateException("Test class does not have an annotated LoggingFacade with @Logger : "
          + testClass.getName());
    } else if (loggers.size() > 1) {
      throw new IllegalStateException("Test class should not have more than one @Logger annotation: "
          + testClass.getName());
    }

    return loggers.get(0);
  }
}
