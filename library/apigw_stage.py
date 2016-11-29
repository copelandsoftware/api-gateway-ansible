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
#    Only processes 'replace' patches.
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
  from botocore.exceptions import BotoCoreError, ClientError
  HAS_BOTO3 = True
except ImportError:
  HAS_BOTO3 = False

def create_patch(path, value):
  return {'op': 'replace', 'path': path, 'value': str(value)}

def build_patch_args(stage, params):
  args = None

  arg_map = {
    'description': {'boto_field': 'description', 'default': ''},
    'cache_cluster_enabled': {'boto_field': 'cacheClusterEnabled', 'default': False},
    'cache_cluster_size': {'boto_field': 'cacheClusterSize', 'default': ''},
  }

  stage = {} if stage is None else stage
  stg_methods = stage.get('methodSettings', {})

  patches = []
  for ans_param, blob in arg_map.iteritems():
    if ans_param in params:
      if blob['boto_field'] in stage and str(params[ans_param]) == str(stage[blob['boto_field']]):
        pass
      else:
        patches.append(create_patch("/{}".format(blob['boto_field']), params[ans_param]))
    else:
      if blob['boto_field'] in stage and str(stage[blob['boto_field']]) != str(blob['default']):
        patches.append(create_patch("/{}".format(blob['boto_field']), blob['default']))

  for m in params.get('method_settings', []):
    method_key = "/{0}/{1}".format(re.sub('/', '~1', m['method_name']), m['method_verb'])

    if method_key not in stg_methods or str(stg_methods[method_key]['cachingEnabled']) != str(m.get('caching_enabled', False)):
      patches.append(create_patch("{}/cache/enabled".format(method_key), m.get('caching_enabled', False)))

  if patches:
    args = {
      'restApiId': params['rest_api_id'],
      'stageName': params['name'],
      'patchOperations': patches
    }

  return args

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
                   required=False,
                   default=[],
                   type='list',
                   method_name=dict(required=True),
                   method_verb=dict(required=True, choices=['GET','PUT','POST','DELETE','HEAD','OPTIONS','PATCH']),
                   caching_enabled=dict(required=False, default=False, type='bool')
                 ),
                 state=dict(required=False, default='present', choices=['absent', 'present'])
    )

  def _find_stage(self):
    """
    Attempts to find the stage
    :return: Returns boolean indicating whether api has been called.  Calls fail_json
             on error
    """
    try:
      return self.client.get_stage(
          restApiId=self.module.params.get('rest_api_id'),
          stageName=self.module.params.get('name')
      )
    except ClientError as e:
      if 'NotFoundException' in e.message:
        return None
      else:
        self.module.fail_json(msg='Error while finding stage via boto3: {}'.format(e))
    except BotoCoreError as e:
      self.module.fail_json(msg='Error while finding stage via boto3: {}'.format(e))


  def _delete_stage(self):
    """
    Delete the stage
    :return: Returns boolean indicating whether api has been called.  Calls fail_json
             on error
    """
    changed = False

    if not self.module.check_mode:
      try:
        changed = True
        self.client.delete_stage(
          restApiId=self.module.params.get('rest_api_id'),
          stageName=self.module.params.get('name')
        )
      except BotoCoreError as e:
        self.module.fail_json(msg="Error while deleting stage via boto3: {}".format(e))

    return changed

  def _update_stage(self):
    """
    Update the stage
    :return:
      changed - boolean indicating whether a change has occurred
      result  - results of a find after a change has occurred
    """
    changed = False
    result = None

    patch_args = build_patch_args(self.stage, self.module.params)

    try:
      if patch_args is not None:
        changed = True
        if not self.module.check_mode:
          self.client.update_stage(**patch_args)
          result = self.client.get_stage(
            restApiId=self.module.params.get('rest_api_id'),
            stageName=self.module.params.get('name')
          )
    except BotoCoreError as e:
      self.module.fail_json(msg="Error while updating stage via boto3: {}".format(e))

    return (changed, result)

  def process_request(self):
    """
    Process the user's request -- the primary code path
    :return: Returns either fail_json or exit_json
    """
    changed = False
    result = None

    self.stage = self._find_stage()

    if self.stage is not None and self.module.params.get('state', 'present') == 'absent':
      changed = self._delete_stage()
    elif self.module.params.get('state', 'present') == 'present':
      changed, result = self._update_stage()

    self.module.exit_json(changed=changed, stage=result)

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
