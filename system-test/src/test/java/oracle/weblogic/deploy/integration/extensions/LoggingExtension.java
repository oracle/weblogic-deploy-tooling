package oracle.weblogic.deploy.integration.extensions;

import java.util.List;
import java.util.logging.Level;
import java.util.logging.Logger;

import oracle.weblogic.deploy.integration.annotations.TestingLogger;
import org.junit.jupiter.api.extension.AfterTestExecutionCallback;
import org.junit.jupiter.api.extension.BeforeTestExecutionCallback;
import org.junit.jupiter.api.extension.ExtensionContext;
import org.junit.platform.commons.support.AnnotationSupport;

public class LoggingExtension implements BeforeTestExecutionCallback {

  @Override
  public void beforeTestExecution(ExtensionContext context) {
    getLogger(context.getRequiredTestClass())
        .log(Level.INFO, () -> String.format("========== Starting test [%s] method=%s ==========",
            context.getDisplayName(),
            context.getRequiredTestMethod().getName()));
  }


  /**
   * Return the declared logger from the test class by finding the annotated logger with @Logger.
   * @param testClass JUnit5 test class
   * @return LoggingFacade instance from the test class
   */
  public static Logger getLogger(Class<?> testClass) {
    List<Logger> loggers = AnnotationSupport
        .findAnnotatedFieldValues(testClass, TestingLogger.class, Logger.class);
    if (loggers == null || loggers.isEmpty()) {
      throw new IllegalStateException("Test class does not have an annotated LoggingFacade with @TestingLogger : "
          + testClass.getName());
    } else if (loggers.size() > 1) {
      throw new IllegalStateException("Test class should not have more than one @TestingLogger annotation: "
          + testClass.getName());
    }

    return loggers.get(0);
  }
}
