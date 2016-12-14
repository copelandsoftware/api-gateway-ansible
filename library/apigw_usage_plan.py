#!/usr/bin/python

# API Gateway Ansible Modules
#
# Modules in this project allow management of the AWS API Gateway service.
#
# Authors:
#  - Brian Felton <bjfelton@gmail.com>
#
# apigw_usage_plan
#    Manage creation, update, and removal of API Gateway UsagePlan resources
#
# NOTE: While it is possible via the boto api to update the UsagePlan's name,
#       this module does not support this functionality since it searches
#       for the UsagePlan's id by its name.

## TODO: Add an appropriate license statement

DOCUMENTATION='''
module: apigw_usage_plan
description: An Ansible module to add, update, or remove UsagePlan
  and UsagePlanKey resources for AWS API Gateway.
version_added: "2.2"
options:
  name:
    description: The domain name of the UsagePlan resource on which to operate
    type: string
    required: True
  description:
    description: UsagePlan description
    type: string
    default: None
    required: False
  api_stages:
    description: List of associated api stages
    type: list
    default: []
    required: False
    options:
      rest_api_id:
        description: ID of the associated API stage in the usage plan
        type: string
        required: True
      stage:
        description: API stage name of the associated API stage in the usage plan
        type: string
        required: True
  throttle_burst_limit:
    description: API request burst limit
    type: int
    default: -1
    required: False
  throttle_rate_limit:
    description: API request steady-state limit
    type: double
    default: -1.0
    required: False
  quota_limit:
    description: Maxiumum number of requests that can be made in a given time period
    type: integer
    default: -1
    required: False
  quota_offset:
    description: Number of requests subtracted from the given limit in the initial time period
    type: integer
    default: -1
    required: False
  quota_period:
    description: The time period in which the limit applies
    type: string
    default: ''
    choices: ['', 'DAY', 'WEEK', 'MONTH']
    required: False
  state:
    description: Should usage_plan exist or not
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

class ApiGwUsagePlan:
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

  def _delete_usage_plan(self):
    """
    Delete usage_plan that matches the returned id
    :return: True
    """
    try:
      if not self.module.check_mode:
        self.client.delete_usage_plan(usagePlanId=self.me['id'])
      return True
    except BotoCoreError as e:
      self.module.fail_json(msg="Error when deleting usage_plan via boto3: {}".format(e))

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
