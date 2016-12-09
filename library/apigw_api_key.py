#!/usr/bin/python

# API Gateway Ansible Modules
#
# Modules in this project allow management of the AWS API Gateway service.
#
# Authors:
#  - Brian Felton <bjfelton@gmail.com>
#
# apigw_api_key
#    Manage creation, update, and removal of API Gateway ApiKey resources
#

## TODO: Add an appropriate license statement

DOCUMENTATION='''
module: apigw_api_key
description: An Ansible module to add, update, or remove ApiKey
  resources for AWS API Gateway.
version_added: "2.2"
options:
  name:
    description: The domain name of the ApiKey resource on which to operate
    type: string
    required: True
  value:
    description: Value of the api key. Required for create.
    type: string
    default: None
    required: False
  description:
    description: ApiKey description
    type: string
    default: None
    required: False
  enabled:
    description: Can ApiKey be used by called
    type: bool
    default: False
    required: False
  generate_distinct_id:
    description: Specifies whether key identifier is distinct from created apikey value
    type: bool
    default: False
    required: False
  customer_id:
    description: AWS Marketplace customer identifier when integrating with AWS SaaS marketplace
    type: string
    default: None
    required: False
  state:
    description: Should api_key exist or not
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

class ApiGwApiKey:
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
    return dict( name=dict(required=True),
                 description=dict(required=False),
                 value=dict(required=False),
                 customer_id=dict(required=False),
                 enabled=dict(required=False, type='bool', default=False),
                 generate_distinct_id=dict(required=False, type='bool', default=False),
                 state=dict(default='present', choices=['present', 'absent']),
    )

  def process_request(self):
    """
    Process the user's request -- the primary code path
    :return: Returns either fail_json or exit_json
    """
    raise NotImplementedError

def main():
    """
    Instantiates the module and calls process_request.
    :return: none
    """
    module = AnsibleModule(
        argument_spec=ApiGwApiKey._define_module_argument_spec(),
        supports_check_mode=True
    )

    api_key = ApiGwApiKey(module)
    api_key.process_request()

from ansible.module_utils.basic import *  # pylint: disable=W0614
if __name__ == '__main__':
    main()
