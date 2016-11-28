#!/usr/bin/python

# API Gateway Ansible Modules
#
# Modules in this project allow management of the AWS API Gateway service.
#
# Authors:
#  - Brian Felton <bjfelton@gmail.com>
#
# apigw_stage
#    Update or remove API Gateway Stage resources
#

## TODO: Add an appropriate license statement

DOCUMENTATION='''
module: apigw_stage
description: An Ansible module to update or remove an apigateway Stage
version_added: "2.2"
options:
  name:
    description: The name of the stage to deploy
    type: 'string'
    required: True
    aliases: ['stage_name']
  rest_api_id:
    description: The id of the parent rest api
    type: 'string'
    required: True
  description:
    description: The description for the Stage resource to create
    type: 'string'
    default: ''
    required: False
  cache_cluster_enabled:
    description: Cache cluster setting for the Stage resource
    type: 'bool'
    default: False
    required: False
  cache_cluster_size:
    description: Specifies the size of the cache cluster for the Stage resource
    type: 'string'
    default: None
    choices: ['0.5','1.6','6.1','13.5','28.4','58.2','118','237']
    required: False
  method_settings:
    description: List of dictionaries capturing methods to be patched
    type: 'list'
    default: []
    required: False
    options:
      method_name:
        description: Name of the method to be patched
        type: 'string'
        required: True
      method_verb:
        description: Verb of the method to be patched
        type: 'string'
        choices: ['GET', 'PUT', 'POST', 'DELETE', 'HEAD', 'PATCH', 'OPTIONS']
        required: True
      caching_enabled:
        description: Flag indicating if caching should be enabled
        type: 'bool'
        default: False
        required: False
  state:
    description: State of the stage resource
    type: 'string'
    default: 'present'
    choices: ['present', 'absent']
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
- name: Test playbook for creating API GW Method resource
  hosts: localhost
  gather_facts: False
  tasks:
TBD
'''

RETURN = '''
TBD
'''

__version__ = '${version}'

import copy
try:
  import boto3
  import boto
  from botocore.exceptions import BotoCoreError
  HAS_BOTO3 = True
except ImportError:
  HAS_BOTO3 = False

class ApiGwStage:
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
    return dict( name=dict(required=True, aliases=['stage_name']),
                 rest_api_id=dict(required=True),
                 description=dict(required=False),
                 cache_cluster_enabled=dict(required=False, type='bool', default=False),
                 cache_cluster_size=dict(required=False, choices=['0.5','1.6','6.1','13.5','28.4','58.2','118','237']),
                 method_settings=dict(
                   method_name=dict(required=True),
                   method_verb=dict(required=True, choices=['GET','PUT','POST','DELETE','HEAD','OPTIONS','PATCH']),
                   caching_enabled=dict(required=False, default=False, type='bool')
                 ),
                 state=dict(required=False, default='present', choices=['absent', 'present'])
    )

  def process_request(self):
    """
    Process the user's request -- the primary code path
    :return: Returns either fail_json or exit_json
    """
    changed = False
    result = None

    raise NotImplementedError

def main():
    """
    Instantiates the module and calls process_request.
    :return: none
    """
    module = AnsibleModule(
        argument_spec=ApiGwStage._define_module_argument_spec(),
        supports_check_mode=True
    )

    stage = ApiGwStage(module)
    stage.process_request()

from ansible.module_utils.basic import *  # pylint: disable=W0614
if __name__ == '__main__':
    main()
