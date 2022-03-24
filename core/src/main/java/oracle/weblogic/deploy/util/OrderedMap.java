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
    private transient CommentMap commentMap = new CommentMap();

    public OrderedMap() {
        super();
    }

    public CommentMap getCommentMap() {
        return commentMap;
    }

    public void setCommentMap(CommentMap commentMap) {
        this.commentMap = commentMap;
    }

    /**
     * {@inheritDoc}
     */
    @Override
    public boolean equals(Object other) {
        boolean result;
        if (this == other) {
            result = true;
        } else if (other == null || this.getClass() != other.getClass()) {
            result = false;
        } else {
            result = super.equals(other);
            if (result) {
                result = this.getCommentMap().equals(((OrderedMap) other).getCommentMap());
            }
        }
        return result;
    }

    /**
     * {@inheritDoc}
     */
    @Override
    public int hashCode() {
        return super.hashCode() >> 8 + commentMap.hashCode();
    }
}
