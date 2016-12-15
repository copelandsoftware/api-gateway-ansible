#!/usr/bin/python
# TODO: License goes here

import library.apigw_usage_plan_key as apigw_usage_plan_key
from library.apigw_usage_plan_key import ApiGwUsagePlanKey
import mock
from mock import patch
from mock import create_autospec
from mock import ANY
import unittest
import boto
from botocore.exceptions import BotoCoreError

class TestApiGwUsagePlanKey(unittest.TestCase):

  def setUp(self):
    self.module = mock.MagicMock()
    self.module.check_mode = False
    self.module.exit_json = mock.MagicMock()
    self.module.fail_json = mock.MagicMock()
    self.usage_plan_key  = ApiGwUsagePlanKey(self.module)
    self.usage_plan_key.client = mock.MagicMock()
    self.usage_plan_key.module.params = {
      'usage_plan_id': 'upid' ,
      'api_key_id': 'akid',
      'key_type': 'API_KEY',
      'state': 'present',
    }
    reload(apigw_usage_plan_key)

  def test_boto_module_not_found(self):
    # Setup Mock Import Function
    import __builtin__ as builtins
    real_import = builtins.__import__

    def mock_import(name, *args):
      if name == 'boto': raise ImportError
      return real_import(name, *args)

    with mock.patch('__builtin__.__import__', side_effect=mock_import):
      reload(apigw_usage_plan_key)
      ApiGwUsagePlanKey(self.module)

    self.module.fail_json.assert_called_with(msg='boto and boto3 are required for this module')

  def test_boto3_module_not_found(self):
    # Setup Mock Import Function
    import __builtin__ as builtins
    real_import = builtins.__import__

    def mock_import(name, *args):
      if name == 'boto3': raise ImportError
      return real_import(name, *args)

    with mock.patch('__builtin__.__import__', side_effect=mock_import):
      reload(apigw_usage_plan_key)
      ApiGwUsagePlanKey(self.module)

    self.module.fail_json.assert_called_with(msg='boto and boto3 are required for this module')

  @patch.object(apigw_usage_plan_key, 'boto3')
  def test_boto3_client_properly_instantiated(self, mock_boto):
    ApiGwUsagePlanKey(self.module)
    mock_boto.client.assert_called_once_with('apigateway')

  def test_process_request_calls_get_usage_plan_keys_and_stores_result_when_invoked(self):
    resp = {
      'items': [
        {'id': 'wrong_id'},
        {'id': 'akid'},
      ],
    }
    self.usage_plan_key.client.get_usage_plan_keys = mock.MagicMock(return_value=resp)

    self.usage_plan_key.process_request()

    self.assertEqual(resp['items'][1], self.usage_plan_key.me)
    self.usage_plan_key.client.get_usage_plan_keys.assert_called_once_with(usagePlanId='upid')

  def test_process_request_stores_None_result_when_not_found_in_get_usage_plan_keys_result(self):
    resp = {
      'items': [
        {'id': 'wrong id'},
        {'id': 'wronger id'},
      ],
    }
    self.usage_plan_key.client.get_usage_plan_keys = mock.MagicMock(return_value=resp)

    self.usage_plan_key.process_request()

    self.assertEqual(None, self.usage_plan_key.me)
    self.usage_plan_key.client.get_usage_plan_keys.assert_called_once_with(usagePlanId='upid')

  def test_process_request_calls_fail_json_when_get_usage_plan_keys_raises_exception(self):
    self.usage_plan_key.client.get_usage_plan_keys = mock.MagicMock(side_effect=BotoCoreError())

    self.usage_plan_key.process_request()

    self.usage_plan_key.client.get_usage_plan_keys.assert_called_once_with(usagePlanId='upid')
    self.usage_plan_key.module.fail_json.assert_called_once_with(
      msg='Error when getting usage_plan_keys from boto3: An unspecified error occurred'
    )

  @patch.object(ApiGwUsagePlanKey, '_delete_usage_plan_key', return_value='Mitchell!')
  @patch.object(ApiGwUsagePlanKey, '_retrieve_usage_plan_key', return_value={'id': 'found'})
  def test_process_request_calls_exit_json_with_expected_value_after_successful_delete(self, mr, md):
    self.usage_plan_key.module.params = {
      'usage_plan_id': 'upid',
      'api_key_id': 'akid',
      'state': 'absent',
    }

    self.usage_plan_key.process_request()

    self.usage_plan_key.module.exit_json.assert_called_once_with(changed='Mitchell!', usage_plan_key=None)

  @patch.object(ApiGwUsagePlanKey, '_retrieve_usage_plan_key', return_value={'id': 'found'})
  def test_process_request_calls_delete_usage_plan_key_when_state_absent_and_usage_plan_key_found(self, m):
    self.usage_plan_key.module.params = {
      'usage_plan_id': 'upid',
      'api_key_id': 'akid',
      'state': 'absent',
    }

    self.usage_plan_key.process_request()

    self.usage_plan_key.client.delete_usage_plan_key.assert_called_once_with(usagePlanId='upid', apiKeyId='akid')

  @patch.object(ApiGwUsagePlanKey, '_retrieve_usage_plan_key', return_value={'id': 'found'})
  def test_process_request_skips_delete_and_calls_exit_json_with_true_when_check_mode_set_and_auth_found(self, m):
    self.usage_plan_key.module.params = {
      'usage_plan_id': 'upid',
      'api_key_id': 'akid',
      'state': 'absent',
    }
    self.usage_plan_key.module.check_mode = True

    self.usage_plan_key.process_request()

    self.assertEqual(0, self.usage_plan_key.client.delete_usage_plan_key.call_count)
    self.usage_plan_key.module.exit_json.assert_called_once_with(changed=True, usage_plan_key=None)


  @patch.object(ApiGwUsagePlanKey, '_retrieve_usage_plan_key', return_value={'id': 'found'})
  def test_process_request_calls_fail_json_when_delete_usage_plan_key_raises_error(self, m):
    self.usage_plan_key.module.params = {
      'usage_plan_id': 'upid',
      'api_key_id': 'akid',
      'state': 'absent',
    }

    self.usage_plan_key.client.delete_usage_plan_key = mock.MagicMock(side_effect=BotoCoreError)
    self.usage_plan_key.process_request()

    self.usage_plan_key.client.delete_usage_plan_key.assert_called_once_with(usagePlanId='upid', apiKeyId='akid')
    self.usage_plan_key.module.fail_json.assert_called_once_with(
      msg='Error when deleting usage_plan_key via boto3: An unspecified error occurred'
    )

  @patch.object(ApiGwUsagePlanKey, '_retrieve_usage_plan_key', return_value=None)
  def test_process_request_skips_delete_when_usage_plan_key_not_found(self, m):
    self.usage_plan_key.module.params = {
      'usage_plan_id': 'upid',
      'api_key_id': 'akid',
      'state': 'absent',
    }

    self.usage_plan_key.process_request()

    self.assertEqual(0, self.usage_plan_key.client.delete_usage_plan_key.call_count)

  def test_define_argument_spec(self):
    result = ApiGwUsagePlanKey._define_module_argument_spec()
    self.assertIsInstance(result, dict)
    self.assertEqual(result, dict(
                     usage_plan_id=dict(required=True),
                     api_key_id=dict(required=True),
                     key_type=dict(required=False, default='API_KEY', choices=['API_KEY']),
                     state=dict(default='present', choices=['present', 'absent']),
    ))

  @patch.object(apigw_usage_plan_key, 'AnsibleModule')
  @patch.object(apigw_usage_plan_key, 'ApiGwUsagePlanKey')
  def test_main(self, mock_ApiGwUsagePlanKey, mock_AnsibleModule):
    mock_ApiGwUsagePlanKey_instance      = mock.MagicMock()
    mock_AnsibleModule_instance     = mock.MagicMock()
    mock_ApiGwUsagePlanKey.return_value  = mock_ApiGwUsagePlanKey_instance
    mock_AnsibleModule.return_value = mock_AnsibleModule_instance

    apigw_usage_plan_key.main()

    mock_ApiGwUsagePlanKey.assert_called_once_with(mock_AnsibleModule_instance)
    assert mock_ApiGwUsagePlanKey_instance.process_request.call_count == 1


if __name__ == '__main__':
    unittest.main()

