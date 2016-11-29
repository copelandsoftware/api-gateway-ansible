#!/usr/bin/python
# TODO: License goes here

import library.apigw_stage as apigw_stage
from library.apigw_stage import ApiGwStage
import mock
from mock import patch
from mock import create_autospec
from mock import ANY
import unittest
import boto
from botocore.exceptions import BotoCoreError, ClientError

class TestApiGwStage(unittest.TestCase):

  def setUp(self):
    self.module = mock.MagicMock()
    self.module.check_mode = False
    self.module.exit_json = mock.MagicMock()
    self.module.fail_json = mock.MagicMock()
    self.stage  = ApiGwStage(self.module)
    self.stage.client = mock.MagicMock()
    reload(apigw_stage)

  def test_boto_module_not_found(self):
    # Setup Mock Import Function
    import __builtin__ as builtins
    real_import = builtins.__import__

    def mock_import(name, *args):
      if name == 'boto': raise ImportError
      return real_import(name, *args)

    with mock.patch('__builtin__.__import__', side_effect=mock_import):
      reload(apigw_stage)
      ApiGwStage(self.module)

    self.module.fail_json.assert_called_with(msg='boto and boto3 are required for this module')

  def test_boto3_module_not_found(self):
    # Setup Mock Import Function
    import __builtin__ as builtins
    real_import = builtins.__import__

    def mock_import(name, *args):
      if name == 'boto3': raise ImportError
      return real_import(name, *args)

    with mock.patch('__builtin__.__import__', side_effect=mock_import):
      reload(apigw_stage)
      ApiGwStage(self.module)

    self.module.fail_json.assert_called_with(msg='boto and boto3 are required for this module')

  @patch.object(apigw_stage, 'boto3')
  def test_boto3_client_properly_instantiated(self, mock_boto):
    ApiGwStage(self.module)
    mock_boto.client.assert_called_once_with('apigateway')

  def test_define_argument_spec(self):
    result = ApiGwStage._define_module_argument_spec()
    self.assertIsInstance(result, dict)
    self.assertEqual(result, dict(
                     name=dict(required=True, aliases=['stage_name']),
                     rest_api_id=dict(required=True),
                     description=dict(required=False),
                     cache_cluster_enabled=dict(required=False, type='bool'),
                     cache_cluster_size=dict(required=False, choices=['0.5','1.6','6.1','13.5','28.4','58.2','118','237']),
                     method_settings=dict(
                       required=False,
                       type='list',
                       default=[],
                       method_name=dict(required=True),
                       method_verb=dict(required=True, choices=['GET','PUT','POST','DELETE','HEAD','OPTIONS','PATCH']),
                       caching_enabled=dict(required=False, default=False, type='bool')
                     ),
                     state=dict(required=False, default='present', choices=['absent', 'present'])
    ))

  def test_process_request_calls_exit_json_when_delete_succeeds(self):
    self.stage.module.params = {
      'rest_api_id': 'bob',
      'name': 'testme',
      'state': 'absent'
    }

    self.stage.process_request()

    self.stage.module.exit_json.assert_called_once_with(changed=True, stage=None)

  def test_process_request_calls_delete_stage_when_state_is_absent(self):
    self.stage.module.params = {
      'rest_api_id': 'bob',
      'name': 'testme',
      'state': 'absent'
    }

    self.stage.process_request()

    self.stage.client.delete_stage.assert_called_once_with(restApiId='bob', stageName='testme')

  def test_process_request_calls_fail_json_when_delete_fails(self):
    self.stage.module.params = {
      'rest_api_id': 'bob',
      'name': 'testme',
      'state': 'absent'
    }

    self.stage.client.delete_stage = mock.MagicMock(side_effect=BotoCoreError())

    self.stage.process_request()

    self.stage.client.delete_stage.assert_called_once_with(restApiId='bob', stageName='testme')
    self.stage.module.fail_json.assert_called_once_with(
        msg='Error while deleting stage via boto3: An unspecified error occurred'
    )

  @patch.object(ApiGwStage, '_find_stage', return_value=None)
  def test_process_request_skips_delete_and_calls_exit_json_when_stage_does_not_exist(self, mock_find):
    self.stage.module.params = {
      'rest_api_id': 'bob',
      'name': 'testme',
      'state': 'absent'
    }

    self.stage.process_request()

    self.assertEqual(0, self.stage.client.delete_stage.call_count)
    self.stage.module.exit_json.assert_called_once_with(changed=False, stage=None)

  def test_process_request_skips_delete_and_calls_exit_json_when_check_mode_is_set(self):
    self.stage.module.params = {
      'rest_api_id': 'bob',
      'name': 'testme',
      'state': 'absent'
    }

    self.stage.module.check_mode = True

    self.stage.process_request()

    self.assertEqual(0, self.stage.client.delete_stage.call_count)
    self.stage.module.exit_json.assert_called_once_with(changed=False, stage=None)

  def test_process_request_calls_get_stage_when_called(self):
    self.stage.module.params = {
      'rest_api_id': 'bob',
      'name': 'testme'
    }

    self.stage.client.get_stage = mock.MagicMock(return_value={'Schaden': 'freude'})

    self.stage.process_request()

    self.stage.client.get_stage.assert_called_once_with(restApiId='bob', stageName='testme')
    self.assertEqual({'Schaden': 'freude'}, self.stage.stage)

  def test_process_request_sets_find_result_to_None_when_get_stage_returns_404(self):
    self.stage.module.params = {
      'rest_api_id': 'bob',
      'name': 'testme'
    }

    self.stage.client.get_stage = mock.MagicMock(
        side_effect=ClientError({'Error': {'Code': 'x NotFoundException x'}}, 'xxx'))

    self.stage.process_request()

    self.stage.client.get_stage.assert_called_once_with(restApiId='bob', stageName='testme')
    self.assertEqual(None, self.stage.stage)

  def test_process_request_calls_fail_json_when_get_stage_returns_non_404_ClientError(self):
    self.stage.module.params = {
      'rest_api_id': 'bob',
      'name': 'testme'
    }

    self.stage.client.get_stage = mock.MagicMock(
        side_effect=ClientError({'Error': {'Code': 'x SomeOtherError x'}}, 'xxx'))

    self.stage.process_request()

    self.stage.client.get_stage.assert_called_once_with(restApiId='bob', stageName='testme')
    self.stage.module.fail_json.assert_called_once_with(
        msg='Error while finding stage via boto3: An error occurred (x SomeOtherError x) when calling the xxx operation: Unknown'
    )

  def test_process_request_calls_fail_json_when_get_stage_raises_exception(self):
    self.stage.module.params = {
      'rest_api_id': 'bob',
      'name': 'testme'
    }

    self.stage.client.get_stage = mock.MagicMock(side_effect=BotoCoreError())

    self.stage.process_request()

    self.stage.client.get_stage.assert_called_once_with(restApiId='bob', stageName='testme')
    self.stage.module.fail_json.assert_called_once_with(
        msg='Error while finding stage via boto3: An unspecified error occurred'
    )

  def test_process_request_calls_update_stage_when_changes_are_needed(self):
    self.stage.module.params = {
      'rest_api_id': 'bob',
      'name': 'testme',
      'description': 'new description',
      'cache_cluster_enabled': True,
      'cache_cluster_size': 1.6,
      'method_settings': [
        {'method_name': '/test', 'method_verb': 'GET', 'caching_enabled': True},
        {'method_name': '/test', 'method_verb': 'PUT', 'caching_enabled': True},
      ]
    }

    mock_result = {
      'cacheClusterEnabled': True,
      'cacheClusterSize': '0.5',
      'methodSettings': {
        '~1test/GET': {'cachingEnabled': True},
        '~1test/PUT': {'cachingEnabled': False},
      }
    }

    self.stage.client.get_stage = mock.MagicMock(return_value=mock_result)

    expected_patch_ops = [
      {'op': 'replace', 'path': '/~1test/PUT/caching/enabled', 'value': 'True'},
      {'op': 'replace', 'path': '/description', 'value': 'new description'},
      {'op': 'replace', 'path': '/cacheClusterSize', 'value': '1.6'},
    ]

    self.stage.process_request()

    self.stage.client.update_stage.assert_called_once_with(restApiId='bob', stageName='testme', patchOperations=mock.ANY)
    self.assertEqual(len(expected_patch_ops), len(self.stage.client.update_stage.call_args[1]['patchOperations']))
    self.assertItemsEqual(expected_patch_ops, self.stage.client.update_stage.call_args[1]['patchOperations'])

  def test_process_request_skips_update_method_call_when_no_differences_found(self):
    self.stage.module.params = {
      'rest_api_id': 'bob',
      'name': 'testme',
      'cache_cluster_size': 'something',
    }

    mock_result = {
      'cacheClusterSize': 'something',
    }

    self.stage.client.get_stage = mock.MagicMock(return_value=mock_result)

    self.stage.process_request()

    self.assertEqual(0, self.stage.client.update_stage.call_count)
    self.stage.module.exit_json.assert_called_once_with(changed=False, stage=None)

  def test_process_request_skips_update_method_call_when_check_mode_set(self):
    self.stage.module.params = {
      'rest_api_id': 'bob',
      'name': 'testme',
      'cache_cluster_size': 'something else',
    }

    mock_result = {
      'cacheClusterSize': 'something',
    }

    self.stage.module.check_mode = True

    self.stage.client.get_stage = mock.MagicMock(return_value=mock_result)

    self.stage.process_request()

    self.assertEqual(0, self.stage.client.update_stage.call_count)
    self.stage.module.exit_json.assert_called_once_with(changed=True, stage=None)

  def test_process_request_calls_fail_json_when_update_stage_raises_exception(self):
    self.stage.module.params = {
      'rest_api_id': 'bob',
      'name': 'testme',
      'cache_cluster_size': 'something else',
    }

    mock_result = {
      'cacheClusterSize': 'something',
    }

    self.stage.client.get_stage = mock.MagicMock(return_value=mock_result)
    self.stage.client.update_stage = mock.MagicMock(side_effect=BotoCoreError)

    self.stage.process_request()

    self.stage.client.update_stage.assert_called_once_with(
        restApiId='bob', stageName='testme',
        patchOperations=[{'op': 'replace', 'path': '/cacheClusterSize', 'value': 'something else'}])
    self.stage.module.fail_json.assert_called_once_with(
        msg='Error while updating stage via boto3: An unspecified error occurred'
    )

  def test_process_request_calls_get_stage_after_successful_update(self):
    self.stage.module.params = {
      'rest_api_id': 'bob',
      'name': 'testme',
      'cache_cluster_size': 'something else',
    }

    mock_result = {
      'cacheClusterSize': 'something',
    }

    self.stage.client.get_stage = mock.MagicMock(side_effect=[mock_result, 'Hurray! It worked!'])

    self.stage.process_request()

    self.stage.client.update_stage.assert_called_once_with(
        restApiId='bob', stageName='testme',
        patchOperations=[{'op': 'replace', 'path': '/cacheClusterSize', 'value': 'something else'}])
    self.stage.client.get_stage.assert_called_with(restApiId='bob', stageName='testme')
    self.stage.module.exit_json.assert_called_once_with(changed=True, stage='Hurray! It worked!')
    self.assertEqual(2, self.stage.client.get_stage.call_count)


  @patch.object(apigw_stage, 'AnsibleModule')
  @patch.object(apigw_stage, 'ApiGwStage')
  def test_main(self, mock_ApiGwStage, mock_AnsibleModule):
    mock_ApiGwStage_instance      = mock.MagicMock()
    mock_AnsibleModule_instance     = mock.MagicMock()
    mock_ApiGwStage.return_value  = mock_ApiGwStage_instance
    mock_AnsibleModule.return_value = mock_AnsibleModule_instance

    apigw_stage.main()

    mock_ApiGwStage.assert_called_once_with(mock_AnsibleModule_instance)
    self.assertEqual(1, mock_ApiGwStage_instance.process_request.call_count)



if __name__ == '__main__':
    unittest.main()

