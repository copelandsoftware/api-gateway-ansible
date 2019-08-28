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
            description=dict(required=False, type=str)
        )

    def _upsert_model(self):
        rest_api_id = self.module.params.get('rest_api_id')
        args = {
            'restApiId': rest_api_id,
            'name': self.module.params.get('name'),
            'contentType': self.module.params.get('content_type'),
            'description': self.module.params.get('description', '')
        }

        self.client.create_model(**args)

    def process_request(self):
        self._upsert_model()
        return

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
