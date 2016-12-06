#!/usr/bin/python
# TODO: License goes here

import library.apigw_authorizer as apigw_authorizer
from library.apigw_authorizer import ApiGwAuthorizer
import mock
from mock import patch
from mock import create_autospec
from mock import ANY
import unittest
import boto
from botocore.exceptions import BotoCoreError

class TestApiGwAuthorizer(unittest.TestCase):

  def setUp(self):
    self.module = mock.MagicMock()
    self.module.check_mode = False
    self.module.exit_json = mock.MagicMock()
    self.module.fail_json = mock.MagicMock()
    self.authorizer  = ApiGwAuthorizer(self.module)
    self.authorizer.client = mock.MagicMock()
    self.authorizer.module.params = {
      'rest_api_id': 'rest_id',
      'name': 'testify',
      'type': 'token',
      'uri': 'my uri',
      'identity_source': 'source-arn',
      'auth_type': 'yolo',
      'state': 'present',
    }
    reload(apigw_authorizer)

  def test_boto_module_not_found(self):
    # Setup Mock Import Function
    import __builtin__ as builtins
    real_import = builtins.__import__

    def mock_import(name, *args):
      if name == 'boto': raise ImportError
      return real_import(name, *args)

    with mock.patch('__builtin__.__import__', side_effect=mock_import):
      reload(apigw_authorizer)
      ApiGwAuthorizer(self.module)

    self.module.fail_json.assert_called_with(msg='boto and boto3 are required for this module')

  def test_boto3_module_not_found(self):
    # Setup Mock Import Function
    import __builtin__ as builtins
    real_import = builtins.__import__

    def mock_import(name, *args):
      if name == 'boto3': raise ImportError
      return real_import(name, *args)

    with mock.patch('__builtin__.__import__', side_effect=mock_import):
      reload(apigw_authorizer)
      ApiGwAuthorizer(self.module)

    self.module.fail_json.assert_called_with(msg='boto and boto3 are required for this module')

  @patch.object(apigw_authorizer, 'boto3')
  def test_boto3_client_properly_instantiated(self, mock_boto):
    ApiGwAuthorizer(self.module)
    mock_boto.client.assert_called_once_with('apigateway')

  def test_process_request_calls_get_authorizers_and_stores_result_when_invoked(self):
    resp = {
      'items': [
        {'id': 'nope', 'name': 'nope'},
        {'id': 'match', 'name': 'testify'}
      ],
    }
    self.authorizer.client.get_authorizers = mock.MagicMock(return_value=resp)

    self.authorizer.process_request()

    self.assertEqual(resp['items'][1], self.authorizer.me)
    self.authorizer.client.get_authorizers.assert_called_once_with(restApiId='rest_id')

  def test_process_request_stores_None_result_when_not_found_in_get_authorizers_result(self):
    resp = {
      'items': [
        {'id': 'nope', 'name': 'nope'},
        {'id': 'not match', 'name': 'also nope'}
      ],
    }
    self.authorizer.client.get_authorizers = mock.MagicMock(return_value=resp)

    self.authorizer.process_request()

    self.assertEqual(None, self.authorizer.me)
    self.authorizer.client.get_authorizers.assert_called_once_with(restApiId='rest_id')

  def test_process_request_calls_fail_json_when_get_authorizers_raises_exception(self):
    self.authorizer.client.get_authorizers = mock.MagicMock(side_effect=BotoCoreError())

    self.authorizer.process_request()

    self.authorizer.client.get_authorizers.assert_called_once_with(restApiId='rest_id')
    self.authorizer.module.fail_json.assert_called_once_with(
      msg='Error when getting authorizers from boto3: An unspecified error occurred'
    )

  @patch.object(ApiGwAuthorizer, '_delete_authorizer', return_value='sprinkles')
  @patch.object(ApiGwAuthorizer, '_retrieve_authorizer', return_value={'id': 'found'})
  def test_process_request_calls_exit_json_with_expected_value_after_successful_delete(self, mra, mda):
    self.authorizer.module.params = {
      'rest_api_id': 'rest_id',
      'name': 'testify',
      'state': 'absent',
    }

    self.authorizer.process_request()

    self.authorizer.module.exit_json.assert_called_once_with(changed='sprinkles', authorizer=None)

  @patch.object(ApiGwAuthorizer, '_retrieve_authorizer', return_value={'id': 'found'})
  def test_process_request_calls_delete_authorizer_when_state_absent_and_authorizer_found(self, m):
    self.authorizer.module.params = {
      'rest_api_id': 'rest_id',
      'name': 'testify',
      'state': 'absent',
    }

    self.authorizer.process_request()

    self.authorizer.client.delete_authorizer.assert_called_once_with(
      restApiId='rest_id',
      authorizerId='found'
    )

  @patch.object(ApiGwAuthorizer, '_retrieve_authorizer', return_value={'id': 'found'})
  def test_process_request_skips_delete_and_calls_exit_json_with_true_when_check_mode_set_and_auth_found(self, m):
    self.authorizer.module.params = {
      'rest_api_id': 'rest_id',
      'name': 'testify',
      'state': 'absent',
    }
    self.authorizer.module.check_mode = True

    self.authorizer.process_request()

    self.assertEqual(0, self.authorizer.client.delete_authorizer.call_count)
    self.authorizer.module.exit_json.assert_called_once_with(changed=True, authorizer=None)


  @patch.object(ApiGwAuthorizer, '_retrieve_authorizer', return_value={'id': 'found'})
  def test_process_request_calls_fail_json_when_delete_authorizer_raises_error(self, m):
    self.authorizer.module.params = {
      'rest_api_id': 'rest_id',
      'name': 'testify',
      'state': 'absent',
    }

    self.authorizer.client.delete_authorizer = mock.MagicMock(side_effect=BotoCoreError)
    self.authorizer.process_request()

    self.authorizer.client.delete_authorizer.assert_called_once_with(
      restApiId='rest_id',
      authorizerId='found'
    )
    self.authorizer.module.fail_json.assert_called_once_with(
      msg='Error when deleting authorizer via boto3: An unspecified error occurred'
    )

  @patch.object(ApiGwAuthorizer, '_retrieve_authorizer', return_value=None)
  def test_process_request_skips_delete_when_authorizer_not_found(self, m):
    self.authorizer.module.params = {
      'rest_api_id': 'rest_id',
      'name': 'testify',
      'state': 'absent',
    }

    self.authorizer.process_request()

    self.assertEqual(0, self.authorizer.client.delete_authorizer.call_count)

  @patch.object(ApiGwAuthorizer, '_create_authorizer', return_value=('time', 'lord'))
  @patch.object(ApiGwAuthorizer, '_retrieve_authorizer', return_value=None)
  def test_process_request_calls_exit_json_with_expected_value_after_successful_create(self, mra, mca):
    self.authorizer.process_request()

    self.authorizer.module.exit_json.assert_called_once_with(changed='time', authorizer='lord')

  @patch.object(ApiGwAuthorizer, '_retrieve_authorizer', return_value=None)
  def test_process_request_returns_create_authorizer_result_when_create_succeeds(self, m):
    self.authorizer.client.create_authorizer = mock.MagicMock(return_value='woot')
    self.authorizer.process_request()

    self.authorizer.module.exit_json.assert_called_once_with(changed=True, authorizer='woot')


  @patch.object(ApiGwAuthorizer, '_retrieve_authorizer', return_value=None)
  def test_process_request_calls_create_authorizer_when_state_present_and_authorizer_not_found(self, m):
    self.authorizer.process_request()

    self.authorizer.client.create_authorizer.assert_called_once_with(
      restApiId='rest_id',
      name='testify',
      type='token',
      authType='yolo',
      authorizerUri='my uri',
      identitySource='source-arn'
    )

  @patch.object(ApiGwAuthorizer, '_retrieve_authorizer', return_value=None)
  def test_process_request_calls_fail_json_when_create_authorizer_raises_exception(self, m):
    self.authorizer.client.create_authorizer = mock.MagicMock(side_effect=BotoCoreError())
    self.authorizer.process_request()

    self.authorizer.client.create_authorizer.assert_called_once_with(
      restApiId='rest_id',
      name='testify',
      type='token',
      authType='yolo',
      authorizerUri='my uri',
      identitySource='source-arn'
    )
    self.authorizer.module.fail_json.assert_called_once_with(
      msg='Error when creating authorizer via boto3: An unspecified error occurred'
    )

  @patch.object(ApiGwAuthorizer, '_retrieve_authorizer', return_value=None)
  def test_process_request_skips_create_call_and_returns_changed_True_when_check_mode(self, m):
    self.authorizer.module.check_mode = True
    self.authorizer.process_request()

    self.assertEqual(0, self.authorizer.client.create_authorizer.call_count)
    self.authorizer.module.exit_json.assert_called_once_with(changed=True, authorizer=None)

  def test_define_argument_spec(self):
    result = ApiGwAuthorizer._define_module_argument_spec()
    self.assertIsInstance(result, dict)
    self.assertEqual(result, dict(
                     rest_api_id=dict(required=True),
                     name=dict(required=True),
                     type=dict(required=False, choices=['token', 'cognito_user_pools']),
                     uri=dict(required=False),
                     identity_source=dict(required=False),
                     identity_validation_expression=dict(required=False, default=''),
                     provider_arns=dict(required=False, type='list', default=[]),
                     auth_type=dict(required=False),
                     credentials=dict(required=False),
                     result_ttl_seconds=dict(required=False, type='int', default=0),
                     state=dict(default='present', choices=['present', 'absent']),
    ))

  @patch.object(apigw_authorizer, 'AnsibleModule')
  @patch.object(apigw_authorizer, 'ApiGwAuthorizer')
  def test_main(self, mock_ApiGwAuthorizer, mock_AnsibleModule):
    mock_ApiGwAuthorizer_instance      = mock.MagicMock()
    mock_AnsibleModule_instance     = mock.MagicMock()
    mock_ApiGwAuthorizer.return_value  = mock_ApiGwAuthorizer_instance
    mock_AnsibleModule.return_value = mock_AnsibleModule_instance

    apigw_authorizer.main()

    mock_ApiGwAuthorizer.assert_called_once_with(mock_AnsibleModule_instance)
    assert mock_ApiGwAuthorizer_instance.process_request.call_count == 1


if __name__ == '__main__':
    unittest.main()

