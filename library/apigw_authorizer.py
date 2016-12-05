#!/usr/bin/python

# API Gateway Ansible Modules
#
# Modules in this project allow management of the AWS API Gateway service.
#
# Authors:
#  - Brian Felton <bjfelton@gmail.com>
#
# apigw_authorizer
#    Manage creation, update, and removal of API Gateway REST APIs
#

## TODO: Add an appropriate license statement

DOCUMENTATION='''
module: apigw_authorizer
description:
  - An Ansible module to add, update, or remove Authorizer resources for
    AWS API Gateway.
version_added: "2.2"
options:
  rest_api_id:
    description: The id of the Rest API to which this Authorizer belongs
    required: True
  name:
    description: The name of the authorizer on which to operate
    required: True
    aliases: ['authorizer']
  type:
    description: Type of the authorizer (required when C(state) is 'present')
    required: False
    choices: ['token', 'cognito_user_pools']
    default: None
  uri:
    description: The autorizer's uri (required with C(state) is 'present')
    required: False
    default: None
  identity_source:
    description: Source of the identity in an incoming request (required when C(state) is 'present')
    required: False
    default: None
  identity_validation_expression:
    description: Validation expression for the incoming entity
    required: False
    default: ''
  provider_arns:
    description:
    required: False
    default: []
  auth_type:
    description: Optional customer-defined field used in Swagger docs - has no functional impact
    required: False
    default: None
  credentials:
    description: Specifies credentials required for the authorizer, if any
    required: False
    default: None
  result_ttl_seconds:
    description: The TTL of cached authorizer results in seconds
    required: False
    default: 0
  state:
    description: Should authorizer exist or not
    choices: ['present', 'absent']
    default: 'present'
    required: False
requirements:
    - python = 2.7
    - boto
    - boto3
notes:
    - This module requires that you have boto and boto3 installed and that your
      credentials are created or stored in a way that is compatible (see
      U(https://boto3.readthedocs.io/en/latest/guide/quickstart.html#configuration)).
'''

EXAMPLES = '''
TBD
'''

RETURN = '''
TBD
'''

__version__ = '${version}'

try:
  import boto3
  import boto
  from botocore.exceptions import BotoCoreError
  HAS_BOTO3 = True
except ImportError:
  HAS_BOTO3 = False

class ApiGwAuthorizer:
  def __init__(self, module):
    """
    Constructor
    """
    self.module = module
    if (not HAS_BOTO3):
      self.module.fail_json(msg="boto and boto3 are required for this module")
    self.client = boto3.client('apigateway')

  @staticmethod
  def _define_module_argument_spec():
    """
    Defines the module's argument spec
    :return: Dictionary defining module arguments
    """
    return dict( rest_api_id=dict(required=True),
                 name=dict(required=True),
                 type=dict(required=False, choices=['token', 'cognito_user_pools']),
                 uri=dict(required=False),
                 identity_source=dict(required=False),
                 identity_validation_expression=dict(required=False, default=''),
                 provider_arns=dict(required=False, type='list', default=[]),
                 auth_type=dict(required=False),
                 credentials=dict(required=False),
                 result_ttl_seconds=dict(required=False, type='int', default=0),
                 state=dict(default='present', choices=['present', 'absent']),
    )

  def _retrieve_authorizer(self):
    """
    Retrieve all authorizers in the account and match them against the provided name
    :return: Result matching the provided api name or an empty hash
    """
    resp = None
    try:
      get_resp = self.client.get_authorizers(restApiId=self.module.params['rest_api_id'])

      for item in get_resp.get('items', []):
        if item['name'] == self.module.params.get('name'):
          resp = item
    except BotoCoreError as e:
      self.module.fail_json(msg="Error when getting authorizers from boto3: {}".format(e))

    return resp

  @staticmethod
  def _is_changed(api, params):
    """
    Determine if the discovered authorizer differs from the user-provided params
    :param api: Result from _retrieve_authorizer()
    :param params: Module params
    :return: Boolean telling if result matches params
    """
    raise NotImplementedError

  def process_request(self):
    """
    Process the user's request -- the primary code path
    :return: Returns either fail_json or exit_json
    """
    self.me = self._retrieve_authorizer()

def main():
    """
    Instantiates the module and calls process_request.
    :return: none
    """
    module = AnsibleModule(
        argument_spec=ApiGwAuthorizer._define_module_argument_spec(),
        supports_check_mode=True
    )

    authorizer = ApiGwAuthorizer(module)
    authorizer.process_request()

from ansible.module_utils.basic import *  # pylint: disable=W0614
if __name__ == '__main__':
    main()
