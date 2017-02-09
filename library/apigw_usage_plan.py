#!/usr/bin/python

# API Gateway Ansible Modules
#
# Modules in this project allow management of the AWS API Gateway service.
#
# Authors:
#  - Brian Felton <github: bjfelton>
#
# apigw_usage_plan
#    Manage creation, update, and removal of API Gateway UsagePlan resources
#
# NOTE: While it is possible via the boto api to update the UsagePlan's name,
#       this module does not support this functionality since it searches
#       for the UsagePlan's id by its name.

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
module: apigw_usage_plan
author: Brian Felton (@bjfelton)
short_description: Add, update, or remove UsagePlan and UsagePlanKey resources
description:
- Basic CRUD operations on Usage Plan Key resources
- Does not support updating name (see Notes)
version_added: "2.2"
options:
  name:
    description:
    - The domain name of the UsagePlan resource on which to operate
    type: string
    required: True
  description:
    description:
    - UsagePlan description
    type: string
    default: None
    required: False
  api_stages:
    description:
    - List of associated api stages
    type: list
    default: []
    required: False
    options:
      rest_api_id:
        description:
        - ID of the associated API stage in the usage plan
        type: string
        required: True
      stage:
        description:
        - API stage name of the associated API stage in the usage plan
        type: string
        required: True
  throttle_burst_limit:
    description:
    - API request burst limit
    type: int
    default: -1
    required: False
  throttle_rate_limit:
    description:
    - API request steady-state limit
    type: double
    default: -1.0
    required: False
  quota_limit:
    description:
    - Maxiumum number of requests that can be made in a given time period
    type: integer
    default: -1
    required: False
  quota_offset:
    description:
    - Number of requests subtracted from the given limit in the initial time period
    type: integer
    default: -1
    required: False
  quota_period:
    description:
    - The time period in which the limit applies
    type: string
    default: ''
    choices: ['', 'DAY', 'WEEK', 'MONTH']
    required: False
  state:
    description:
    - Should usage_plan exist or not
    choices: ['present', 'absent']
    default: 'present'
    required: False
requirements:
    - python = 2.7
    - boto
    - boto3
notes:
- While it is possible via the boto api to update the UsagePlan's name, this module does not support this functionality since it searches for the UsagePlan's id by its name.
- This module requires that you have boto and boto3 installed and that your credentials are created or stored in a way that is compatible (see U(https://boto3.readthedocs.io/en/latest/guide/quickstart.html#configuration)).
'''

EXAMPLES = '''
---
- hosts: localhost
  gather_facts: False
  tasks:
  - name: usage plan creation
    apigw_usage_plan:
      name: testplan
      description: 'this is an awesome test'
      api_stages:
        - rest_api_id: abcde12345
          stage: live
      throttle_burst_limit: 111
      throttle_rate_limit: 222.0
      quota_limit: 333
      quota_offset: 0
      quota_period: WEEK
      state: "{{ state | default('present') }}"
    register: plan

  - debug: var=plan
'''

RETURN = '''
{
  "plan": {
    "changed": true,
    "usage_plan": {
      "ResponseMetadata": {
        "HTTPHeaders": {
          "content-length": "223",
          "content-type": "application/json",
          "date": "Thu, 15 Dec 2016 15:49:47 GMT",
        },
        "HTTPStatusCode": 201,
        "RetryAttempts": 0
      },
      "apiStages": [
        {
          "apiId": "abcde12345",
          "stage": "live"
        }
      ],
      "description": "this is an awesome test",
      "id": "abc123",
      "name": "testplan",
      "quota": {
        "limit": 333,
        "offset": 0,
        "period": "WEEK"
      },
      "throttle": {
        "burstLimit": 111,
        "rateLimit": 222.0
      }
    }
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

class ApiGwUsagePlan:
  def __init__(self, module):
    """
    Constructor
    """
    self.module = module
    if (not HAS_BOTO3):
      self.module.fail_json(msg="boto and boto3 are required for this module")
    self.client = boto3.client('apigateway')
    self.param_map = {
      'throttle_burst_limit': 'throttle/burstLimit',
      'throttle_rate_limit': 'throttle/rateLimit',
      'quota_offset': 'quota/offset',
      'quota_limit': 'quota/limit',
      'quota_period': 'quota/period',
    }

  @staticmethod
  def _define_module_argument_spec():
    """
    Defines the module's argument spec
    :return: Dictionary defining module arguments
    """
    return dict( name=dict(required=True),
                 description=dict(required=False, default=''),
                 api_stages=dict(
                   type='list',
                   required=False,
                   default=[],
                   rest_api_id=dict(required=True),
                   stage=dict(required=True)
                 ),
                 throttle_burst_limit=dict(required=False, default=-1, type='int'),
                 throttle_rate_limit=dict(required=False, default=-1.0, type='float'),
                 quota_limit=dict(required=False, default=-1, type='int'),
                 quota_offset=dict(required=False, default=-1, type='int'),
                 quota_period=dict(required=False, default='', choices=['', 'DAY','WEEK','MONTH']),
                 state=dict(default='present', choices=['present', 'absent']),
    )

  def _retrieve_usage_plan(self):
    """
    Retrieve all usage_plans in the account and match them against the provided name
    :return: Result matching the provided api name or an empty hash
    """
    resp = None
    try:
      get_resp = self.client.get_usage_plans()

      for item in get_resp.get('items', []):
        if item['name'] == self.module.params.get('name'):
          resp = item
    except BotoCoreError as e:
      self.module.fail_json(msg="Error when getting usage_plans from boto3: {}".format(e))

    return resp

  @staticmethod
  def _build_api_stages_remove_patches(me):
    patches = []
    for entry in me.get('apiStages', []):
      key = "{0}:{1}".format(entry['apiId'], entry['stage'])
      patches.append({'op': 'remove', 'path': '/apiStages', 'value': key})

    return patches

  def _delete_usage_plan(self):
    """
    Delete usage_plan that matches the returned id
    :return: True
    """
    try:
      if not self.module.check_mode:
        if 'apiStages' in self.me:
          patches = ApiGwUsagePlan._build_api_stages_remove_patches(self.me)
          if patches:
            self.client.update_usage_plan(usagePlanId=self.me['id'], patchOperations=patches)

        self.client.delete_usage_plan(usagePlanId=self.me['id'])
      return True
    except BotoCoreError as e:
      self.module.fail_json(msg="Error when deleting usage_plan via boto3: {}".format(e))

  @staticmethod
  def _is_default_value(param_name, param_value):
    defaults = ApiGwUsagePlan._define_module_argument_spec()

    if defaults[param_name].get('type', 'string') in ['int', 'float']:
      return param_value < 0
    else:
      return param_value in [None, '']

  def _create_usage_plan(self):
    """
    Create usage_plan from provided args
    :return: True, result from create_usage_plan
    """
    usage_plan = None
    changed = False

    try:
      changed = True
      if not self.module.check_mode:
        args = dict(name=self.module.params['name'])

        for f in ['description','throttle_burst_limit','throttle_rate_limit','quota_limit','quota_period','quota_offset']:
          if not ApiGwUsagePlan._is_default_value(f, self.module.params.get(f, None)):
            boto_param = self.param_map.get(f, f)
            if '/' in boto_param:
              (p1, p2) = boto_param.split('/')
              if p1 not in args:
                args[p1] = {}
              args[p1].update({p2: self.module.params[f]})
            else:
              args[boto_param] = self.module.params[f]

        for stage in self.module.params.get('api_stages', []):
          if 'apiStages' not in args:
            args['apiStages'] = []
          args['apiStages'].append({'apiId': stage.get('rest_api_id'), 'stage': stage.get('stage')})

        usage_plan = self.client.create_usage_plan(**args)
    except BotoCoreError as e:
      self.module.fail_json(msg="Error when creating usage_plan via boto3: {}".format(e))

    return (changed, usage_plan)

  @staticmethod
  def _all_defaults(ans_params, params_list):
    is_default = False
    for p in params_list:
      is_default = is_default or ApiGwUsagePlan._is_default_value(p, ans_params.get(p, None))

    return is_default

  @staticmethod
  def _create_patches(params, me, pmap):
    patches = []

    # delete ops
    if 'throttle' in me and ApiGwUsagePlan._all_defaults(params, ['throttle_rate_limit','throttle_burst_limit']):
      patches.append({'op': 'remove', 'path': "/throttle"})
    if 'quota' in me and ApiGwUsagePlan._all_defaults(params, ['quota_limit','quota_offset','quota_period']):
      patches.append({'op': 'remove', 'path': "/quota"})
    if 'apiStages' in me and params.get('api_stages', []) == []:
      patches.extend(ApiGwUsagePlan._build_api_stages_remove_patches(me))

    # add/replace ops
    for p in ['description','throttle_rate_limit','throttle_burst_limit','quota_limit','quota_offset','quota_period']:
      boto_param = pmap.get(p, p)
      if '/' in boto_param:
        (parent, child) = boto_param.split('/')
        if not ApiGwUsagePlan._is_default_value(p, params.get(p, None)):
          if child not in me.get(parent, {}):
            patches.append({'op': 'add', 'path': "/{}".format(boto_param), 'value': str(params[p])})
          elif me[parent][child] != params[p]:
            patches.append({'op': 'replace', 'path': "/{}".format(boto_param), 'value': str(params[p])})
      else:
        # must be description
        if p not in me and params.get(p, '') in [None, '']:
          pass
        elif p in me and me[p] != params.get(p, ''):
          patches.append({'op': 'replace', 'path': "/{}".format(boto_param), 'value': str(params.get(p, ''))})

    # add handling for api_stages
    api_stages = []
    for stage in me.get('apiStages', []):
      api_stages.append("{0}:{1}".format(stage['apiId'], stage['stage']))
    for entry in params.get('api_stages', []):
      key = "{0}:{1}".format(entry['rest_api_id'], entry['stage'])
      if key not in api_stages:
        patches.append({'op': 'add', 'path': '/apiStages', 'value': key})

    return patches

  def _update_usage_plan(self):
    """
    Create usage_plan from provided args
    :return: True, result from create_usage_plan
    """
    usage_plan = self.me
    changed = False

    try:
      patches = ApiGwUsagePlan._create_patches(self.module.params, self.me, self.param_map)
      if patches:
        changed = True

        if not self.module.check_mode:
          self.client.update_usage_plan(
            usagePlanId=self.me['id'],
            patchOperations=patches
          )
          usage_plan = self._retrieve_usage_plan()
    except BotoCoreError as e:
      self.module.fail_json(msg="Error when updating usage_plan via boto3: {}".format(e))

    return (changed, usage_plan)

  def process_request(self):
    """
    Process the user's request -- the primary code path
    :return: Returns either fail_json or exit_json
    """

    usage_plan = None
    changed = False
    self.me = self._retrieve_usage_plan()

    if self.module.params.get('state', 'present') == 'absent' and self.me is not None:
      changed = self._delete_usage_plan()
    elif self.module.params.get('state', 'present') == 'present':
      if self.me is None:
        (changed, usage_plan) = self._create_usage_plan()
      else:
        (changed, usage_plan) = self._update_usage_plan()

    self.module.exit_json(changed=changed, usage_plan=usage_plan)

def main():
    """
    Instantiates the module and calls process_request.
    :return: none
    """
    module = AnsibleModule(
        argument_spec=ApiGwUsagePlan._define_module_argument_spec(),
        supports_check_mode=True
    )

    usage_plan = ApiGwUsagePlan(module)
    usage_plan.process_request()

from ansible.module_utils.basic import *  # pylint: disable=W0614
if __name__ == '__main__':
    main()
