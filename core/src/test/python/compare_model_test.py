"""
Copyright (c) 2020, 2022 Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import unittest

import os
import shutil
import tempfile
from java.util.logging import Level
from oracle.weblogic.deploy.compare import CompareException
from oracle.weblogic.deploy.logging import SummaryHandler
from oracle.weblogic.deploy.logging import WLSDeployLogEndHandler
from oracle.weblogic.deploy.util import PyWLSTException

from compare_model import ModelFileDiffer
from wlsdeploy.aliases.model_constants import APPLICATION
from wlsdeploy.aliases.model_constants import APP_DEPLOYMENTS
from wlsdeploy.aliases.model_constants import LIBRARY
from wlsdeploy.aliases.model_constants import MAX_THREADS_CONSTRAINT
from wlsdeploy.aliases.model_constants import MIN_THREADS_CONSTRAINT
from wlsdeploy.aliases.model_constants import RESOURCES
from wlsdeploy.aliases.model_constants import SELF_TUNING
from wlsdeploy.aliases.model_constants import SOURCE_PATH
from wlsdeploy.aliases.model_constants import TOPOLOGY
from wlsdeploy.aliases.model_constants import WORK_MANAGER
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.util import dictionary_utils
from wlsdeploy.util import model_helper
from wlsdeploy.util.model_context import ModelContext
from wlsdeploy.util.model_translator import FileToPython


class CompareModelTestCase(unittest.TestCase):
    _resources_dir = '../../test-classes'
    _tests_dir = '../../unit-tests'
    _results_dir = _tests_dir + '/compare'
    _use_ordering = True

    def setUp(self):
        self.name = 'CompareModelTestCase'
        self._logger = PlatformLogger('wlsdeploy.compare_model')
        self._program_name = 'CompareModelTestCase'

        if not os.path.isdir(self._tests_dir):
            os.mkdir(self._tests_dir)

        if not os.path.isdir(self._results_dir):
            os.mkdir(self._results_dir)

        # add summary handler to validate logger to check results
        self._summary_handler = SummaryHandler()
        self._validate_logger = PlatformLogger('wlsdeploy.validate')
        self._validate_logger.logger.addHandler(self._summary_handler)

    def tearDown(self):
        # remove summary handler for next test suite
        PlatformLogger('wlsdeploy.validate').logger.removeHandler(self._summary_handler)
        WLSDeployLogEndHandler.clearHandlers()

    def testLogHandlerConfiguration(self):
        _method_name = 'testLogHandlerConfiguration'

        self.assertNotEqual(self._summary_handler, None, 'self._summary_handler was None')
        handlers = self._validate_logger.logger.getHandlers()
        self.assertNotEqual(handlers, None, 'getHandlers() returned None')
        self.assertNotEqual(len(handlers), 0, 'getHandlers() returned an empty list')

        found_summary_handler = False
        for handler in handlers:
            if handler.getClass().getName() == "oracle.weblogic.deploy.logging.SummaryHandler":
                found_summary_handler = True
                break
        self.assertEquals(found_summary_handler, True, "Failed to find summary handler")

        handlers = WLSDeployLogEndHandler.getEndHandlers()
        self.assertNotEqual(handlers, None, 'getEndHandlers() returned None')
        self.assertNotEqual(len(handlers), 0, 'getEndHandlers() returned an empty list')
        self.assertEqual(len(handlers), 1, 'getEndHandlers() returned a list with ' + str(len(handlers)) + ' handlers')

    def testCompareModelFull(self):
        _method_name = 'testCompareModelFull'

        _variables_file = self._resources_dir + '/compare_model_model1.10.properties'
        _new_model_file = self._resources_dir + '/compare_model_model2.yaml'
        _old_model_file = self._resources_dir + '/compare_model_model1.yaml'
        _temp_dir = os.path.join(tempfile.gettempdir(), _method_name)

        if os.path.exists(_temp_dir):
            shutil.rmtree(_temp_dir)

        os.mkdir(_temp_dir)

        mw_home = os.environ['MW_HOME']
        args_map = {
            '-oracle_home': mw_home,
            '-variable_file': _variables_file,
            '-output_dir' : _temp_dir,
            '-domain_type' : 'WLS',
            '-trailing_arguments': [ _new_model_file, _old_model_file ]
        }

        try:
            model_context = ModelContext('CompareModelTestCase', args_map)
            obj = ModelFileDiffer(_new_model_file, _old_model_file, model_context, _temp_dir)
            return_code = obj.compare()
            self.assertEqual(return_code, 0)

            yaml_result = _temp_dir + os.sep + 'diffed_model.yaml'
            json_result = _temp_dir + os.sep + 'diffed_model.json'
            stdout_result = obj.get_compare_msgs()
            model_dictionary = FileToPython(yaml_result).parse()
            yaml_exists = os.path.exists(yaml_result)
            json_exists = os.path.exists(json_result)

            self.assertEqual(yaml_exists, True)
            self.assertEqual(json_exists, True)
            self.assertEqual(len(stdout_result), 14)

            self.assertEqual(model_dictionary.has_key('resources'), True)
            self.assertEqual(model_dictionary.has_key('topology'), True)
            self.assertEqual(model_dictionary.has_key('appDeployments'), True)
            self.assertEqual(model_dictionary['topology'].has_key('ServerTemplate'), True)
            self.assertEqual(model_dictionary['topology'].has_key('Cluster'), True)
            self.assertEqual(model_dictionary['topology']['ServerTemplate'].has_key('cluster-1-template'), True)
            self.assertEqual(model_dictionary['topology']['Cluster'].has_key('cluster-2'), True)
            self.assertEqual(model_dictionary['appDeployments'].has_key('Library'), True)
            self.assertEqual(model_dictionary['appDeployments'].has_key('Application'), True)
            self.assertEqual(model_dictionary['appDeployments']['Application'].has_key('myear'), True)
            self.assertEqual(model_dictionary['resources'].has_key('JMSSystemResource'), True)
            self.assertEqual(model_dictionary['resources']['JMSSystemResource'].has_key('MyJmsModule'), True)
            self.assertEqual(model_dictionary['resources'].has_key('SingletonService'), True)
            self.assertEqual(model_dictionary['appDeployments']['Library'].has_key('!jax-rs#2.0@2.22.4.0'), True)
            self.assertEqual(model_dictionary['appDeployments']['Library'].has_key('!jsf#1.2@1.2.9.0'), True)
            self.assertEqual(model_dictionary['appDeployments']['Application']['myear'].has_key('ModuleType'), True)

        except (CompareException, PyWLSTException), te:
            return_code = 2
            self._logger.severe('WLSDPLY-05709',
                                te.getLocalizedMessage(), error=te,
                                class_name=self._program_name, method_name=_method_name)

        if os.path.exists(_temp_dir):
            shutil.rmtree(_temp_dir)

        self.assertEqual(return_code, 0)

    def testCompareModelSecurityConfigurationAttribute(self):
        _method_name = 'testCompareModelSecurityConfigurationAttribute'

        _new_model_file = self._resources_dir + '/compare/model-sc1-new.yaml'
        _old_model_file = self._resources_dir + '/compare/model-sc1-old.yaml'
        _temp_dir = os.path.join(tempfile.gettempdir(), _method_name)

        if os.path.exists(_temp_dir):
            shutil.rmtree(_temp_dir)

        os.mkdir(_temp_dir)

        mw_home = os.environ['MW_HOME']
        args_map = {
            '-oracle_home': mw_home,
            '-output_dir' : _temp_dir,
            '-domain_type' : 'WLS',
            '-trailing_arguments': [ _new_model_file, _old_model_file ]
        }

        try:
            model_context = ModelContext('CompareModelTestCase', args_map)
            obj = ModelFileDiffer(_new_model_file, _old_model_file, model_context, _temp_dir)
            return_code = obj.compare()
            self.assertEqual(return_code, 0)

            yaml_result = _temp_dir + os.sep + 'diffed_model.yaml'
            json_result = _temp_dir + os.sep + 'diffed_model.json'
            stdout_result = obj.get_compare_msgs()
            model_dictionary = FileToPython(yaml_result).parse()
            self.assertEqual(model_dictionary.has_key('topology'), True)
            self.assertEqual(model_dictionary['topology'].has_key('SecurityConfiguration'), True)
            self.assertEqual(model_dictionary['topology']['SecurityConfiguration'].has_key('Realm'), True)
            self.assertEqual(model_dictionary['topology']['SecurityConfiguration']['Realm'].has_key('myrealm'), True)
            self.assertEqual(model_dictionary['topology']['SecurityConfiguration']['Realm']['myrealm'].has_key('Auditor'), False)
            self.assertEqual(model_dictionary['topology']['SecurityConfiguration']['Realm']['myrealm'].has_key('AuthenticationProvider'), True)
            self.assertEqual(model_dictionary['topology']['SecurityConfiguration']['Realm']['myrealm'].has_key('PasswordValidator'), False)

        except (CompareException, PyWLSTException), te:
            return_code = 2
            self._logger.severe('WLSDPLY-05709',
                                te.getLocalizedMessage(), error=te,
                                class_name=self._program_name, method_name=_method_name)

        if os.path.exists(_temp_dir):
            shutil.rmtree(_temp_dir)

        self.assertEqual(return_code, 0)

    def testCompareModelSecurityConfigurationCustomList(self):
        _method_name = 'testCompareModelSecurityConfigurationCustomList'

        _new_model_file = self._resources_dir + '/compare/model-sc2-new.yaml'
        _old_model_file = self._resources_dir + '/compare/model-sc2-old.yaml'
        _temp_dir = os.path.join(tempfile.gettempdir(), _method_name)

        if os.path.exists(_temp_dir):
            shutil.rmtree(_temp_dir)

        os.mkdir(_temp_dir)

        mw_home = os.environ['MW_HOME']
        args_map = {
            '-oracle_home': mw_home,
            '-output_dir' : _temp_dir,
            '-domain_type' : 'WLS',
            '-trailing_arguments': [ _new_model_file, _old_model_file ]
        }

        try:
            model_context = ModelContext('CompareModelTestCase', args_map)
            obj = ModelFileDiffer(_new_model_file, _old_model_file, model_context, _temp_dir)
            return_code = obj.compare()
            self.assertEqual(return_code, 0)

            yaml_result = _temp_dir + os.sep + 'diffed_model.yaml'
            json_result = _temp_dir + os.sep + 'diffed_model.json'
            stdout_result = obj.get_compare_msgs()
            model_dictionary = FileToPython(yaml_result).parse()
            self.assertEqual(model_dictionary.has_key('topology'), True)
            self.assertEqual(model_dictionary['topology'].has_key('SecurityConfiguration'), True)
            self.assertEqual(model_dictionary['topology']['SecurityConfiguration'].has_key('Realm'), True)
            self.assertEqual(model_dictionary['topology']['SecurityConfiguration']['Realm'].has_key('myrealm'), True)
            self.assertEqual(model_dictionary['topology']['SecurityConfiguration']['Realm']['myrealm'].has_key('Auditor'), False)
            self.assertEqual(model_dictionary['topology']['SecurityConfiguration']['Realm']['myrealm'].has_key('AuthenticationProvider'), True)
            self.assertEqual(model_dictionary['topology']['SecurityConfiguration']['Realm']['myrealm'].has_key('PasswordValidator'), True)
        except (CompareException, PyWLSTException), te:
            return_code = 2
            self._logger.severe('WLSDPLY-05709',
                                te.getLocalizedMessage(), error=te,
                                class_name=self._program_name, method_name=_method_name)

        if os.path.exists(_temp_dir):
            shutil.rmtree(_temp_dir)

        self.assertEqual(return_code, 0)

    def testCompareModelInvalidModel(self):
        _method_name = 'testCompareModelInvalidModel'

        _variables_file = self._resources_dir + '/compare_model_model1.10.properties'
        _new_model_file = self._resources_dir + '/compare_model_model3.yaml'
        _old_model_file = self._resources_dir + '/compare_model_model1.yaml'
        _temp_dir = os.path.join(tempfile.gettempdir(), _method_name)

        if os.path.exists(_temp_dir):
            shutil.rmtree(_temp_dir)
        os.mkdir(_temp_dir)


        mw_home = os.environ['MW_HOME']
        args_map = {
            '-oracle_home': mw_home,
            '-variable_file': _variables_file,
            '-output_dir' : _temp_dir,
            '-domain_type' : 'WLS',
            '-trailing_arguments': [ _new_model_file, _old_model_file ]
        }
        try:
            model_context = ModelContext('CompareModelTestCase', args_map)
            obj = ModelFileDiffer(_new_model_file, _old_model_file, model_context, _temp_dir)
            return_code = obj.compare()
        except (CompareException, PyWLSTException), te:
            return_code = 2
            # self._logger.severe('WLSDPLY-05709', te.getLocalizedMessage(), error=te,
            #                     class_name=self._program_name, method_name=_method_name)

        if os.path.exists(_temp_dir):
            shutil.rmtree(_temp_dir)

        self.assertNotEqual(return_code, 0)

    def testCompareModelInvalidFile(self):
        _method_name = 'testCompareModelInvalidFile'

        _variables_file = self._resources_dir + '/compare_model_model1.10.properties'
        _new_model_file = self._resources_dir + '/compare_model_model4.yaml'
        _old_model_file = self._resources_dir + '/compare_model_model1.yaml'
        _temp_dir = os.path.join(tempfile.gettempdir(), _method_name)

        if os.path.exists(_temp_dir):
            shutil.rmtree(_temp_dir)
        os.mkdir(_temp_dir)

        mw_home = os.environ['MW_HOME']
        args_map = {
            '-oracle_home': mw_home,
            '-variable_file': _variables_file,
            '-output_dir' : _temp_dir,
            '-domain_type' : 'WLS',
            '-trailing_arguments': [ _new_model_file, _old_model_file ]
        }

        try:
            model_context = ModelContext('CompareModelTestCase', args_map)
            obj = ModelFileDiffer(_new_model_file, _old_model_file, model_context, _temp_dir)

            # expected parse error for model4, disable logging
            yaml_logger = PlatformLogger('wlsdeploy.yaml')
            yaml_level = yaml_logger.get_level()
            yaml_logger.set_level(Level.OFF)

            compare_logger = PlatformLogger('wlsdeploy.compare_model')
            compare_level = compare_logger.get_level()
            compare_logger.set_level(Level.OFF)

            return_code = obj.compare()

            # Restore original log levels
            yaml_logger.set_level(yaml_level)
            compare_logger.set_level(compare_level)

        except (CompareException, PyWLSTException), te:
            return_code = 2
            # self._logger.severe('WLSDPLY-05709', te.getLocalizedMessage(), error=te,
            #                     class_name=self._program_name, method_name=_method_name)

        if os.path.exists(_temp_dir):
            shutil.rmtree(_temp_dir)

        self.assertNotEqual(return_code, 0)

    def testDeleteModelAppDeployments(self):
        _method_name = 'testDeleteModelAppDeployments'

        _variables_file = self._resources_dir + '/compare_model_model1.10.properties'
        _new_model_file = self._resources_dir + '/compare_model_model5.yaml'
        _old_model_file = self._resources_dir + '/compare_model_model1.yaml'
        _temp_dir = os.path.join(tempfile.gettempdir(), _method_name)

        if os.path.exists(_temp_dir):
            shutil.rmtree(_temp_dir)

        os.mkdir(_temp_dir)

        mw_home = os.environ['MW_HOME']
        args_map = {
            '-oracle_home': mw_home,
            '-variable_file': _variables_file,
            '-output_dir' : _temp_dir,
            '-domain_type' : 'WLS',
            '-trailing_arguments': [ _new_model_file, _old_model_file ]
        }

        try:
            model_context = ModelContext('CompareModelTestCase', args_map)
            obj = ModelFileDiffer(_new_model_file, _old_model_file, model_context, _temp_dir)
            return_code = obj.compare()
            self.assertEqual(return_code, 0)

            yaml_result = _temp_dir + os.sep + 'diffed_model.yaml'
            stdout_result = obj.get_compare_msgs()
            model_dictionary = FileToPython(yaml_result).parse()
            yaml_exists = os.path.exists(yaml_result)

            self.assertEqual(yaml_exists, True)
            self.assertEqual(len(stdout_result), 0)

            self.assertEqual(model_dictionary.has_key('appDeployments'), True)
            self.assertEqual(model_dictionary['appDeployments'].has_key('Library'), True)
            self.assertEqual(model_dictionary['appDeployments'].has_key('Application'), True)
            self.assertEqual(model_dictionary['appDeployments']['Application'].has_key('!myear'), True)
            self.assertEqual(model_dictionary['appDeployments']['Library'].has_key('!jax-rs#2.0@2.22.4.0'), True)
            self.assertEqual(model_dictionary['appDeployments']['Library'].has_key('!jsf#1.2@1.2.9.0'), True)

        except (CompareException, PyWLSTException), te:
            return_code = 2
            self._logger.severe('WLSDPLY-05709',
                                te.getLocalizedMessage(), error=te,
                                class_name=self._program_name, method_name=_method_name)

        if os.path.exists(_temp_dir):
            shutil.rmtree(_temp_dir)

        self.assertEqual(return_code, 0)

    def testCompareModelFull2(self):
        _method_name = 'testCompareModelFull2'
        # This test for
        # 1. Changing weblogic password
        # 2. Changing RCU password
        # 3. Deleting an application

        _variables_file = self._resources_dir + '/compare_model_model1.10.properties'
        _new_model_file = self._resources_dir + '/compare_model_model7.yaml'
        _old_model_file = self._resources_dir + '/compare_model_model6.yaml'
        _temp_dir = os.path.join(tempfile.gettempdir(), _method_name)

        if os.path.exists(_temp_dir):
            shutil.rmtree(_temp_dir)

        os.mkdir(_temp_dir)

        mw_home = os.environ['MW_HOME']
        args_map = {
            '-oracle_home': mw_home,
            '-variable_file': _variables_file,
            '-output_dir' : _temp_dir,
            '-domain_type' : 'WLS',
            '-trailing_arguments': [ _new_model_file, _old_model_file ]
        }

        try:
            model_context = ModelContext('CompareModelTestCase', args_map)
            obj = ModelFileDiffer(_new_model_file, _old_model_file, model_context, _temp_dir)
            return_code = obj.compare()
            self.assertEqual(return_code, 0)

            yaml_result = _temp_dir + os.sep + 'diffed_model.yaml'
            json_result = _temp_dir + os.sep + 'diffed_model.json'
            stdout_result = obj.get_compare_msgs()
            model_dictionary = FileToPython(yaml_result).parse()
            yaml_exists = os.path.exists(yaml_result)
            json_exists = os.path.exists(json_result)

            self.assertEqual(yaml_exists, True)
            self.assertEqual(json_exists, True)
            self.assertEqual(len(stdout_result), 0)

            self.assertEqual(model_dictionary.has_key('domainInfo'), True)
            self.assertEqual(model_dictionary['domainInfo'].has_key('AdminPassword'), True)
            self.assertEqual(model_dictionary['domainInfo']['AdminPassword'], 'welcome2')
            self.assertEqual(model_dictionary['domainInfo'].has_key('AdminUser'), False)
            self.assertEqual(model_dictionary['domainInfo'].has_key('RCUDbInfo'), True)
            self.assertEqual(model_dictionary['domainInfo']['RCUDbInfo'].has_key('rcu_admin_password'), True)
            self.assertEqual(len(model_dictionary['domainInfo']['RCUDbInfo']), 1)
            self.assertEqual(len(model_dictionary['domainInfo']), 2)
            self.assertEqual(model_dictionary.has_key('appDeployments'), True)
            self.assertEqual(model_dictionary['appDeployments'].has_key('Application'), True)
            self.assertEqual(model_dictionary['appDeployments']['Application'].has_key('!yourear'), True)
            self.assertEqual(len(model_dictionary['appDeployments']['Application']), 1)


        except (CompareException, PyWLSTException), te:
            return_code = 2
            self._logger.severe('WLSDPLY-05709',
                                te.getLocalizedMessage(), error=te,
                                class_name=self._program_name, method_name=_method_name)

        if os.path.exists(_temp_dir):
            shutil.rmtree(_temp_dir)

        self.assertEqual(return_code, 0)

    def testCompareModelFull3(self):
        _method_name = 'testCompareModelFull3'
        # This test for
        # 1. Changing MailSessionProperty
        # 2. Changing ODL HandlerDefaults
        # 3. Changing ODL Handler property
        # 4. Changing ODL Logger attributes

        _variables_file = self._resources_dir + '/compare_model_model1.10.properties'
        _new_model_file = self._resources_dir + '/compare_model_model8.yaml'
        _old_model_file = self._resources_dir + '/compare_model_model7.yaml'
        _temp_dir = os.path.join(tempfile.gettempdir(), _method_name)

        if os.path.exists(_temp_dir):
            shutil.rmtree(_temp_dir)

        os.mkdir(_temp_dir)

        mw_home = os.environ['MW_HOME']
        args_map = {
            '-oracle_home': mw_home,
            '-variable_file': _variables_file,
            '-output_dir' : _temp_dir,
            '-domain_type' : 'WLS',
            '-trailing_arguments': [ _new_model_file, _old_model_file ]
        }

        try:
            model_context = ModelContext('CompareModelTestCase', args_map)
            obj = ModelFileDiffer(_new_model_file, _old_model_file, model_context, _temp_dir)
            return_code = obj.compare()
            self.assertEqual(return_code, 0)

            yaml_result = _temp_dir + os.sep + 'diffed_model.yaml'
            json_result = _temp_dir + os.sep + 'diffed_model.json'
            stdout_result = obj.get_compare_msgs()
            model_dictionary = FileToPython(yaml_result).parse()
            yaml_exists = os.path.exists(yaml_result)
            json_exists = os.path.exists(json_result)

            self.assertEqual(yaml_exists, True)
            self.assertEqual(json_exists, True)
            self.assertEqual(len(stdout_result), 0)

            self.assertEqual(model_dictionary.has_key('resources'), True)
            self.assertEqual(model_dictionary['resources'].has_key('MailSession'), True)
            self.assertEqual(model_dictionary['resources']['MailSession'].has_key('MyMailSession'), True)

            mail_session = model_dictionary['resources']['MailSession']['MyMailSession']
            self.assertEqual(mail_session.has_key('Properties'), True)
            self.assertEqual(mail_session['Properties'].has_key('mail.imap.port'), True)
            self.assertEqual(mail_session['Properties']['mail.imap.port'], 993)

            self.assertEqual(model_dictionary['resources'].has_key('ODLConfiguration'), True)
            self.assertEqual(model_dictionary['resources']['ODLConfiguration'].has_key('config'), True)
            self.assertEqual(model_dictionary['resources']['ODLConfiguration']['config'].has_key('HandlerDefaults'),
                             True)
            self.assertEqual(
                model_dictionary['resources']['ODLConfiguration']['config']['HandlerDefaults'].has_key('maxFileSize'),
                             True)
            self.assertEqual(
                model_dictionary['resources']['ODLConfiguration']['config']['HandlerDefaults']['maxFileSize'],
                14857620)

            self.assertEqual(model_dictionary['resources']['ODLConfiguration']['config'].has_key('Handler'),
                             True)
            self.assertEqual(
                model_dictionary['resources']['ODLConfiguration']['config']['Handler'].has_key('odl-handler'),
                True)
            self.assertEqual(
                model_dictionary['resources']['ODLConfiguration']['config']['Handler']['odl-handler']
                    .has_key('Properties'), True)
            self.assertEqual(
                model_dictionary['resources']['ODLConfiguration']['config']['Handler']['odl-handler']['Properties']
                .has_key('maxFileSize'), True)
            self.assertEqual(
                model_dictionary['resources']['ODLConfiguration']['config']['Handler']['odl-handler']
                ['Properties']['maxFileSize'], '14857620')


            self.assertEqual(model_dictionary['resources']['ODLConfiguration']['config'].has_key('Logger'),
                             True)
            self.assertEqual(
                model_dictionary['resources']['ODLConfiguration']['config']['Logger']
                    .has_key('oracle.communications.ordermanagement.automation.plugin.AutomationPluginManager'),
                    True)
            self.assertEqual(
                model_dictionary['resources']['ODLConfiguration']['config']['Logger']
                ['oracle.communications.ordermanagement.automation.plugin.AutomationPluginManager']
                    .has_key('Level'), True)
            self.assertEqual(
                model_dictionary['resources']['ODLConfiguration']['config']['Logger']
                ['oracle.communications.ordermanagement.automation.plugin.AutomationPluginManager']['Level'],
                'TRACE:16')
            self.assertEqual(
                len(model_dictionary['resources']['ODLConfiguration']['config']), 3)

            self.assertEqual(
                len(model_dictionary['resources']['ODLConfiguration']['config']['Logger']), 1)

            self.assertEqual(
                len(model_dictionary['resources']['ODLConfiguration']['config']['HandlerDefaults']), 1)

        except (CompareException, PyWLSTException), te:
            return_code = 2
            self._logger.severe('WLSDPLY-05709',
                                te.getLocalizedMessage(), error=te,
                                class_name=self._program_name, method_name=_method_name)

        if os.path.exists(_temp_dir):
            shutil.rmtree(_temp_dir)

        self.assertEqual(return_code, 0)

    def testCompareModel4(self):
        _method_name = 'testCompareModel4'

        _models_dir = self._resources_dir + '/compare'
        _new_model_file = _models_dir + '/model-4-new.yaml'
        _old_model_file = _models_dir + '/model-4-old.yaml'

        _output_dir = os.path.join(self._results_dir, 'model-4')
        if not os.path.isdir(_output_dir):
            os.mkdir(_output_dir)

        args_map = {
            '-oracle_home': '/oracle',
            '-output_dir': _output_dir,
            '-trailing_arguments': [_new_model_file, _old_model_file]
        }

        try:
            model_context = ModelContext('CompareModelTestCase', args_map)
            differ = ModelFileDiffer(_new_model_file, _old_model_file, model_context, _output_dir)
            return_code = differ.compare()
            self.assertEqual(return_code, 0)

            yaml_result = _output_dir + os.sep + 'diffed_model.yaml'
            self.assertEqual(os.path.exists(yaml_result), True, "YAML result should exist: " + yaml_result)

            json_result = _output_dir + os.sep + 'diffed_model.json'
            self.assertEqual(os.path.exists(json_result), True, "JSON result should exist: " + json_result)

            # see comments in the model for erased attributes
            messages = differ.get_compare_msgs()
            self.assertEqual(len(messages), 2)

            model_root = FileToPython(yaml_result).parse()

            # topology section not present, since no Server differences
            topology = dictionary_utils.get_element(model_root, TOPOLOGY)
            self.assertEqual(topology, None, "topology should not be present")

            resources = dictionary_utils.get_dictionary_element(model_root, RESOURCES)

            # the SelfTuning should contain delete keys for nested, named folders
            self_tuning = dictionary_utils.get_dictionary_element(resources, SELF_TUNING)

            work_manager = dictionary_utils.get_dictionary_element(self_tuning, WORK_MANAGER)
            delete_name = model_helper.get_delete_name('newWM')
            self.assertEqual(delete_name in work_manager, True, WORK_MANAGER + ' should contain ' + delete_name)

            min_constraint = dictionary_utils.get_dictionary_element(self_tuning, MIN_THREADS_CONSTRAINT)
            delete_name = model_helper.get_delete_name('SampleMinThreads')
            self.assertEqual(delete_name in min_constraint, True,
                             MIN_THREADS_CONSTRAINT + ' should contain ' + delete_name)

            max_constraint = dictionary_utils.get_dictionary_element(self_tuning, MAX_THREADS_CONSTRAINT)
            delete_name = model_helper.get_delete_name('SampleMaxThreads')
            self.assertEqual(delete_name in max_constraint, True,
                             MAX_THREADS_CONSTRAINT + ' should contain ' + delete_name)

            deployments = dictionary_utils.get_dictionary_element(model_root, APP_DEPLOYMENTS)

            libraries = dictionary_utils.get_dictionary_element(deployments, LIBRARY)
            # mylib should not appear in change model, it had no changes
            self.assertEqual(len(libraries), 1, "only one entry should be present in " + LIBRARY)
            # retarget should have a source path in change model, even though only targeting changed
            retarget = dictionary_utils.get_dictionary_element(libraries, 'retarget')
            self.assertEqual(SOURCE_PATH in retarget, True, LIBRARY + ' retarget should  contain ' + SOURCE_PATH)

            applications = dictionary_utils.get_dictionary_element(deployments, APPLICATION)
            # myapp should not appear in change model, it had no changes
            self.assertEqual(len(applications), 1, "only one entry should be present in " + APPLICATION)
            # retarget should have a source path in change model, even though only targeting changed
            retarget = dictionary_utils.get_dictionary_element(applications, 'retarget')
            self.assertEqual(SOURCE_PATH in retarget, True, APPLICATION + ' retarget should  contain ' + SOURCE_PATH)

        except (CompareException, PyWLSTException), te:
            return_code = 2
            self._logger.severe('WLSDPLY-05709', te.getLocalizedMessage(), error=te,
                                class_name=self._program_name, method_name=_method_name)

        self.assertEqual(return_code, 0)

    # This test is to ensure any behavior change does not impact WKO
    def testCompareModel5(self):
        _method_name = 'testCompareModel5'

        _models_dir = self._resources_dir + '/compare'
        _new_model_file = _models_dir + '/model-4-new.yaml'
        _old_model_file = _models_dir + '/model-4-new.yaml'

        _output_dir = os.path.join(self._results_dir, 'model-5')
        if not os.path.isdir(_output_dir):
            os.mkdir(_output_dir)

        args_map = {
            '-oracle_home': '/oracle',
            '-output_dir': _output_dir,
            '-trailing_arguments': [_new_model_file, _old_model_file]
        }

        try:
            model_context = ModelContext('CompareModelTestCase', args_map)
            differ = ModelFileDiffer(_new_model_file, _old_model_file, model_context, _output_dir)
            return_code = differ.compare()
            self.assertEqual(return_code, 0)

            yaml_result = _output_dir + os.sep + 'diffed_model.yaml'
            self.assertEqual(os.path.exists(yaml_result), False, "YAML result should not exist: " + yaml_result)

            json_result = _output_dir + os.sep + 'diffed_model.json'
            self.assertEqual(os.path.exists(json_result), False, "JSON result should not exist: " + json_result)

            json_result = _output_dir + os.sep + 'compare_model_stdout'
            self.assertEqual(os.path.exists(json_result), False, "compare_model.stdout result should not exist: " +
                             json_result)

        except (CompareException, PyWLSTException), te:
            return_code = 2
            self._logger.severe('WLSDPLY-05709', te.getLocalizedMessage(), error=te,
                                class_name=self._program_name, method_name=_method_name)

        self.assertEqual(return_code, 0)


if __name__ == '__main__':
    unittest.main()
