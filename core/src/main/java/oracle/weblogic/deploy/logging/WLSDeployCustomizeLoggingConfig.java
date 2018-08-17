package oracle.weblogic.deploy.logging;

import oracle.weblogic.deploy.util.StringUtils;

import java.lang.reflect.Method;
import java.text.MessageFormat;
import java.util.*;
import java.util.logging.Handler;

public class WLSDeployCustomizeLoggingConfig extends WLSDeployLoggingConfig {

    private static final String WLSDEPLOY_HANDLER_PROP = WLSDEPLOY_LOGGER_NAME + ".handlers";
    private static final String WLSDEPLOY_HANDLER_METHOD = "getHandlerProperties";

    @Override
    public void customizeLoggingProperties(String programName, Properties logProps) {
        List<Class<?>> classList  = new ArrayList<>();
        for (String handlerName : findExtraHandlers(logProps)) {
            classList.add(getHandlerClass(handlerName));
        }
        List<String> handlerList = new ArrayList<>();
        for (Class<?> handler : classList) {
            handlerList.add(handler.getName());
            addHandlerProperties(logProps, handler);
        }
        logProps.setProperty(WLSDEPLOY_HANDLER_PROP, StringUtils.getCommaSeparatedListString(handlerList));
    }

    private static Set<String> findExtraHandlers(Properties logProps) {
        // The handlers are applied in order - process environment variable first, then logging properties
        Set<String> handlers = new HashSet<>();
        String[] addTo = StringUtils.splitCommaSeparatedList(System.getenv(WLSDEPLOY_LOG_HANDLERS_ENV_VARIABLE));
        if (addTo.length > 0) {
            handlers.addAll(Arrays.asList(addTo));
        }
        addTo = StringUtils.splitCommaSeparatedList(logProps.getProperty(WLSDEPLOY_HANDLER_PROP));
        if (addTo.length > 0) {
            handlers.addAll(Arrays.asList(addTo));
        }
        return handlers;
    }
    private static Class<?> getHandlerClass(String handlerName) {
        String message = null;
        Class<?> handler = null;
        try {
            handler = Class.forName(handlerName);
            if (!Handler.class.isAssignableFrom(handler)) {
                message = MessageFormat.format("Class {0} is not a Handler", handlerName);
            }
        } catch(ClassNotFoundException cnf) {
            message = MessageFormat.format("Unable to find handler class {0} so skipping logging configuration",
                    handlerName);
        }
        if (message != null) {
            System.err.println(message);
            System.exit(ERROR_EXIT_CODE);
        }
        return handler;
    }

    private static void addHandlerProperties(Properties logProps, Class<?> clazz) {
        Properties props = null;
        // a forEach would be good here!
        String clazzName = clazz.getName();
        // make sure some formatter is set
        //logProps.setProperty(clazzName + HANDLER_FORMATTER_PROP, LOG_FORMATTER);
        Set<String> propSet = logProps.stringPropertyNames();
        try {
            // only look in this class
            Method method = clazz.getDeclaredMethod(WLSDEPLOY_HANDLER_METHOD);
            props =  (Properties)method.invoke(null);
        } catch (NoSuchMethodException nsm) {
            return;
        } catch (Exception e) {
            String message = MessageFormat.format("Unable to successfully populate properties for handler {0} " +
                    "so skipping logging configuration : {1}", clazzName, e.getLocalizedMessage());
            System.err.println(message);
            System.exit(ERROR_EXIT_CODE);
        }

        if (props != null) {
            for (Map.Entry<?, ?> listItem : props.entrySet()) {
                if (listItem.getKey() instanceof String && listItem.getValue() instanceof String) {
                    // requires the handler property name without the handler class name
                    // this method will add the class to make sure the handler is not setting global properties
                    // or properties for other handlers
                    String property = clazzName + '.' + listItem.getKey();
                    if (!propSet.contains(property)) {
                        // logging.properties property takes precedent
                        logProps.setProperty(property, (String)listItem.getValue());
                    }
                }
            }
        }
    }

}