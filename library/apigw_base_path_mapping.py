#!/usr/bin/python

# API Gateway Ansible Modules
#
# Modules in this project allow management of the AWS API Gateway service.
#
# Authors:
#  - Brian Felton <github: bjfelton>
#
# apigw_base_path_mapping
#    Manage creation, update, and removal of API Gateway Base Path Mapping resources
#

# MIT License
# 
# Copyright (c) 2016 Brian Felton, Emerson
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


DOCUMENTATION='''
module: apigw_base_path_mapping
description: An Ansible module to add, update, or remove Base Path Mapping
  resources for AWS API Gateway.
version_added: "2.2"
options:
  name:
    description: The domain name of the Base Path Mapping resource on which to operate
    required: True
    aliases: ['domain_name']
  rest_api_id:
    description: The id of the Rest API to which this BasePathMapping belongs.
      Required to create a base path mapping.
    default: None
    required: False
  base_path:
    description: The base path name that callers of the api must provide.
      Required when updating or deleting the mapping.
    default: (none)
    required: False
  stage:
    description: The name of the api's stage to which to apply this mapping.
      Required to create the base path mapping.
    default: None
    required: False
  state:
    description: Should base_path_mapping exist or not
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
---
- hosts: localhost
  gather_facts: False
  tasks:
  - name: do base path stuff
    apigw_base_path_mapping:
      name: dev.example.com
      rest_api_id: abcd1234
      stage: live
      state: present
    register: bpm

  - debug: var=bpm
'''

RETURN = '''
{
  "bpm": {
    "base_path_mapping": {
      "basePath": "(none)",
      "restApiId": "41pz250gl3",
      "stage": "live"
    },
    "changed": false
  }
}
'''

__version__ = '${version}'

try:
  import boto3
  import boto
  from botocore.exceptions import BotoCoreError
  HAS_BOTO3 = True
except ImportError:
  HAS_BOTO3 = False

class ApiGwBasePathMapping:
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
    return dict( name=dict(required=True, aliases=['domain_name']),
                 rest_api_id=dict(required=False),
                 base_path=dict(required=False, default='(none)'),
                 stage=dict(required=False),
                 state=dict(default='present', choices=['present', 'absent']),
    )

  def _retrieve_base_path_mapping(self):
    """
    Retrieve all base_path_mappings in the account and match them against the provided name
    :return: Result matching the provided api name or an empty hash
    """
    resp = None
    try:
      get_resp = self.client.get_base_path_mappings(domainName=self.module.params['name'])

      for item in get_resp.get('items', []):
        if item['basePath'] == self.module.params.get('base_path', '(none)'):
          resp = item
    except BotoCoreError as e:
      self.module.fail_json(msg="Error when getting base_path_mappings from boto3: {}".format(e))

    return resp

  def _delete_base_path_mapping(self):
    """
    Delete base_path_mapping that matches the returned id
    :return: True
    """
    try:
      if not self.module.check_mode:
        self.client.delete_base_path_mapping(
          domainName=self.module.params['name'],
          basePath=self.module.params['base_path']
        )
      return True
    except BotoCoreError as e:
      self.module.fail_json(msg="Error when deleting base_path_mapping via boto3: {}".format(e))

  def _create_base_path_mapping(self):
    """
    Create base_path_mapping from provided args
    :return: True, result from create_base_path_mapping
    """
    bpm = None
    changed = False

    if self.module.params.get('rest_api_id', None) is None:
      self.module.fail_json(msg="Field 'rest_api_id' is required when attempting to create a Base Path Mapping resource")

    else:
      try:
        changed = True
        if not self.module.check_mode:
          args = dict(
            domainName=self.module.params['name'],
            restApiId=self.module.params['rest_api_id'],
            basePath=self.module.params.get('base_path', '(none)'),
          )

          stage = self.module.params.get('stage', None)
          if stage is not None and stage != '':
            args['stage'] = stage

          bpm = self.client.create_base_path_mapping(**args)
      except BotoCoreError as e:
        self.module.fail_json(msg="Error when creating base_path_mapping via boto3: {}".format(e))

    return (changed, bpm)

  @staticmethod
  def _create_patches(params, me):
    patches = []

    stage = params.get('stage', '')
    if stage != '' and stage is not None and stage != me['stage']:
      patches.append({'op': 'replace', 'path': '/stage', 'value': stage})

    return patches

  def _update_base_path_mapping(self):
    """
    Create base_path_mapping from provided args
    :return: True, result from create_base_path_mapping
    """
    bpm = self.me
    changed = False

    try:
      patches = ApiGwBasePathMapping._create_patches(self.module.params, self.me)
      if patches:
        changed = True

        if not self.module.check_mode:
          self.client.update_base_path_mapping(
            domainName=self.module.params['name'],
            basePath=self.module.params['base_path'],
            patchOperations=patches
          )
          bpm = self._retrieve_base_path_mapping()
    except BotoCoreError as e:
      self.module.fail_json(msg="Error when updating base_path_mapping via boto3: {}".format(e))

    return (changed, bpm)

  def process_request(self):
    """
    Process the user's request -- the primary code path
    :return: Returns either fail_json or exit_json
    """
    bpm = None
    changed = False
    self.me = self._retrieve_base_path_mapping()

    if self.module.params.get('state', 'present') == 'absent' and self.me is not None:
      changed = self._delete_base_path_mapping()
    elif self.module.params.get('state', 'present') == 'present':
      if self.me is None:
        (changed, bpm) = self._create_base_path_mapping()
      else:
        (changed, bpm) = self._update_base_path_mapping()

    self.module.exit_json(changed=changed, base_path_mapping=bpm)

def main():
    """
    Instantiates the module and calls process_request.
    :return: none
    """
    module = AnsibleModule(
        argument_spec=ApiGwBasePathMapping._define_module_argument_spec(),
        supports_check_mode=True
    )

    base_path_mapping = ApiGwBasePathMapping(module)
    base_path_mapping.process_request()

from ansible.module_utils.basic import *  # pylint: disable=W0614
if __name__ == '__main__':
    main()
