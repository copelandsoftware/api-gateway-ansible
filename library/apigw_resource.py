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
TODO: Complete this
module: apigw_resource
description:
  - An Ansible module to add, update, or remove Resource
    resources for AWS API Gateway.
version_added: "2.2"
options:

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
      try:
        operations = ApiGwResource._build_create_resources_list(self.path_map, self.module.params.get('name'))
        changed = True


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
