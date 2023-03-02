/*
 * Copyright (c) 2023, Oracle Corporation and/or its affiliates.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.logging;

import java.util.logging.Level;

public class ToDoLevel extends Level {
    public static final Level TODO = new ToDoLevel("TODO", 820);

    private static final long serialVersionUID = 1L;

    protected ToDoLevel(String name, int value) {
        super(name, value);
    }
}
