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
      'description': 'test_description',
      'value': 'test_value',
      'generate_distinct_id': False,
      'enabled': True,
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

  def test_process_request_calls_get_api_keys_and_stores_result_when_invoked(self):
    resp = {
      'items': [
        {'name': 'not a match', 'id': 'rest_api_id'},
        {'name': 'testify', 'id': 'rest_api_id'},
      ],
    }
    self.api_key.client.get_api_keys = mock.MagicMock(return_value=resp)

    self.api_key.process_request()

    self.assertEqual(resp['items'][1], self.api_key.me)
    self.api_key.client.get_api_keys.assert_called_once_with(nameQuery='testify', includeValues=True)

  def test_process_request_stores_None_result_when_not_found_in_get_api_keys_result(self):
    resp = {
      'items': [
        {'name': 'not a match', 'id': 'rest_api_id'},
        {'name': 'also not a match', 'id': 'rest_api_id'},
      ],
    }
    self.api_key.client.get_api_keys = mock.MagicMock(return_value=resp)

    self.api_key.process_request()

    self.assertEqual(None, self.api_key.me)
    self.api_key.client.get_api_keys.assert_called_once_with(nameQuery='testify', includeValues=True)

  def test_process_request_calls_fail_json_when_get_api_keys_raises_exception(self):
    self.api_key.client.get_api_keys = mock.MagicMock(side_effect=BotoCoreError())

    self.api_key.process_request()

    self.api_key.client.get_api_keys.assert_called_once_with(nameQuery='testify', includeValues=True)
    self.api_key.module.fail_json.assert_called_once_with(
      msg='Error when getting api_keys from boto3: An unspecified error occurred'
    )

  @patch.object(ApiGwApiKey, '_delete_api_key', return_value='Mitchell!')
  @patch.object(ApiGwApiKey, '_retrieve_api_key', return_value={'id': 'found'})
  def test_process_request_calls_exit_json_with_expected_value_after_successful_delete(self, mr, md):
    self.api_key.module.params = {
      'name': 'testify',
      'state': 'absent',
    }

    self.api_key.process_request()

    self.api_key.module.exit_json.assert_called_once_with(changed='Mitchell!', api_key=None)

  @patch.object(ApiGwApiKey, '_retrieve_api_key', return_value={'id': 'found'})
  def test_process_request_calls_delete_api_key_when_state_absent_and_api_key_found(self, m):
    self.api_key.module.params = {
      'name': 'testify',
      'state': 'absent',
    }

    self.api_key.process_request()

    self.api_key.client.delete_api_key.assert_called_once_with(apiKey='found')

  @patch.object(ApiGwApiKey, '_retrieve_api_key', return_value={'id': 'found'})
  def test_process_request_skips_delete_and_calls_exit_json_with_true_when_check_mode_set_and_auth_found(self, m):
    self.api_key.module.params = {
      'name': 'testify',
      'state': 'absent',
    }
    self.api_key.module.check_mode = True

    self.api_key.process_request()

    self.assertEqual(0, self.api_key.client.delete_api_key.call_count)
    self.api_key.module.exit_json.assert_called_once_with(changed=True, api_key=None)


  @patch.object(ApiGwApiKey, '_retrieve_api_key', return_value={'id': 'found'})
  def test_process_request_calls_fail_json_when_delete_api_key_raises_error(self, m):
    self.api_key.module.params = {
      'name': 'testify',
      'state': 'absent',
    }

    self.api_key.client.delete_api_key = mock.MagicMock(side_effect=BotoCoreError)
    self.api_key.process_request()

    self.api_key.client.delete_api_key.assert_called_once_with(apiKey='found')
    self.api_key.module.fail_json.assert_called_once_with(
      msg='Error when deleting api_key via boto3: An unspecified error occurred'
    )

  @patch.object(ApiGwApiKey, '_retrieve_api_key', return_value=None)
  def test_process_request_skips_delete_when_api_key_not_found(self, m):
    self.api_key.module.params = {
      'name': 'testify',
      'state': 'absent',
    }

    self.api_key.process_request()

    self.assertEqual(0, self.api_key.client.delete_api_key.call_count)

  @patch.object(ApiGwApiKey, '_create_api_key', return_value=('veins', 'clogging'))
  @patch.object(ApiGwApiKey, '_retrieve_api_key', return_value=None)
  def test_process_request_calls_exit_json_with_expected_value_after_successful_create(self, mra, mca):
    self.api_key.process_request()

    self.api_key.module.exit_json.assert_called_once_with(changed='veins', api_key='clogging')

  @patch.object(ApiGwApiKey, '_retrieve_api_key', return_value=None)
  def test_process_request_returns_create_api_key_result_when_create_succeeds(self, m):
    self.api_key.client.create_api_key = mock.MagicMock(return_value='woot')
    self.api_key.process_request()

    self.api_key.module.exit_json.assert_called_once_with(changed=True, api_key='woot')


  @patch.object(ApiGwApiKey, '_retrieve_api_key', return_value=None)
  def test_process_request_calls_create_api_key_when_state_present_and_api_key_not_found(self, m):
    self.api_key.process_request()

    self.api_key.client.create_api_key.assert_called_once_with(
      name='testify',
      description='test_description',
      enabled=True,
      generateDistinctId=False,
      value='test_value',
    )

  @patch.object(ApiGwApiKey, '_retrieve_api_key', return_value=None)
  def test_process_request_calls_fail_json_when_create_api_key_raises_exception(self, m):
    self.api_key.client.create_api_key = mock.MagicMock(side_effect=BotoCoreError())
    self.api_key.process_request()

    self.api_key.client.create_api_key.assert_called_once_with(
      name='testify',
      description='test_description',
      enabled=True,
      generateDistinctId=False,
      value='test_value',
    )
    self.api_key.module.fail_json.assert_called_once_with(
      msg='Error when creating api_key via boto3: An unspecified error occurred'
    )

  @patch.object(ApiGwApiKey, '_retrieve_api_key', return_value=None)
  def test_process_request_skips_create_call_and_returns_changed_True_when_check_mode(self, m):
    self.api_key.module.check_mode = True
    self.api_key.process_request()

    self.assertEqual(0, self.api_key.client.create_api_key.call_count)
    self.api_key.module.exit_json.assert_called_once_with(changed=True, api_key=None)


  def test_define_argument_spec(self):
    result = ApiGwApiKey._define_module_argument_spec()
    self.assertIsInstance(result, dict)
    self.assertEqual(result, dict(
                     name=dict(required=True),
                     description=dict(required=False),
                     value=dict(required=False),
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

