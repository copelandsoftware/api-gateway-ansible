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
                rest_api_id=dict(required=True, type=str),
                name=dict(require=True, type=str),
                content_type=dict(required=True, type=str),
                schema=dict(require=False, type=str),
                description=dict(required=False, type=str),
                state=dict(default='present', choices=['present', 'absent'])
            )
        )

    # process_request tests
    @patch.object(ApiGwModel, '_does_model_exist')
    def test_process_request_calls_does_model_exist(self, mockDoesModelExist):
        self.model.process_request()

        mockDoesModelExist.assert_called_once()

    @patch.object(ApiGwModel, '_create_model')
    @patch.object(ApiGwModel, '_does_model_exist')
    def test_process_request_calls_exit_json_with_changed_and_response_from_create_model(self, mockDoesModelExist, mockCreateModel):
        mockDoesModelExist.return_value = False
        mock_changed = mock.MagicMock()
        mock_response = mock.MagicMock()
        mockCreateModel.return_value = mock_changed, mock_response

        self.model.process_request()

        self.module.exit_json.assert_called_with(changed=mock_changed, model=mock_response)

    @patch.object(ApiGwModel, '_update_model')
    @patch.object(ApiGwModel, '_does_model_exist')
    def test_process_request_calls_exit_json_with_changed_and_response_from_update_model(self, mockDoesModelExist, mockUpdateModel):
        mockDoesModelExist.return_value = True
        mock_changed = mock.MagicMock()
        mock_response = mock.MagicMock()
        mockUpdateModel.return_value = mock_changed, mock_response

        self.model.process_request()

        self.module.exit_json.assert_called_with(changed=mock_changed, model=mock_response)

    @patch.object(ApiGwModel, '_create_model')
    @patch.object(ApiGwModel, '_does_model_exist')
    def test_process_request_calls_create_model_if_model_does_not_exist(self, mockDoesModelExist, mockCreateModel):
        mockCreateModel.return_value = '', ''
        mockDoesModelExist.return_calue = False

        self.model.process_request()

        mockCreateModel.assert_called_once()

    @patch.object(ApiGwModel, '_update_model')
    @patch.object(ApiGwModel, '_does_model_exist')
    def test_process_request_calls_update_model_if_model_exists(self, mockDoesModelExist, mockUpdateModel):
        mockDoesModelExist.return_value = True
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
    def test_process_request_calls_exit_json_with_true_and_none_after_delete_model_succeeds(self, mockDeleteModel):
        mock_response = mock.MagicMock()
        self.module.params['state'] = 'absent'
        mockDeleteModel.return_value = mock_response

        self.model.process_request()

        self.module.exit_json.assert_called_with(changed=True, model=None)

    # _create_model tests
    def test_create_model_creates_models_with_required_and_optional_properties(self):
        mock_response = mock.MagicMock()
        self.model.client.create_model.return_value = mock_response

        changed, response = self.model._create_model()

        self.model.client.create_model.assert_called_with(
            restApiId=self.module.params['rest_api_id'],
            name=self.module.params['name'],
            contentType=self.module.params['content_type'],
            description=self.module.params['description']
        )
        assert changed == True
        assert response == mock_response

    def test_create_model_makes_model_with_schema_if_content_type_is_application_json(self):
        self.module.params = {
            'rest_api_id': 'rest_id',
            'name': 'model2',
            'content_type': 'application/json',
            'schema': 'schema'
        }

        self.model._create_model()

        self.model.client.create_model.assert_called_with(
            restApiId=self.module.params['rest_api_id'],
            name=self.module.params['name'],
            contentType=self.module.params['content_type'],
            description='',
            schema=self.module.params['schema']
        )

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
        test_cases = [
            {
                'params': dict(
                    rest_api_id='some_id',
                    name='model',
                    description='lengthy description'
                ),
                'expected_patches': [
                    dict(
                        op='replace',
                        path='/description',
                        value='lengthy description'
                    )
                ]
            },
            {
                'params': dict(
                    rest_api_id='some_id',
                    name='model_name',
                    schema='schema'
                ),
                'expected_patches': [
                    dict(
                        op='replace',
                        path='/schema',
                        value='schema'
                    )
                ]
            },
            {
                'params': dict(
                    rest_api_id='some_id',
                    name='name',
                    description='description',
                    schema='schema'
                ),
                'expected_patches': [
                    dict(
                        op='replace',
                        path='/description',
                        value='description'
                    ),
                    dict(
                        op='replace',
                        path='/schema',
                        value='schema'
                    )
                ]
            }
        ]

        for case in test_cases:
            mock_response = mock.MagicMock()
            self.model.client.update_model.return_value = mock_response
            self.module.params = case['params']

            changed, response = self.model._update_model()

            self.model.client.update_model.assert_called_with(
                restApiId=self.module.params['rest_api_id'],
                modelName=self.module.params['name'],
                patchOperations=case['expected_patches']
            )
            assert changed == True
            assert response == mock_response

    def test_update_model_does_not_update_model_if_no_patches_were_found(self):
        self.module.params = {
            'rest_api_id': 'rest_id',
            'name': 'name'
        }
        changed, response = self.model._update_model()

        self.model.client.update_model.assert_not_called()
        assert changed == False
        assert response == None

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

    # _does_model_exist tests
    def test_does_model_exist_calls_client_get_model(self):
        self.model._does_model_exist()

        self.model.client.get_model.assert_called_with(
            restApiId=self.module.params['rest_api_id'],
            modelName=self.module.params['name'],
            flatten=True
        )

    def test_does_model_exist_returns_true_if_model_exists(self):
        self.model.client.get_model.return_value = True

        actual = self.model._does_model_exist()

        assert actual == True

    def test_does_model_exist_returns_false_if_model_does_not_exist(self):
        self.model.client.get_model.side_effect = ClientError({'Error': {'Code': 'x NotFoundException x'}}, 'something')

        actual = self.model._does_model_exist()

        assert actual == False

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