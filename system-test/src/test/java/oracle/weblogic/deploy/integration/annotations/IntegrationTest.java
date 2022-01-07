package oracle.weblogic.deploy.integration.annotations;

import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

import oracle.weblogic.deploy.integration.extensions.LoggingExtension;
import oracle.weblogic.deploy.integration.extensions.TimingExtension;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.extension.ExtendWith;

@Target({ElementType.TYPE})
@Retention(RetentionPolicy.RUNTIME)
@ExtendWith(TimingExtension.class)
@ExtendWith(LoggingExtension.class)
@Tag("integration")
public @interface IntegrationTest {
}
