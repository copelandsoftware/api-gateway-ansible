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
from botocore.exceptions import BotoCoreError

class TestApiGwMethod(unittest.TestCase):

  def setUp(self):
    self.module = mock.MagicMock()
    self.module.check_mode = False
    self.module.exit_json = mock.MagicMock()
    self.module.fail_json = mock.MagicMock()
    self.resource  = ApiGwMethod(self.module)
    self.resource.client = mock.MagicMock()
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
                     name=dict(required=True, choices=['get', 'put', 'post', 'delete', 'patch', 'head']),
                     rest_api_id=dict(required=True),
                     resource_id=dict(required=True),
                     authorization_type=dict(required=True),
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

