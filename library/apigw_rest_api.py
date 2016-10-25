#!/usr/bin/python

# API Gateway Ansible Modules
#
# Modules in this project allow management of the AWS API Gateway service.
#
# Authors:
#  - Brian Felton <bjfelton@gmail.com>
#
# apigw_rest_api
#    Manage creation and removal of API Gateway REST APIs
#

## TODO: Add an appropriate license statement

DOCUMENTATION='''
module: apigw_rest_api
description:
  - An Ansible module to add or remove REST API resources for AWS API Gateway
version_added: "2.2"
options:
  <field>:
    description:
      - <words>
    default: <default>
    choices: <words>
    required: <boolean>
requirements:
    - python = 2.7
    - <other modules>
notes:
    - <probably something about boto and AWS creds>
'''

EXAMPLES = '''
TODO: Example plays go here
'''

RETURN = '''
TODO: Add example return structure
'''

__version__ = '${version}'

try:
  import boto3
  import boto
  from botocore.exceptions import ClientError, MissingParametersError, ParamValidationError
  HAS_BOTO3 = True
except ImportError:
  HAS_BOTO3 = False

class ApiGwRestApi:
  def __init__(self, module):
    self.module = module
    if (not HAS_BOTO3):
      self.module.fail_json(msg="boto and boto3 are required for this module")
    self.client = boto3.client('apigateway')

  @staticmethod
  def _define_module_argument_spec():
    return dict( id=dict(required=True, aliases=['name']),
                 description=dict(required=False),
                 state=dict(default='present', choices=['present', 'absent'])
		)

  def _retrieve_rest_api(self):
    try:
      results = self.client.get_rest_apis()
      id = self.module.params.get('id')

      api = filter(lambda result: result['name'] == id, results['items'])

      if len(api):
        return api[0]
      else:
        return {}
    except:
      return {}

  def process_request(self):
    params = self.module.params
    api = self._retrieve_rest_api()

    if params.get('state') == 'absent' and not api:
      self.module.exit_json(changed=False, api={})
    else:
      self.module.fail_json(msg='API <'+params.get('id')+'> not found')


def main():
    """
    Instantiates the module and calls process_request.
    :return: none
    """
    module = AnsibleModule(
        argument_spec=ApiGwRestApi._define_module_argument_spec(),
        supports_check_mode=True
    )

    rest_api = ApiGwRestApi(module)
    rest_api.process_request()

from ansible.module_utils.basic import *  # pylint: disable=W0614
if __name__ == '__main__':
    main()
