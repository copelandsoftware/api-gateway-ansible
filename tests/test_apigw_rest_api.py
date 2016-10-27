#!/usr/bin/python
# TODO: License goes here

import library.apigw_rest_api as apigw_rest_api
from library.apigw_rest_api import ApiGwRestApi
import mock
from mock import patch
from mock import create_autospec
import unittest

class TestApiGwRestApi(unittest.TestCase):

  def setUp(self):
    self.module = mock.MagicMock()
    self.module.exit_json = mock.MagicMock()
    self.module.fail_json = mock.MagicMock()
    self.restapi  = ApiGwRestApi(self.module)
    self.restapi.client = mock.MagicMock()
    reload(apigw_rest_api)

  def test_boto_module_not_found(self):
    # Setup Mock Import Function
    import __builtin__ as builtins
    real_import = builtins.__import__

    def mock_import(name, *args):
      if name == 'boto': raise ImportError
      return real_import(name, *args)

    with mock.patch('__builtin__.__import__', side_effect=mock_import):
      reload(apigw_rest_api)
      ApiGwRestApi(self.module)

    self.module.fail_json.assert_called_with(msg='boto and boto3 are required for this module')

  def test_boto3_module_not_found(self):
    # Setup Mock Import Function
    import __builtin__ as builtins
    real_import = builtins.__import__

    def mock_import(name, *args):
      if name == 'boto3': raise ImportError
      return real_import(name, *args)

    with mock.patch('__builtin__.__import__', side_effect=mock_import):
      reload(apigw_rest_api)
      ApiGwRestApi(self.module)

    self.module.fail_json.assert_called_with(msg='boto and boto3 are required for this module')

  @patch.object(apigw_rest_api, 'boto3')
  def test_boto3_client_properly_instantiated(self, mock_boto):
    ApiGwRestApi(self.module)
    mock_boto.client.assert_called_once_with('apigateway')

  def test_process_request_calls_boto3_get_rest_apis(self):
    self.restapi.module.params = { 'name': 'whatever' }
    self.restapi.process_request()

    self.restapi.client.get_rest_apis.assert_called_once_with()

  def test_process_request_fails_when_get_rest_apis_returns_error(self):
    self.restapi.module.params = { 'name': 'whatever' }
    self.restapi.client.get_rest_apis = mock.MagicMock(side_effect=Exception('kaboom'))
    self.restapi.process_request()

    self.restapi.module.fail_json.assert_called_once_with(msg='Encountered fatal error calling boto3 get_rest_apis function')

  def test_process_request_exits_with_no_change_when_removing_non_existent_api(self):
    self.restapi.module.params = { 'name': 'whatever', 'state': 'absent' }
    self.restapi.client.get_rest_apis = mock.MagicMock(return_value={'items': []})
    self.restapi.process_request()

    self.restapi.module.exit_json.assert_called_once_with(changed=False, api=None)

  def test_process_request_exits_with_no_change_when_adding_existing_and_unchanged_api(self):
    get_response = {
      'items': [{
        'id': 12345,
        'name': 'whatever',
        'description': 'very awesome'
      }]
    }
    self.restapi.module.params = { 'name': 'whatever', 'state': 'present', 'description': 'very awesome' }
    self.restapi.client.get_rest_apis = mock.MagicMock(return_value=get_response)
    self.restapi.process_request()

    self.restapi.module.exit_json.assert_called_once_with(changed=False, api=get_response['items'][0])

  def test_process_request_creates_api_when_missing(self):
    create_response = {
			'id': 'aws-whatever',
			'name': 'a-name',
			'description': 'a-desc',
			'createdDate': 'some-date'
		}
    self.restapi.module.params = { 'name': 'whatever', 'state': 'present', 'description': 'very awesome' }
    self.restapi.client.get_rest_apis = mock.MagicMock(return_value={'items': []})
    self.restapi.client.create_rest_api = mock.MagicMock(return_value=create_response)
    self.restapi.process_request()

    self.restapi.client.create_rest_api.assert_called_once_with(name='whatever', description='very awesome')
    self.restapi.module.exit_json.assert_called_once_with(changed=True, api=create_response)

  def test_process_request_fails_when_create_rest_api_throws_error(self):
    self.restapi.module.params = { 'name': 'whatever', 'state': 'present' }
    self.restapi.client.get_rest_apis = mock.MagicMock(return_value={'items': []})
    self.restapi.client.create_rest_api = mock.MagicMock(side_effect=Exception('no soup for you'))
    self.restapi.process_request()

    self.restapi.client.create_rest_api.assert_called_once_with(name='whatever')
    self.restapi.module.fail_json.assert_called_once_with(msg='Encountered fatal error calling boto3 create_rest_api function')

  def test_process_request_updates_api_when_params_do_not_match(self):
    get_response = {
      'items': [{
        'id': 12345,
        'name': 'whatever',
        'description': 'very awesome'
      }]
    }
    self.restapi.module.params = { 'name': 'whatever', 'state': 'present', 'description': 'awesomer' }
    self.restapi.client.get_rest_apis = mock.MagicMock(return_value=get_response)
    self.restapi.client.update_rest_api = mock.MagicMock(return_value='TotallyUpdated')
    self.restapi.process_request()

    self.restapi.client.update_rest_api.assert_called_once_with(restApiId=12345, patchOperations=[
        {'op': 'replace', 'path': '/name', 'value': 'whatever'},
        {'op': 'replace', 'path': '/description', 'value': 'awesomer'},
    ])
    self.restapi.module.exit_json.assert_called_once_with(changed=True, api='TotallyUpdated')

  def test_process_request_sets_description_to_empty_string_when_missing_during_update(self):
    get_response = {
      'items': [{
        'id': 12345,
        'name': 'whatever',
        'description': 'very awesome'
      }]
    }
    self.restapi.module.params = { 'name': 'whatever', 'state': 'present' }
    self.restapi.client.get_rest_apis = mock.MagicMock(return_value=get_response)
    self.restapi.client.update_rest_api = mock.MagicMock(return_value='TotallyUpdated')
    self.restapi.process_request()

    self.restapi.client.update_rest_api.assert_called_once_with(restApiId=12345, patchOperations=[
        {'op': 'replace', 'path': '/name', 'value': 'whatever'},
        {'op': 'replace', 'path': '/description', 'value': ''}
    ])
    self.restapi.module.exit_json.assert_called_once_with(changed=True, api='TotallyUpdated')

  def test_process_request_fails_when_update_rest_api_throws_exception(self):
    get_response = {
      'items': [{
        'id': 12345,
        'name': 'whatever',
        'description': 'very awesome'
      }]
    }
    self.restapi.module.params = { 'name': 'whatever', 'state': 'present', 'description': 'awesomer' }
    self.restapi.client.get_rest_apis = mock.MagicMock(return_value=get_response)
    self.restapi.client.update_rest_api = mock.MagicMock(side_effect=Exception('asplode'))
    self.restapi.process_request()

    self.restapi.client.update_rest_api.assert_called_once_with(restApiId=12345, patchOperations=[
        {'op': 'replace', 'path': '/name', 'value': 'whatever'},
        {'op': 'replace', 'path': '/description', 'value': 'awesomer'},
    ])
    self.restapi.module.fail_json.assert_called_once_with(msg='Encountered fatal error calling boto3 update_rest_api function')

  def test_process_request_deletes_api_when_api_is_present(self):
    get_response = {
      'items': [{
        'id': 12345,
        'name': 'whatever',
        'description': 'very awesome'
      }]
    }
    self.restapi.module.params = { 'name': 'whatever', 'state': 'absent' }
    self.restapi.client.get_rest_apis = mock.MagicMock(return_value=get_response)
    self.restapi.client.delete_rest_api = mock.MagicMock(return_value=None)
    self.restapi.process_request()

    self.restapi.client.delete_rest_api.assert_called_once_with(restApiId=12345)
    self.restapi.module.exit_json.assert_called_once_with(changed=True, api=None)

  def test_process_request_fails_when_delete_rest_api_throws_exception(self):
    get_response = {
      'items': [{
        'id': 12345,
        'name': 'whatever',
        'description': 'very awesome'
      }]
    }
    self.restapi.module.params = { 'name': 'whatever', 'state': 'absent' }
    self.restapi.client.get_rest_apis = mock.MagicMock(return_value=get_response)
    self.restapi.client.delete_rest_api = mock.MagicMock(side_effect=Exception('not today'))
    self.restapi.process_request()

    self.restapi.client.delete_rest_api.assert_called_once_with(restApiId=12345)
    self.restapi.module.fail_json.assert_called_once_with(msg='Encountered fatal error calling boto3 delete_rest_api function')

  def test_define_argument_spec(self):
    result = ApiGwRestApi._define_module_argument_spec()
    self.assertIsInstance(result, dict)
    self.assertEqual(result, dict(
                     name=dict(required=True),
                     description=dict(required=False),
                     state=dict(default='present', choices=['present', 'absent'])
    ))

  @patch.object(apigw_rest_api, 'AnsibleModule')
  @patch.object(apigw_rest_api, 'ApiGwRestApi')
  def test_main(self, mock_ApiGwRestApi, mock_AnsibleModule):
    mock_ApiGwRestApi_instance      = mock.MagicMock()
    mock_AnsibleModule_instance     = mock.MagicMock()
    mock_ApiGwRestApi.return_value  = mock_ApiGwRestApi_instance
    mock_AnsibleModule.return_value = mock_AnsibleModule_instance

    apigw_rest_api.main()

    mock_ApiGwRestApi.assert_called_once_with(mock_AnsibleModule_instance)
    assert mock_ApiGwRestApi_instance.process_request.call_count == 1


if __name__ == '__main__':
    unittest.main()

