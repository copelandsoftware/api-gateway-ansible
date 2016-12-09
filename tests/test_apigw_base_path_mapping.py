#!/usr/bin/python
# TODO: License goes here

import library.apigw_base_path_mapping as apigw_base_path_mapping
from library.apigw_base_path_mapping import ApiGwBasePathMapping
import mock
from mock import patch
from mock import create_autospec
from mock import ANY
import unittest
import boto
from botocore.exceptions import BotoCoreError

class TestApiGwBasePathMapping(unittest.TestCase):

  def setUp(self):
    self.module = mock.MagicMock()
    self.module.check_mode = False
    self.module.exit_json = mock.MagicMock()
    self.module.fail_json = mock.MagicMock()
    self.bpm  = ApiGwBasePathMapping(self.module)
    self.bpm.client = mock.MagicMock()
    self.bpm.module.params = {
      'name': 'testify',
      'rest_api_id': 'rest_id',
      'base_path': 'test_base_path',
      'stage': 'test_stage',
      'state': 'present',
    }
    reload(apigw_base_path_mapping)

  def test_boto_module_not_found(self):
    # Setup Mock Import Function
    import __builtin__ as builtins
    real_import = builtins.__import__

    def mock_import(name, *args):
      if name == 'boto': raise ImportError
      return real_import(name, *args)

    with mock.patch('__builtin__.__import__', side_effect=mock_import):
      reload(apigw_base_path_mapping)
      ApiGwBasePathMapping(self.module)

    self.module.fail_json.assert_called_with(msg='boto and boto3 are required for this module')

  def test_boto3_module_not_found(self):
    # Setup Mock Import Function
    import __builtin__ as builtins
    real_import = builtins.__import__

    def mock_import(name, *args):
      if name == 'boto3': raise ImportError
      return real_import(name, *args)

    with mock.patch('__builtin__.__import__', side_effect=mock_import):
      reload(apigw_base_path_mapping)
      ApiGwBasePathMapping(self.module)

    self.module.fail_json.assert_called_with(msg='boto and boto3 are required for this module')

  @patch.object(apigw_base_path_mapping, 'boto3')
  def test_boto3_client_properly_instantiated(self, mock_boto):
    ApiGwBasePathMapping(self.module)
    mock_boto.client.assert_called_once_with('apigateway')

  @patch.object(ApiGwBasePathMapping, '_update_base_path_mapping', return_value=(None, None))
  def test_process_request_calls_get_base_path_mappings_and_stores_result_when_invoked(self, m):
    resp = {
      'items': [
        {'basePath': 'not a match', 'restApiId': 'rest_api_id', 'stage': 'whatever'},
        {'basePath': 'test_base_path', 'restApiId': 'rest_api_id', 'stage': 'yes'},
      ],
    }
    self.bpm.client.get_base_path_mappings = mock.MagicMock(return_value=resp)

    self.bpm.process_request()

    self.assertEqual(resp['items'][1], self.bpm.me)
    self.bpm.client.get_base_path_mappings.assert_called_once_with(domainName='testify')

  def test_process_request_stores_None_result_when_not_found_in_get_base_path_mappings_result(self):
    resp = {
      'items': [
        {'basePath': 'not a match', 'restApiId': 'rest_api_id', 'stage': 'whatever'},
        {'basePath': 'not so much', 'restApiId': 'rest_api_id', 'stage': 'yes'},
      ],
    }
    self.bpm.client.get_base_path_mappings = mock.MagicMock(return_value=resp)

    self.bpm.process_request()

    self.assertEqual(None, self.bpm.me)
    self.bpm.client.get_base_path_mappings.assert_called_once_with(domainName='testify')

  def test_process_request_calls_fail_json_when_get_base_path_mappings_raises_exception(self):
    self.bpm.client.get_base_path_mappings = mock.MagicMock(side_effect=BotoCoreError())

    self.bpm.process_request()

    self.bpm.client.get_base_path_mappings.assert_called_once_with(domainName='testify')
    self.bpm.module.fail_json.assert_called_once_with(
      msg='Error when getting base_path_mappings from boto3: An unspecified error occurred'
    )

  @patch.object(ApiGwBasePathMapping, '_delete_base_path_mapping', return_value='Mitchell!')
  @patch.object(ApiGwBasePathMapping, '_retrieve_base_path_mapping', return_value='found')
  def test_process_request_calls_exit_json_with_expected_value_after_successful_delete(self, mr, md):
    self.bpm.module.params = {
      'base_path': 'test_base_path',
      'name': 'testify',
      'state': 'absent',
    }

    self.bpm.process_request()

    self.bpm.module.exit_json.assert_called_once_with(changed='Mitchell!', base_path_mapping=None)

  @patch.object(ApiGwBasePathMapping, '_retrieve_base_path_mapping', return_value='found!')
  def test_process_request_calls_delete_base_path_mapping_when_state_absent_and_base_path_mapping_found(self, m):
    self.bpm.module.params = {
      'base_path': 'test_base_path',
      'name': 'testify',
      'state': 'absent',
    }

    self.bpm.process_request()

    self.bpm.client.delete_base_path_mapping.assert_called_once_with(domainName='testify', basePath='test_base_path')

  @patch.object(ApiGwBasePathMapping, '_retrieve_base_path_mapping', return_value={'id': 'found'})
  def test_process_request_skips_delete_and_calls_exit_json_with_true_when_check_mode_set_and_auth_found(self, m):
    self.bpm.module.params = {
      'base_path': 'test_base_path',
      'name': 'testify',
      'state': 'absent',
    }
    self.bpm.module.check_mode = True

    self.bpm.process_request()

    self.assertEqual(0, self.bpm.client.delete_base_path_mapping.call_count)
    self.bpm.module.exit_json.assert_called_once_with(changed=True, base_path_mapping=None)


  @patch.object(ApiGwBasePathMapping, '_retrieve_base_path_mapping', return_value={'id': 'found'})
  def test_process_request_calls_fail_json_when_delete_base_path_mapping_raises_error(self, m):
    self.bpm.module.params = {
      'base_path': 'test_base_path',
      'name': 'testify',
      'state': 'absent',
    }

    self.bpm.client.delete_base_path_mapping = mock.MagicMock(side_effect=BotoCoreError)
    self.bpm.process_request()

    self.bpm.client.delete_base_path_mapping.assert_called_once_with(domainName='testify', basePath='test_base_path')
    self.bpm.module.fail_json.assert_called_once_with(
      msg='Error when deleting base_path_mapping via boto3: An unspecified error occurred'
    )

  @patch.object(ApiGwBasePathMapping, '_retrieve_base_path_mapping', return_value=None)
  def test_process_request_skips_delete_when_base_path_mapping_not_found(self, m):
    self.bpm.module.params = {
      'base_path': 'test_base_path',
      'name': 'testify',
      'state': 'absent',
    }

    self.bpm.process_request()

    self.assertEqual(0, self.bpm.client.delete_base_path_mapping.call_count)

  @patch.object(ApiGwBasePathMapping, '_create_base_path_mapping', return_value=('heart', 'pumping'))
  @patch.object(ApiGwBasePathMapping, '_retrieve_base_path_mapping', return_value=None)
  def test_process_request_calls_exit_json_with_expected_value_after_successful_create(self, mra, mca):
    self.bpm.process_request()

    self.bpm.module.exit_json.assert_called_once_with(changed='heart', base_path_mapping='pumping')

  @patch.object(ApiGwBasePathMapping, '_retrieve_base_path_mapping', return_value=None)
  def test_process_request_returns_create_base_path_mapping_result_when_create_succeeds(self, m):
    self.bpm.client.create_base_path_mapping = mock.MagicMock(return_value='woot')
    self.bpm.process_request()

    self.bpm.module.exit_json.assert_called_once_with(changed=True, base_path_mapping='woot')


  @patch.object(ApiGwBasePathMapping, '_retrieve_base_path_mapping', return_value=None)
  def test_process_request_calls_create_base_path_mapping_when_state_present_and_base_path_mapping_not_found(self, m):
    self.bpm.process_request()

    self.bpm.client.create_base_path_mapping.assert_called_once_with(
      domainName='testify',
      restApiId='rest_id',
      basePath='test_base_path',
      stage='test_stage'
    )

  @patch.object(ApiGwBasePathMapping, '_retrieve_base_path_mapping', return_value=None)
  def test_process_request_calls_fail_json_when_create_base_path_mapping_raises_exception(self, m):
    self.bpm.client.create_base_path_mapping = mock.MagicMock(side_effect=BotoCoreError())
    self.bpm.process_request()

    self.bpm.client.create_base_path_mapping.assert_called_once_with(
      domainName='testify',
      restApiId='rest_id',
      basePath='test_base_path',
      stage='test_stage'
    )
    self.bpm.module.fail_json.assert_called_once_with(
      msg='Error when creating base_path_mapping via boto3: An unspecified error occurred'
    )

  @patch.object(ApiGwBasePathMapping, '_retrieve_base_path_mapping', return_value=None)
  def test_process_request_skips_create_call_and_returns_changed_True_when_check_mode(self, m):
    self.bpm.module.check_mode = True
    self.bpm.process_request()

    self.assertEqual(0, self.bpm.client.create_base_path_mapping.call_count)
    self.bpm.module.exit_json.assert_called_once_with(changed=True, base_path_mapping=None)

  @patch.object(ApiGwBasePathMapping, '_retrieve_base_path_mapping', return_value=None)
  def test_process_request_calls_fail_json_when_state_present_and_required_field_missing(self, mra):

    self.bpm.module.params.pop('rest_api_id', None)
    self.bpm.process_request()

    self.bpm.module.fail_json.assert_called_with(
      msg="Field 'rest_api_id' is required when attempting to create a Base Path Mapping resource"
    )

  @patch.object(ApiGwBasePathMapping, '_retrieve_base_path_mapping')
  def test_process_request_calls_update_base_path_mapping_when_state_present_and_base_path_mapping_changed(self, m):
    m.return_value = {
      'basePath': 'test_base_path',
      'stage': 'original stage',
      'restApiId': 'ab12345',
    }

    expected_patches = [
      {'op': 'replace', 'path': '/stage', 'value': 'test_stage'},
    ]

    self.bpm.process_request()

    self.bpm.client.update_base_path_mapping.assert_called_once_with(
      domainName='testify',
      basePath='test_base_path',
      patchOperations=expected_patches
    )

  @patch('library.apigw_base_path_mapping.ApiGwBasePathMapping._create_patches', return_value=[])
  @patch.object(ApiGwBasePathMapping, '_retrieve_base_path_mapping', return_value={'something': 'here'})
  def test_process_request_skips_update_base_path_mapping_and_replies_false_when_no_changes(self, m, mcp):
    self.bpm.process_request()

    self.assertEqual(0, self.bpm.client.update_method.call_count)
    self.bpm.module.exit_json.assert_called_once_with(changed=False, base_path_mapping={'something': 'here'})

  @patch('library.apigw_base_path_mapping.ApiGwBasePathMapping._create_patches', return_value=['patches!'])
  @patch.object(ApiGwBasePathMapping, '_retrieve_base_path_mapping', return_value={'id': 'hi'})
  def test_process_request_calls_fail_json_when_update_base_path_mapping_raises_exception(self, m, mcp):
    self.bpm.client.update_base_path_mapping = mock.MagicMock(side_effect=BotoCoreError())
    self.bpm.process_request()

    self.bpm.client.update_base_path_mapping.assert_called_once_with(
      domainName='testify',
      basePath='test_base_path',
      patchOperations=['patches!']
    )
    self.bpm.module.fail_json.assert_called_once_with(
      msg='Error when updating base_path_mapping via boto3: An unspecified error occurred'
    )

  @patch('library.apigw_base_path_mapping.ApiGwBasePathMapping._create_patches', return_value=['patches!'])
  @patch.object(ApiGwBasePathMapping, '_retrieve_base_path_mapping', side_effect=[{'id': 'hi'}, 'second call'])
  def test_process_request_returns_result_of_find_when_update_is_successful(self, m, mcp):
    self.bpm.process_request()

    self.bpm.client.update_base_path_mapping.assert_called_once_with(
      domainName='testify',
      basePath='test_base_path',
      patchOperations=['patches!']
    )
    self.bpm.module.exit_json.assert_called_once_with(changed=True, base_path_mapping='second call')

  @patch('library.apigw_base_path_mapping.ApiGwBasePathMapping._create_patches', return_value=['patches!'])
  @patch.object(ApiGwBasePathMapping, '_retrieve_base_path_mapping', return_value={'something': 'here'})
  def test_process_request_skips_update_base_path_mapping_and_replies_true_when_check_mode(self, m, mcp):
    self.bpm.module.check_mode = True
    self.bpm.process_request()

    self.assertEqual(0, self.bpm.client.update_method.call_count)
    self.bpm.module.exit_json.assert_called_once_with(changed=True, base_path_mapping={'something': 'here'})

  def test_define_argument_spec(self):
    result = ApiGwBasePathMapping._define_module_argument_spec()
    self.assertIsInstance(result, dict)
    self.assertEqual(result, dict(
                     name=dict(required=True, aliases=['domain_name']),
                     rest_api_id=dict(required=False),
                     stage=dict(required=False),
                     base_path=dict(required=False, default='(none)'),
                     state=dict(default='present', choices=['present', 'absent']),
    ))

  @patch.object(apigw_base_path_mapping, 'AnsibleModule')
  @patch.object(apigw_base_path_mapping, 'ApiGwBasePathMapping')
  def test_main(self, mock_ApiGwBasePathMapping, mock_AnsibleModule):
    mock_ApiGwBasePathMapping_instance      = mock.MagicMock()
    mock_AnsibleModule_instance     = mock.MagicMock()
    mock_ApiGwBasePathMapping.return_value  = mock_ApiGwBasePathMapping_instance
    mock_AnsibleModule.return_value = mock_AnsibleModule_instance

    apigw_base_path_mapping.main()

    mock_ApiGwBasePathMapping.assert_called_once_with(mock_AnsibleModule_instance)
    assert mock_ApiGwBasePathMapping_instance.process_request.call_count == 1


if __name__ == '__main__':
    unittest.main()

