#!/usr/bin/python

# API Gateway Ansible Modules
#
# Modules in this project allow management of the AWS API Gateway service.
# WARNING: Module is not idempotent.
#
# Authors:
#  - Brian Felton <github: bjfelton>
#
# apigw_deployment
#    Create API Gateway Deployment resource
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
module: apigw_deployment
author: Brian Felton (@bjfelton)
short_description: Create an apigateway Deployment
description:
- Creates Deployments (no other operations)
- A deployment is always created -- this module is not idempotent
version_added: "2.2"
options:
  name:
    description:
    - The name of the stage to deploy
    type: 'string'
    required: True
    aliases: ['stage_name']
  rest_api_id:
    description:
    - The id of the parent rest api
    type: 'string'
    required: True
  stage_description:
    description:
    - The description of the stage resource for the Deployment resource to create
    type: 'string'
    default: ''
    required: False
  description:
    description:
    - The description for the Deployment resource to create
    type: 'string'
    default: ''
    required: False
  cache_cluster_enabled:
    description:
    - Enables a cache cluster for the resource if True
    type: 'bool'
    default: False
    required: False
  cache_cluster_size:
    description:
    - Specifies the size of the cache cluster
    type: 'string'
    default: None
    choices: ['0.5','1.6','6.1','13.5','28.4','58.2','118','237']
    required: False

requirements:
    - python = 2.7
    - boto
    - boto3
notes:
    - WARNING: This module is not idempotent
    - This module requires that you have boto and boto3 installed and that your credentials are created or stored in a way that is compatible (see U(https://boto3.readthedocs.io/en/latest/guide/quickstart.html#configuration)).
'''

EXAMPLES = '''
- name: Test playbook for creating API GW Method resource
  hosts: localhost
  gather_facts: False
  tasks:
    - name: deploy it
      apigw_deployment:
        rest_api_id: 'someIdHere
        name: 'dev'
        description: 'This is a test of the emergency deployment system'
        cache_cluster_enabled: True
        cache_cluster_size: 0.5
      register: deploy

    - debug: var=deploy
'''

RETURN = '''
{
  "deploy": {
    "changed": true,
    "deployment": {
      "ResponseMetadata": {
        "HTTPHeaders": {
          "content-length": "107",
          "content-type": "application/json",
          "date": "Mon, 28 Nov 2016 15:02:40 GMT",
          "x-amzn-requestid": "some id"
        },
        "HTTPStatusCode": 201,
        "RequestId": "some id",
        "RetryAttempts": 0
      },
      "createdDate": "2016-11-28T09:02:39-06:00",
      "description": "This is a test of the emergency deployment system",
      "id": "rv7xsx"
    }
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

class ApiGwDeployment:
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
                 stage_description=dict(required=False),
                 description=dict(required=False),
                 cache_cluster_enabled=dict(required=False, type='bool', default=False),
                 cache_cluster_size=dict(required=False, choices=['', '0.5','1.6','6.1','13.5','28.4','58.2','118','237'])
    )

  def process_request(self):
    """
    Process the user's request -- the primary code path
    :return: Returns either fail_json or exit_json
    """
    result = None

    p = self.module.params

    # So ansible seems to do something weird wherein it converts a default
    # of '' to None, which boto won't accept, hence the "or ''"
    kwargs = {
      'restApiId': p.get('rest_api_id'),
      'stageName': p.get('name'),
      'stageDescription': p.get('stage_description', '') or '',
      'description': p.get('description', '') or '',
      'cacheClusterEnabled': p.get('cache_cluster_enabled', False)
    }

    if p.get('cache_cluster_enabled', False):
      kwargs['cacheClusterSize'] = str(p.get('cache_cluster_size', ''))

    if not self.module.check_mode:
      try:
        result = self.client.create_deployment(**kwargs)
      except BotoCoreError as e:
        self.module.fail_json(msg="Error while creating deployment via boto3: {}".format(e))

    self.module.exit_json(changed=True, deployment=result)

def main():
    """
    Instantiates the module and calls process_request.
    :return: none
    """
    module = AnsibleModule(
        argument_spec=ApiGwDeployment._define_module_argument_spec(),
        supports_check_mode=True
    )

    deployment = ApiGwDeployment(module)
    deployment.process_request()

from ansible.module_utils.basic import *  # pylint: disable=W0614
if __name__ == '__main__':
    main()
