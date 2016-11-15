#!/usr/bin/python

# API Gateway Ansible Modules
#
# Modules in this project allow management of the AWS API Gateway service.
#
# Authors:
#  - Brian Felton <bjfelton@gmail.com>
#
# apigw_resource
#    Manage creation, update, and removal of API Gateway Method resources
#

## TODO: Add an appropriate license statement

DOCUMENTATION='''
module: apigw_method
description:
  - An Ansible module to add, update, or remove AWS API Gateway
    method resources
version_added: "2.2"
options:
  name:
    description:
      - The name of the method on which to operate
    choices: ['get', 'put', 'post', 'delete', 'patch', 'head']
    required: True
  rest_api_id:
    description:
      - The id of the parent rest api
    required: True
  resource_id:
    description:
      - The id of the resource to which the method belongs
    required: True
  state:
    description:
      - Determine whether to assert if resource should exist or not
    choices: ['present', 'absent']
    default: 'present'
    required: False

TODO: FINISH THIS

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
TODO: FINISH THIS
'''

RETURN = '''
TODO: FINISH THIS
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

class InvalidInputError(Exception):
  def __init__(self, param, fail_message):
    """
    Exceptions raised for parameter validation errors
    :param param: The parameter with an illegal value
    :param fail_message: Message specifying why exception is being raised
    """
    Exception.__init__(self, "Error validating {0}: {1}".format(param, fail_message))

class ArgBuilder:
  @staticmethod
  def put_method(params):
    return dict(
      restApiId=params.get('rest_api_id'),
      resourceId=params.get('resource_id'),
      httpMethod=params.get('name'),
      authorizationType=params.get('authorization_type'),
      apiKeyRequired=params.get('api_key_required', False),
      requestParameters=ArgBuilder.request_params(params.get('request_params', []))
    )

  @staticmethod
  def put_integration(params):
    args = dict(
      restApiId=params.get('rest_api_id'),
      resourceId=params.get('resource_id'),
      httpMethod=params.get('name'),
      type=params['method_integration'].get('integration_type'),
      requestParameters=ArgBuilder.request_params(params['method_integration'].get('integration_params', [])),
      requestTemplates=ArgBuilder.add_templates(params['method_integration'].get('request_templates', []))
    )

    optional_map = {
      'http_method': 'integrationHttpMethod',
      'uri': 'uri',
      'passthrough_behavior': 'passthroughBehavior',
      'cache_namespace': 'cacheNamespace',
      'cache_key_parameters': 'cacheKeyParameters'
    }

    ArgBuilder.add_optional_params(params['method_integration'], args, optional_map)

    return args

  @staticmethod
  def add_templates(params):
    resp = {}
    for p in params:
      resp[p.get('content_type')] = p.get('template')

    return resp

  @staticmethod
  def add_optional_params(params, args_dict, optional_args):
    for arg in optional_args:
      if arg in params:
        args_dict[optional_args[arg]] = params.get(arg)

  @staticmethod
  def request_params(params_list):
    params = {}

    for param in params_list:
      key = "method.request.{0}.{1}".format(param['location'], param['name'])
      if 'param_required' in param:
        params[key] = param['param_required']
      elif 'value' in param:
        params[key] = param['value']

    return params


class ApiGwMethod:
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
    return dict(
        name=dict(
          required=True,
          choices=['GET', 'PUT', 'POST', 'DELETE', 'PATCH', 'HEAD', 'ANY', 'OPTIONS'],
          aliases=['method']
        ),
        rest_api_id=dict(required=True),
        resource_id=dict(required=True),
        authorization_type=dict(required=False, default='NONE'),
        authorizer_id=dict(required=False),
        api_key_required=dict(required=False, type='bool', default=False),
        request_params=dict(
          type='list',
          required=False,
          default=[],
          name=dict(required=True),
          location=dict(required=True, choices=['querystring', 'path', 'header']),
          param_required=dict(type='bool')
        ),
        method_integration=dict(
          required=True,
          integration_type=dict(
            required=False,
            default='AWS',
            choices=['AWS', 'MOCK', 'HTTP', 'HTTP_PROXY', 'AWS_PROXY']
          ),
          http_method=dict(required=False, default='POST', choices=['POST', 'GET', 'PUT']),
          uri=dict(required=False),
          passthrough_behavior=dict(
            required=False,
            default='when_no_templates',
            choices=['when_no_templates', 'when_no_match', 'never']
          ),
          request_templates=dict(
            required=False,
            type='list',
            default=[],
            content_type=dict(required=True),
            template=dict(required=True)
          ),
          cache_namespace=dict(required=False, default=''),
          cache_key_parameters=dict(required=False, type='list', default=[]),
          integration_params=dict(
            type='list',
            required=False,
            default=[],
            name=dict(required=True),
            location=dict(required=True, choices=['querystring', 'path', 'header']),
            value=dict(required=True)
          )
        ),
        method_responses=dict(
          type='list',
          required=True,
          status_code=dict(required=True),
          response_models=dict(
            type='list',
            required=False,
            default=[],
            content_type=dict(required=True),
            model=dict(required=False, default='Empty', choices=['Empty', 'Error'])
          )
        ),
        integration_responses=dict(
          type='list',
          required=True,
          status_code=dict(required=True),
          is_default=dict(required=False, default=False, type='bool'),
          pattern=dict(required=False),
          response_params=dict(
            type='list',
            required=False,
            default=[],
            name=dict(required=True),
            location=dict(required=True, choices=['querystring', 'path', 'header']),
            value=dict(required=True)
          ),
          response_templates=dict(
            required=False,
            type='list',
            default=[],
            content_type=dict(required=True),
            template=dict(required=True)
          ),
        ),
        state=dict(default='present', choices=['present', 'absent'])
    )

  def validate_params(self):
    """
    Validate the module's argument spec for illegal combinations of arguments
    Throws InvalidInputError for any issues
    :return: Returns nothing
    """
    p = self.module.params
    if p['authorization_type'] == 'CUSTOM' and 'authorizer_id' not in p:
      raise InvalidInputError('authorizer_id', "authorizer_id must be provided when authorization_type is 'CUSTOM'")

    if p['method_integration']['integration_type'] in ['AWS', 'HTTP']:
      if 'http_method' not in p['method_integration']:
        raise InvalidInputError('method_integration', "http_method must be provided when integration_type is 'AWS' or 'HTTP'")
      elif 'uri' not in p['method_integration']:
        raise InvalidInputError('method_integration', "uri must be provided when integration_type is 'AWS' or 'HTTP'")

    for ir in p['integration_responses']:
      if 'is_default' in ir and ir['is_default'] and 'pattern' in ir:
        raise InvalidInputError('integration_responses', "'pattern' must not be provided when 'is_default' is True")
      elif 'pattern' not in ir and ('is_default' not in ir or not ir['is_default']):
        raise InvalidInputError('integration_responses', "'pattern' must be provided when 'is_default' is False")


  def _find_method(self):
    """
    Execute a find to determine if the method exists
    :return: Returns result of find or exits with fail_json
    """
    p = self.module.params

    try:
      response = self.client.get_method(
          restApiId=p.get('rest_api_id'),
          resourceId=p.get('resource_id'),
          httpMethod=p.get('name')
      )
      return response
    except ClientError as e:
      if 'NotFoundException' in e.message:
        return None
      else:
        self.module.fail_json(msg='Error calling boto3 get_method: {}'.format(e))
    except BotoCoreError as e:
      self.module.fail_json(msg='Error calling boto3 get_method: {}'.format(e))

  def _delete_method(self):
    """
    Delete the method
    :return: nothing
    """
    if not self.module.check_mode:
      try:
        self.client.delete_method(
          restApiId=self.module.params.get('rest_api_id'),
          resourceId=self.module.params.get('resource_id'),
          httpMethod=self.module.params.get('name')
        )
      except BotoCoreError as e:
        self.module.fail_json(msg="Error calling boto3 delete_method: {}".format(e))

  def _create_method(self):
    """
    Create or update the method
    :return: nothing
    """
    response = None
    changed = True
    p = self
    if not self.module.check_mode:
      try:
        self.client.put_method(**ArgBuilder.put_method(self.module.params))
        self.client.put_integration(**ArgBuilder.put_integration(self.module.params))
        response = self._find_method()
      except BotoCoreError as e:
        self.module.fail_json(msg="Error while creating method via boto3: {}".format(e))

    return changed, response

  def process_request(self):
    """
    Process the user's request -- the primary code path
    :return: Returns either fail_json or exit_json
    """
    self.method = self._find_method()

    changed = False
    response = None

    if self.method is not None and self.module.params.get('state') == 'absent':
      self._delete_method()
      changed = True
    elif self.module.params.get('state') == 'present':
      (changed, response) = self._create_method()

    self.module.exit_json(changed=changed, method=response)

def main():
    """
    Instantiates the module and calls process_request.
    :return: none
    """
    module = AnsibleModule(
        argument_spec=ApiGwMethod._define_module_argument_spec(),
        supports_check_mode=True
    )

    rest_api = ApiGwMethod(module)
    rest_api.process_request()

from ansible.module_utils.basic import *  # pylint: disable=W0614
if __name__ == '__main__':
    main()
