package oracle.weblogic.deploy.integration.annotations;

import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

/**
 * Logger to use with the LoggingExtension class.
 * Mark the PlatformLogger static variable of the integration test with this annotation.
 */
@Target({ElementType.FIELD})
@Retention(RetentionPolicy.RUNTIME)
public @interface TestingLogger {
}
