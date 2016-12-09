#!/usr/bin/python
# TODO: License goes here

import library.apigw_api_key as apigw_api_key
from library.apigw_api_key import ApiGwApiKey
import mock
from mock import patch
from mock import create_autospec
from mock import ANY
import unittest
import boto
from botocore.exceptions import BotoCoreError

class TestApiGwApiKey(unittest.TestCase):

  def setUp(self):
    self.module = mock.MagicMock()
    self.module.check_mode = False
    self.module.exit_json = mock.MagicMock()
    self.module.fail_json = mock.MagicMock()
    self.api_key  = ApiGwApiKey(self.module)
    self.api_key.client = mock.MagicMock()
    self.api_key.module.params = {
      'name': 'testify',
      'rest_api_id': 'rest_id',
      'base_path': 'test_base_path',
      'stage': 'test_stage',
      'state': 'present',
    }
    reload(apigw_api_key)

  def test_boto_module_not_found(self):
    # Setup Mock Import Function
    import __builtin__ as builtins
    real_import = builtins.__import__

    def mock_import(name, *args):
      if name == 'boto': raise ImportError
      return real_import(name, *args)

    with mock.patch('__builtin__.__import__', side_effect=mock_import):
      reload(apigw_api_key)
      ApiGwApiKey(self.module)

    self.module.fail_json.assert_called_with(msg='boto and boto3 are required for this module')

  def test_boto3_module_not_found(self):
    # Setup Mock Import Function
    import __builtin__ as builtins
    real_import = builtins.__import__

    def mock_import(name, *args):
      if name == 'boto3': raise ImportError
      return real_import(name, *args)

    with mock.patch('__builtin__.__import__', side_effect=mock_import):
      reload(apigw_api_key)
      ApiGwApiKey(self.module)

    self.module.fail_json.assert_called_with(msg='boto and boto3 are required for this module')

  @patch.object(apigw_api_key, 'boto3')
  def test_boto3_client_properly_instantiated(self, mock_boto):
    ApiGwApiKey(self.module)
    mock_boto.client.assert_called_once_with('apigateway')

  def test_define_argument_spec(self):
    result = ApiGwApiKey._define_module_argument_spec()
    self.assertIsInstance(result, dict)
    self.assertEqual(result, dict(
                     name=dict(required=True),
                     description=dict(required=False),
                     value=dict(required=False),
                     customer_id=dict(required=False),
                     enabled=dict(required=False, type='bool', default=False),
                     generate_distinct_id=dict(required=False, type='bool', default=False),
                     state=dict(default='present', choices=['present', 'absent']),
    ))

  @patch.object(apigw_api_key, 'AnsibleModule')
  @patch.object(apigw_api_key, 'ApiGwApiKey')
  def test_main(self, mock_ApiGwApiKey, mock_AnsibleModule):
    mock_ApiGwApiKey_instance      = mock.MagicMock()
    mock_AnsibleModule_instance     = mock.MagicMock()
    mock_ApiGwApiKey.return_value  = mock_ApiGwApiKey_instance
    mock_AnsibleModule.return_value = mock_AnsibleModule_instance

    apigw_api_key.main()

    mock_ApiGwApiKey.assert_called_once_with(mock_AnsibleModule_instance)
    assert mock_ApiGwApiKey_instance.process_request.call_count == 1


if __name__ == '__main__':
    unittest.main()

