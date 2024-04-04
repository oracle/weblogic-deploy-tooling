"""
Copyright (c) 2024, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""

from base_test import BaseTestCase
from wlsdeploy.aliases.aliases import Aliases
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.deploy import deployer_utils
from wlsdeploy.util.model import Model
from wlsdeploy.util.model_context import ModelContext


class ApplicationsDeployerTest(BaseTestCase):
    __class_name = 'ApplicationsDeployerTest'
    __logger = PlatformLogger('wlsdeploy.deploy')

    wls_version = '12.2.1.3'

    def __init__(self, *args):
        BaseTestCase.__init__(self, *args)

    def setUp(self):
        BaseTestCase.setUp(self)

    def tearDown(self):
        BaseTestCase.tearDown(self)

    def test_is_structured_app(self):
        """
        Test that _is_structured_app() returns correct values for different deployments.
        """
        # structured app in the archive
        self.check_is_structured_app('wlsdeploy/structuredApplications/myApp/app/my.war',
                                     'wlsdeploy/structuredApplications/myApp/plan/Plan.xml',
                                     True,
                                     'wlsdeploy/structuredApplications/myApp')

        # not structured: need a parent dir under structuredApplications/myApp
        self.check_is_structured_app('wlsdeploy/structuredApplications/my.war',
                                     'wlsdeploy/structuredApplications/Plan.xml',
                                     False, None)

        # not structured: archive location for non-structured apps
        self.check_is_structured_app('wlsdeploy/applications/myApp/app/my.war',
                                     'wlsdeploy/applications/myApp/plan/Plan.xml',
                                     False, None)

        # structured app using plan dir
        self.check_is_structured_app('wlsdeploy/structuredApplications/myApp/app/my.war',
                                     'plan/Plan.xml',
                                     True,
                                     'wlsdeploy/structuredApplications/myApp',
                                     plan_dir='wlsdeploy/structuredApplications/myApp')

        # structured app using plan dir
        self.check_is_structured_app('wlsdeploy/structuredApplications/myApp/app/my.war',
                                     'my_plan.xml',
                                     True,
                                     'wlsdeploy/structuredApplications/myApp',
                                     plan_dir='wlsdeploy/structuredApplications/myApp/plan4')

        # structured app using version dir
        self.check_is_structured_app('wlsdeploy/structuredApplications/myApp/1.0/app/my.war',
                                     'my_plan.xml',
                                     True,
                                     'wlsdeploy/structuredApplications/myApp',
                                     plan_dir='wlsdeploy/structuredApplications/myApp/1.0/plan4')

        # not structured: app in archive, plan dir outside archive
        self.check_is_structured_app('wlsdeploy/structuredApplications/myApp/app/my.war',
                                     'plan/Plan.xml',
                                     False,
                                     None,
                                     plan_dir='/myApp')

        # structured app outside archive
        self.check_is_structured_app('/home/myApp/app/my.war',
                                     '/home/myApp/plan/Plan.xml',
                                     True, '/home/myApp')

        # structured app outside archive with version dir
        self.check_is_structured_app('/home/myApp/1.0.1#1.0.1/app/my.war',
                                     '/home/myApp/1.0.1#1.0.1/plan/Plan.xml',
                                     True, '/home/myApp')

        # not structured: app outside archive no match
        self.check_is_structured_app('/home/myApp/app/my.war',
                                     '/home/myOtherApp/plan/Plan.xml',
                                     False, None)

        # structured app outside archive using plan dir
        self.check_is_structured_app('/home/myApp/app/my.war',
                                     'plan/Plan.xml',
                                     True,
                                     '/home/myApp',
                                     plan_dir='/home/myApp')

        # structured app outside archive using plan dir with version dir
        self.check_is_structured_app('/home/myApp/1.0-beta/app/my.war',
                                     'Plan.xml',
                                     True,
                                     '/home/myApp',
                                     plan_dir='/home/myApp/1.0-beta/plan1')

        # not structured: app outside archive, plan dir doesn't match
        self.check_is_structured_app('/home/myApp/1.0-beta/app/my.war',
                                     'Plan.xml',
                                     False, None,
                                     plan_dir='/home/myApp/plan')

        # not structured: app outside archive, plan dir doesn't match
        self.check_is_structured_app('/home/myApp/app/my.war',
                                     'plan/Plan.xml',
                                     False, None,
                                     plan_dir='/home/myOtherApp')

        # not structured: app outside archive no plan path or dir
        self.check_is_structured_app('/home/myApp/app/my.war',
                                     None, False, None)

    def check_is_structured_app(self, source_path, plan_path, expected_result, expected_install_root, plan_dir=None):
        """
        Check if the source path and plan path identify a structured application.
        :param source_path: the source path to check
        :param plan_path: the plan path to check
        :param expected_result: the expected result, True or False
        :param expected_install_root: the expected install root directory (or None).
        :param plan_dir: plan directory to check (optional)
        """
        app_dict = {
            'SourcePath': source_path,
            'PlanPath': plan_path,
            'PlanDir': plan_dir
        }

        model_dict = {
            'appDeployments': {
                'Application': {
                    'myApp': app_dict
                }
            }
        }

        model = Model(model_dict)
        model_context = ModelContext(self.__class_name, {'-archive_file': 'fake.zip'})
        aliases = Aliases(model_context=model_context, wlst_mode=WlstModes.OFFLINE, wls_version=self.wls_version)
        applications_deployer = deployer_utils.get_applications_deployer(model, model_context, aliases)

        result, structured_app_dir = applications_deployer._is_structured_app('dummy_app', app_dict)
        self.assertEqual(expected_result, result,
                         '_is_structured_app() should return %s for source path %s, plan path %s, and plan dir %s' % \
                         (expected_result, source_path, plan_path, plan_dir))
        self.assertEqual(expected_install_root, structured_app_dir,
                         '_is_structured_app() should return %s for source path %s, plan path %s, and plan dir %s' % \
                         (expected_install_root, source_path, plan_path, plan_dir))
