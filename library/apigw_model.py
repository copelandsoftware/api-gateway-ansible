#!/usr/bin/python

# API Gateway Ansible Modules
#
# Modules in this project allow management of the AWS API Gateway service.
#
# Authors:
#  - Jarrod McEvers     <github: JarrodAMcEvers>
#
# apigw_model
#    Manage creation, update, and removal of API Gateway Models.
#

# MIT License
#
# Copyright (c) 2019 Jarrod McEvers, Emerson
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
module: apigw_model
authors: Jarrod McEvers (@JarrodAMcEvers)
short_description: Add, update, or remove AWS API Gateway Models.
description:
- Create, Update, and Delete operations for Models
version_added: "2.4"
options:
  rest_api_id:
    description:
    - The id of the parent rest api.
    type: 'string'
    required: True
  name:
    description:
    - The name of the model on which to operate.
    type: 'string'
    required: True
  content_type:
    description:
    - The content-type for the model.
    type: 'string'
    required: True
  schema:
    description:
    - Schema for the model. If content_type is application/json, this should be a JSON schema draft 4 model.
    type: 'string'
    required: True
  description:
    description:
    - Description for the model.
    type: 'string'
    default: ''
    required: False
  state:
    description:
    - Determine whether to assert if model should exist or not.
    type: 'string'
    choices: ['present', 'absent']
    default: 'present'
    required: False

requirements:
    - python = 2.7
    - boto
    - boto3
notes:
  - Even though the docs for create model does not require the schema, I could not find an example where you did not have to pass in schema.
  - This module requires that you have boto and boto3 installed and that your credentials are created or stored in a way that is compatible (see U(https://boto3.readthedocs.io/en/latest/guide/quickstart.html#configuration)).
'''

EXAMPLES = '''
- name: Test playbook for creating API GW Models
  hosts: localhost
  gather_facts: False
  tasks:
    - name: Create an api
      apigw_rest_api:
        name: 'my.example.com'
        state: present
      register: restapi

    - name: Create a resource
      apigw_model:
        rest_api_id: "{{ restapi.api.id }}"
        name: 'Model'
        content_type: 'application/pdf'
        schema: '{}'
        state: 'present'
'''

RETURN = '''
Response after create
{
    "model": {
        "name": "Model",
        "contentType": "application/pdf",
        "id": "some_model_id",
        "ResponseMetadata": {
            "RetryAttempts": 0,
            "HTTPStatusCode": 201,
            "RequestId": "77777777-7777-7777-7777-77777777777",
            "HTTPHeaders": {
                "x-amzn-requestid": "77777777-7777-7777-7777-77777777777",
                "content-length": "77",
                "x-amz-apigw-id": "some_id",
                "connection": "keep-alive",
                "date": "Thu, 29 Aug 2019 16:18:20 GMT",
                "content-type": "application/json"
            }
        },
        "schema": "{}"
    }
}
'''

from ansible.module_utils import basic
from ansible.module_utils.basic import * # pylint: disable=W0614

try:
  import boto3
  import boto
  from botocore.exceptions import BotoCoreError, ClientError
  HAS_BOTO3 = True
except ImportError:
  HAS_BOTO3 = False

class ApiGwModel:
    def __init__(self, module):
        self.module = module
        if (not HAS_BOTO3):
            self.module.fail_json(msg="boto and boto3 are required for this module")
        self.client = boto3.client('apigateway')

    @staticmethod
    def _define_module_argument_spec():
        return dict(
            rest_api_id=dict(required=True, type=str),
            name=dict(require=True, type=str),
            content_type=dict(required=True, type=str),
            schema=dict(require=True, type=str),
            description=dict(required=False, type=str),
            state=dict(default='present', choices=['present', 'absent'])
        )

    def _does_model_exist(self):
        try:
            self.client.get_model(
                restApiId=self.module.params.get('rest_api_id'),
                modelName=self.module.params.get('name'),
                flatten=True
            )
            return True
        except ClientError:
            return False

    def _delete_model(self):
        if not self.module.check_mode:
            try:
                self.client.delete_model(
                    restApiId=self.module.params.get('rest_api_id'),
                    modelName=self.module.params.get('name')
                )
            except ClientError as e:
                if 'NotFoundException' in e.message:
                    return None
                self.module.fail_json(msg='Error while deleting model: {}'.format(e))

        return None

    def _patch_builder(self):
        return [
            dict(
                op='replace',
                path='/schema',
                value=self.module.params.get('schema')
            ),
            dict(
                op='replace',
                path='/description',
                value=self.module.params.get('description', '')
            )
        ]

    def _update_model(self):
        patches = self._patch_builder()

        if self.module.check_mode:
            return True, None
        try:
            response = self.client.update_model(
                restApiId=self.module.params.get('rest_api_id'),
                modelName=self.module.params.get('name'),
                patchOperations=patches
            )
            return True, response
        except ClientError as e:
            self.module.fail_json(msg='Error while updating model: {}'.format(e))

    def _create_model(self):
        if self.module.check_mode:
            return True, None

        content_type = self.module.params.get('content_type')
        args = dict(
            restApiId=self.module.params.get('rest_api_id'),
            name=self.module.params.get('name'),
            contentType=content_type,
            schema=self.module.params.get('schema'),
            description=self.module.params.get('description', '')
        )

        try:
            response = self.client.create_model(**args)
            return True, response
        except ClientError as e:
            self.module.fail_json(msg='Error while creating model: {}'.format(e))

    def process_request(self):
        changed = False
        response = None

        if self.module.params.get('state') == 'absent':
            self._delete_model()
            changed = True
        elif self._does_model_exist() == True:
            changed, response = self._update_model()
        else:
            changed, response = self._create_model()

        self.module.exit_json(changed=changed, model=response)

def main():
    module = basic.AnsibleModule(
        argument_spec=ApiGwModel._define_module_argument_spec(),
        supports_check_mode=True
    )
    model = ApiGwModel(module)
    model.process_request()

if __name__ == '__main__':
    main()
