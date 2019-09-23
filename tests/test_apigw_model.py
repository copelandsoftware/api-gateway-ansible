import library.apigw_model as apigw_model
from library.apigw_model import ApiGwModel
import mock
from mock import call, patch
import unittest
import boto
from botocore.exceptions import BotoCoreError, ClientError
from ansible.module_utils import basic

class TestApiGwModel(unittest.TestCase):
    def setUp(self):
        self.module = mock.MagicMock()
        self.module.check_mode = False
        self.module.params = {
            'rest_api_id': 'other_rest_id',
            'name': 'model',
            'content_type': 'application/pdf',
            'schema': 'schema',
            'description': 'description',
            'state': 'present'
        }
        self.module.exit_json = mock.MagicMock()
        self.module.fail_json = mock.MagicMock()

        self.model = ApiGwModel(self.module)
        self.model.client = mock.MagicMock()
        self.model.client.create_model = mock.MagicMock()
        self.model.client.update_model = mock.MagicMock()
        self.model.client.delete_model = mock.MagicMock()
        self.model.client.get_model = mock.MagicMock()

        basic.AnsibleModule = mock.MagicMock(return_value=self.module)

    def test_boto_module_not_found(self):
        # Setup Mock Import Function
        import __builtin__ as builtins
        real_import = builtins.__import__

        def mock_import(name, *args):
            if name == 'boto': raise ImportError
            return real_import(name, *args)

        with mock.patch('__builtin__.__import__', side_effect=mock_import):
            reload(apigw_model)
            ApiGwModel(self.module)

        self.module.fail_json.assert_called_with(msg='boto and boto3 are required for this module')

    @patch.object(apigw_model, 'boto3')
    def test_boto3_client_properly_instantiated(self, mock_boto):
        ApiGwModel(self.module)
        mock_boto.client.assert_called_once_with('apigateway')

    # _define_module_argument_spec test
    def test_define_argument_spec(self):
        result = ApiGwModel._define_module_argument_spec()
        self.assertIsInstance(result, dict)
        self.assertEqual(result,
            dict(
                rest_api_id=dict(required=True, type='str'),
                name=dict(required=True, type='str'),
                content_type=dict(required=False, type='str'),
                schema=dict(required=False, type='str'),
                description=dict(required=False, type='str', default=''),
                state=dict(default='present', choices=['present', 'absent'])
            )
        )

    # process_request tests
    @patch.object(ApiGwModel, '_find_model')
    def test_process_request_calls_find_model(self, mockFindModel):
        self.model.process_request()

        mockFindModel.assert_called_once()

    @patch.object(ApiGwModel, '_create_model')
    @patch.object(ApiGwModel, '_find_model')
    def test_process_request_calls_exit_json_with_changed_and_response_from_create_model(self, mockFindModel, mockCreateModel):
        mockFindModel.return_value = None
        mock_changed = mock.MagicMock()
        mock_response = mock.MagicMock()
        mockCreateModel.return_value = mock_changed, mock_response

        self.model.process_request()

        self.module.exit_json.assert_called_with(changed=mock_changed, model=mock_response)

    @patch.object(ApiGwModel, '_update_model')
    @patch.object(ApiGwModel, '_find_model')
    def test_process_request_calls_exit_json_with_changed_and_response_from_update_model(self, mockFindModel, mockUpdateModel):
        mockFindModel.return_value = mock.MagicMock()
        mock_changed = mock.MagicMock()
        mock_response = mock.MagicMock()
        mockUpdateModel.return_value = mock_changed, mock_response

        self.model.process_request()

        self.module.exit_json.assert_called_with(changed=mock_changed, model=mock_response)

    @patch.object(ApiGwModel, '_create_model')
    @patch.object(ApiGwModel, '_find_model')
    def test_process_request_calls_create_model_if_model_does_not_exist(self, mockFindModel, mockCreateModel):
        mockCreateModel.return_value = '', ''
        mockFindModel.return_value = None

        self.model.process_request()

        mockCreateModel.assert_called_once()

    @patch.object(ApiGwModel, '_update_model')
    @patch.object(ApiGwModel, '_find_model')
    def test_process_request_calls_update_model_if_model_exists(self, mockFindModel, mockUpdateModel):
        mockFindModel.return_value = True
        mockUpdateModel.return_value = '', ''

        self.model.process_request()

        mockUpdateModel.assert_called_once()

    @patch.object(ApiGwModel, '_delete_model')
    def test_process_request_calls_delete_model_if_state_is_absent(self, mockDeleteModel):
        self.module.params['state'] = 'absent'
        mockDeleteModel.return_value = '', ''

        self.model.process_request()

        mockDeleteModel.assert_called_once()

    @patch.object(ApiGwModel, '_delete_model')
    @patch.object(ApiGwModel, '_find_model')
    def test_process_request_does_not_call_delete_model_if_model_does_not_exist(self, mockFindModel, mockDeleteModel):
        self.module.params['state'] = 'absent'
        mockFindModel.return_value = None

        self.model.process_request()

        mockDeleteModel.assert_not_called()

    @patch.object(ApiGwModel, '_delete_model')
    def test_process_request_calls_exit_json_with_true_and_none_after_delete_model_succeeds(self, mockDeleteModel):
        mock_response = mock.MagicMock()
        self.module.params['state'] = 'absent'
        mockDeleteModel.return_value = mock_response

        self.model.process_request()

        self.module.exit_json.assert_called_with(changed=True, model=None)

    @patch.object(ApiGwModel, '_delete_model')
    @patch.object(ApiGwModel, '_find_model')
    def test_process_request_calls_exit_json_with_changed_false_and_none_if_model_does_not_exist(self, mockFindModel, mockDeleteModel):
        self.module.params['state'] = 'absent'
        mock_response = mock.MagicMock()
        mockDeleteModel.return_value = mock_response
        mockFindModel.return_value = None

        self.model.process_request()

        self.module.exit_json.assert_called_with(changed=False, model=None)

    # _create_model tests
    def test_create_model_creates_models_with_passed_in_description(self):
        mock_response = mock.MagicMock()
        self.model.client.create_model.return_value = mock_response

        changed, response = self.model._create_model()

        self.model.client.create_model.assert_called_with(
            restApiId=self.module.params['rest_api_id'],
            name=self.module.params['name'],
            schema=self.module.params['schema'],
            contentType=self.module.params['content_type'],
            description=self.module.params['description']
        )
        assert changed == True
        assert response == mock_response

    def test_create_model_does_not_call_create_model_if_in_check_mode(self):
        self.module.check_mode = True

        changed, response = self.model._create_model()

        assert changed == True
        assert response == None
        self.model.client.create_model.assert_not_called()

    def test_create_model_calls_fail_json_if_create_model_throws_exception(self):
        self.model.client.create_model.side_effect = ClientError({'Error': {'Code': 'x NotFoundException x'}}, 'error')

        self.model._create_model()

        self.module.fail_json.assert_called_with(msg='Error while creating model: An error occurred (x NotFoundException x) when calling the error operation: Unknown')

    # _update_model tests
    def test_update_model_patches_existing_model(self):
        expected_patches = [
            dict(
                op='replace',
                path='/schema',
                value='schema'
            ),
            dict(
                op='replace',
                path='/description',
                value='description'
            )
        ]

        mock_response = mock.MagicMock()
        self.model.client.update_model.return_value = mock_response

        changed, response = self.model._update_model()

        self.model.client.update_model.assert_called_with(
            restApiId=self.module.params['rest_api_id'],
            modelName=self.module.params['name'],
            patchOperations=expected_patches
        )
        assert changed == True
        assert response == mock_response

    def test_update_model_does_not_update_model_if_in_check_mode(self):
        self.module.check_mode = True
        changed, response = self.model._update_model()

        self.model.client.update_model.assert_not_called()
        assert changed == True
        assert response == None

    def test_update_model_calls_fail_json_if_update_model_throws_exception(self):
        self.model.client.update_model.side_effect = ClientError({'Error': {'Code': 'some error'}}, 'error')

        self.model._update_model()

        self.module.fail_json.assert_called_with(msg='Error while updating model: An error occurred (some error) when calling the error operation: Unknown')

    # _delete_model tests
    def test_delete_model_calls_delete_model(self):
        self.model._delete_model()

        self.model.client.delete_model.assert_called_with(
            restApiId=self.module.params['rest_api_id'],
            modelName=self.module.params['name']
        )

    def test_delete_model_does_not_call_delete_model_if_in_check_mode(self):
        self.module.check_mode = True
        response = self.model._delete_model()

        assert response == None
        self.model.client.delete_model.assert_not_called()

    def test_delete_model_returns_nothing_if_delete_model_works(self):
        response = self.model._delete_model()

        assert response == None

    def test_delete_model_returns_nothing_if_delete_model_returns_not_found_exception(self):
        self.module.fail_json.reset_mock()
        self.model.client.delete_model.side_effect = ClientError({'Error': {'Code': '(NotFoundException)'}}, 'error')

        response = self.model._delete_model()
        
        assert response == None
        self.module.fail_json.assert_not_called()

    def test_delete_model_calls_fail_json_if_delete_model_returns_any_other_exception(self):
        self.model.client.delete_model.side_effect = ClientError({'Error': {'Code': '(AnyOtherException)'}}, 'error')

        self.model._delete_model()

        self.module.fail_json.assert_called_with(msg='Error while deleting model: An error occurred ((AnyOtherException)) when calling the error operation: Unknown')

    # _find_model tests
    def test_find_model_calls_client_get_model(self):
        self.model._find_model()

        self.model.client.get_model.assert_called_with(
            restApiId=self.module.params['rest_api_id'],
            modelName=self.module.params['name'],
            flatten=True
        )

    def test_find_model_returns_true_if_model_exists(self):
        self.model.client.get_model.return_value = True

        actual = self.model._find_model()

        assert actual == True

    def test_find_model_returns_None_if_model_does_not_exist(self):
        self.model.client.get_model.side_effect = ClientError({'Error': {'Code': 'x NotFoundException x'}}, 'something')

        actual = self.model._find_model()

        assert actual == None

    # main test
    @patch.object(apigw_model, 'AnsibleModule')
    @patch.object(apigw_model, 'ApiGwModel')
    def test_main(self, mockApiGwModel, mockAnsibleModule):
        argumentSpec = mock.MagicMock()
        apiGwModel = ApiGwModel(self.module)
        apiGwModel.process_request = mock.MagicMock()
        mockApiGwModel._define_module_argument_spec.return_value = argumentSpec
        mockApiGwModel.return_value = apiGwModel
        
        apigw_model.main()

        basic.AnsibleModule.assert_called_with(argument_spec=argumentSpec, supports_check_mode=True)
        mockApiGwModel.assert_called_once_with(self.module)
        self.assertEqual(1, apiGwModel.process_request.call_count)