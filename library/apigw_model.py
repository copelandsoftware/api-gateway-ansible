from ansible.module_utils import basic
from ansible.module_utils.basic import * # pylint: disable=W0614

try:
  import boto3
  import boto
  from botocore.exceptions import BotoCoreError, ClientError
  HAS_BOTO3 = True
except ImportError:
  HAS_BOTO3 = False

class ApiGwModel:
    def __init__(self, module):
        self.module = module
        if (not HAS_BOTO3):
            self.module.fail_json(msg="boto and boto3 are required for this module")
        self.client = boto3.client('apigateway')

    @staticmethod
    def _define_module_argument_spec():
        return dict(
            rest_api_id=dict(required=True, type=str),
            name=dict(require=True, type=str),
            content_type=dict(required=True, type=str),
            schema=dict(require=False, type=str),
            description=dict(required=False, type=str),
            state=dict(default='present', choices=['present', 'absent'])
        )

    def _does_model_exist(self):
        try:
            self.client.get_model(
                restApiId=self.module.params.get('rest_api_id'),
                modelName=self.module.params.get('name'),
                flatten=True
            )
            return True
        except ClientError:
            return False

    def _delete_model(self):
        if not self.module.check_mode:
            try:
                self.client.delete_model(
                    restApiId=self.module.params.get('rest_api_id'),
                    modelName=self.module.params.get('name')
                )
            except ClientError as e:
                if 'NotFoundException' in e.message:
                    return None
                self.module.fail_json(msg='Error while deleting model: {}'.format(e))

        return None

    def _update_model(self):
        changed = False
        response = None

        patches = []
        if self.module.params.get('description') is not None:
            patches.append(dict(
                op='replace',
                path='/description',
                value=self.module.params.get('description')
            ))
        if self.module.params.get('schema') is not None:
            patches.append(dict(
                op='replace',
                path='/schema',
                value=self.module.params.get('schema')
            ))

        if len(patches) == 0:
            return changed, response

        if self.module.check_mode:
            return True, None

        try:
            response = self.client.update_model(
                restApiId=self.module.params.get('rest_api_id'),
                modelName=self.module.params.get('name'),
                patchOperations=patches
            )
            return True, response
        except ClientError as e:
            self.module.fail_json(msg='Error while updating model: {}'.format(e))

    def _create_model(self):
        if self.module.check_mode:
            return True, None

        content_type = self.module.params.get('content_type')
        args = dict(
            restApiId=self.module.params.get('rest_api_id'),
            name=self.module.params.get('name'),
            contentType=content_type,
            description=self.module.params.get('description', '')
        )
        if content_type == 'application/json':
            args['schema'] = self.module.params['schema']

        try:
            response = self.client.create_model(**args)
            return True, response
        except ClientError as e:
            self.module.fail_json(msg='Error while creating model: {}'.format(e))

    def process_request(self):
        changed = False
        response = None

        if self.module.params.get('state') == 'absent':
            self._delete_model()
            changed = True
        elif self._does_model_exist() == True:
            changed, response = self._update_model()
        else:
            changed, response = self._create_model()

        self.module.exit_json(changed=changed, model=response)

def main():
    module = basic.AnsibleModule(
        argument_spec=ApiGwModel._define_module_argument_spec(),
        supports_check_mode=True
    )
    model = ApiGwModel(module)
    model.process_request()
    return

if __name__ == '__main__':
    main()
