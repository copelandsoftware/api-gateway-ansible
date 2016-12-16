#!/usr/bin/python
# TODO: License goes here

import library.apigw_domain_name as apigw_domain_name
from library.apigw_domain_name import ApiGwDomainName
import mock
from mock import patch
from mock import create_autospec
from mock import ANY
import unittest
import boto
from botocore.exceptions import BotoCoreError, ClientError
import copy

class TestApiGwDomainName(unittest.TestCase):

  def setUp(self):
    self.module = mock.MagicMock()
    self.module.check_mode = False
    self.module.exit_json = mock.MagicMock()
    self.module.fail_json = mock.MagicMock()
    self.domain_name  = ApiGwDomainName(self.module)
    self.domain_name.client = mock.MagicMock()
    self.domain_name.module.params = {
      'name': 'testify',
      'cert_name': 'cert-name',
      'cert_body': 'cert-body',
      'cert_private_key': 'cert-private-key',
      'cert_chain': 'cert-chain',
      'state': 'present',
    }
    reload(apigw_domain_name)

  def test_boto_module_not_found(self):
    # Setup Mock Import Function
    import __builtin__ as builtins
    real_import = builtins.__import__

    def mock_import(name, *args):
      if name == 'boto': raise ImportError
      return real_import(name, *args)

    with mock.patch('__builtin__.__import__', side_effect=mock_import):
      reload(apigw_domain_name)
      ApiGwDomainName(self.module)

    self.module.fail_json.assert_called_with(msg='boto and boto3 are required for this module')

  def test_boto3_module_not_found(self):
    # Setup Mock Import Function
    import __builtin__ as builtins
    real_import = builtins.__import__

    def mock_import(name, *args):
      if name == 'boto3': raise ImportError
      return real_import(name, *args)

    with mock.patch('__builtin__.__import__', side_effect=mock_import):
      reload(apigw_domain_name)
      ApiGwDomainName(self.module)

    self.module.fail_json.assert_called_with(msg='boto and boto3 are required for this module')

  @patch.object(apigw_domain_name, 'boto3')
  def test_boto3_client_properly_instantiated(self, mock_boto):
    ApiGwDomainName(self.module)
    mock_boto.client.assert_called_once_with('apigateway')

  def test_process_request_calls_get_domain_name_and_stores_result_when_invoked(self):
    self.domain_name.client.get_domain_name = mock.MagicMock(return_value='found it!')

    self.domain_name.process_request()

    self.assertEqual('found it!', self.domain_name.me)
    self.domain_name.client.get_domain_name.assert_called_once_with(domainName='testify')

  def test_process_request_stores_None_result_when_not_found_in_get_domain_name_result(self):
    self.domain_name.client.get_domain_name = mock.MagicMock(side_effect=ClientError({'Error': {'Code': 'x NotFoundException x'}}, 'xxx'))

    self.domain_name.process_request()

    self.assertEqual(None, self.domain_name.me)
    self.domain_name.client.get_domain_name.assert_called_once_with(domainName='testify')

  def test_process_request_calls_fail_json_when_get_domain_name_raises_exception(self):
    self.domain_name.client.get_domain_name = mock.MagicMock(side_effect=BotoCoreError())

    self.domain_name.process_request()

    self.domain_name.client.get_domain_name.assert_called_once_with(domainName='testify')
    self.domain_name.module.fail_json.assert_called_once_with(
      msg='Error when getting domain_name from boto3: An unspecified error occurred'
    )

  @patch.object(ApiGwDomainName, '_delete_domain_name', return_value='Mitchell!')
  @patch.object(ApiGwDomainName, '_retrieve_domain_name', return_value={'id': 'found'})
  def test_process_request_calls_exit_json_with_expected_value_after_successful_delete(self, mr, md):
    self.domain_name.module.params = {
      'name': 'testify',
      'state': 'absent',
    }

    self.domain_name.process_request()

    self.domain_name.module.exit_json.assert_called_once_with(changed='Mitchell!', domain_name=None)

  @patch.object(ApiGwDomainName, '_retrieve_domain_name', return_value={'id': 'found'})
  def test_process_request_calls_delete_domain_name_when_state_absent_and_domain_name_found(self, m):
    self.domain_name.module.params = {
      'name': 'testify',
      'state': 'absent',
    }

    self.domain_name.process_request()

    self.domain_name.client.delete_domain_name.assert_called_once_with(domainName='testify')

  @patch.object(ApiGwDomainName, '_retrieve_domain_name', return_value={'id': 'found'})
  def test_process_request_skips_delete_and_calls_exit_json_with_true_when_check_mode_set_and_auth_found(self, m):
    self.domain_name.module.params = {
      'name': 'testify',
      'state': 'absent',
    }
    self.domain_name.module.check_mode = True

    self.domain_name.process_request()

    self.assertEqual(0, self.domain_name.client.delete_domain_name.call_count)
    self.domain_name.module.exit_json.assert_called_once_with(changed=True, domain_name=None)


  @patch.object(ApiGwDomainName, '_retrieve_domain_name', return_value={'id': 'found'})
  def test_process_request_calls_fail_json_when_delete_domain_name_raises_error(self, m):
    self.domain_name.module.params = {
      'name': 'testify',
      'state': 'absent',
    }

    self.domain_name.client.delete_domain_name = mock.MagicMock(side_effect=BotoCoreError)
    self.domain_name.process_request()

    self.domain_name.client.delete_domain_name.assert_called_once_with(domainName='testify')
    self.domain_name.module.fail_json.assert_called_once_with(
      msg='Error when deleting domain_name via boto3: An unspecified error occurred'
    )

  @patch.object(ApiGwDomainName, '_retrieve_domain_name', return_value=None)
  def test_process_request_skips_delete_when_domain_name_not_found(self, m):
    self.domain_name.module.params = {
      'name': 'testify',
      'state': 'absent',
    }

    self.domain_name.process_request()

    self.assertEqual(0, self.domain_name.client.delete_domain_name.call_count)

  @patch.object(ApiGwDomainName, '_create_domain_name', return_value=('veins', 'clogging'))
  @patch.object(ApiGwDomainName, '_retrieve_domain_name', return_value=None)
  def test_process_request_calls_exit_json_with_expected_value_after_successful_create(self, mra, mca):
    self.domain_name.process_request()

    self.domain_name.module.exit_json.assert_called_once_with(changed='veins', domain_name='clogging')

  @patch.object(ApiGwDomainName, '_retrieve_domain_name', return_value=None)
  def test_process_request_returns_create_domain_name_result_when_create_succeeds(self, m):
    self.domain_name.client.create_domain_name = mock.MagicMock(return_value='woot')
    self.domain_name.process_request()

    self.domain_name.module.exit_json.assert_called_once_with(changed=True, domain_name='woot')


  @patch.object(ApiGwDomainName, '_retrieve_domain_name', return_value=None)
  def test_process_request_calls_create_domain_name_when_state_present_and_domain_name_not_found(self, m):
    self.domain_name.process_request()

    self.domain_name.client.create_domain_name.assert_called_once_with(
      name='testify',
      certificateName='cert-name',
      certificateBody='cert-body',
      certificatePrivateKey='cert-private-key',
      certificateChain='cert-chain',
    )

  @patch.object(ApiGwDomainName, '_retrieve_domain_name', return_value=None)
  def test_process_request_calls_fail_json_when_create_domain_name_raises_exception(self, m):
    self.domain_name.client.create_domain_name = mock.MagicMock(side_effect=BotoCoreError())
    self.domain_name.process_request()

    self.domain_name.client.create_domain_name.assert_called_once_with(
      name='testify',
      certificateName='cert-name',
      certificateBody='cert-body',
      certificatePrivateKey='cert-private-key',
      certificateChain='cert-chain',
    )
    self.domain_name.module.fail_json.assert_called_once_with(
      msg='Error when creating domain_name via boto3: An unspecified error occurred'
    )

  @patch.object(ApiGwDomainName, '_retrieve_domain_name', return_value=None)
  def test_process_request_validates_required_params_when_state_is_present(self, m):
    orig = copy.deepcopy(self.domain_name.module.params)

    for p in ['cert_name', 'cert_body', 'cert_private_key', 'cert_chain']:
      self.domain_name.module.params = copy.deepcopy(orig)
      self.domain_name.module.params.pop(p)
      self.domain_name.process_request()
      self.assertEqual(0, self.domain_name.client.create_domain_name.call_count)
      self.domain_name.module.fail_json.assert_called_with(msg='All certificate parameters are required to create a domain name')

  @patch.object(ApiGwDomainName, '_retrieve_domain_name', return_value=None)
  def test_process_request_skips_create_call_and_returns_changed_True_when_check_mode(self, m):
    self.domain_name.module.check_mode = True
    self.domain_name.process_request()

    self.assertEqual(0, self.domain_name.client.create_domain_name.call_count)
    self.domain_name.module.exit_json.assert_called_once_with(changed=True, domain_name=None)

  def test_define_argument_spec(self):
    result = ApiGwDomainName._define_module_argument_spec()
    self.assertIsInstance(result, dict)
    self.assertEqual(result, dict(
                     name=dict(required=True, aliases=['domain_name']),
                     cert_name=dict(required=False),
                     cert_body=dict(required=False),
                     cert_private_key=dict(required=False),
                     cert_chain=dict(required=False),
                     state=dict(default='present', choices=['present', 'absent']),
    ))

  @patch.object(apigw_domain_name, 'AnsibleModule')
  @patch.object(apigw_domain_name, 'ApiGwDomainName')
  def test_main(self, mock_ApiGwDomainName, mock_AnsibleModule):
    mock_ApiGwDomainName_instance      = mock.MagicMock()
    mock_AnsibleModule_instance     = mock.MagicMock()
    mock_ApiGwDomainName.return_value  = mock_ApiGwDomainName_instance
    mock_AnsibleModule.return_value = mock_AnsibleModule_instance

    apigw_domain_name.main()

    mock_ApiGwDomainName.assert_called_once_with(mock_AnsibleModule_instance)
    assert mock_ApiGwDomainName_instance.process_request.call_count == 1


if __name__ == '__main__':
    unittest.main()

