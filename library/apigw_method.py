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
  - An Ansible module to add, update, or remove AWS API Gateway method resources
version_added: "2.2"
options:
  name:
    description: The name of the method on which to operate
    type: 'string'
    choices: ['GET', 'PUT', 'POST', 'DELETE', 'PATCH', 'HEAD']
    required: True
  rest_api_id:
    description: The id of the parent rest api
    type: 'string'
    required: True
  resource_id:
    description: The id of the resource to which the method belongs
    type: 'string'
    required: True
  authorization_type:
    description: The type of authorization used for the method
    type: 'string'
    default: 'NONE'
    required: False
  authorizer_id:
    description: The id of an Authorizer to use on this method (required when C(authorization_type) is 'CUSTOM').
    type: 'string'
    default: None
    required: False
  api_key_required:
    description: Specifies if an api key is required
    type: 'bool'
    default: False
    required: False
  request_params:
    description: List of dictionaries specifying method request parameters that can be accepted by this method
    type: 'list'
    default: []
    required: False
    options:
      name:
        description: The name of the request parameter
        type: 'string'
        required: True
      location:
        description: Identifies where in the request to find the parameter
        type: 'string'
        choices: ['querystring', 'path', 'header']
        required: True
      param_required:
        description: Specifies if the field is required or optional
        type: 'bool'
        required: True
  method_integration:
    description: Dictionary of parameters that specify how and to which resource API Gateway should map requests. This is required when C(state) is 'present'.
    type: 'dict'
    default: {}
    required: False
    options:
      integration_type:
        description: The type of method integration
        type: 'string'
        default: 'AWS'
        choices: ['AWS', 'MOCK', 'HTTP', 'HTTP_PROXY', 'AWS_PROXY']
        required: False
      http_method:
        description: Method used by the integration.  This is required when C(integration_type) is 'HTTP', 'AWS_PROXY', or 'AWS'.
        type: 'string'
        default: 'POST'
        choices: ['POST', 'GET', 'PUT']
        required: False
      uri:
        description: The URI of the integration input.  This field is required when C(integration_type) is 'HTTP', 'AWS_PROXY', or 'AWS'.
        type: 'string'
        default: None
        required: False
      credentials:
        description: If present, use these credentials for the integration
        type: 'string'
        default: None
        required: False
      passthrough_behavior:
        description: Specifies the pass-through behaving for incoming requests based on the Content-Type header in the request and the available mapping templates specified in C(request_templates).
        type: 'string'
        default: 'when_no_templates'
        choices: ['when_no_templates', 'when_no_match', 'never']
        required: False
      request_templates:
        description: List of dictionaries that represent Velocity templates that are applied to the request payload.
        type: 'list'
        default: []
        required: False
        options:
          content_type:
            description: The type of the content for this template (e.g. application/json)
            type: 'string'
            required: True
          template:
            description: The template to apply
            type: 'string'
            required: True
      uses_caching:
        description: Flag that indicates if this method uses caching.  Specifying false ensures that caching is disabled for the method if it is otherwise enabled .
        type: 'bool'
        default: False
        required: False
      cache_namespace:
        description: Specifies input cache namespace
        type: 'string'
        default: ''
        required: False
      cache_key_parameters:
        description: Specifies input cache key parameters
        type: 'list'
        default: []
        required: False
      integration_params:
        description: List of dictionaries that represent parameters passed from the method request to the back end.
        type: 'list'
        default: []
        required: False
        options:
          name:
            description: A unique name for this request parameter
            type: 'string'
            required: True
          location:
            description: Where in the request to find the parameter
            type: 'string'
            choices: ['querystring', 'path', 'header']
            required: True
          value:
            description: The value to assign to the parameter
            type: 'string'
            required: True
  method_responses:
    description: List of dictionaries specifying mapping of response parameters to be passed back to the caller.  This section is required when C(state) is 'present'.
    type: 'list'
    default: []
    required: False
    options:
      status_code:
        description: The status code used to map the method response
        type: 'string'
        default: None
        required: False
      response_params:
        description: List of dictionaries defining header fields that are available in the integration response
        type: 'list'
        default: []
        required: False
        options:
          name:
            description: A unique name for this response parameter
            type: 'string'
            required: True
          is_required:
            description: Specifies if the field is required or not
            type: 'bool'
            required: True
      response_models:
        description: List of dictionaries that specify Model resources used for the response's content type.
        type: 'list'
        default: []
        required: False
        options:
          content_type:
            description: The type of the content for this model (e.g. application/json)
            type: 'string'
            required: True
          model:
            description: Type of the model
            type: 'string'
            default: 'Empty'
            choices: ['Empty', 'Error']
            required: False
  integration_responses:
    description: List of dictionaries the map backend responses to the outbound response.  This section is required when C(state) is 'present'.
    type: 'list'
    default: []
    required: False
    options:
      status_code:
        description: The status code used to map the integration response
        type: 'string'
        required: True
      is_default:
        description: Flag to specify if this is the default response code
        type: 'bool'
        default: False
        required: False
      pattern:
        description: Selection pattern of the integration response.  This field is required when C(is_default) is False.  This field must be omitted when C(is_default) is True.
        type: 'string'
        default: None
        required: False
      response_params:
        description: List of dictionaries mapping fields in the response to integration response header values, static values, or a JSON expression from the ingration response body.
        type: 'list'
        default: []
        required: False
        options:
          name:
            description: A unique name for this response parameter
            type: 'string'
            required: True
          location:
            description: Where in the response to find the parameter
            type: 'string'
            choices: ['body', 'header']
            required: True
          value:
            description: The value to assign to the parameter
            type: 'string'
            required: True
      response_templates:
        description: Response templates for the integration response
        type: 'list'
        default: []
        required: False
        options:
          content_type:
            description: The type of the content for this template (e.g. application/json)
            type: 'string'
            required: True
          template:
            description: The template to apply
            type: 'string'
            required: True
  state:
    description: Determine whether to assert if resource should exist or not
    type: 'string'
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
- name: Test playbook for creating API GW Method resource
  hosts: localhost
  gather_facts: False
  tasks:
    - name: Create an api
      apigw_rest_api:
        name: 'my.example.com'
        state: present
      register: restapi

    - name: Create a resource
      apigw_resource:
        name: '/test'
        rest_api_id: "{{ restapi.api.id }}"
        state: present
      register: resource

    - name: Create a method
      apigw_method:
        rest_api_id: "{{ restapi.api.id }}"
        resource_id: "{{ resource.resource.id }}"
        name: GET
        api_key_required: False
        method_integration:
          integration_type: AWS
          http_method: POST
          uri: "arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/arn:aws:lambda:us-east-1:1234567890:function:my_test_lambda/invocations"
          passthrough_behavior: when_no_templates
          request_templates:
            - content_type: application/json
              template: '{"field": "value", "action": "GET"}'
        method_responses:
          - status_code: 200
            response_models:
              - content_type: application/json
          - status_code: 404
          - status_code: 500
        integration_responses:
          - status_code: 200
            is_default: True
          - status_code: 404
            pattern: ".*Not Found.*"
            response_templates:
              - content_type: application/json
                template: '{"output_value": "not found"}'
          - status_code: 500
            pattern: ".*(Unknown|stackTrace).*"
        state: present
      register: method

    - debug: var=method

- name: Remove method
  hosts: localhost
  gather_facts: False
  tasks:
    - name: Death
      apigw_method:
        rest_api_id: abcd1234
        resource_id: wxyz9876
        name: GET
        state: absent
      register: method

    - debug: var=method

'''

RETURN = '''
Response after create

{
    "method": {
        "changed": true,
        "method": {
            "ResponseMetadata": {
                "HTTPHeaders": {
                    "content-length": "1044",
                    "content-type": "application/json",
                    "date": "Wed, 23 Nov 2016 04:11:31 GMT",
                    "x-amzn-requestid": "ea41a39d-b132-11e6-a412-1d426252ad50"
                },
                "HTTPStatusCode": 200,
                "RequestId": "some_id_here",
                "RetryAttempts": 0
            },
            "apiKeyRequired": false,
            "authorizationType": "NONE",
            "httpMethod": "GET",
            "methodIntegration": {
                "cacheKeyParameters": [],
                "cacheNamespace": "abcdefg",
                "httpMethod": "POST",
                "integrationResponses": {
                    "200": {
                        "responseParameters": {},
                        "responseTemplates": {},
                        "selectionPattern": "",
                        "statusCode": "200"
                    },
                    "404": {
                        "responseParameters": {},
                        "responseTemplates": {
                            "application/json": "{\"output_value\": \"hurray\"}"
                        },
                        "selectionPattern": ".*Not Found.*",
                        "statusCode": "404"
                    },
                    "500": {
                        "selectionPattern": ".*(Unknown|stackTrace).*",
                        "statusCode": "500"
                    }
                },
                "passthroughBehavior": "WHEN_NO_TEMPLATES",
                "requestTemplates": {
                    "application/json": "{\"field\": \"value\", \"action\": \"GET\"}"
                },
                "type": "AWS",
                "uri": "arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/arn:aws:lambda:us-east-1:1234567890:function:test_lambda/invocations"
            },
            "methodResponses": {
                "200": {
                    "responseModels": {
                        "application/json": "Empty"
                    },
                    "statusCode": "200"
                },
                "404": {
                    "responseModels": {},
                    "statusCode": "404"
                },
                "500": {
                    "responseModels": {},
                    "statusCode": "500"
                }
            }
        }
    }
}

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

def create_patch(op, path, prefix=None, value=None):
  if re.search('/', path):
    path = re.sub('/', '~1', path)

  path = "/{}/{}".format(prefix, path) if prefix else "/{}".format(path)

  resp = {'op': op, 'path': path}
  if value is not None:
    resp['value'] = str(value)
  return resp

def patch_builder(method, params, param_map):
  ops = []
  for ans_param, boto_param in param_map.iteritems():
    if ans_param not in params and boto_param not in method:
      pass
    elif ans_param not in params and boto_param in method:
      ops.append(create_patch('remove', boto_param))
    elif ans_param in params and boto_param not in method:
      ops.append(create_patch('add', boto_param, value=params[ans_param]))
    elif str(params[ans_param]).lower() != str(method[boto_param]).lower():
      ops.append(create_patch('replace', boto_param, value=params[ans_param]))

  return ops

def two_way_compare_patch_builder(aws_dict, ans_dict, prefix):
  ops = []

  for k in ans_dict.keys():
    if k not in aws_dict.get(prefix, {}):
      ops.append(create_patch('add', k, prefix=prefix, value=ans_dict[k]))
    elif str(ans_dict[k]) != str(aws_dict[prefix][k]):
      ops.append(create_patch('replace', k, prefix=prefix, value=ans_dict[k]))

  for k in aws_dict.get(prefix, {}).keys():
    if k not in ans_dict:
      ops.append(create_patch('remove', k, prefix=prefix))

  return ops

def put_method(params):
  resp = dict(
    restApiId=params.get('rest_api_id'),
    resourceId=params.get('resource_id'),
    httpMethod=params.get('name'),
    authorizationType=params.get('authorization_type', 'NONE'),
    apiKeyRequired=params.get('api_key_required', False),
    requestParameters=param_transformer(params.get('request_params', []), 'request')
  )

  add_optional_params(params, resp, {'authorizer_id': 'authorizerId'})

  return resp

def update_method(method, params):
  patches = {}

  param_map = {
    'authorization_type': 'authorizationType',
    'api_key_required': 'apiKeyRequired',
  }

  if params.get('authorization_type', 'NONE') != 'NONE':
    param_map['authorizer_id'] = 'authorizerId'

  ops = patch_builder(method, params, param_map)
  ops.extend(
    two_way_compare_patch_builder(
      method,
      param_transformer(params.get('request_params', []), 'request'),
      'requestParameters'
    )
  )

  if ops:
    patches = dict(
      restApiId=params.get('rest_api_id'),
      resourceId=params.get('resource_id'),
      httpMethod=params.get('name'),
      patchOperations=ops
    )

  return patches

def put_integration(params):
  args = dict(
    restApiId=params.get('rest_api_id'),
    resourceId=params.get('resource_id'),
    httpMethod=params.get('name'),
    type=params['method_integration'].get('integration_type', 'AWS'),
    requestParameters=param_transformer(params['method_integration'].get('integration_params', []), 'request', 'integration'),
    requestTemplates=add_templates(params['method_integration'].get('request_templates', []))
  )

  optional_map = {
    'credentials': 'credentials',
    'passthrough_behavior': 'passthroughBehavior',
    'cache_namespace': 'cacheNamespace',
    'cache_key_parameters': 'cacheKeyParameters'
  }

  if params.get('method_integration', {}).get('credentials', '') != '':
    optional_map['credentials'] = 'credentials'

  if params['method_integration'].get('integration_type', 'AWS') in ['AWS', 'HTTP', 'AWS_PROXY']:
    optional_map['uri'] = 'uri'
    optional_map['http_method'] = 'integrationHttpMethod'

  add_optional_params(params['method_integration'], args, optional_map)

  return args

def update_integration(method, params):
  patches = {}

  mi_params = params.get('method_integration', {})

  param_map = {
    'passthrough_behavior': 'passthroughBehavior',
    'integration_type': 'type',
  }

  if params.get('method_integration', {}).get('credentials', '') != '':
    param_map['credentials'] = 'credentials'

  ops = []
  if params.get('method_integration', {}).get('integration_type', 'AWS').upper() in ['AWS', 'HTTP', 'AWS_PROXY']:
    param_map['uri'] = 'uri'

    # stupid special snowflake crap
    ops.extend(patch_builder(method.get('methodIntegration', {}), mi_params, {'http_method': 'httpMethod'}))
    if ops:
      ops[0]['path'] = '/integrationHttpMethod'

  if mi_params.get('uses_caching', False):
    param_map['cache_namespace'] = 'cacheNamespace'

  ops.extend(patch_builder(method.get('methodIntegration', {}), mi_params, param_map))

  if mi_params.get('uses_caching', False) and 'cache_key_parameters' in mi_params:
    new_params = []
    for ckp in mi_params.get('cache_key_parameters'):
      if ckp not in method.get('methodIntegration', {}).get('cacheKeyParameters', []):
        new_params.append(ckp)

    if new_params:
      ops.append(create_patch('replace', '/cacheKeyParameters', value=new_params))

  ops.extend(
    two_way_compare_patch_builder(
      method.get('methodIntegration', {}),
      param_transformer(mi_params.get('integration_params', []), 'request', 'integration'),
      'requestParameters'
    )
  )
  ops.extend(
    two_way_compare_patch_builder(
      method.get('methodIntegration', {}),
      add_templates(mi_params.get('request_templates', [])),
      'requestTemplates'
    )
  )

  if ops:
    patches = dict(
      restApiId=params.get('rest_api_id'),
      resourceId=params.get('resource_id'),
      httpMethod=params.get('name'),
      patchOperations=ops
    )

  return patches

def put_method_response(params):
  args = []

  for mr_params in params.get('method_responses', []):
    kwargs = dict(
      restApiId=params.get('rest_api_id'),
      resourceId=params.get('resource_id'),
      httpMethod=params.get('name'),
      statusCode=str(mr_params.get('status_code'))
    )

    resp_models = {}
    for model in mr_params.get('response_models', []):
      resp_models[model.get('content_type')] = model.get('model', 'Empty')
    kwargs['responseModels'] = resp_models

    resp_params = {}
    for resp in mr_params.get('response_params', []):
      resp_params["method.response.header.{}".format(resp.get('name'))] = resp.get('is_required')
    kwargs['responseParameters'] = resp_params

    args.append(kwargs)

  return args

def update_method_response(method, params):
  ops = {
    'creates': [],
    'deletes': [],
    'updates': []
  }

  patch_dict = {}

  # Coerce params into struct compatible with boto's response
  mr_dict = {}
  for p in params.get('method_responses', []):
    mr_dict[str(p['status_code'])] = {'models': {}, 'params': {}}
    for model in p.get('response_models', []):
      mr_dict[str(p['status_code'])]['models'][model['content_type']] = model.get('model', 'Empty')
    for rp in p.get('response_params', []):
      mr_dict[str(p['status_code'])]['params'][rp['name']] = rp['is_required']

  mr_aws = method.get('methodResponses', {})

  # Find codes that need to be created and models that need creation or replacement
  for code in mr_dict.keys():
    if code not in mr_aws:
      kwargs = dict(
        restApiId=params.get('rest_api_id'),
        resourceId=params.get('resource_id'),
        httpMethod=params.get('name'),
        statusCode=code
      )

      resp_models = {}
      for content_type, model in mr_dict[code]['models'].iteritems():
        resp_models[content_type] = model
      kwargs['responseModels'] = resp_models

      resp_params = {}
      for param_name, required in mr_dict[code]['params'].iteritems():
        resp_params["method.response.header.{}".format(param_name)] = required
      kwargs['responseParameters'] = resp_params

      ops['creates'].append(kwargs)
    else:
      for content_type, model in mr_dict[code]['models'].iteritems():
        if content_type not in mr_aws[code]['responseModels']:
          patch_dict.setdefault(code, []).append(create_patch('add', content_type, prefix='responseModels', value=model))
        elif model != mr_aws[code]['responseModels'][content_type]:
          patch_dict.setdefault(code, []).append(create_patch('replace', content_type, prefix='responseModels', value=model))

  # Find codes and response models that need to be deleted
  for code in mr_aws:
    if code not in mr_dict:
      kwargs = dict(
        restApiId=params.get('rest_api_id'),
        resourceId=params.get('resource_id'),
        httpMethod=params.get('name'),
        statusCode=code
      )
      ops['deletes'].append(kwargs)
    elif 'responseModels' in mr_aws[code]:
      for content_type, model in mr_aws[code]['responseModels'].iteritems():
        if content_type not in mr_dict[code]['models']:
          patch_dict.setdefault(code, []).append(create_patch('remove', content_type, prefix='responseModels'))

  for code in patch_dict:
    ops['updates'].append(dict(
      restApiId=params.get('rest_api_id'),
      resourceId=params.get('resource_id'),
      httpMethod=params.get('name'),
      statusCode=code,
      patchOperations=patch_dict[code]
    ))

  return ops

def put_integration_response(params):
  args = []

  for ir_params in params.get('integration_responses', []):
    kwargs = dict(
      restApiId=params.get('rest_api_id'),
      resourceId=params.get('resource_id'),
      httpMethod=params.get('name'),
      statusCode=str(ir_params.get('status_code')),
      selectionPattern='' if ir_params.get('is_default', False) else ir_params.get('pattern')
    )
    kwargs['responseParameters'] = param_transformer(ir_params.get('response_params', []), 'response')
    kwargs['responseTemplates'] = add_templates(ir_params.get('response_templates', []))
    args.append(kwargs)

  return args

def update_integration_response(method, params):
  ops = {
    'creates': [],
    'deletes': [],
    'updates': []
  }

  patch_dict = {}

  # Coerce params into struct compatible with boto's response
  ir_dict = {}
  for p in params.get('integration_responses', []):
    ir_dict[str(p['status_code'])] = {
      'pattern': '' if p.get('is_default', False) else p.get('pattern'),
      'response_templates': add_templates(p.get('response_templates', [])),
      'response_params': param_transformer(p.get('response_params', []), 'response'),
    }

  ir_aws = method.get('methodIntegration', {}).get('integrationResponses', {})

  # Find codes that need to be created and models that need creation or replacement
  for code in ir_dict.keys():
    if code not in ir_aws:
      kwargs = dict(
        restApiId=params.get('rest_api_id'),
        resourceId=params.get('resource_id'),
        httpMethod=params.get('name'),
        statusCode=code,
        selectionPattern=ir_dict[code]['pattern'],
        responseParameters=ir_dict[code]['response_params'],
        responseTemplates=ir_dict[code]['response_templates'],
      )
      ops['creates'].append(kwargs)
    else:
      # selectionPattern
      if ir_dict[code]['pattern'] != ir_aws[code].get('selectionPattern', ''):
        patch_dict.setdefault(code, []).append(create_patch('replace', 'selectionPattern', value=ir_dict[code]['pattern']))

      # responseParameters
      for param, value in ir_dict[code]['response_params'].iteritems():
        if 'responseParameters' not in ir_aws[code] or param not in ir_aws[code]['responseParameters']:
          patch_dict.setdefault(code, []).append(create_patch('add', param, prefix='responseParameters', value=value))
        elif value != ir_aws[code]['responseParameters'][param]:
          patch_dict.setdefault(code, []).append(create_patch('replace', param, prefix='responseParameters', value=value))

      # responseTemplates
      for ctype, tmpl in ir_dict[code]['response_templates'].iteritems():
        if 'responseTemplates' not in ir_aws[code] or ctype not in ir_aws[code]['responseTemplates']:
          patch_dict.setdefault(code, []).append(create_patch('add', ctype, prefix='responseTemplates', value=tmpl))
        elif tmpl != ir_aws[code]['responseTemplates'][ctype]:
          patch_dict.setdefault(code, []).append(create_patch('replace', ctype, prefix='responseTemplates', value=tmpl))

  # Find codes and response models that need to be deleted
  for code in ir_aws:
    if code not in ir_dict:
      kwargs = dict(
        restApiId=params.get('rest_api_id'),
        resourceId=params.get('resource_id'),
        httpMethod=params.get('name'),
        statusCode=code
      )
      ops['deletes'].append(kwargs)
    else:
      if 'responseTemplates' in ir_aws[code]:
        for ctype, tmpl in ir_aws[code]['responseTemplates'].iteritems():
          if ctype not in ir_dict[code]['response_templates']:
            patch_dict.setdefault(code, []).append(create_patch('remove', ctype, prefix='responseTemplates'))

      if 'responseParameters' in ir_aws[code]:
        for param, value in ir_aws[code]['responseParameters'].iteritems():
          if param not in ir_dict[code]['response_params']:
            patch_dict.setdefault(code, []).append(create_patch('remove', param, prefix='responseParameters'))

  for code in patch_dict:
    ops['updates'].append(dict(
      restApiId=params.get('rest_api_id'),
      resourceId=params.get('resource_id'),
      httpMethod=params.get('name'),
      statusCode=code,
      patchOperations=patch_dict[code]
    ))

  return ops

def add_templates(params):
  resp = {}
  for p in params:
    resp[p.get('content_type')] = p.get('template')

  return resp

def add_optional_params(params, args_dict, optional_args):
  for arg in optional_args:
    if arg in params and params.get(arg) is not None:
      args_dict[optional_args[arg]] = params.get(arg)

def param_transformer(params_list, type, location='method'):
  params = {}

  for param in params_list:
    key = "{3}.{0}.{1}.{2}".format(type, param['location'], param['name'], location)
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
          type='dict',
          default={},
          integration_type=dict(
            required=False,
            default='AWS',
            choices=['AWS', 'MOCK', 'HTTP', 'HTTP_PROXY', 'AWS_PROXY']
          ),
          http_method=dict(required=False, default='POST', choices=['POST', 'GET', 'PUT']),
          uri=dict(required=False),
          credentials=dict(required=False),
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
          uses_caching=dict(required=False, default=False, type='bool'),
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
          default=[],
          status_code=dict(required=True),
          response_params=dict(
            type='list',
            required=False,
            default=[],
            name=dict(required=True),
            is_required=dict(required=True, type='bool')
          ),
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
          default=[],
          status_code=dict(required=True),
          is_default=dict(required=False, default=False, type='bool'),
          pattern=dict(required=False),
          response_params=dict(
            type='list',
            required=False,
            default=[],
            name=dict(required=True),
            location=dict(required=True, choices=['body', 'header']),
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
    if p['state'] == 'present':
      for param in ['method_integration', 'method_responses', 'integration_responses']:
        if param not in p:
          raise InvalidInputError(param, "'{}' must be provided when 'state' is present".format(param))

    if p['authorization_type'] == 'CUSTOM' and 'authorizer_id' not in p:
      raise InvalidInputError('authorizer_id', "authorizer_id must be provided when authorization_type is 'CUSTOM'")

    if p['method_integration']['integration_type'] in ['AWS', 'HTTP', 'AWS_PROXY']:
      if 'http_method' not in p['method_integration']:
        raise InvalidInputError('method_integration', "http_method must be provided when integration_type is 'AWS', 'AWS_PROXY', or 'HTTP'")
      elif 'uri' not in p['method_integration']:
        raise InvalidInputError('method_integration', "uri must be provided when integration_type is 'AWS', 'AWS_PROXY', or 'HTTP'")

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
    if not self.module.check_mode:
      try:
        self.client.put_method(**put_method(self.module.params))
        self.client.put_integration(**put_integration(self.module.params))
        for args in put_method_response(self.module.params):
          self.client.put_method_response(**args)
        for args in put_integration_response(self.module.params):
          self.client.put_integration_response(**args)
        response = self._find_method()
      except BotoCoreError as e:
        self.module.fail_json(msg="Error while creating method via boto3: {}".format(e))

    return changed, response

  def _update_method(self):
    response = None
    changed = False

    try:
      um_args = update_method(self.method, self.module.params)
      if um_args:
        changed = True
        if not self.module.check_mode:
          self.client.update_method(**um_args)

      if 'methodIntegration' not in self.method:
        changed = True
        if not self.module.check_mode:
          self.client.put_integration(**put_integration(self.module.params))
      else:
        ui_args = update_integration(self.method, self.module.params)
        if ui_args:
          changed = True
          if not self.module.check_mode:
            self.client.update_integration(**ui_args)

      umr_args = update_method_response(self.method, self.module.params)
      if umr_args['creates'] or umr_args['deletes'] or umr_args['updates']:
        changed = True
        if not self.module.check_mode:
          for create_kwargs in umr_args['creates']:
            self.client.put_method_response(**create_kwargs)
          for patch_kwargs in umr_args['updates']:
            self.client.update_method_response(**patch_kwargs)
          for delete_kwargs in umr_args['deletes']:
            self.client.delete_method_response(**delete_kwargs)

      uir_args = update_integration_response(self.method, self.module.params)
      if uir_args['creates'] or uir_args['deletes'] or uir_args['updates']:
        changed = True
        if not self.module.check_mode:
          for create_kwargs in uir_args['creates']:
            self.client.put_integration_response(**create_kwargs)
          for patch_kwargs in uir_args['updates']:
            self.client.update_integration_response(**patch_kwargs)
          for delete_kwargs in uir_args['deletes']:
            self.client.delete_integration_response(**delete_kwargs)

      response = self._find_method()
    except BotoCoreError as e:
      self.module.fail_json(msg="Error while updating method via boto3: {}".format(e))

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
    elif self.module.params.get('state', 'present') == 'present' and self.method is None:
      (changed, response) = self._create_method()
    elif self.module.params.get('state', 'present') == 'present':
      (changed, response) = self._update_method()

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
