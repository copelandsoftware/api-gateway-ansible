#!/usr/bin/python

# API Gateway Ansible Modules
#
# Modules in this project allow management of the AWS API Gateway service.
#
# Authors:
#  - Brian Felton <bjfelton@gmail.com>
#
# apigw_rest_api
#    Manage creation, update, and removal of API Gateway REST APIs
#

## TODO: Add an appropriate license statement

DOCUMENTATION='''
module: apigw_rest_api
description:
  - An Ansible module to add, update, or remove REST API resources for
    AWS API Gateway.
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
    - boto
    - boto3
notes:
    - This module requires that you have boto and boto3 installed and that your
      credentials are created or stored in a way that is compatible (see
      U(https://boto3.readthedocs.io/en/latest/guide/quickstart.html#configuration)).
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
                 state=dict(default='present', choices=['present', 'absent'])
		)

  def _retrieve_rest_api(self):
    """
    Retrieve all rest APIs in the account and match it against the provided name
    :return: Result matching the provided api name or an empty hash
    """
    response = {}
    try:
      results = self.client.get_rest_apis()
      id = self.module.params.get('name')

      api = filter(lambda result: result['name'] == id, results['items'])

      if len(api):
        response = api[0]
    except:
      self.module.fail_json(msg='Encountered fatal error calling boto3 get_rest_apis function')

    return response

  @staticmethod
  def _is_changed(api, params):
    """
    Determine if the discovered api differs from the user-provided params
    :param api: Result from _retrieve_rest_api()
    :param params: Module params
    :return: Boolean telling if result matches params
    """
    return api.get('name') != params.get('name') or api.get('description') != params.get('description')

  def _create_or_update_api(self, api):
    """
    When state is 'present', determine if api creation or update is appropriate
    :return: (changed, result)
              changed: Boolean showing whether a change occurred
              result: The resulting rest api object
    """
    changed = False
    if not api:
      changed, api = self._create_api()
    elif ApiGwRestApi._is_changed(api, self.module.params):
      changed, api = self._update_api(api.get('id'))

    return changed, api

  def _maybe_delete_api(self, api):
    """
    Delete's the discovered api via boto3, as appropriate
    :param api: The discovered API
    :return: (changed, result)
              changed: Boolean showing whether a change occurred
              result: Empty hash
    """
    if not api:
      return False, api

  def _update_api(self, id):
    """
    Updates the API with the provided id using boto3
    :param id: Id of the discovered rest api
    :return: (changed, result)
              changed: Boolean showing whether a change occurred
              result: The resulting rest api object after the update
    """
    api = None
    try:
      api = self.client.update_rest_api(restApiId=id, patchOperations=[
        {'op': 'replace', 'path': '/name', 'value': self.module.params.get('name')},
        {'op': 'replace', 'path': '/description', 'value': self.module.params.get('description')},
      ])
    except:
      self.module.fail_json(msg='Encountered fatal error calling boto3 update_rest_api function')
    return True, api

  def _create_api(self):
    """
    Creates a new api based on user input
    :return: (True, result)
              True
              result: The resulting rest api object after the create
    """
    api = None
    try:
      api = self.client.create_rest_api(name=self.module.params.get('name'), description=self.module.params.get('description'))
    except:
      self.module.fail_json(msg='Encountered fatal error calling boto3 create_rest_api function')
    return True, api

  def process_request(self):
    """
    Process the user's request -- the primary code path
    :return: Returns either fail_json or exit_json
    """
    params = self.module.params
    api = self._retrieve_rest_api()
    changed = False

    if params.get('state') == 'absent':
      changed, api = self._maybe_delete_api(api)
    else:
      changed, api = self._create_or_update_api(api)

    return self.module.exit_json(changed=changed, api=api)


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
