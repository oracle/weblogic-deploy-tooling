/*
 * Copyright (c) 2022, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.util;

import java.util.LinkedHashMap;

/**
 * A map that maintains the order of its assignments,
 * and has a mapping of element keys to a list of comments.
 */
public class OrderedMap extends LinkedHashMap<String, Object> {
    private CommentMap commentMap = new CommentMap();

    public OrderedMap() {
        super();
    }

    public CommentMap getCommentMap() {
        return commentMap;
    }

    public void setCommentMap(CommentMap commentMap) {
        this.commentMap = commentMap;
    }
}
