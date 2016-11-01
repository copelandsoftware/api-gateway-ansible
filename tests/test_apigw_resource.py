#!/usr/bin/python
# TODO: License goes here

import library.apigw_resource as apigw_resource
from library.apigw_resource import ApiGwResource
import mock
from mock import patch
from mock import create_autospec
from mock import ANY
import unittest
import boto
from botocore.exceptions import BotoCoreError

class TestApiGwResource(unittest.TestCase):

  def setUp(self):
    self.module = mock.MagicMock()
    self.module.check_mode = False
    self.module.exit_json = mock.MagicMock()
    self.module.fail_json = mock.MagicMock()
    self.resource  = ApiGwResource(self.module)
    self.resource.client = mock.MagicMock()
    reload(apigw_resource)

  def test_boto_module_not_found(self):
    # Setup Mock Import Function
    import __builtin__ as builtins
    real_import = builtins.__import__

    def mock_import(name, *args):
      if name == 'boto': raise ImportError
      return real_import(name, *args)

    with mock.patch('__builtin__.__import__', side_effect=mock_import):
      reload(apigw_resource)
      ApiGwResource(self.module)

    self.module.fail_json.assert_called_with(msg='boto and boto3 are required for this module')

  def test_boto3_module_not_found(self):
    # Setup Mock Import Function
    import __builtin__ as builtins
    real_import = builtins.__import__

    def mock_import(name, *args):
      if name == 'boto3': raise ImportError
      return real_import(name, *args)

    with mock.patch('__builtin__.__import__', side_effect=mock_import):
      reload(apigw_resource)
      ApiGwResource(self.module)

    self.module.fail_json.assert_called_with(msg='boto and boto3 are required for this module')

  @patch.object(apigw_resource, 'boto3')
  def test_boto3_client_properly_instantiated(self, mock_boto):
    ApiGwResource(self.module)
    mock_boto.client.assert_called_once_with('apigateway')

  def test_process_request_builds_resources_dictionary(self):
    response = {
      'items': [{
        'id': 'root',
        'path': '/'
      },{
        'id': 'abc123',
        'parentId': 'root',
        'path': '/base',
        'pathPart': 'base'
      },{
        'id': 'def456',
        'parentId': 'abc123',
        'path': '/base/{param}',
        'pathPart': '{param}'
      }]
    }
    self.resource.client.get_resources = mock.MagicMock(return_value=response)

    expected = {
      'paths': {
        '/': {'id': 'root'},
        '/base': {'id': 'abc123', 'parent_id': 'root'},
        '/base/{param}': {'id': 'def456', 'parent_id': 'abc123'},
      },
      'has_children': {
        'root': True,
        'abc123': True
      }
    }

    self.resource.module.params = {'name': '/base/{param}', 'rest_api_id': 'rest_id'}

    self.resource.process_request()
    self.resource.client.get_resources.assert_called_once_with(restApiId='rest_id')
    self.assertEqual(self.resource.path_map, expected)

  def test_process_request_calls_fail_json_when_get_resources_fails(self):
    self.resource.client.get_resources = mock.MagicMock(side_effect=BotoCoreError())
    self.resource.process_request()

    self.resource.module.fail_json.assert_called_once_with(
        msg="Error calling boto3 get_resources: An unspecified error occurred")

  def test_define_argument_spec(self):
    result = ApiGwResource._define_module_argument_spec()
    self.assertIsInstance(result, dict)
    self.assertEqual(result, dict(
                     name=dict(required=True),
                     rest_api_id=dict(required=True),
                     state=dict(default='present', choices=['present', 'absent'])
    ))


  @patch.object(apigw_resource, 'AnsibleModule')
  @patch.object(apigw_resource, 'ApiGwResource')
  def test_main(self, mock_ApiGwResource, mock_AnsibleModule):
    mock_ApiGwResource_instance      = mock.MagicMock()
    mock_AnsibleModule_instance     = mock.MagicMock()
    mock_ApiGwResource.return_value  = mock_ApiGwResource_instance
    mock_AnsibleModule.return_value = mock_AnsibleModule_instance

    apigw_resource.main()

    mock_ApiGwResource.assert_called_once_with(mock_AnsibleModule_instance)
    assert mock_ApiGwResource_instance.process_request.call_count == 1


if __name__ == '__main__':
    unittest.main()

###
# NOTES:
#   Step the First: Instantiate two dictionaries:
#     - Dictionary 1 is keyed by path parts and contains all results
#     - Dictionary 2 is keyed by resource id and contains a flag for children present (tree?)
#   For Create:
#     - There is no auto-vivification
#     - The entire resource must be split by forward slash, and you must walk
#       the map to discover the highest-level parent
#     - Now iterate and create each level as needed
#   For delete:
#     - You *can* delete from the root (don't know about methods yet), but it kills everything
#     - Discover last entry without children, then delete this resource
#
