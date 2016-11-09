#!/usr/bin/python

# API Gateway Ansible Modules
#
# Modules in this project allow management of the AWS API Gateway service.
#
# Authors:
#  - Brian Felton <bjfelton@gmail.com>
#
# apigw_resource
#    Manage creation, update, and removal of API Gateway Method resources
#

## TODO: Add an appropriate license statement

DOCUMENTATION='''
module: apigw_method
description:
  - An Ansible module to add, update, or remove AWS API Gateway
    method resources
version_added: "2.2"
options:
  name:
    description:
      - The name of the method on which to operate
    choices: ['get', 'put', 'post', 'delete', 'patch', 'head']
    required: True
  rest_api_id:
    description:
      - The id of the parent rest api
    required: True
  resource_id:
    description:
      - The id of the resource to which the method belongs
    required: True
  state:
    description:
      - Determine whether to assert if resource should exist or not
    choices: ['present', 'absent']
    default: 'present'
    required: False

TODO: FINISH THIS

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
TODO: FINISH THIS
'''

RETURN = '''
TODO: FINISH THIS
'''

__version__ = '${version}'

import copy
try:
  import boto3
  import boto
  from botocore.exceptions import BotoCoreError, ClientError
  HAS_BOTO3 = True
except ImportError:
  HAS_BOTO3 = False

class ApiGwMethod:
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
    return dict( name=dict(
                   required=True,
                   choices=['GET', 'PUT', 'POST', 'DELETE', 'PATCH', 'HEAD', 'ANY', 'OPTIONS'],
                   aliases=['method']
                 ),
                 rest_api_id=dict(required=True),
                 resource_id=dict(required=True),
                 authorization_type=dict(required=False, default='NONE'),
                 authorizer_id=dict(required=False),
                 api_key_required=dict(required=False, type='bool', default=False),
                 request_params=dict(
                   type='list',
                   required=False,
                   default=[],
                   name=dict(required=True),
                   location=dict(required=True, choices=['querystring', 'path', 'header']),
                   param_required=dict(type='bool')
                 ),
                 state=dict(default='present', choices=['present', 'absent'])
    )

  def _find_method(self):
    """
    Execute a find to determine if the method exists
    :return: Returns result of find or exits with fail_json
    """
    p = self.module.params

    try:
      response = self.client.get_method(
          restApiId=p.get('rest_api_id'),
          resourceId=p.get('resource_id'),
          httpMethod=p.get('name')
      )
      return response
    except ClientError as e:
      if 'NotFoundException' in e.message:
        return None
      else:
        self.module.fail_json(msg='Error calling boto3 get_method: {}'.format(e))
    except BotoCoreError as e:
      self.module.fail_json(msg='Error calling boto3 get_method: {}'.format(e))

  def _delete_method(self):
    """
    Delete the method
    :return: nothing
    """
    if not self.module.check_mode:
      try:
        self.client.delete_method(
          restApiId=self.module.params.get('rest_api_id'),
          resourceId=self.module.params.get('resource_id'),
          httpMethod=self.module.params.get('name')
        )
      except BotoCoreError as e:
        self.module.fail_json(msg="Error calling boto3 delete_method: {}".format(e))

  def _create_method(self):
    """
    Create or update the method
    :return: nothing
    """
    response = None
    changed = True
    if not self.module.check_mode:
      try:
        changed = True
        response = self.client.put_method(
          restApiId=self.module.params.get('rest_api_id'),
          resourceId=self.module.params.get('resource_id'),
          httpMethod=self.module.params.get('name'),
          authorizationType=self.module.params.get('authorization_type')
        )
      except BotoCoreError as e:
        self.module.fail_json(msg="Error calling boto3 put_method: {}".format(e))

    return changed, response

  def process_request(self):
    """
    Process the user's request -- the primary code path
    :return: Returns either fail_json or exit_json
    """
    self.method = self._find_method()

    changed = False
    response = None

    if self.method is not None and self.module.params.get('state') == 'absent':
      self._delete_method()
      changed = True
    elif self.module.params.get('state') == 'present':
      (changed, response) = self._create_method()

    self.module.exit_json(changed=changed, method=response)

def main():
    """
    Instantiates the module and calls process_request.
    :return: none
    """
    module = AnsibleModule(
        argument_spec=ApiGwMethod._define_module_argument_spec(),
        supports_check_mode=True
    )

    rest_api = ApiGwMethod(module)
    rest_api.process_request()

from ansible.module_utils.basic import *  # pylint: disable=W0614
if __name__ == '__main__':
    main()
