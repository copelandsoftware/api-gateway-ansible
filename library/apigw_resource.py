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
module: apigw_resource
description:
  - An Ansible module to add or remove Resource
    resources for AWS API Gateway.
version_added: "2.2"
options:
  name:
    description:
      - The name of the resource on which to operate
    required: True
  rest_api_id:
    description:
      - The id of the parent rest api
    required: True
  state:
    description:
      - Determine whether to assert if resource should exist or not
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
- name: Add resource to Api Gateway
  hosts: localhost
  gather_facts: False
  connection: local
  tasks:
    - name: Create resource
      apigw_resource:
        name: '/thing/{param}/awesomeness'
        rest_api_id: 'abcd1234'
        state: present
      register: resource

    - name: debug
      debug: var=resource

- name: Rest api from Api Gateway
  hosts: localhost
  gather_facts: False
  connection: local
  tasks:
    - name: Delete resource
      apigw_rest_api:
        name: '/thing/not-awesome'
        rest_api_id: 'abcd1234'
        state: absent
      register: resource

    - name: debug
      debug: var=resource
'''

RETURN = '''
# Sample create output
{
    "changed": true,
    "invocation": {
        "module_args": {
            "name": "/test",
            "rest_api_id": "abc123def567",
            "state": "present"
        }
    },
    "resource": {
        "ResponseMetadata": {
            "HTTPHeaders": {
                "content-length": "73",
                "content-type": "application/json",
                "date": "Wed, 02 Nov 2016 20:47:23 GMT",
                "x-amzn-requestid": "an id was here"
            },
            "HTTPStatusCode": 201,
            "RequestId": "an id was here",
            "RetryAttempts": 0
        },
        "id": "abc55tda",
        "parentId": "xyz123",
        "path": "/test",
        "pathPart": "test"
    }
}
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
      'paths': {}
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
      resources = self.client.get_resources(restApiId=self.module.params.get('rest_api_id'), limit=500)

      for res in resources.get('items'):
        self.path_map['paths'][res.get('path')] = {'id': res.get('id')}
        if 'parentId' in res:
          self.path_map['paths'][res.get('path')]['parentId'] = res.get('parentId')

    except BotoCoreError as e:
      self.module.fail_json(msg="Error calling boto3 get_resources: {}".format(e))

  @staticmethod
  def _build_create_resources_list(path_map, resource):
    """
    Splits resource and builds a list of create operations
    :param path_map: A map containing path parts
    :param resource: The url to create
    :return: Ordered list of resources to create
    """
    operations = []
    last_part = ''
    parts = resource.split('/')[1:]
    for part in parts:
      new_part = "{0}/{1}".format(last_part, part)
      if new_part not in path_map['paths']:
        operations.append({'part': part, 'path': new_part, 'parent': '/' if last_part == '' else last_part})
      last_part = new_part

    return operations

  def _create_resource(self):
    """
    Create an API Gateway Resource
    :return: (changed, result)
              changed: Boolean indicating whether or not a change occurred
              result: Output of the create_resource call
    """
    changed = False
    result = None
    if self.module.params.get('name') not in self.path_map['paths']:
      changed = True

      if not self.module.check_mode:
        try:
          operations = ApiGwResource._build_create_resources_list(self.path_map, self.module.params.get('name'))

          for op in operations:
            part = op['part']
            result = self.client.create_resource(
              restApiId=self.module.params.get('rest_api_id'),
              parentId=self.path_map['paths'][op['parent']]['id'],
              pathPart=part
            )
            self.path_map['paths'][op['path']] = {'id': result.get('id')}
        except BotoCoreError as e:
          self.module.fail_json(msg="Error calling boto3 create_resource: {}".format(e))
    else:
      result = copy.deepcopy(self.path_map['paths'][self.module.params.get('name')])
      result['path'] = self.module.params.get('name')

    return changed, result

  def _delete_resource(self):
    """
    Delete an API Gateway Resource
    :return: (changed, result)
              changed: Boolean indicating whether or not a change occurred
              result: Output of the delete_resource call
    """
    changed = False
    if self.module.params.get('name') in self.path_map['paths']:
      try:
        changed = True
        if not self.module.check_mode:
          self.client.delete_resource(
            restApiId=self.module.params.get('rest_api_id'),
            resourceId=self.path_map['paths'][self.module.params.get('name')]['id']
          )
      except BotoCoreError as e:
        self.module.fail_json(msg="Error calling boto3 delete_resource: {}".format(e))

    return changed, None

  def process_request(self):
    """
    Process the user's request -- the primary code path
    :return: Returns either fail_json or exit_json
    """
    changed = False
    result = None
    self._build_resource_dictionary()
    if self.module.params.get('state') == 'absent':
      (changed, result) = self._delete_resource()
    else:
      (changed, result) = self._create_resource()

    self.module.exit_json(changed=changed, resource=result)

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
