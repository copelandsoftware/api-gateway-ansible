#!/usr/bin/python

# API Gateway Ansible Modules
#
# Modules in this project allow management of the AWS API Gateway service.
#
# Authors:
#  - Brian Felton <github: bjfelton>
#
# apigw_authorizer
#    Manage creation, update, and removal of API Gateway REST APIs
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
module: apigw_authorizer
description:
  - An Ansible module to add, update, or remove Authorizer resources for
    AWS API Gateway.
version_added: "2.2"
options:
  rest_api_id:
    description: The id of the Rest API to which this Authorizer belongs
    required: True
  name:
    description: The name of the authorizer on which to operate
    required: True
    aliases: ['authorizer']
  type:
    description: Type of the authorizer (required when C(state) is 'present')
    required: False
    choices: ['TOKEN', 'COGNITO_USER_POOLS']
    default: None
  uri:
    description: The autorizer's uri (required with C(state) is 'present')
    required: False
    default: None
  identity_source:
    description: Source of the identity in an incoming request (required when C(state) is 'present')
    required: False
    default: None
  identity_validation_expression:
    description: Validation expression for the incoming entity
    required: False
    default: ''
  provider_arns:
    description:
    required: False
    default: []
  auth_type:
    description: Optional customer-defined field used in Swagger docs - has no functional impact
    required: False
    default: None
  credentials:
    description: Specifies credentials required for the authorizer, if any
    required: False
    default: None
  result_ttl_seconds:
    description: The TTL of cached authorizer results in seconds
    required: False
    default: 0
  state:
    description: Should authorizer exist or not
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
  - name: provision!
    apigw_authorizer:
      rest_api_id: 54321lmnop
      name: test_authorizer
      type: TOKEN
      auth_type: custom
      uri: some.uri.here
      result_ttl_seconds: 456
      identity_source: method.request.header.Authorization
      identity_validation_expression: "^cool.*regex?$"
      state: present
    register: auth

  - debug: var=auth
'''

RETURN = '''
{
	"authorizer": {
		"ResponseMetadata": {
			"HTTPHeaders": {
				"content-length": "426",
				"content-type": "application/json",
				"date": "Thu, 08 Dec 2016 04:01:46 GMT",
				"x-amzn-requestid": "<some id>"
			},
			"HTTPStatusCode": 201,
			"RequestId": "<some id>",
			"RetryAttempts": 0
		},
		"authType": "custom",
		"authorizerResultTtlInSeconds": 456,
		"authorizerUri": "arn:aws:apigateway:more:valid:uri:here",
		"id": "abcdefg43",
		"identitySource": "method.request.header.Authorization",
		"identityValidationExpression": "^nifty.*regex+here",
		"name": "test_authorizer",
		"type": "TOKEN"
	},
	"changed": true
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

class ApiGwAuthorizer:
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
    return dict( rest_api_id=dict(required=True),
                 name=dict(required=True),
                 type=dict(required=False, choices=['TOKEN', 'COGNITO_USER_POOLS']),
                 uri=dict(required=False),
                 identity_source=dict(required=False),
                 identity_validation_expression=dict(required=False, default=''),
                 provider_arns=dict(required=False, type='list', default=[]),
                 auth_type=dict(required=False),
                 credentials=dict(required=False),
                 result_ttl_seconds=dict(required=False, type='int', default=0),
                 state=dict(default='present', choices=['present', 'absent']),
    )

  def _retrieve_authorizer(self):
    """
    Retrieve all authorizers in the account and match them against the provided name
    :return: Result matching the provided api name or an empty hash
    """
    resp = None
    try:
      get_resp = self.client.get_authorizers(restApiId=self.module.params['rest_api_id'])

      for item in get_resp.get('items', []):
        if item['name'] == self.module.params.get('name'):
          resp = item
    except BotoCoreError as e:
      self.module.fail_json(msg="Error when getting authorizers from boto3: {}".format(e))

    return resp

  def _delete_authorizer(self):
    """
    Delete authorizer that matches the returned id
    :return: True
    """
    try:
      if not self.module.check_mode:
        self.client.delete_authorizer(restApiId=self.module.params['rest_api_id'], authorizerId=self.me['id'])
      return True
    except BotoCoreError as e:
      self.module.fail_json(msg="Error when deleting authorizer via boto3: {}".format(e))

  def _create_authorizer(self):
    """
    Create authorizer from provided args
    :return: True, result from create_authorizer
    """
    auth = None
    changed = False

    try:
      changed = True
      if not self.module.check_mode:
        p = self.module.params

        args = dict(
          restApiId=p['rest_api_id'],
          name=p['name'],
          type=p['type'],
          identitySource=p['identity_source']
        )

        optional_params = [
          {'ans_param': 'provider_arns', 'boto_param': 'providerArns', 'default': []},
          {'ans_param': 'auth_type', 'boto_param': 'authType', 'default': ''},
          {'ans_param': 'uri', 'boto_param': 'authorizerUri', 'default': ''},
          {'ans_param': 'credentials', 'boto_param': 'authorizerCredentials', 'default': ''},
          {'ans_param': 'identity_validation_expression', 'boto_param': 'identityValidationExpression', 'default': ''},
          {'ans_param': 'result_ttl_seconds', 'boto_param': 'authorizerResultTtlInSeconds', 'default': 0},
        ]

        for op in optional_params:
          param_value = p.get(op['ans_param'], op['default'])
          if param_value is not None and param_value != op['default']:
            args[op['boto_param']] = p[op['ans_param']]

        auth = self.client.create_authorizer(**args)
    except BotoCoreError as e:
      self.module.fail_json(msg="Error when creating authorizer via boto3: {}".format(e))

    return (changed, auth)

  def _validate_params(self):
    """
    Determine if the provided args contain required fields
    :return: Nothing.  Calls fail_json if fields are missing
    """
    for field in ['type', 'identity_source']:
      if field not in self.module.params:
        self.module.fail_json(msg="Field <{}> is required when state is present".format(field))

  @staticmethod
  def _create_patches(params, me):
    fields = [
      {'ansible': 'type', 'boto': 'type', 'default': ''},
      {'ansible': 'uri', 'boto': 'authorizerUri', 'default': ''},
      {'ansible': 'identity_source', 'boto': 'identitySource', 'default': ''},
      {'ansible': 'identity_validation_expression', 'boto': 'identityValidationExpression', 'default': ''},
      {'ansible': 'auth_type', 'boto': 'authType', 'default': ''},
      {'ansible': 'credentials', 'boto': 'authorizerCredentials', 'default': ''},
      {'ansible': 'result_ttl_seconds', 'boto': 'authorizerResultTtlInSeconds', 'default': 0},
    ]

    patches = []
    for f in fields:
      ans_arg = params.get(f['ansible'], f['default'])
      if ans_arg is not None and str(ans_arg).lower() != str(me.get(f['boto'])).lower():
        patches.append({'op': 'replace', 'path': "/{}".format(f['boto']), 'value': str(ans_arg)})

    # Magic for providerARNs
    if 'providerARNs' in me:
      if params.get('provider_arns', []) == []:
        patches.append({'op': 'remove', 'path': '/providerARNs'})
      # I'm ignoring the possibility of duplicate entries here because why would you do that?
      elif set(params.get('provider_arns', [])) != set(me.get('providerARNs')):
        patches.append({'op': 'replace', 'path': '/providerARNs', 'value': str(params.get('provider_arns'))})
    elif params.get('provider_arns', []) != []:
      patches.append({'op': 'add', 'path': '/providerARNs', 'value': str(params.get('provider_arns'))})

    return patches

  def _update_authorizer(self):
    """
    Create authorizer from provided args
    :return: True, result from create_authorizer
    """
    auth = self.me
    changed = False

    try:
      patches = ApiGwAuthorizer._create_patches(self.module.params, self.me)
      if patches:
        changed = True

        if not self.module.check_mode:
          self.client.update_authorizer(
            restApiId=self.module.params['rest_api_id'],
            authorizerId=self.me['id'],
            patchOperations=patches
          )
          auth = self._retrieve_authorizer()
    except BotoCoreError as e:
      self.module.fail_json(msg="Error when updating authorizer via boto3: {}".format(e))

    return (changed, auth)

  def process_request(self):
    """
    Process the user's request -- the primary code path
    :return: Returns either fail_json or exit_json
    """
    auth = None
    changed = False
    self.me = self._retrieve_authorizer()

    if self.module.params.get('state', 'present') == 'absent' and self.me is not None:
      changed = self._delete_authorizer()
    elif self.module.params.get('state', 'present') == 'present':
      self._validate_params()
      if self.me is None:
        (changed, auth) = self._create_authorizer()
      else:
        (changed, auth) = self._update_authorizer()

    self.module.exit_json(changed=changed, authorizer=auth)

def main():
    """
    Instantiates the module and calls process_request.
    :return: none
    """
    module = AnsibleModule(
        argument_spec=ApiGwAuthorizer._define_module_argument_spec(),
        supports_check_mode=True
    )

    authorizer = ApiGwAuthorizer(module)
    authorizer.process_request()

from ansible.module_utils.basic import *  # pylint: disable=W0614
if __name__ == '__main__':
    main()
