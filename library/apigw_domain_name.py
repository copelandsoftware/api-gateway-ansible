#!/usr/bin/python

# API Gateway Ansible Modules
#
# Modules in this project allow management of the AWS API Gateway service.
#
# Authors:
#  - Brian Felton <github: bjfelton>
#
# apigw_domain_name
#    Manage creation, update, and removal of API Gateway DomainName resources
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
---
module: apigw_domain_name
author: Brian Felton (@bjfelton)
short_description: Add, update, or remove DomainName resources
description:
- Uses domain name for identifying resources for CRUD operations
- Update only covers certificate name
version_added: "2.2"
options:
  name:
    description:
    - The name of the DomainName resource on which to operate
    type: string
    required: True
    aliases: domain_name
  cert_name:
    description:
    - Name of the associated certificate. Required when C(state) is 'present'
    type: string
    required: False
    default: None
  cert_private_key:
    description:
    - Certificate's private key. Required when C(state) is 'present'
    type: string
    required: False
    default: None
  cert_body:
    description:
    - Body of the server certificate. Required when C(state) is 'present'
    type: string
    required: False
    default: None
  cert_chain:
    description:
    - Intermediate certificates and optionally the root certificate.  If root is included, it must follow the intermediate certificates. Required when C(state) is 'present'
    type: string
    required: False
    default: None
  state:
    description:
    - Should domain_name exist or not
    choices: ['present', 'absent']
    default: 'present'
    required: False
requirements:
    - python = 2.7
    - boto
    - boto3
notes:
    - This module requires that you have boto and boto3 installed and that your credentials are created or stored in a way that is compatible (see U(https://boto3.readthedocs.io/en/latest/guide/quickstart.html#configuration)).
'''

EXAMPLES = '''
---
- hosts: localhost
  gather_facts: False
  tasks:
  - name: api key creation
    apigw_domain_name:
      name: testdomain.io.edu.mil
      cert_name: 'test-cert'
      cert_body: 'cert body'
      cert_private_key: 'totally secure key'
      cert_chain: 'sure, this is real'
      state: "{{ state | default('present') }}"
    register: dn

  - debug: var=dn
'''

RETURN = '''
---
domain_name:
	description: dictionary representing the domain name
	returned: success
	type: dict
changed:
  description: standard boolean indicating if something changed
  returned: always
  type: boolean
'''

__version__ = '${version}'

try:
  import boto3
  import boto
  from botocore.exceptions import BotoCoreError, ClientError
  HAS_BOTO3 = True
except ImportError:
  HAS_BOTO3 = False

class ApiGwDomainName:
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
                 cert_name=dict(required=False),
                 cert_body=dict(required=False),
                 cert_private_key=dict(required=False),
                 cert_chain=dict(required=False),
                 state=dict(default='present', choices=['present', 'absent']),
    )

  def _retrieve_domain_name(self):
    """
    Retrieve domain name by provided name
    :return: Result matching the provided domain name or an empty hash
    """
    resp = None
    try:
      resp = self.client.get_domain_name(domainName=self.module.params['name'])

    except ClientError as e:
      if 'NotFoundException' in e.message:
        resp = None
      else:
        self.module.fail_json(msg="Error when getting domain_name from boto3: {}".format(e))
    except BotoCoreError as e:
      self.module.fail_json(msg="Error when getting domain_name from boto3: {}".format(e))

    return resp

  def _delete_domain_name(self):
    """
    Delete domain_name that matches the returned id
    :return: True
    """
    try:
      if not self.module.check_mode:
        self.client.delete_domain_name(domainName=self.module.params['name'])
      return True
    except BotoCoreError as e:
      self.module.fail_json(msg="Error when deleting domain_name via boto3: {}".format(e))

  def _create_domain_name(self):
    """
    Create domain_name from provided args
    :return: True, result from create_domain_name
    """
    domain_name = None
    changed = False

    for required in ['cert_name', 'cert_body', 'cert_private_key', 'cert_chain']:
      if self.module.params.get(required, None) is None:
        self.module.fail_json(msg="All certificate parameters are required to create a domain name")
        return (changed, domain_name)

    try:
      changed = True
      if not self.module.check_mode:
        domain_name = self.client.create_domain_name(
          domainName=self.module.params['name'],
          certificateName=self.module.params['cert_name'],
          certificateBody=self.module.params['cert_body'],
          certificatePrivateKey=self.module.params['cert_private_key'],
          certificateChain=self.module.params['cert_chain'],
        )

    except BotoCoreError as e:
      self.module.fail_json(msg="Error when creating domain_name via boto3: {}".format(e))

    return (changed, domain_name)

  def _update_domain_name(self):
    """
    Create domain_name from provided args
    :return: True, result from create_domain_name
    """
    domain_name = self.me
    changed = False

    try:
      patches = []
      cert_name = self.module.params.get('cert_name', None)
      if cert_name not in ['', None] and cert_name != self.me['certificateName']:
        patches.append({'op': 'replace', 'path': '/certificateName', 'value': cert_name})

      if patches:
        changed = True

        if not self.module.check_mode:
          self.client.update_domain_name(
            domainName=self.module.params['name'],
            patchOperations=patches
          )
          domain_name = self._retrieve_domain_name()
    except BotoCoreError as e:
      self.module.fail_json(msg="Error when updating domain_name via boto3: {}".format(e))

    return (changed, domain_name)

  def process_request(self):
    """
    Process the user's request -- the primary code path
    :return: Returns either fail_json or exit_json
    """

    domain_name = None
    changed = False
    self.me = self._retrieve_domain_name()

    if self.module.params.get('state', 'present') == 'absent' and self.me is not None:
      changed = self._delete_domain_name()
    elif self.module.params.get('state', 'present') == 'present':
      if self.me is None:
        (changed, domain_name) = self._create_domain_name()
      else:
        (changed, domain_name) = self._update_domain_name()

    self.module.exit_json(changed=changed, domain_name=domain_name)

def main():
    """
    Instantiates the module and calls process_request.
    :return: none
    """
    module = AnsibleModule(
        argument_spec=ApiGwDomainName._define_module_argument_spec(),
        supports_check_mode=True
    )

    domain_name = ApiGwDomainName(module)
    domain_name.process_request()

from ansible.module_utils.basic import *  # pylint: disable=W0614
if __name__ == '__main__':
    main()
