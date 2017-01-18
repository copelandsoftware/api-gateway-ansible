#!/usr/bin/python
# TODO: License goes here

import library.apigw_method as apigw_method
from library.apigw_method import ApiGwMethod, InvalidInputError
import mock
from mock import patch
from mock import create_autospec
from mock import ANY
import unittest
import boto
from botocore.exceptions import BotoCoreError, ClientError
import copy

def merge(a, b):
  for key in b:
    if key in a:
      if isinstance(a[key], dict) and isinstance(b[key], dict):
        merge(a[key], b[key])
      else:
        a[key] = b[key]
    else:
      a[key] = b[key]

  return a

def purge(a, keys):
  for key in keys:
    parts = key.split('.')
    k = parts[0]
    newkey = ".".join(parts[1:])
    if newkey:
      purge(a[k], [newkey])
    else:
      a.pop(key, None)

  return a

def mock_args(*args, **kwargs):
  return {'mock': 'args'}

class TestApiGwMethod(unittest.TestCase):

  def setUp(self):
    self.module = mock.MagicMock()
    self.module.check_mode = False
    self.module.exit_json = mock.MagicMock()
    self.module.fail_json = mock.MagicMock()
    self.method  = ApiGwMethod(self.module)
    self.method.client = mock.MagicMock()
    self.method.client.get_method = mock.MagicMock()
    self.method.client.put_method = mock.MagicMock()
    self.method.client.put_method_response = mock.MagicMock()
    self.method.client.put_integration = mock.MagicMock()
    self.method.client.put_integration_response = mock.MagicMock()
    self.method.module.params = {
      'rest_api_id': 'restid',
      'resource_id': 'rsrcid',
      'name': 'GET',
      'authorization_type': 'NONE',
      'api_key_required': False,
      'request_params': [],
      'method_integration': {'integration_type': 'value'},
      'method_responses': [],
      'state': 'present'
    }
    reload(apigw_method)

### boto3 tests
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
### end boto3 tests


### Find tests
  @patch.object(ApiGwMethod, '_update_method', return_value=[None, None])
  @patch.object(ApiGwMethod, '_create_method', return_value=[None, None])
  def test_process_request_gets_method_on_invocation(self, mock_create, mock_update):
    self.method.client.get_method=mock.MagicMock(return_value='response')
    self.method.process_request()

    self.method.client.get_method.assert_called_once_with(
        restApiId='restid',
        resourceId='rsrcid',
        httpMethod='GET'
    )
    self.assertEqual('response', self.method.method)

  @patch.object(ApiGwMethod, '_create_method', return_value=[None, None])
  def test_process_request_sets_method_result_to_None_when_get_method_throws_not_found(self, mock_create):
    self.method.client.get_method=mock.MagicMock(
        side_effect=ClientError({'Error': {'Code': 'x NotFoundException x'}}, 'xxx'))
    self.method.process_request()

    self.method.client.get_method.assert_called_once_with(
        restApiId='restid',
        resourceId='rsrcid',
        httpMethod='GET'
    )
    self.assertIsNone(self.method.method)

  @patch.object(ApiGwMethod, '_create_method', return_value=[None, None])
  def test_process_request_calls_fail_json_when_ClientError_is_not_NotFoundException(self, mock_create):
    self.method.client.get_method=mock.MagicMock(
        side_effect=ClientError({'Error': {'Code': 'boom', 'Message': 'error'}}, 'xxx'))
    self.method.process_request()

    self.method.client.get_method.assert_called_once_with(
        restApiId='restid',
        resourceId='rsrcid',
        httpMethod='GET'
    )
    self.method.module.fail_json.assert_called_once_with(msg='Error calling boto3 get_method: An error occurred (boom) when calling the xxx operation: error')

  @patch.object(ApiGwMethod, '_create_method', return_value=[None, None])
  def test_process_request_calls_fail_json_when_get_method_throws_other_boto_core_error(self, mock_create):
    self.method.client.get_method=mock.MagicMock(side_effect=BotoCoreError())
    self.method.process_request()

    self.method.client.get_method.assert_called_once_with(
        restApiId='restid',
        resourceId='rsrcid',
        httpMethod='GET'
    )
    self.method.module.fail_json.assert_called_once_with(msg='Error calling boto3 get_method: An unspecified error occurred')
### End find teste

### Delete tests
  @patch.object(ApiGwMethod, '_find_method', return_value=True)
  def test_process_request_deletes_method_when_method_is_present(self, mock_find):
    self.method.client.delete_method = mock.MagicMock()
    self.method.module.params['state'] = 'absent'
    self.method.process_request()
    self.method.client.delete_method.assert_called_once_with(
        restApiId='restid',
        resourceId='rsrcid',
        httpMethod='GET'
    )
    self.method.module.exit_json.assert_called_once_with(changed=True, method=None)

  @patch.object(ApiGwMethod, '_find_method', return_value=True)
  def test_process_skips_delete_and_returns_true_when_check_mode_enabled_and_method_exists(self, mock_find):
    self.method.client.delete_method = mock.MagicMock()
    self.method.module.params['state'] = 'absent'
    self.method.module.check_mode = True
    self.method.process_request()
    self.assertEqual(0, self.method.client.delete_method.call_count)
    self.method.module.exit_json.assert_called_once_with(changed=True, method=None)

  @patch.object(ApiGwMethod, '_find_method', return_value=True)
  def test_process_request_calls_fail_json_when_delete_method_throws_error(self, mock_find):
    self.method.client.delete_method = mock.MagicMock(side_effect=BotoCoreError())
    self.method.module.params['state'] = 'absent'
    self.method.process_request()
    self.method.client.delete_method.assert_called_once_with(
        restApiId='restid',
        resourceId='rsrcid',
        httpMethod='GET'
    )
    self.method.module.fail_json.assert_called_once_with(
        msg='Error calling boto3 delete_method: An unspecified error occurred')

  @patch.object(ApiGwMethod, '_find_method', return_value=None)
  def test_process_request_skips_delete_when_method_is_absent(self, mock_find):
    self.method.client.delete_method = mock.MagicMock()
    self.method.module.params['state'] = 'absent'
    self.method.process_request()
    self.assertEqual(0, self.method.client.delete_method.call_count)
    self.method.module.exit_json.assert_called_once_with(changed=False, method=None)
### End delete

### Update
  @patch('library.apigw_method.put_integration', mock_args)
  @patch.object(ApiGwMethod, 'validate_params')
  @patch.object(ApiGwMethod, '_find_method')
  def test_process_request_calls_update_method_when_present_and_changed(self, mock_find, mock_vp):
    mock_find.return_value = {
      'apiKeyRequired': False,
      'authorizationType': 'NONE',
      'httpMethod': 'GET',
      'requestParameters': {'method.request.querystring.qs_test': False, 'method.request.header.frank': True}
    }

    self.method.module.params = {
      'rest_api_id': 'restid',
      'resource_id': 'rsrcid',
      'name': 'GET',
      'api_key_required': True,
      'request_params': [
        {'name': 'bob', 'location': 'path', 'param_required': True},
        {'name': 'frank', 'location': 'header', 'param_required': False},
      ],
      'state': 'present'
    }

    expected_patch_ops = [
      {'op': 'replace', 'path': '/apiKeyRequired', 'value': 'True'},
      {'op': 'remove', 'path': '/authorizationType'},
      {'op': 'add', 'path': '/requestParameters/method.request.path.bob', 'value': 'True'},
      {'op': 'remove', 'path': '/requestParameters/method.request.querystring.qs_test'},
      {'op': 'replace', 'path': '/requestParameters/method.request.header.frank', 'value': 'False'},
    ]

    self.method.process_request()

    self.method.client.update_method.assert_called_once_with(
      restApiId='restid',
      resourceId='rsrcid',
      httpMethod='GET',
      patchOperations=mock.ANY
    )
    self.assertItemsEqual(expected_patch_ops, self.method.client.update_method.call_args[1]['patchOperations'])

  @patch('library.apigw_method.put_integration', mock_args)
  @patch.object(ApiGwMethod, 'validate_params')
  @patch.object(ApiGwMethod, '_find_method', return_value={})
  def test_process_request_skips_update_and_returns_true_when_check_mode_set(self, mock_find, mock_vp):
    mock_find.return_value = {
      'apiKeyRequired': False,
      'authorizationType': 'NONE',
      'httpMethod': 'GET',
      'requestParameters': {},
      'methodIntegration': {}
    }

    self.method.module.params = {
      'rest_api_id': 'restid',
      'resource_id': 'rsrcid',
      'name': 'GET',
      'api_key_required': True,
      'authorizer_id': 'authid',
      'method_responses': [{'status_code': 202}],
      'integration_responses': [
        {'status_code': 202, 'is_default': True}
      ],
      'state': 'present'
    }
    self.method.module.check_mode = True
    self.method.process_request()

    self.assertEqual(0, self.method.client.update_method.call_count)
    self.assertEqual(0, self.method.client.put_integration.call_count)
    self.assertEqual(0, self.method.client.update_integration.call_count)
    self.assertEqual(0, self.method.client.put_method_response.call_count)
    self.assertEqual(0, self.method.client.update_method_response.call_count)
    self.assertEqual(0, self.method.client.delete_method_response.call_count)
    self.assertEqual(0, self.method.client.put_integration_response.call_count)
    self.assertEqual(0, self.method.client.update_integration_response.call_count)
    self.assertEqual(0, self.method.client.delete_integration_response.call_count)
    self.method.module.exit_json(changed=True, method=None)

  @patch('library.apigw_method.update_method', mock_args)
  @patch.object(ApiGwMethod, 'validate_params')
  @patch.object(ApiGwMethod, '_find_method', return_value={})
  def test_process_request_calls_fail_json_when_update_method_raises_exception(self, mock_find, mock_vp):
    self.method.client.update_method = mock.MagicMock(side_effect=BotoCoreError())
    self.method.process_request()

    self.method.client.update_method.assert_called_once_with(mock="args")
    self.method.module.fail_json(
        msg='Error while updating method via boto3: An unspecified error occurred')

  @patch.object(ApiGwMethod, 'validate_params')
  @patch.object(ApiGwMethod, '_find_method')
  def test_process_request_calls_update_integration_when_present_and_changed(self, mock_find, mock_vp):
    mock_find.return_value = {
      'methodIntegration': {
        'type': 'wrong',
        'httpMethod': 'POST',
        'uri': 'less-magical-uri',
        'passthroughBehavior': 'when_no_templates',
        'credentials': 'existing creds',
        'requestParameters': {'integration.request.path.bob': 'not-sure'},
        'cacheNamespace': '',
        'cacheKeyParameters': [u'ckp1', u'ckp2'],
        'requestTemplates': {
          'deleteme': 'whatevs',
          'change/me': 'totally different value',
        }
      }
    }

    self.method.module.params = {
      'rest_api_id': 'restid',
      'resource_id': 'rsrcid',
      'name': 'GET',
      'method_integration': {
        'integration_type': 'aws',
        'http_method': 'POST',
        'uri': 'magical-uri',
        'credentials': 'new creds',
        'passthrough_behavior': 'when_no_templates',
        'request_templates': [
          {'content_type': 'addme', 'template': 'addval'},
          {'content_type': 'change/me', 'template': 'changeval'},
        ],
        'uses_caching': True,
        'cache_namespace': 'cn',
        'cache_key_parameters': ['ckp2', 'ckp1'],
        'integration_params': [
          {'name': 'bob', 'location': 'path', 'value': 'sure'},
        ],
      },
      'state': 'present'
    }

    expected_patch_ops = [
      {'op': 'replace', 'path': '/type', 'value': 'aws'},
      {'op': 'replace', 'path': '/uri', 'value': 'magical-uri'},
      {'op': 'replace', 'path': '/cacheNamespace', 'value': 'cn'},
      {'op': 'replace', 'path': '/credentials', 'value': 'new creds'},
      {'op': 'replace', 'path': '/requestParameters/integration.request.path.bob', 'value': 'sure'},
      {'op': 'add', 'path': '/requestTemplates/addme', 'value': 'addval'},
      {'op': 'remove', 'path': '/requestTemplates/deleteme'},
      {'op': 'replace', 'path': '/requestTemplates/change~1me', 'value': 'changeval'},
    ]

    self.method.process_request()

    self.method.client.update_integration.assert_called_once_with(
      restApiId='restid',
      resourceId='rsrcid',
      httpMethod='GET',
      patchOperations=mock.ANY
    )
    self.assertItemsEqual(expected_patch_ops, self.method.client.update_integration.call_args[1]['patchOperations'])

  @patch.object(ApiGwMethod, 'validate_params')
  @patch.object(ApiGwMethod, '_find_method')
  def test_process_request_calls_skips_patching_http_method_and_uri_when_type_not_AWS(self, mock_find, mock_vp):
    mock_find.return_value = {
      'methodIntegration': {
        'type': 'XXX',
        'httpMethod': 'POST',
        'uri': 'magical-uri',
        'passthroughBehavior': 'when_no_templates',
        'requestParameters': {},
        'requestTemplates': {}
      }
    }

    self.method.module.params = {
      'rest_api_id': 'restid',
      'resource_id': 'rsrcid',
      'name': 'GET',
      'method_integration': {
        'integration_type': 'XXX',
        'http_method': 'totally different',
        'uri': 'also totally different',
        'passthrough_behavior': 'when_no_templates',
        'request_templates': [],
        'uses_caching': False,
        'integration_params': [],
      },
      'state': 'present'
    }

    self.method.process_request()

    self.assertEqual(0, self.method.client.update_integration.call_count)

  @patch.object(ApiGwMethod, 'validate_params')
  @patch.object(ApiGwMethod, '_find_method')
  def test_process_request_calls_skips_patching_inherited_cache_values_when_not_using_cache(self, mock_find, mock_vp):
    mock_find.return_value = {
      'methodIntegration': {
        'type': 'XXX',
        'httpMethod': 'POST',
        'uri': 'magical-uri',
        'passthroughBehavior': 'when_no_templates',
        'requestParameters': {},
        'cacheNamespace': 'stupid inherited cache namespace',
        'cacheKeyParameters': [],
        'requestTemplates': {}
      }
    }

    self.method.module.params = {
      'rest_api_id': 'restid',
      'resource_id': 'rsrcid',
      'name': 'GET',
      'method_integration': {
        'integration_type': 'XXX',
        'http_method': 'POST',
        'uri': 'magical-uri',
        'passthrough_behavior': 'when_no_templates',
        'request_templates': [],
        'uses_caching': False,
        'integration_params': [],
      },
      'state': 'present'
    }

    self.method.process_request()

    self.assertEqual(0, self.method.client.update_integration.call_count)

  @patch.object(ApiGwMethod, 'validate_params')
  @patch.object(ApiGwMethod, '_find_method', return_value={'something': 'here'})
  def test_process_request_calls_put_integration_when_method_exists_but_integration_does_not(self, mock_find, mock_vp):
    self.method.module.params = {
      'rest_api_id': 'restid',
      'resource_id': 'rsrcid',
      'name': 'GET',
      'method_integration': {
        'integration_type': 'AWS',
        'http_method': 'POST',
        'uri': 'magical-uri',
        'passthrough_behavior': 'when_no_templates',
        'request_templates': [
          {'content_type': 'addme', 'template': 'addval'},
          {'content_type': 'change/me', 'template': 'changeval'},
        ],
        'cache_namespace': 'cn',
        'cache_key_parameters': [],
        'integration_params': [
          {'name': 'bob', 'location': 'path', 'value': 'sure'},
        ],
      },
      'state': 'present'
    }

    expected = dict(
      restApiId='restid',
      resourceId='rsrcid',
      httpMethod='GET',
      type='AWS',
      integrationHttpMethod='POST',
      uri='magical-uri',
      requestParameters={
        'integration.request.path.bob': 'sure',
      },
      requestTemplates={'addme': 'addval', 'change/me': 'changeval'},
      passthroughBehavior='when_no_templates',
      cacheNamespace='cn',
      cacheKeyParameters=[]
    )

    self.method.process_request()

    self.method.client.put_integration.assert_called_once_with(**expected)

  @patch('library.apigw_method.update_method', mock_args)
  @patch.object(ApiGwMethod, 'validate_params')
  @patch.object(ApiGwMethod, '_find_method', return_value={})
  def test_process_request_calls_fail_json_when_update_integration_raises_exception(self, mock_find, mock_vp):
    self.method.client.update_integration = mock.MagicMock(side_effect=BotoCoreError())
    self.method.process_request()

    self.method.client.update_method.assert_called_once_with(mock="args")
    self.method.module.fail_json(
        msg='Error while updating method via boto3: An unspecified error occurred')

  @patch('library.apigw_method.put_integration', mock_args)
  @patch.object(ApiGwMethod, 'validate_params')
  @patch.object(ApiGwMethod, '_find_method')
  def test_process_request_updates_method_responses_when_present_and_changed(self, mock_find, mock_vp):
    mock_find.return_value = {
      'methodResponses': {
        '202': {'statusCode': '202', 'responseModels': {'application/json': 'Empty', 'delete': 'me'}},
        '400': {'statusCode': '400'},
        '404': {'statusCode': '404'}
      }
    }

    self.method.module.params = {
      'rest_api_id': 'restid',
      'resource_id': 'rsrcid',
      'name': 'GET',
      'method_responses': [
        {'status_code': 202,
          'response_models': [
            {'content_type': 'application/json', 'model': 'Error'},
            {'content_type': 'add', 'model': 'me'}
        ]},
        {'status_code': 400},
        {'status_code': 500},
      ],
      'state': 'present'
    }

    expected_patch_ops = [
      {'op': 'replace', 'path': '/responseModels/application~1json', 'value': 'Error'},
      {'op': 'add', 'path': '/responseModels/add', 'value': 'me'},
      {'op': 'remove', 'path': '/responseModels/delete'},
    ]

    self.method.process_request()

    self.method.client.update_method_response.assert_called_once_with(
      restApiId='restid',
      resourceId='rsrcid',
      httpMethod='GET',
      statusCode='202',
      patchOperations=mock.ANY
    )
    self.assertItemsEqual(expected_patch_ops, self.method.client.update_method_response.call_args[1]['patchOperations'])
    self.method.client.put_method_response.assert_called_once_with(
      restApiId='restid',
      resourceId='rsrcid',
      httpMethod='GET',
      statusCode='500',
      responseModels={}
    )
    self.method.client.delete_method_response.assert_called_once_with(
      restApiId='restid',
      resourceId='rsrcid',
      httpMethod='GET',
      statusCode='404'
    )

  @patch('library.apigw_method.put_integration', mock_args)
  @patch.object(ApiGwMethod, 'validate_params')
  @patch.object(ApiGwMethod, '_find_method', return_value={'some': 'thing'})
  def test_process_request_calls_put_method_response_when_method_exists_without_methodResponses(self, mock_find, mock_vp):
    self.method.module.params = {
      'rest_api_id': 'restid',
      'resource_id': 'rsrcid',
      'name': 'GET',
      'method_responses': [
        {'status_code': 202, 'response_models': [ {'content_type': 'application/json', 'model': 'Error'}, ]},
      ],
      'state': 'present'
    }

    self.method.process_request()

    self.assertEqual(0, self.method.client.update_method_response.call_count)
    self.assertEqual(0, self.method.client.delete_method_response.call_count)
    self.method.client.put_method_response.assert_called_once_with(
      restApiId='restid',
      resourceId='rsrcid',
      httpMethod='GET',
      statusCode='202',
      responseModels={'application/json': 'Error'}
    )

  @patch.object(ApiGwMethod, 'validate_params')
  @patch.object(ApiGwMethod, '_find_method')
  def test_process_request_updates_method_integrations_when_present_and_changed(self, mock_find, mock_vp):
    mock_find.return_value = {
      'methodIntegration': {
        'integrationResponses': {
          '202': {
            'statusCode': '202',
            'responseTemplates': {'application/json': 'orig-value', 'delete': 'me'},
            'responseParameters': {'also-delete': 'me', 'method.response.header.change': 'me'}
          },
          '400': {'statusCode': '400', 'selectionPattern': '.*Bad.*'},
          '404': {'statusCode': '404', 'selectionPattern': '.*Not Found.*'}
        }
      }
    }

    self.method.module.params = {
      'rest_api_id': 'restid',
      'resource_id': 'rsrcid',
      'name': 'GET',
      'integration_responses': [
        {'status_code': 202,
          'pattern': 'totally-invalid-but-whatever',
          'response_templates': [
            {'content_type': 'application/json', 'template': 'new-value'},
            {'content_type': 'add', 'template': 'me'}
          ],
          'response_params': [
            {'name': 'addme', 'location': 'body', 'value': 'bodyval'},
            {'name': 'change', 'location': 'header', 'value': 'newval'},
          ],
        },
        {'status_code': 400, 'pattern': '.*Bad.*'},
        {'status_code': 500, 'pattern': '.*Unknown.*'},
      ],
      'state': 'present'
    }

    expected_patch_ops = [
      {'op': 'replace', 'path': '/selectionPattern', 'value': 'totally-invalid-but-whatever'},
      {'op': 'replace', 'path': '/responseTemplates/application~1json', 'value': 'new-value'},
      {'op': 'add', 'path': '/responseTemplates/add', 'value': 'me'},
      {'op': 'remove', 'path': '/responseTemplates/delete'},
      {'op': 'replace', 'path': '/responseParameters/method.response.header.change', 'value': 'newval'},
      {'op': 'add', 'path': '/responseParameters/method.response.body.addme', 'value': 'bodyval'},
      {'op': 'remove', 'path': '/responseParameters/also-delete'},
    ]

    self.method.process_request()

    self.method.client.update_integration_response.assert_called_once_with(
      restApiId='restid',
      resourceId='rsrcid',
      httpMethod='GET',
      statusCode='202',
      patchOperations=mock.ANY
    )
    self.assertItemsEqual(
      expected_patch_ops,
      self.method.client.update_integration_response.call_args[1]['patchOperations']
    )
    self.method.client.put_integration_response.assert_called_once_with(
      restApiId='restid',
      resourceId='rsrcid',
      httpMethod='GET',
      statusCode='500',
      selectionPattern='.*Unknown.*',
      responseParameters={},
      responseTemplates={}
    )
    self.method.client.delete_integration_response.assert_called_once_with(
      restApiId='restid',
      resourceId='rsrcid',
      httpMethod='GET',
      statusCode='404'
    )

  @patch.object(ApiGwMethod, 'validate_params')
  @patch.object(ApiGwMethod, '_find_method')
  def test_process_request_calls_put_integration_response_when_method_is_present_but_missing_integrationResponses(self, mock_find, mock_vp):
    mock_find.return_value = {
      'methodIntegration': {}
    }

    self.method.module.params = {
      'rest_api_id': 'restid',
      'resource_id': 'rsrcid',
      'name': 'GET',
      'integration_responses': [
        {'status_code': 1234, 'pattern': '.*Bad.*'},
      ],
      'state': 'present'
    }

    self.method.process_request()

    self.assertEqual(0, self.method.client.update_integration_response.call_count)
    self.assertEqual(0, self.method.client.delete_integration_response.call_count)
    self.method.client.put_integration_response.assert_called_once_with(
      restApiId='restid',
      resourceId='rsrcid',
      httpMethod='GET',
      statusCode='1234',
      selectionPattern='.*Bad.*',
      responseParameters={},
      responseTemplates={}
    )

  @patch.object(ApiGwMethod, '_find_method', side_effect=[None, 'Called post-update'])
  def test_process_request_calls_get_method_and_returns_result_after_update_when_method_is_up_to_date(self, mock_find):
    initial_find = {
      'apiKeyRequired': False,
      'authorizationType': 'NONE',
      'httpMethod': 'GET',
      'requestParameters': {},
      'methodResponses': {'24601': {'statusCode': '24601'}},
      'methodIntegration': {
        'type': 'XXX',
        'httpMethod': 'POST',
        'uri': 'this-is-uri',
        'passthroughBehavior': 'WHEN_NO_TEMPLATES',
        'requestParameters': {},
        'requestTemplates': {},
        'integrationResponses': {'24601': {'statusCode': '24601', 'selectionPattern': 'pattern'}},
      }
    }

    self.method.module.params = {
      'rest_api_id': 'restid',
      'resource_id': 'rsrcid',
      'name': 'GET',
      'authorization_type': 'NONE',
      'api_key_required': False,
      'request_params': [],
      'method_integration': {
        'integration_type': 'XXX',
        'http_method': 'POST',
        'uri': 'this-is-uri',
        'passthrough_behavior': 'when_no_templates',
      },
      'method_responses': [{'status_code': 24601}],
      'integration_responses': [{'status_code': 24601, 'pattern': 'pattern'}],
      'state': 'present'
    }

    mock_find.side_effect = [initial_find, 'Called post-update']

    self.method.process_request()

    self.assertEqual(0, self.method.client.update_method.call_count)
    self.assertEqual(0, self.method.client.put_integration.call_count)
    self.assertEqual(0, self.method.client.update_integration.call_count)
    self.assertEqual(0, self.method.client.put_method_response.call_count)
    self.assertEqual(0, self.method.client.update_method_response.call_count)
    self.assertEqual(0, self.method.client.delete_method_response.call_count)
    self.assertEqual(0, self.method.client.put_integration_response.call_count)
    self.assertEqual(0, self.method.client.update_integration_response.call_count)
    self.assertEqual(0, self.method.client.delete_integration_response.call_count)

    self.method.module.exit_json.assert_called_once_with(changed=False, method='Called post-update')

### End update

### Create tests
  @patch.object(ApiGwMethod, '_find_method', side_effect=[None, 'Called post-create'])
  def test_process_request_calls_get_method_and_returns_result_after_create_when_method_is_absent(self, mock_find):

    self.method.process_request()

    self.method.module.exit_json.assert_called_once_with(changed=True, method='Called post-create')

  @patch.object(ApiGwMethod, '_find_method', return_value=None)
  def test_process_request_calls_put_method_when_method_is_absent(self, mock_find):
    self.method.module.params['api_key_required'] = True
    self.method.module.params['request_params'] = [{
      'name': 'qs_param',
      'param_required': False,
      'location': 'querystring'
    },{
      'name': 'path_param',
      'param_required': True,
      'location': 'path'
    },{
      'name': 'header_param',
      'param_required': True,
      'location': 'header'
    }]
    request_params = {
      'method.request.querystring.qs_param': False,
      'method.request.path.path_param': True,
      'method.request.header.header_param': True
    }

    self.method.process_request()

    self.method.client.put_method.assert_called_once_with(
        restApiId='restid',
        resourceId='rsrcid',
        httpMethod='GET',
        authorizationType='NONE',
        apiKeyRequired=True,
        requestParameters=request_params
    )

  @patch.object(ApiGwMethod, '_find_method', return_value=None)
  def test_process_request_calls_put_integration_when_method_is_absent(self, mock_find):
    p = {
      'integration_type': 'AWS',
      'http_method': 'POST',
      'uri': 'valid_uri',
      'credentials': 'creds',
      'passthrough_behavior': 'ptb',
      'request_templates': [{'content_type': 'application/json', 'template': '{}'}],
      'cache_namespace': 'cn',
      'cache_key_parameters': ['param1', 'param2'],
      'integration_params': [
        {'name': 'qs_param', 'value': 'qsval', 'location': 'querystring'},
        {'name': 'path_param', 'value': 'pathval', 'location': 'path'},
        {'name': 'header_param', 'value': 'headerval', 'location': 'header'}
      ]
    }
    self.method.module.params['method_integration'] = p;
    expected = dict(
      restApiId='restid',
      resourceId='rsrcid',
      httpMethod='GET',
      type='AWS',
      integrationHttpMethod='POST',
      uri='valid_uri',
      credentials='creds',
      requestParameters={
        'integration.request.querystring.qs_param': 'qsval',
        'integration.request.path.path_param': 'pathval',
        'integration.request.header.header_param': 'headerval'
      },
      requestTemplates={'application/json': '{}'},
      passthroughBehavior='ptb',
      cacheNamespace='cn',
      cacheKeyParameters=['param1', 'param2']
    )

    self.method.process_request()

    self.method.client.put_integration.assert_called_once_with(**expected)

  @patch.object(ApiGwMethod, '_find_method', return_value=None)
  def test_process_request_calls_put_method_response_when_method_is_absent(self, mock_find):
    p = [
        {'status_code': 200, 'response_models': [{'content_type': 'ct1', 'model': 'model'},{'content_type': 'ct2'}]},
        {'status_code': 400},
        {'status_code': 500}
    ]
    self.method.module.params['method_responses'] = p;
    expected = [
      dict(
        restApiId='restid', resourceId='rsrcid', httpMethod='GET',
        statusCode='200', responseModels={'ct1': 'model', 'ct2': 'Empty'}
      ),
      dict(restApiId='restid', resourceId='rsrcid', httpMethod='GET', statusCode='400', responseModels={}),
      dict(restApiId='restid', resourceId='rsrcid', httpMethod='GET', statusCode='500', responseModels={})
    ]

    self.method.process_request()

    self.assertEqual(3, self.method.client.put_method_response.call_count)
    for kwargs in expected:
      self.method.client.put_method_response.assert_any_call(**kwargs)

  @patch.object(ApiGwMethod, '_find_method', return_value=None)
  def test_process_request_calls_put_integration_response_when_method_is_absent(self, mock_find):
    p = [
        {
          'status_code': 200,
          'is_default': True,
        },
        {
          'status_code': 400,
          'is_default': False,
          'pattern': '.*Bad Request.*',
          'response_params': [
            {'name': 'body_param', 'value': 'json-expression', 'location': 'body'},
            {'name': 'header_param', 'value': 'headerval', 'location': 'header'}
          ],
          'response_templates': [{'content_type': 'application/json', 'template': '{}'}]
        },
    ]
    self.method.module.params['integration_responses'] = p;
    expected = [
      dict(
        restApiId='restid',
        resourceId='rsrcid',
        httpMethod='GET',
        statusCode='200',
        selectionPattern='',
        responseParameters={},
        responseTemplates={}
      ),
      dict(
        restApiId='restid',
        resourceId='rsrcid',
        httpMethod='GET',
        statusCode='400',
        selectionPattern='.*Bad Request.*',
        responseParameters={
          'method.response.body.body_param': 'json-expression',
          'method.response.header.header_param': 'headerval'
        },
        responseTemplates={'application/json': '{}'}
      ),
    ]

    self.method.process_request()

    self.assertEqual(2, self.method.client.put_integration_response.call_count)
    for kwargs in expected:
      self.method.client.put_integration_response.assert_any_call(**kwargs)

  @patch.object(ApiGwMethod, '_find_method', return_value=None)
  def test_process_request_calls_fail_json_when_put_method_throws_error(self, mock_find):
    self.method.client.put_method = mock.MagicMock(side_effect=BotoCoreError())
    self.method.process_request()
    self.method.client.put_method.assert_called_once_with(
        restApiId='restid',
        resourceId='rsrcid',
        httpMethod='GET',
        authorizationType='NONE',
        apiKeyRequired=False,
        requestParameters={}
    )
    self.method.module.fail_json.assert_called_once_with(
        msg='Error while creating method via boto3: An unspecified error occurred')

  @patch.object(ApiGwMethod, '_find_method', return_value=None)
  def test_process_request_calls_fail_json_when_put_integration_throws_error(self, mock_find):
    self.method.client.put_integration = mock.MagicMock(side_effect=BotoCoreError())
    self.method.process_request()
    self.method.client.put_integration.assert_called_once_with(
        restApiId='restid',
        resourceId='rsrcid',
        httpMethod='GET',
        type='value',
        requestParameters={},
        requestTemplates={}
    )
    self.method.module.fail_json.assert_called_once_with(
        msg='Error while creating method via boto3: An unspecified error occurred')

  @patch.object(ApiGwMethod, '_find_method', return_value=None)
  def test_process_request_calls_fail_json_when_put_method_response_throws_error(self, mock_find):
    self.method.client.put_method_response = mock.MagicMock(side_effect=BotoCoreError())
    self.method.module.params['method_responses'] = [{'status_code': 200}]
    self.method.process_request()
    self.method.client.put_method_response.assert_called_once_with(
        restApiId='restid',
        resourceId='rsrcid',
        httpMethod='GET',
        statusCode='200',
        responseModels={}
    )
    self.method.module.fail_json.assert_called_once_with(
        msg='Error while creating method via boto3: An unspecified error occurred')

  @patch.object(ApiGwMethod, '_find_method', return_value=None)
  def test_process_request_calls_fail_json_when_put_integration_response_throws_error(self, mock_find):
    self.method.client.put_integration_response = mock.MagicMock(side_effect=BotoCoreError())
    self.method.module.params['integration_responses'] = [{'status_code': 200, 'is_default': True}]
    self.method.process_request()
    self.method.client.put_integration_response.assert_called_once_with(
        restApiId='restid',
        resourceId='rsrcid',
        httpMethod='GET',
        statusCode='200',
        selectionPattern='',
        responseParameters={},
        responseTemplates={}
    )
    self.method.module.fail_json.assert_called_once_with(
        msg='Error while creating method via boto3: An unspecified error occurred')

  @patch.object(ApiGwMethod, '_find_method', return_value=None)
  def test_process_request_skips_create_and_returns_true_when_method_is_absent_and_check_mode_set(self, mock_find):
    self.method.module.check_mode = True
    self.method.process_request()
    self.assertEqual(0, self.method.client.put_method.call_count)
    self.assertEqual(0, self.method.client.put_integration.call_count)
    self.method.module.exit_json.assert_called_once_with(changed=True, method=None)


### End create


### Gauntlet of validation
  # This 'test' is a facility to allow testing of all validation scenarios.  This
  # probably isn't the best of practices, but it gives us a one-stop shop for capturing
  # tests of all of the conditional requirements of the various boto method invocations.
  #
  # This is not meant to test that ansible enforces the various conditions in the
  # argument spec and instead tests errors arising from illegal combinations of
  # parameters (as per the boto3 apigateway docs)
  def test_validation_of_arguments(self):
    # A complete and valid param list
    params = {
      'rest_api_id': 'restid',
      'resource_id': 'rsrcid',
      'name': 'GET',
      'authorization_type': 'NONE',
      'api_key_required': False,
      'request_params': [{'name': 'reqparm', 'location': 'header', 'param_required': True}],
      'method_integration': {
        'integration_type': 'AWS',
        'http_method': 'POST',
        'uri': 'this.is.a.uri',
        'passthrough_behavior': 'when_no_templates',
        'request_templates': [{
          'content_type': 'application/json',
          'template': '{"key": "value"}'
        }],
        'integration_params': [{'name': 'intparam', 'location': 'querystring', 'value': 'yes'}]
      },
      'method_responses': [{
        'status_code': '200',
        'response_models': [{'content_type': 'application/json', 'model': 'Empty'}],
      }],
      'integration_responses': [{
        'status_code': '200',
        'is_default': False,
        'pattern': '.*whatever.*',
        'response_params': [{'name': 'irparam', 'location': 'path', 'value': 'sure'}],
        'response_templates': [{'content_type': 'application/xml', 'template': 'xml stuff'}]
      }],
      'state': 'present',
    }

    # Changes needed to invoke an exception
    tests = [
        {
          'changes': {'authorization_type': 'CUSTOM'},
          'delete_keys': [],
          'error': {
            'param': 'authorizer_id',
            'msg': "authorizer_id must be provided when authorization_type is 'CUSTOM'"
          }
        },
        {
          'changes': {},
          'delete_keys': ['method_integration.http_method'],
          'error': {
            'param': 'method_integration',
            'msg': "http_method must be provided when integration_type is 'AWS', 'AWS_PROXY', or 'HTTP'"
          }
        },
        {
          'changes': {'method_integration': {'integration_type': 'HTTP'}},
          'delete_keys': ['method_integration.http_method'],
          'error': {
            'param': 'method_integration',
            'msg': "http_method must be provided when integration_type is 'AWS', 'AWS_PROXY', or 'HTTP'"
          }
        },
        {
          'changes': {'method_integration': {'integration_type': 'AWS_PROXY'}},
          'delete_keys': ['method_integration.http_method'],
          'error': {
            'param': 'method_integration',
            'msg': "http_method must be provided when integration_type is 'AWS', 'AWS_PROXY', or 'HTTP'"
          }
        },
        {
          'changes': {},
          'delete_keys': ['method_integration.uri'],
          'error': {
            'param': 'method_integration',
            'msg': "uri must be provided when integration_type is 'AWS', 'AWS_PROXY', or 'HTTP'"
          }
        },
        {
          'changes': {'method_integration': {'integration_type': 'HTTP'}},
          'delete_keys': ['method_integration.uri'],
          'error': {
            'param': 'method_integration',
            'msg': "uri must be provided when integration_type is 'AWS', 'AWS_PROXY', or 'HTTP'"
          }
        },
        {
          'changes': {'method_integration': {'integration_type': 'AWS_PROXY'}},
          'delete_keys': ['method_integration.uri'],
          'error': {
            'param': 'method_integration',
            'msg': "uri must be provided when integration_type is 'AWS', 'AWS_PROXY', or 'HTTP'"
          }
        },
        {
          'changes': {'integration_responses': [{'status_code': 'x', 'is_default': True, 'pattern': 'xxx'}]},
          'delete_keys': [],
          'error': {
            'param': 'integration_responses',
            'msg': "'pattern' must not be provided when 'is_default' is True"
          }
        },
        {
          'changes': {'integration_responses': [{'status_code': 'x', 'is_default': False}]},
          'delete_keys': [],
          'error': {
            'param': 'integration_responses',
            'msg': "'pattern' must be provided when 'is_default' is False"
          }
        },
        {
          'changes': {},
          'delete_keys': ['method_integration'],
          'error': {
            'param': 'method_integration',
            'msg': "'method_integration' must be provided when 'state' is present"
          }
        },
        {
          'changes': {},
          'delete_keys': ['method_responses'],
          'error': {
            'param': 'method_responses',
            'msg': "'method_responses' must be provided when 'state' is present"
          }
        },
        {
          'changes': {},
          'delete_keys': ['integration_responses'],
          'error': {
            'param': 'integration_responses',
            'msg': "'integration_responses' must be provided when 'state' is present"
          }
        },
    ]

    for test in tests:
      p = copy.deepcopy(params)
      p = merge(p, test['changes'])
      p = purge(p, test['delete_keys'])
      self.method.module.params = p
      try:
        self.method.validate_params()
        self.assertEqual("", test['error']['msg'])
      except apigw_method.InvalidInputError as e:
        self.assertEqual("Error validating {0}: {1}".format(test['error']['param'], test['error']['msg']), str(e))


### End validation


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
                     api_key_required=dict(required=False, type='bool', default=False),
                     request_params=dict(
                       type='list',
                       required=False,
                       default=[],
                       name=dict(required=True),
                       location=dict(required=True, choices=['querystring', 'path', 'header']),
                       param_required=dict(type='bool')
                     ),
                     method_integration=dict(
                       type='dict',
                       default={},
                       integration_type=dict(required=False, default='AWS', choices=['AWS', 'MOCK', 'HTTP', 'HTTP_PROXY', 'AWS_PROXY']),
                       http_method=dict(required=False, default='POST', choices=['POST', 'GET', 'PUT']),
                       uri=dict(required=False),
                       credentials=dict(required=False),
                       passthrough_behavior=dict(required=False, default='when_no_templates', choices=['when_no_templates', 'when_no_match', 'never']),
                       request_templates=dict(
                         required=False,
                         type='list',
                         default=[],
                         content_type=dict(required=True),
                         template=dict(required=True)
                       ),
                       uses_caching=dict(required=False, default=False, type='bool'),
                       cache_namespace=dict(required=False, default=''),
                       cache_key_parameters=dict(required=False, type='list', default=[]),
                       integration_params=dict(
                         type='list',
                         required=False,
                         default=[],
                         name=dict(required=True),
                         location=dict(required=True, choices=['querystring', 'path', 'header']),
                         value=dict(required=True)
                       )
                     ),
                     method_responses=dict(
                       type='list',
                       default=[],
                       status_code=dict(required=True),
                       response_models=dict(
                         type='list',
                         required=False,
                         default=[],
                         content_type=dict(required=True),
                         model=dict(required=False, default='Empty', choices=['Empty', 'Error'])
                       )
                     ),
                     integration_responses=dict(
                       type='list',
                       default=[],
                       status_code=dict(required=True),
                       is_default=dict(required=False, default=False, type='bool'),
                       pattern=dict(required=False),
                       response_params=dict(
                         type='list',
                         required=False,
                         default=[],
                         name=dict(required=True),
                         location=dict(required=True, choices=['body', 'header']),
                         value=dict(required=True)
                       ),
                       response_templates=dict(
                         required=False,
                         type='list',
                         default=[],
                         content_type=dict(required=True),
                         template=dict(required=True)
                       ),
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

