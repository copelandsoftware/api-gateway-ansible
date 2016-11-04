#!/usr/bin/python
# TODO: License goes here

import library.apigw_method as apigw_method
from library.apigw_method import ApiGwMethod
import mock
from mock import patch
from mock import create_autospec
from mock import ANY
import unittest
import boto
from botocore.exceptions import BotoCoreError, ClientError

class TestApiGwMethod(unittest.TestCase):

  def setUp(self):
    self.module = mock.MagicMock()
    self.module.check_mode = False
    self.module.exit_json = mock.MagicMock()
    self.module.fail_json = mock.MagicMock()
    self.method  = ApiGwMethod(self.module)
    self.method.client = mock.MagicMock()
    self.method.module.params = {
      'rest_api_id': 'restid',
      'resource_id': 'rsrcid',
      'name': 'GET',
      'authorization_type': 'NONE',
      'state': 'present'
    }
    reload(apigw_method)

  def test_boto_module_not_found(self):
    # Setup Mock Import Function
    import __builtin__ as builtins
    real_import = builtins.__import__

    def mock_import(name, *args):
      if name == 'boto': raise ImportError
      return real_import(name, *args)

    with mock.patch('__builtin__.__import__', side_effect=mock_import):
      reload(apigw_method)
      ApiGwMethod(self.module)

    self.module.fail_json.assert_called_with(msg='boto and boto3 are required for this module')

  def test_boto3_module_not_found(self):
    # Setup Mock Import Function
    import __builtin__ as builtins
    real_import = builtins.__import__

    def mock_import(name, *args):
      if name == 'boto3': raise ImportError
      return real_import(name, *args)

    with mock.patch('__builtin__.__import__', side_effect=mock_import):
      reload(apigw_method)
      ApiGwMethod(self.module)

    self.module.fail_json.assert_called_with(msg='boto and boto3 are required for this module')

  @patch.object(apigw_method, 'boto3')
  def test_boto3_client_properly_instantiated(self, mock_boto):
    ApiGwMethod(self.module)
    mock_boto.client.assert_called_once_with('apigateway')


  def test_define_argument_spec(self):
    result = ApiGwMethod._define_module_argument_spec()
    self.assertIsInstance(result, dict)
    self.assertEqual(result, dict(
                     name=dict(
                       required=True,
                       choices=['GET', 'PUT', 'POST', 'DELETE', 'PATCH', 'HEAD', 'ANY', 'OPTIONS'],
                       aliases=['method']
                     ),
                     rest_api_id=dict(required=True),
                     resource_id=dict(required=True),
                     authorization_type=dict(required=False, default='NONE'),
                     authorizer_id=dict(required=False),
                     request_params=dict(
                       type='list',
                       required=False,
                       default=[],
                       name=dict(required=True),
                       location=dict(required=True, choices=['querystring', 'path', 'header']),
                       param_required=dict(type='bool')
                     ),
                     state=dict(default='present', choices=['present', 'absent'])
                     ))

  def test_process_request_gets_method_on_invocation(self):
    self.method.client.get_method=mock.MagicMock(return_value='response')
    self.method.process_request()

    self.method.client.get_method.assert_called_once_with(
        restApiId='restid',
        resourceId='rsrcid',
        httpMethod='GET'
    )
    self.assertEqual('response', self.method.method)

  def test_process_request_sets_method_result_to_None_when_get_method_throws_not_found(self):
    self.method.client.get_method=mock.MagicMock(
        side_effect=ClientError({'Error': {'Code': 'x NotFoundException x'}}, 'xxx'))
    self.method.process_request()

    self.method.client.get_method.assert_called_once_with(
        restApiId='restid',
        resourceId='rsrcid',
        httpMethod='GET'
    )
    self.assertIsNone(self.method.method)

  def test_process_request_calls_fail_json_when_ClientError_is_not_NotFoundException(self):
    self.method.client.get_method=mock.MagicMock(
        side_effect=ClientError({'Error': {'Code': 'boom', 'Message': 'error'}}, 'xxx'))
    self.method.process_request()

    self.method.client.get_method.assert_called_once_with(
        restApiId='restid',
        resourceId='rsrcid',
        httpMethod='GET'
    )
    self.method.module.fail_json.assert_called_once_with(msg='Error calling boto3 get_method: An error occurred (boom) when calling the xxx operation: error')

  def test_process_request_calls_fail_json_when_get_method_throws_other_boto_core_error(self):
    self.method.client.get_method=mock.MagicMock(side_effect=BotoCoreError())
    self.method.process_request()

    self.method.client.get_method.assert_called_once_with(
        restApiId='restid',
        resourceId='rsrcid',
        httpMethod='GET'
    )
    self.method.module.fail_json.assert_called_once_with(msg='Error calling boto3 get_method: An unspecified error occurred')


  @patch.object(apigw_method, 'AnsibleModule')
  @patch.object(apigw_method, 'ApiGwMethod')
  def test_main(self, mock_ApiGwMethod, mock_AnsibleModule):
    mock_ApiGwMethod_instance       = mock.MagicMock()
    mock_AnsibleModule_instance     = mock.MagicMock()
    mock_ApiGwMethod.return_value   = mock_ApiGwMethod_instance
    mock_AnsibleModule.return_value = mock_AnsibleModule_instance

    apigw_method.main()

    mock_ApiGwMethod.assert_called_once_with(mock_AnsibleModule_instance)
    self.assertEqual(1, mock_ApiGwMethod_instance.process_request.call_count)


if __name__ == '__main__':
    unittest.main()

