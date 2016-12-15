#!/usr/bin/python
# TODO: License goes here

import library.apigw_usage_plan as apigw_usage_plan
from library.apigw_usage_plan import ApiGwUsagePlan
import mock
from mock import patch
from mock import create_autospec
from mock import ANY
import unittest
import boto
from botocore.exceptions import BotoCoreError

class TestApiGwUsagePlan(unittest.TestCase):

  def setUp(self):
    self.module = mock.MagicMock()
    self.module.check_mode = False
    self.module.exit_json = mock.MagicMock()
    self.module.fail_json = mock.MagicMock()
    self.usage_plan  = ApiGwUsagePlan(self.module)
    self.usage_plan.client = mock.MagicMock()
    self.usage_plan.module.params = {
      'name': 'testify',
      'description': 'test_description',
      'api_stages': [{'rest_api_id': 'id1', 'stage': 'stage1'}],
      'throttle_burst_limit': 111,
      'throttle_rate_limit': 222.0,
      'quota_limit': 333,
      'quota_offset': 444,
      'quota_period': 'WEEK',
      'state': 'present',
    }
    reload(apigw_usage_plan)

  def test_boto_module_not_found(self):
    # Setup Mock Import Function
    import __builtin__ as builtins
    real_import = builtins.__import__

    def mock_import(name, *args):
      if name == 'boto': raise ImportError
      return real_import(name, *args)

    with mock.patch('__builtin__.__import__', side_effect=mock_import):
      reload(apigw_usage_plan)
      ApiGwUsagePlan(self.module)

    self.module.fail_json.assert_called_with(msg='boto and boto3 are required for this module')

  def test_boto3_module_not_found(self):
    # Setup Mock Import Function
    import __builtin__ as builtins
    real_import = builtins.__import__

    def mock_import(name, *args):
      if name == 'boto3': raise ImportError
      return real_import(name, *args)

    with mock.patch('__builtin__.__import__', side_effect=mock_import):
      reload(apigw_usage_plan)
      ApiGwUsagePlan(self.module)

    self.module.fail_json.assert_called_with(msg='boto and boto3 are required for this module')

  @patch.object(apigw_usage_plan, 'boto3')
  def test_boto3_client_properly_instantiated(self, mock_boto):
    ApiGwUsagePlan(self.module)
    mock_boto.client.assert_called_once_with('apigateway')

  @patch.object(ApiGwUsagePlan, '_update_usage_plan', return_value=('hi', 'mom'))
  def test_process_request_calls_get_usage_plans_and_stores_result_when_invoked(self, m):
    resp = {
      'items': [
        {'name': 'not a match', 'id': 'usage_plan_id'},
        {'name': 'testify', 'id': 'usage_plan_id'},
      ],
    }
    self.usage_plan.client.get_usage_plans = mock.MagicMock(return_value=resp)

    self.usage_plan.process_request()

    self.assertEqual(resp['items'][1], self.usage_plan.me)
    self.usage_plan.client.get_usage_plans.assert_called_once_with()

  def test_process_request_stores_None_result_when_not_found_in_get_usage_plans_result(self):
    resp = {
      'items': [
        {'name': 'not a match', 'id': 'usage_plan_id'},
        {'name': 'also not a match', 'id': 'usage_plan_id'},
      ],
    }
    self.usage_plan.client.get_usage_plans = mock.MagicMock(return_value=resp)

    self.usage_plan.process_request()

    self.assertEqual(None, self.usage_plan.me)
    self.usage_plan.client.get_usage_plans.assert_called_once_with()

  def test_process_request_calls_fail_json_when_get_usage_plans_raises_exception(self):
    self.usage_plan.client.get_usage_plans = mock.MagicMock(side_effect=BotoCoreError())

    self.usage_plan.process_request()

    self.usage_plan.client.get_usage_plans.assert_called_once_with()
    self.usage_plan.module.fail_json.assert_called_once_with(
      msg='Error when getting usage_plans from boto3: An unspecified error occurred'
    )

  @patch.object(ApiGwUsagePlan, '_delete_usage_plan', return_value='Egah!')
  @patch.object(ApiGwUsagePlan, '_retrieve_usage_plan', return_value={'id': 'found'})
  def test_process_request_calls_exit_json_with_expected_value_after_successful_delete(self, mr, md):
    self.usage_plan.module.params = {
      'name': 'testify',
      'state': 'absent',
    }

    self.usage_plan.process_request()

    self.usage_plan.module.exit_json.assert_called_once_with(changed='Egah!', usage_plan=None)

  @patch.object(ApiGwUsagePlan, '_retrieve_usage_plan')
  def test_process_request_removes_api_stages_before_executing_delete(self, m):
    m.return_value = {
      'id': 'found',
      'apiStages': [{'apiId': '1', 'stage': 's1'}, {'apiId': '2', 'stage': 's2'}]
    }
    self.usage_plan.module.params = {
      'name': 'testify',
      'state': 'absent',
    }

    expected_patches = [
      {'op': 'remove', 'path': '/apiStages', 'value': '1:s1'},
      {'op': 'remove', 'path': '/apiStages', 'value': '2:s2'},
    ]

    self.usage_plan.process_request()

    self.usage_plan.client.update_usage_plan.assert_called_once_with(
      usagePlanId='found',
      patchOperations=mock.ANY
    )
    self.assertEqual(len(expected_patches), len(self.usage_plan.client.update_usage_plan.call_args[1]['patchOperations']))
    self.assertItemsEqual(expected_patches, self.usage_plan.client.update_usage_plan.call_args[1]['patchOperations'])

  @patch.object(ApiGwUsagePlan, '_retrieve_usage_plan', return_value={'id': 'found'})
  def test_process_request_calls_delete_usage_plan_when_state_absent_and_usage_plan_found(self, m):
    self.usage_plan.module.params = {
      'name': 'testify',
      'state': 'absent',
    }

    self.usage_plan.process_request()

    self.usage_plan.client.delete_usage_plan.assert_called_once_with(usagePlanId='found')

  @patch.object(ApiGwUsagePlan, '_retrieve_usage_plan', return_value={'id': 'found'})
  def test_process_request_skips_delete_and_calls_exit_json_with_true_when_check_mode_set_and_auth_found(self, m):
    self.usage_plan.module.params = {
      'name': 'testify',
      'state': 'absent',
    }
    self.usage_plan.module.check_mode = True

    self.usage_plan.process_request()

    self.assertEqual(0, self.usage_plan.client.delete_usage_plan.call_count)
    self.usage_plan.module.exit_json.assert_called_once_with(changed=True, usage_plan=None)


  @patch.object(ApiGwUsagePlan, '_retrieve_usage_plan', return_value={'id': 'found'})
  def test_process_request_calls_fail_json_when_delete_usage_plan_raises_error(self, m):
    self.usage_plan.module.params = {
      'name': 'testify',
      'state': 'absent',
    }

    self.usage_plan.client.delete_usage_plan = mock.MagicMock(side_effect=BotoCoreError)
    self.usage_plan.process_request()

    self.usage_plan.client.delete_usage_plan.assert_called_once_with(usagePlanId='found')
    self.usage_plan.module.fail_json.assert_called_once_with(
      msg='Error when deleting usage_plan via boto3: An unspecified error occurred'
    )

  @patch.object(ApiGwUsagePlan, '_retrieve_usage_plan', return_value=None)
  def test_process_request_skips_delete_when_usage_plan_not_found(self, m):
    self.usage_plan.module.params = {
      'name': 'testify',
      'state': 'absent',
    }

    self.usage_plan.process_request()

    self.assertEqual(0, self.usage_plan.client.delete_usage_plan.call_count)

  @patch.object(ApiGwUsagePlan, '_create_usage_plan', return_value=('eye', 'on the sandwich'))
  @patch.object(ApiGwUsagePlan, '_retrieve_usage_plan', return_value=None)
  def test_process_request_calls_exit_json_with_expected_value_after_successful_create(self, mra, mca):
    self.usage_plan.process_request()

    self.usage_plan.module.exit_json.assert_called_once_with(changed='eye', usage_plan='on the sandwich')

  @patch.object(ApiGwUsagePlan, '_retrieve_usage_plan', return_value=None)
  def test_process_request_returns_create_usage_plan_result_when_create_succeeds(self, m):
    self.usage_plan.client.create_usage_plan = mock.MagicMock(return_value='woot')
    self.usage_plan.process_request()

    self.usage_plan.module.exit_json.assert_called_once_with(changed=True, usage_plan='woot')


  @patch.object(ApiGwUsagePlan, '_retrieve_usage_plan', return_value=None)
  def test_process_request_calls_create_usage_plan_when_state_present_and_usage_plan_not_found(self, m):
    self.usage_plan.process_request()

    self.usage_plan.client.create_usage_plan.assert_called_once_with(
      name='testify',
      description='test_description',
      apiStages=[{'apiId': 'id1', 'stage': 'stage1'}],
      throttle={'burstLimit': 111, 'rateLimit': 222},
      quota={'limit': 333, 'offset': 444, 'period': 'WEEK'},
    )

  @patch.object(ApiGwUsagePlan, '_retrieve_usage_plan', return_value=None)
  def test_process_request_calls_fail_json_when_create_usage_plan_raises_exception(self, m):
    self.usage_plan.module.params = {
      'name': 'testify',
      'state': 'present',
    }
    self.usage_plan.client.create_usage_plan = mock.MagicMock(side_effect=BotoCoreError())
    self.usage_plan.process_request()

    self.usage_plan.client.create_usage_plan.assert_called_once_with(name='testify')
    self.usage_plan.module.fail_json.assert_called_once_with(
      msg='Error when creating usage_plan via boto3: An unspecified error occurred'
    )

  @patch.object(ApiGwUsagePlan, '_retrieve_usage_plan', return_value=None)
  def test_process_request_skips_create_call_and_returns_changed_True_when_check_mode(self, m):
    self.usage_plan.module.check_mode = True
    self.usage_plan.process_request()

    self.assertEqual(0, self.usage_plan.client.create_usage_plan.call_count)
    self.usage_plan.module.exit_json.assert_called_once_with(changed=True, usage_plan=None)

  @patch.object(ApiGwUsagePlan, '_retrieve_usage_plan', return_value={'id': 'hi'})
  def test_process_request_calls_update_usage_plan_for_replace_ops_when_state_present_and_usage_plan_changed(self, m):
    m.return_value = {
      'name': 'testify',
      'id': 'ab12345',
      'description': 'old and busted',
      'apiStages': [{'apiId': 'id1', 'stage': 'stage1'}],
      'throttle': {'burstLimit': 'old', 'rateLimit': 'old'},
      'quota': {'limit': 'old', 'offset': 'old', 'period': 'old'},
    }

    expected_patches = [
      {'op': 'replace', 'path': '/description', 'value': 'test_description'},
      {'op': 'replace', 'path': '/quota/period', 'value': 'WEEK'},
      {'op': 'replace', 'path': '/quota/offset', 'value': '444'},
      {'op': 'replace', 'path': '/quota/limit', 'value': '333'},
      {'op': 'replace', 'path': '/throttle/rateLimit', 'value': '222.0'},
      {'op': 'replace', 'path': '/throttle/burstLimit', 'value': '111'},
    ]

    self.usage_plan.process_request()

    self.usage_plan.client.update_usage_plan.assert_called_once_with(
      usagePlanId='ab12345',
      patchOperations=mock.ANY
    )
    self.assertEqual(len(expected_patches), len(self.usage_plan.client.update_usage_plan.call_args[1]['patchOperations']))
    self.assertItemsEqual(expected_patches, self.usage_plan.client.update_usage_plan.call_args[1]['patchOperations'])

  @patch.object(ApiGwUsagePlan, '_retrieve_usage_plan', return_value={'id': 'hi'})
  def test_process_request_calls_update_usage_plan_for_remove_ops_when_state_present_and_usage_plan_changed(self, m):
    self.usage_plan.module.params = {
      'name': 'testify',
      'description': 'test_description',
      'api_stages': [],
      'state': 'present',
    }

    m.return_value = {
      'name': 'testify',
      'id': 'ab12345',
      'description': 'test_description',
      'apiStages': [{'apiId': 'id1', 'stage': 'stage1'},{'apiId': 'id2', 'stage': 'stage2'}],
      'throttle': {'burstLimit': 'old', 'rateLimit': 'old'},
      'quota': {'limit': 'old', 'offset': 'old', 'period': 'old'},
    }

    expected_patches = [
      {'op': 'remove', 'path': '/quota'},
      {'op': 'remove', 'path': '/throttle'},
      {'op': 'remove', 'path': '/apiStages', 'value': 'id1:stage1'},
      {'op': 'remove', 'path': '/apiStages', 'value': 'id2:stage2'},
    ]

    self.usage_plan.process_request()

    self.usage_plan.client.update_usage_plan.assert_called_once_with(
      usagePlanId='ab12345',
      patchOperations=mock.ANY
    )
    self.assertEqual(len(expected_patches), len(self.usage_plan.client.update_usage_plan.call_args[1]['patchOperations']))
    self.assertItemsEqual(expected_patches, self.usage_plan.client.update_usage_plan.call_args[1]['patchOperations'])

  @patch.object(ApiGwUsagePlan, '_retrieve_usage_plan', return_value={'id': 'hi'})
  def test_process_request_calls_update_usage_plan_for_add_ops_when_state_present_and_usage_plan_changed(self, m):
    self.usage_plan.module.params = {
      'name': 'testify',
      'api_stages': [{'rest_api_id': 'id1', 'stage': 'stage1'}],
      'throttle_burst_limit': 111,
      'throttle_rate_limit': 222.0,
      'quota_limit': 333,
      'quota_offset': 444,
      'quota_period': 'WEEK',
    }

    m.return_value = {
      'name': 'testify',
      'id': 'ab12345',
      'description': 'old and busted',
      'apiStages': [{'apiId': 'idx', 'stage': 'stagex'}],
    }

    expected_patches = [
      {'op': 'replace', 'path': '/description', 'value': ''},
      {'op': 'add', 'path': '/quota/period', 'value': 'WEEK'},
      {'op': 'add', 'path': '/quota/offset', 'value': '444'},
      {'op': 'add', 'path': '/quota/limit', 'value': '333'},
      {'op': 'add', 'path': '/throttle/rateLimit', 'value': '222.0'},
      {'op': 'add', 'path': '/throttle/burstLimit', 'value': '111'},
      {'op': 'add', 'path': '/apiStages', 'value': 'id1:stage1'},
    ]

    self.usage_plan.process_request()

    self.usage_plan.client.update_usage_plan.assert_called_once_with(
      usagePlanId='ab12345',
      patchOperations=mock.ANY
    )
    self.assertEqual(len(expected_patches), len(self.usage_plan.client.update_usage_plan.call_args[1]['patchOperations']))
    self.assertItemsEqual(expected_patches, self.usage_plan.client.update_usage_plan.call_args[1]['patchOperations'])

  @patch('library.apigw_usage_plan.ApiGwUsagePlan._create_patches', return_value=[])
  @patch.object(ApiGwUsagePlan, '_retrieve_usage_plan', return_value={'something': 'here'})
  def test_process_request_skips_update_usage_plan_and_replies_false_when_no_changes(self, m, mcp):
    self.usage_plan.process_request()

    self.assertEqual(0, self.usage_plan.client.update_usage_plan.call_count)
    self.usage_plan.module.exit_json.assert_called_once_with(changed=False, usage_plan={'something': 'here'})

  @patch('library.apigw_usage_plan.ApiGwUsagePlan._create_patches', return_value=['patches!'])
  @patch.object(ApiGwUsagePlan, '_retrieve_usage_plan', return_value={'id': 'hi'})
  def test_process_request_calls_fail_json_when_update_usage_plan_raises_exception(self, m, mcp):
    self.usage_plan.client.update_usage_plan = mock.MagicMock(side_effect=BotoCoreError())
    self.usage_plan.process_request()

    self.usage_plan.client.update_usage_plan.assert_called_once_with(
      usagePlanId='hi',
      patchOperations=['patches!']
    )
    self.usage_plan.module.fail_json.assert_called_once_with(
      msg='Error when updating usage_plan via boto3: An unspecified error occurred'
    )

  @patch('library.apigw_usage_plan.ApiGwUsagePlan._create_patches', return_value=['patches!'])
  @patch.object(ApiGwUsagePlan, '_retrieve_usage_plan', side_effect=[{'id': 'hi'}, 'second call'])
  def test_process_request_returns_result_of_find_when_update_is_successful(self, m, mcp):
    self.usage_plan.process_request()

    self.usage_plan.client.update_usage_plan.assert_called_once_with(
      usagePlanId='hi',
      patchOperations=['patches!']
    )
    self.usage_plan.module.exit_json.assert_called_once_with(changed=True, usage_plan='second call')

  @patch('library.apigw_usage_plan.ApiGwUsagePlan._create_patches', return_value=['patches!'])
  @patch.object(ApiGwUsagePlan, '_retrieve_usage_plan', return_value={'something': 'here'})
  def test_process_request_skips_update_usage_plan_and_replies_true_when_check_mode(self, m, mcp):
    self.usage_plan.module.check_mode = True
    self.usage_plan.process_request()

    self.assertEqual(0, self.usage_plan.client.update_usage_plan.call_count)
    self.usage_plan.module.exit_json.assert_called_once_with(changed=True, usage_plan={'something': 'here'})

  def test_define_argument_spec(self):
    result = ApiGwUsagePlan._define_module_argument_spec()
    self.assertIsInstance(result, dict)
    self.assertEqual(result, dict(
                     name=dict(required=True),
                     description=dict(required=False),
                     api_stages=dict(
                       type='list',
                       required=False,
                       default=[],
                       rest_api_id=dict(required=True),
                       stage=dict(required=True)
                     ),
                     throttle_burst_limit=dict(required=False, default=-1, type='int'),
                     throttle_rate_limit=dict(required=False, default=-1.0, type='float'),
                     quota_limit=dict(required=False, default=-1, type='int'),
                     quota_offset=dict(required=False, default=-1, type='int'),
                     quota_period=dict(required=False, default='', choices=['', 'DAY','WEEK','MONTH']),
                     state=dict(default='present', choices=['present', 'absent']),
    ))

  @patch.object(apigw_usage_plan, 'AnsibleModule')
  @patch.object(apigw_usage_plan, 'ApiGwUsagePlan')
  def test_main(self, mock_ApiGwUsagePlan, mock_AnsibleModule):
    mock_ApiGwUsagePlan_instance      = mock.MagicMock()
    mock_AnsibleModule_instance     = mock.MagicMock()
    mock_ApiGwUsagePlan.return_value  = mock_ApiGwUsagePlan_instance
    mock_AnsibleModule.return_value = mock_AnsibleModule_instance

    apigw_usage_plan.main()

    mock_ApiGwUsagePlan.assert_called_once_with(mock_AnsibleModule_instance)
    assert mock_ApiGwUsagePlan_instance.process_request.call_count == 1


if __name__ == '__main__':
    unittest.main()

