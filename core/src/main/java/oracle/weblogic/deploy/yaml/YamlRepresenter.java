/*
 * Copyright (c) 2022, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
 */
package oracle.weblogic.deploy.yaml;

import oracle.weblogic.deploy.util.CommentMap;
import oracle.weblogic.deploy.util.OrderedMap;
import org.yaml.snakeyaml.DumperOptions;
import org.yaml.snakeyaml.comments.CommentLine;
import org.yaml.snakeyaml.comments.CommentType;
import org.yaml.snakeyaml.nodes.MappingNode;
import org.yaml.snakeyaml.nodes.Node;
import org.yaml.snakeyaml.nodes.NodeTuple;
import org.yaml.snakeyaml.nodes.ScalarNode;
import org.yaml.snakeyaml.nodes.Tag;
import org.yaml.snakeyaml.representer.Representer;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

import static oracle.weblogic.deploy.util.CommentMap.BLANK_LINE_KEY;

/**
 * Attach comments from mappings to the associated elements.
 */
public class YamlRepresenter extends Representer {

  public YamlRepresenter(DumperOptions dumperOptions) {
    super(dumperOptions);
  }

  @Override
  protected Node representMapping(Tag tag, Map<?, ?> mapping, DumperOptions.FlowStyle flowStyle) {
    MappingNode node = (MappingNode) super.representMapping(tag, mapping, flowStyle);

    if(mapping instanceof OrderedMap) {
      for (NodeTuple tuple : node.getValue()) {
        Object keyNode = tuple.getKeyNode();
        if(keyNode instanceof ScalarNode) {
          CommentMap commentMap = ((OrderedMap) mapping).getCommentMap();
          String key = ((ScalarNode) keyNode).getValue();
          List<String> comments = commentMap.getComments(key);
          if(!comments.isEmpty()) {
            List<CommentLine> tupleComments = new ArrayList<>();
            for (String comment: comments) {
              if(BLANK_LINE_KEY.equals(comment)) {
                tupleComments.add(new CommentLine(null, null, "", CommentType.BLANK_LINE));
              } else {
                tupleComments.add(new CommentLine(null, null, " " + comment, CommentType.BLOCK));
              }
            }
            tuple.getKeyNode().setBlockComments(tupleComments);
          }
        }
      }
    }

    return node;
  }
}
