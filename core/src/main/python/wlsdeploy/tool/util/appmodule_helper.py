"""
Copyright (c) 2022, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""

import re


def process_group(begtag, df, handler, result_tokens, search_only):
    updated_text = ''
    endtag = begtag.replace('<', '</')
    properties_pattern_regex = r'(.*)(' + begtag + '[\s\S]*?(?=(' + endtag + ')))(.*)'
    properties_pattern = re.compile(properties_pattern_regex, re.DOTALL)
    properties_match = properties_pattern.match(df)

    # collapse the lookahread duplicated group returned

    fixed_groups = []    
    if properties_match and len(properties_match.groups()) > 0:
        for matched_group in properties_match.groups():
            if matched_group != endtag:
                fixed_groups.append(matched_group)

    for matched_group in fixed_groups:
        if matched_group.startswith(begtag):
            updated_text += handler.process(matched_group, result_tokens, search_only)
        else:
            updated_text += matched_group

    return updated_text                


class GenericTagReplacement(object):        
    def __init__(self, begtag):
        self.begtag = begtag
        self.endtag = self.begtag.replace('<', '</')

    def process(self, xml_text, result_tokens, search_only):
        pattern = r'%s(.*)%s' % (self.begtag, self.endtag)
        p = re.compile(pattern, re.DOTALL)
        matched_groups = re.match(p, xml_text + self.endtag)
        if matched_groups:
            for g in matched_groups.groups():
                if search_only:
                    if g.startswith("@@SECRET:"):
                        result_tokens['found_tokens'].append(g)
        return xml_text


class OracleParamsTag(object):        
    def __init__(self, ons_password_handler):
        self.ons_password_handler = ons_password_handler

    def process(self, xml_text, result_tokens, search_only):
        xml_text = process_group('<ons-wallet-password-encrypted>', xml_text, self.ons_password_handler, result_tokens,
                                 search_only)
        return xml_text


class ProcessProperties(object):        
    def __init__(self):
        pass

    def process(self, xmltext, result_tokens, search_only):
        property_pairs = re.split(r'<property>|</property>', xmltext.replace("<properties>","").replace("</properties>",""))
        result = ''
        for token in property_pairs:
            if token.find("<name>user</name") > 0:
                result += '<property>'
                if search_only:
                    result += '<property>' + token + '</property>'
            elif token.find("<name>") > 0:
                result += '<property>' + token + '</property>'
            else:
                result += token

        if result == '':
            result = xmltext
        else:
            result = '<properties>' + result + '</properties>'

        return result


class ProcessJdbcDriverParam(object):        
    def __init__(self, url_handler, properties_handler, password_handler):
        self.url_handler = url_handler
        self.properties_handler = properties_handler
        self.password_handler = password_handler

    def process(self, xml_text, result_tokens, search_only):
        xml_text = process_group('<url>', xml_text, self.url_handler, result_tokens, search_only)
        xml_text = process_group('<password-encrypted>', xml_text, self.password_handler, result_tokens, search_only)
        xml_text = process_group('<properties>', xml_text, self.properties_handler, result_tokens, search_only)
        return xml_text


def process_jdbc_appmodule_xml(xml_file, search_password_only=True):
    result_tokens = {'found_tokens': []}

    url_handler = GenericTagReplacement('<url>')
    password_handler = GenericTagReplacement('<password-encrypted>')
    oracle_params_ons_handler = GenericTagReplacement('<ons-wallet-password-encrypted>')

    properties_handler = ProcessProperties()
    jdbc_driver_param_handler = ProcessJdbcDriverParam(url_handler, properties_handler, password_handler)
    oracle_params_handler = OracleParamsTag(oracle_params_ons_handler)
    result = process_group('<jdbc-driver-params>', xml_file, jdbc_driver_param_handler, result_tokens,
                           search_password_only)
    result = process_group('<jdbc-oracle-params>', result, oracle_params_handler, result_tokens, search_password_only)
    return result, result_tokens

