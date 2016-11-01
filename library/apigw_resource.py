#!/usr/bin/python

# API Gateway Ansible Modules
#
# Modules in this project allow management of the AWS API Gateway service.
#
# Authors:
#  - Brian Felton <bjfelton@gmail.com>
#
# apigw_resource
#    Manage creation, update, and removal of API Gateway Resource resources
#

## TODO: Add an appropriate license statement

DOCUMENTATION='''
TODO: Update this
module: apigw_resource
description:
  - An Ansible module to add, update, or remove REST API resources for
    AWS API Gateway.
version_added: "2.2"
options:
  name:
    description:
      - The name of the rest api on which to operate
    required: True
  description:
    description:
      - A description for the rest api
    required: False
  state:
    description:
      - Determine whether to assert if api should exist or not
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
TODO: Complete me
'''

RETURN = '''
TODO: Add Example
'''

__version__ = '${version}'

try:
  import boto3
  import boto
  from botocore.exceptions import BotoCoreError
  HAS_BOTO3 = True
except ImportError:
  HAS_BOTO3 = False

class ApiGwResource:
  def __init__(self, module):
    """
    Constructor
    """
    self.module = module
    if (not HAS_BOTO3):
      self.module.fail_json(msg="boto and boto3 are required for this module")
    self.client = boto3.client('apigateway')
    self.path_map = {
      'paths': {},
      'has_children': {}
    }

  @staticmethod
  def _define_module_argument_spec():
    """
    Defines the module's argument spec
    :return: Dictionary defining module arguments
    """
    return dict( name=dict(required=True),
                 rest_api_id=dict(required=True),
                 state=dict(default='present', choices=['present', 'absent'])
    )

  def _build_resource_dictionary(self):
    try:
      resources = self.client.get_resources(restApiId=self.module.params.get('rest_api_id'))

      for res in resources.get('items'):
        self.path_map['paths'][res.get('path')] = {'id': res.get('id')}
        if 'parentId' in res:
          self.path_map['paths'][res.get('path')]['parent_id'] = res.get('parentId')
          self.path_map['has_children'][res.get('parentId')] = True

    except BotoCoreError as e:
      self.module.fail_json(msg="Error calling boto3 get_resources: {}".format(e))


  def process_request(self):
    """
    Process the user's request -- the primary code path
    :return: Returns either fail_json or exit_json
    """
    self._build_resource_dictionary()


def main():
    """
    Instantiates the module and calls process_request.
    :return: none
    """
    module = AnsibleModule(
        argument_spec=ApiGwResource._define_module_argument_spec(),
        supports_check_mode=True
    )

    rest_api = ApiGwResource(module)
    rest_api.process_request()

from ansible.module_utils.basic import *  # pylint: disable=W0614
if __name__ == '__main__':
    main()
