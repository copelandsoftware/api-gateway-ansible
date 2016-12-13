#!/usr/bin/python
# TODO: License goes here

import library.apigw_usage_plan as apigw_usage_plan
from library.apigw_usage_plan import ApiGwUsagePlan
import mock
from mock import patch
from mock import create_autospec
from mock import ANY
import unittest
import boto
from botocore.exceptions import BotoCoreError

class TestApiGwUsagePlan(unittest.TestCase):

  def setUp(self):
    self.module = mock.MagicMock()
    self.module.check_mode = False
    self.module.exit_json = mock.MagicMock()
    self.module.fail_json = mock.MagicMock()
    self.usage_plan  = ApiGwUsagePlan(self.module)
    self.usage_plan.client = mock.MagicMock()
    self.usage_plan.module.params = {
      'name': 'testify',
      'description': 'test_description',
      'value': 'test_value',
      'generate_distinct_id': False,
      'enabled': True,
      'state': 'present',
    }
    reload(apigw_usage_plan)

  def test_boto_module_not_found(self):
    # Setup Mock Import Function
    import __builtin__ as builtins
    real_import = builtins.__import__

    def mock_import(name, *args):
      if name == 'boto': raise ImportError
      return real_import(name, *args)

    with mock.patch('__builtin__.__import__', side_effect=mock_import):
      reload(apigw_usage_plan)
      ApiGwUsagePlan(self.module)

    self.module.fail_json.assert_called_with(msg='boto and boto3 are required for this module')

  def test_boto3_module_not_found(self):
    # Setup Mock Import Function
    import __builtin__ as builtins
    real_import = builtins.__import__

    def mock_import(name, *args):
      if name == 'boto3': raise ImportError
      return real_import(name, *args)

    with mock.patch('__builtin__.__import__', side_effect=mock_import):
      reload(apigw_usage_plan)
      ApiGwUsagePlan(self.module)

    self.module.fail_json.assert_called_with(msg='boto and boto3 are required for this module')

  @patch.object(apigw_usage_plan, 'boto3')
  def test_boto3_client_properly_instantiated(self, mock_boto):
    ApiGwUsagePlan(self.module)
    mock_boto.client.assert_called_once_with('apigateway')

  def test_define_argument_spec(self):
    result = ApiGwUsagePlan._define_module_argument_spec()
    self.assertIsInstance(result, dict)
    self.assertEqual(result, dict(
                     name=dict(required=True),
                     description=dict(required=False),
                     api_stages=dict(
                       type='list',
                       required=False,
                       default=[],
                       rest_api_id=dict(required=True),
                       stage=dict(required=True)
                     ),
                     throttle_burst_limit=dict(required=False, default=-1, type='int'),
                     throttle_rate_limit=dict(required=False, default=-1.0, type='float'),
                     quota_limit=dict(required=False, default=-1, type='int'),
                     quota_offset=dict(required=False, default=-1, type='int'),
                     quota_period=dict(required=False, default='', choices=['', 'DAY','WEEK','MONTH']),
                     state=dict(default='present', choices=['present', 'absent']),
    ))

  @patch.object(apigw_usage_plan, 'AnsibleModule')
  @patch.object(apigw_usage_plan, 'ApiGwUsagePlan')
  def test_main(self, mock_ApiGwUsagePlan, mock_AnsibleModule):
    mock_ApiGwUsagePlan_instance      = mock.MagicMock()
    mock_AnsibleModule_instance     = mock.MagicMock()
    mock_ApiGwUsagePlan.return_value  = mock_ApiGwUsagePlan_instance
    mock_AnsibleModule.return_value = mock_AnsibleModule_instance

    apigw_usage_plan.main()

    mock_ApiGwUsagePlan.assert_called_once_with(mock_AnsibleModule_instance)
    assert mock_ApiGwUsagePlan_instance.process_request.call_count == 1


if __name__ == '__main__':
    unittest.main()

