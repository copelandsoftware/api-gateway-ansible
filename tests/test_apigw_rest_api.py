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
    self.restapi.module.params = { 'id': 'whatever' }
    self.restapi.process_request()

    self.restapi.client.get_rest_apis.assert_called_once_with()

  def test_process_request_fails_when_get_rest_apis_returns_error(self):
    self.restapi.module.params = { 'id': 'whatever' }
    self.restapi.client.get_rest_apis = mock.MagicMock(side_effect=Exception('kaboom'))
    self.restapi.process_request()

    self.restapi.module.fail_json.assert_called_once_with(msg='No rest apis found for this account')

  def test_process_request_fails_when_requested_api_is_not_present(self):
    get_response = {
      'items': [{
        'id': 12345,
        'name': 'not here',
      },
      {
        'id': 54321,
        'name': 'also not found'
      }]
    }
    self.restapi.module.params = { 'id': 'whatever' }
    self.restapi.client.get_rest_apis = mock.MagicMock(return_value=get_response)
    self.restapi.process_request()

    self.restapi.module.fail_json.assert_called_once_with(msg='API <whatever> not found')

  def test_define_argument_spec(self):
    result = ApiGwRestApi._define_module_argument_spec()
    self.assertIsInstance(result, dict)
    self.assertEqual(result, dict(
                     id=dict(required=True, aliases=['name']),
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

