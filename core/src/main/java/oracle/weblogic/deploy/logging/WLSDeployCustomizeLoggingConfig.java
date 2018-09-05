/*
 * Copyright (c) 2018, Oracle and/or its affiliates. All rights reserved.
 * The Universal Permissive License (UPL), Version 1.0
 */
package oracle.weblogic.deploy.logging;

import oracle.weblogic.deploy.util.StringUtils;

import java.lang.reflect.Method;
import java.text.MessageFormat;
import java.util.*;
import java.util.logging.Handler;

/**
 * Use this class to add custom handlers to the root WLSDEPLOY logger. The WLSDeployLoggingConfig
 * loads the properties to the LogManager. .
 *
 * <p>You must add this class to the -Djava.util.logging.config.class parameter before the tool JVM is started.
 * To inject one or more handlers into the WLSDEPLOY logger, you may either add the comma separated list to the
 * logger.properties file as WLSDEPLOY_LOGGER_NAME.handlers=list, or set the list on the environment variable
 * WLSDEPLOY_LOG_HANDLERS_ENV_VARIABLE. The property in the logging.properties file takes precedence
 * over the environment variable.
 *
 * <p>This class will check each handler in the list to see if it has implemented the WLSDEPLOY_HANDLER_METHOD. This method
 * returns a handler's properties. Any property that already exists in the logging.properties will be discarded -
 * as logging.properties takes precedence. Any property that does not start with the handler class name will
 * be rejected. This class' ONLY purpose is to dynamically add a handler and/or its properties to the
 * WLSDEPLOY root logger.
 *
 * <p>The WLSDEPLOY logger is instantiated by WLSDeployLoggingConfig (and thus, the handlers are
 * instantiated). The WLSDEPLOY logger's parameters are not inherited by a child logger unless the
 * parameter instances already exist before the child logger is added.
 */
public class WLSDeployCustomizeLoggingConfig extends WLSDeployLoggingConfig {

    private static final String WLSDEPLOY_HANDLER_PROP = WLSDEPLOY_LOGGER_NAME + ".handlers";
    private static final String WLSDEPLOY_HANDLER_METHOD = "getHandlerProperties";

    /**
     * Check the logging.properties file for a "WLSDEPLOY".handlers property. If the property does not exist,
     * check to see if the WLSDEPLOY_LOG_HANDLERS_ENV_VARIABLE environment variable has been set.
     *
     * <p>Check each handler to see if has implemented the WLSDEPLOY_HANDLER_METHOD. A property
     * returned from the method is added to the provided properties if the property does not exist in the list.
     *
     * @param programName name of the tool calling this method
     * @param logProps properties comprised by the WLSDeployLoggingConfig class as the base list
     */
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
