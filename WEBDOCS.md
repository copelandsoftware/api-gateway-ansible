# Ansible Modules for AWS API Gateway
### *Granular, Idempotent Goodness*

---
### Requirements
* See official Ansible docs

---
### Modules

  * [apigw_domain_name - add, update, or remove domainname resources](#apigw_domain_name)
  * [apigw_base_path_mapping - add, update, or remove base path mapping resources](#apigw_base_path_mapping)
  * [apigw_rest_api - add, update, or remove rest api resources](#apigw_rest_api)
  * [apigw_deployment - create an apigateway deployment](#apigw_deployment)
  * [apigw_usage_plan_key - add or remove usageplankey resources](#apigw_usage_plan_key)
  * [apigw_authorizer - add, update, or remove authorizer resources](#apigw_authorizer)
  * [apigw_usage_plan - add, update, or remove usageplan and usageplankey resources](#apigw_usage_plan)
  * [apigw_method - add, update, or remove aws api gateway method resources](#apigw_method)
  * [apigw_stage - an ansible module to update or remove an apigateway stage](#apigw_stage)
  * [apigw_api_key - add, update, or remove apikey resources](#apigw_api_key)
  * [apigw_resource - add or remove resource resources](#apigw_resource)
  * [apigw_model - add or remove models](#apigw_model)

---

## <a id="apigw_domain_name"></a>apigw_domain_name
Add, update, or remove DomainName resources

  * [Synopsis](#apigw_domain_name-synopsis)
  * [Options](#apigw_domain_name-options)
  * [Examples](#apigw_domain_name-examples)
  * [Notes](#apigw_domain_name-notes)

#### <a id="apigw_domain_name-synopsis"></a>Synopsis
* Uses domain name for identifying resources for CRUD operations
* Update only covers certificate name

#### <a id="apigw_domain_name-options"></a>Options

| Parent | Parameter     | required    | default  | choices    | comments |
|--------| ------------- |-------------| ---------|----------- |--------- |
| None | name |   yes  |  | |  The name of the DomainName resource on which to operate  |
| None | cert_private_key |   no  |    | |  Certificate's private key. Required when C(state) is 'present'  |
| None | cert_body |   no  |    | |  Body of the server certificate. Required when C(state) is 'present'  |
| None | state |   no  |  present  | <ul> <li>present</li>  <li>absent</li> </ul> |  Should domain_name exist or not  |
| None | cert_name |   no  |    | |  Name of the associated certificate. Required when C(state) is 'present'  |
| None | cert_chain |   no  |    | |  Intermediate certificates and optionally the root certificate.  If root is included, it must follow the intermediate certificates. Required when C(state) is 'present'  |


 
#### <a id="apigw_domain_name-examples"></a>Examples

```
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

```


#### <a id="apigw_domain_name-notes"></a>Notes

- This module requires that you have boto and boto3 installed and that your credentials are created or stored in a way that is compatible (see U(https://boto3.readthedocs.io/en/latest/guide/quickstart.html#configuration)).


---


## <a id="apigw_base_path_mapping"></a>apigw_base_path_mapping
Add, update, or remove Base Path Mapping resources

  * [Synopsis](#apigw_base_path_mapping-synopsis)
  * [Options](#apigw_base_path_mapping-options)
  * [Examples](#apigw_base_path_mapping-examples)
  * [Notes](#apigw_base_path_mapping-notes)

#### <a id="apigw_base_path_mapping-synopsis"></a>Synopsis
* Basic CRUD operations for Base Path Mapping resources

#### <a id="apigw_base_path_mapping-options"></a>Options

| Parent | Parameter     | required    | default  | choices    | comments |
|--------| ------------- |-------------| ---------|----------- |--------- |
| None | rest_api_id |   no  |    | |  The id of the Rest API to which this BasePathMapping belongs.  Required to create a base path mapping.  |
| None | state |   no  |  present  | <ul> <li>present</li>  <li>absent</li> </ul> |  Should base_path_mapping exist or not  |
| None | name |   yes  |  | |  The domain name of the Base Path Mapping resource on which to operate  |
| None | base_path |   no  |  (none)  | |  The base path name that callers of the api must provide.  Required when updating or deleting the mapping.  |
| None | stage |   no  |    | |  The name of the api's stage to which to apply this mapping.  Required to create the base path mapping.  |


 
#### <a id="apigw_base_path_mapping-examples"></a>Examples

```
---
- hosts: localhost
  gather_facts: False
  tasks:
  - name: do base path stuff
    apigw_base_path_mapping:
      name: dev.example.com
      rest_api_id: abcd1234
      stage: live
      state: present
    register: bpm

  - debug: var=bpm

```


#### <a id="apigw_base_path_mapping-notes"></a>Notes

- This module requires that you have boto and boto3 installed and that your credentials are created or stored in a way that is compatible (see U(https://boto3.readthedocs.io/en/latest/guide/quickstart.html#configuration)).


---


## <a id="apigw_rest_api"></a>apigw_rest_api
Add, update, or remove REST API resources

  * [Synopsis](#apigw_rest_api-synopsis)
  * [Options](#apigw_rest_api-options)
  * [Examples](#apigw_rest_api-examples)
  * [Notes](#apigw_rest_api-notes)

#### <a id="apigw_rest_api-synopsis"></a>Synopsis
* An Ansible module to add, update, or remove REST API resources for AWS API Gateway.

#### <a id="apigw_rest_api-options"></a>Options

| Parent | Parameter     | required    | default  | choices    | comments |
|--------| ------------- |-------------| ---------|----------- |--------- |
| None | state |   no  |  present  | <ul> <li>present</li>  <li>absent</li> </ul> |  Determine whether to assert if api should exist or not  |
| None | name |   yes  |  | |  The name of the rest api on which to operate  |
| None | description |   no  |  | |  A description for the rest api  |


 
#### <a id="apigw_rest_api-examples"></a>Examples

```
- name: Add rest api to Api Gateway
  hosts: localhost
  gather_facts: False
  connection: local
  tasks:
    - name: Create rest api
      apigw_rest_api:
        name: 'docs.example.io'
        description: 'stolen straight from the docs'
        state: present
      register: api

    - name: debug
      debug: var=api

- name: Rest api from Api Gateway
  hosts: localhost
  gather_facts: False
  connection: local
  tasks:
    - name: Create rest api
      apigw_rest_api:
        name: 'docs.example.io'
        state: absent
      register: api

    - name: debug
      debug: var=api

```


#### <a id="apigw_rest_api-notes"></a>Notes

- This module requires that you have boto and boto3 installed and that your credentials are created or stored in a way that is compatible (see U(https://boto3.readthedocs.io/en/latest/guide/quickstart.html#configuration)).


---


## <a id="apigw_deployment"></a>apigw_deployment
Create an apigateway Deployment

  * [Synopsis](#apigw_deployment-synopsis)
  * [Options](#apigw_deployment-options)
  * [Examples](#apigw_deployment-examples)
  * [Notes](#apigw_deployment-notes)

#### <a id="apigw_deployment-synopsis"></a>Synopsis
* Creates Deployments (no other operations)
* A deployment is always created -- this module is not idempotent

#### <a id="apigw_deployment-options"></a>Options

| Parent | Parameter     | required    | default  | choices    | comments |
|--------| ------------- |-------------| ---------|----------- |--------- |
| None | name |   yes  |  | |  The name of the stage to deploy  |
| None | cache_cluster_size |   no  |    | <ul> <li>0.5</li>  <li>1.6</li>  <li>6.1</li>  <li>13.5</li>  <li>28.4</li>  <li>58.2</li>  <li>118</li>  <li>237</li> </ul> |  Specifies the size of the cache cluster  |
| None | stage_description |   no  |    | |  The description of the stage resource for the Deployment resource to create  |
| None | rest_api_id |   yes  |  | |  The id of the parent rest api  |
| None | cache_cluster_enabled |   no  |  False  | |  Enables a cache cluster for the resource if True  |
| None | description |   no  |    | |  The description for the Deployment resource to create  |


 
#### <a id="apigw_deployment-examples"></a>Examples

```
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

```


#### <a id="apigw_deployment-notes"></a>Notes

- {u'WARNING': u'This module is not idempotent'}

- This module requires that you have boto and boto3 installed and that your credentials are created or stored in a way that is compatible (see U(https://boto3.readthedocs.io/en/latest/guide/quickstart.html#configuration)).


---


## <a id="apigw_usage_plan_key"></a>apigw_usage_plan_key
Add or remove UsagePlanKey resources

  * [Synopsis](#apigw_usage_plan_key-synopsis)
  * [Options](#apigw_usage_plan_key-options)
  * [Examples](#apigw_usage_plan_key-examples)
  * [Notes](#apigw_usage_plan_key-notes)

#### <a id="apigw_usage_plan_key-synopsis"></a>Synopsis
* Create or remove Usage Plan Key resources

#### <a id="apigw_usage_plan_key-options"></a>Options

| Parent | Parameter     | required    | default  | choices    | comments |
|--------| ------------- |-------------| ---------|----------- |--------- |
| None | key_type |   no  |  API_KEY  | <ul> <li>API_KEY</li> </ul> |  Type of the api key.  You can choose any value you like, so long as you choose 'API_KEY'.  |
| None | state |   no  |  present  | <ul> <li>present</li>  <li>absent</li> </ul> |  Should usage_plan_key exist or not  |
| None | usage_plan_id |   yes  |  | |  Id of the UsagePlan resource to which a key will be associated  |
| None | api_key_id |   yes  |  | |  Id of the UsagePlan resource to which a key will be associated  |


 
#### <a id="apigw_usage_plan_key-examples"></a>Examples

```
---
- hosts: localhost
  gather_facts: False
  tasks:
  - name: usage plan creation
    apigw_usage_plan_key:
      usage_plan_id: 12345abcde
      api_key_id: zyxw9876
      key_type: API_KEY
      state: present
    register: plankey

  - debug: var=plankey

```


#### <a id="apigw_usage_plan_key-notes"></a>Notes

- This module requires that you have boto and boto3 installed and that your credentials are created or stored in a way that is compatible (see U(https://boto3.readthedocs.io/en/latest/guide/quickstart.html#configuration)).


---


## <a id="apigw_authorizer"></a>apigw_authorizer
Add, update, or remove Authorizer resources

  * [Synopsis](#apigw_authorizer-synopsis)
  * [Options](#apigw_authorizer-options)
  * [Examples](#apigw_authorizer-examples)
  * [Notes](#apigw_authorizer-notes)

#### <a id="apigw_authorizer-synopsis"></a>Synopsis
* Standard CRUD operations for Authorizer resources

#### <a id="apigw_authorizer-options"></a>Options

| Parent | Parameter     | required    | default  | choices    | comments |
|--------| ------------- |-------------| ---------|----------- |--------- |
| None | auth_type |   no  |    | |  Optional customer-defined field used in Swagger docs - has no functional impact  |
| None | name |   yes  |  | |  The name of the authorizer on which to operate  |
| None | rest_api_id |   yes  |  | |  The id of the Rest API to which this Authorizer belongs  |
| None | identity_validation_expression |   no  |    | |  Validation expression for the incoming entity  |
| None | uri |   no  |    | |  The autorizer's uri (required with C(state) is 'present')  |
| None | provider_arns |   no  |  []  | |  |
| None | state |   no  |  present  | <ul> <li>present</li>  <li>absent</li> </ul> |  Should authorizer exist or not  |
| None | result_ttl_seconds |   no  |  0  | |  The TTL of cached authorizer results in seconds  |
| None | identity_source |   no  |    | |  Source of the identity in an incoming request (required when C(state) is 'present')  |
| None | credentials |   no  |    | |  Specifies credentials required for the authorizer, if any  |
| None | type |   no  |    | <ul> <li>TOKEN</li>  <li>COGNITO_USER_POOLS</li> </ul> |  Type of the authorizer (required when C(state) is 'present')  |


 
#### <a id="apigw_authorizer-examples"></a>Examples

```
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

```


#### <a id="apigw_authorizer-notes"></a>Notes

- This module requires that you have boto and boto3 installed and that your credentials are created or stored in a way that is compatible (see U(https://boto3.readthedocs.io/en/latest/guide/quickstart.html#configuration)).


---


## <a id="apigw_usage_plan"></a>apigw_usage_plan
Add, update, or remove UsagePlan and UsagePlanKey resources

  * [Synopsis](#apigw_usage_plan-synopsis)
  * [Options](#apigw_usage_plan-options)
  * [Examples](#apigw_usage_plan-examples)
  * [Notes](#apigw_usage_plan-notes)

#### <a id="apigw_usage_plan-synopsis"></a>Synopsis
* Basic CRUD operations on Usage Plan Key resources
* Does not support updating name (see Notes)

#### <a id="apigw_usage_plan-options"></a>Options

| Parent | Parameter     | required    | default  | choices    | comments |
|--------| ------------- |-------------| ---------|----------- |--------- |
| None | quota_offset |   no  |  -1  | |  Number of requests subtracted from the given limit in the initial time period  |
| None | name |   yes  |  | |  The domain name of the UsagePlan resource on which to operate  |
| None | quota_limit |   no  |  -1  | |  Maxiumum number of requests that can be made in a given time period  |
| None | throttle_burst_limit |   no  |  -1  | |  API request burst limit  |
| None | throttle_rate_limit |   no  |  -1.0  | |  API request steady-state limit  |
| None | quota_period |   no  |    | <ul> <li></li>  <li>DAY</li>  <li>WEEK</li>  <li>MONTH</li> </ul> |  The time period in which the limit applies  |
| None | state |   no  |  present  | <ul> <li>present</li>  <li>absent</li> </ul> |  Should usage_plan exist or not  |
| None | api_stages |   no  |  []  | |  List of associated api stages  |
| api_stages | rest_api_id |   yes  |  | |  ID of the associated API stage in the usage plan  |
| api_stages | stage |   yes  |  | |  API stage name of the associated API stage in the usage plan  |
| None | description |   no  |    | |  UsagePlan description  |


 
#### <a id="apigw_usage_plan-examples"></a>Examples

```
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

```


#### <a id="apigw_usage_plan-notes"></a>Notes

- While it is possible via the boto api to update the UsagePlan's name, this module does not support this functionality since it searches for the UsagePlan's id by its name.

- This module requires that you have boto and boto3 installed and that your credentials are created or stored in a way that is compatible (see U(https://boto3.readthedocs.io/en/latest/guide/quickstart.html#configuration)).


---


## <a id="apigw_method"></a>apigw_method
Add, update, or remove AWS API Gateway Method resources

  * [Synopsis](#apigw_method-synopsis)
  * [Options](#apigw_method-options)
  * [Examples](#apigw_method-examples)
  * [Notes](#apigw_method-notes)

#### <a id="apigw_method-synopsis"></a>Synopsis
* CRUD operations for Method resources
* Covers Method, Method Integration, Method Response, and Integration Response APIs
* Utilizes non-standard argument structure due to the complexity of the module contract

#### <a id="apigw_method-options"></a>Options

| Parent | Parameter     | required    | default  | choices    | comments |
|--------| ------------- |-------------| ---------|----------- |--------- |
| None | authorization_type |   no  |  NONE  | |  The type of authorization used for the method  |
| None | name |   yes  |  | <ul> <li>GET</li>  <li>PUT</li>  <li>POST</li>  <li>DELETE</li>  <li>PATCH</li>  <li>HEAD</li> </ul> |  The name of the method on which to operate  |
| None | request_params |   no  |  []  | |  List of dictionaries specifying method request parameters that can be accepted by this method  |
| request_params | location |   yes  |  | <ul> <li>querystring</li>  <li>path</li>  <li>header</li> </ul> |  Identifies where in the request to find the parameter  |
| request_params | name |   yes  |  | |  The name of the request parameter  |
| request_params | param_required |   yes  |  | |  Specifies if the field is required or optional  |
| None | request_models |   no  | [] | |  List of dictionaries of known models to attach to the method request  |
| None | resource_id |   yes  |  | |  The id of the resource to which the method belongs  |
| None | state |   no  |  present  | <ul> <li>present</li>  <li>absent</li> </ul> |  Determine whether to assert if resource should exist or not  |
| None | integration_responses |   no  |  []  | |  List of dictionaries the map backend responses to the outbound response.  This section is required when C(state) is 'present'.  |
| integration_responses | is_default |   no  |  False  | |  Flag to specify if this is the default response code  |
| integration_responses | status_code |   yes  |  | |  The status code used to map the integration response  |
| integration_responses | response_templates |   no  |  []  | |  Response templates for the integration response  |
| integration_responses.<br />response_templates | content_type |   yes  |  | |  The type of the content for this template (e.g. application/json)  |
| integration_responses.<br />response_templates | template |   yes  |  | |  The template to apply  |
| integration_responses | response_params |   no  |  []  | |  List of dictionaries mapping fields in the response to integration response header values, static values, or a JSON expression from the integration response body.  |
| integration_responses.<br />response_params | name |   yes  |  | |  A unique name for this response parameter  |
| integration_responses.<br />response_params | value |   yes  |  | |  The value to assign to the parameter  |
| integration_responses.<br />response_params | location |   yes  |  | <ul> <li>body</li>  <li>header</li> </ul> |  Where in the response to find the parameter  |
| integration_responses | pattern |   no  |    | |  Selection pattern of the integration response.  This field is required when C(is_default) is False.  This field must be omitted when C(is_default) is True.  |
| None | rest_api_id |   yes  |  | |  The id of the parent rest api  |
| None | authorizer_id |   no  |    | |  The id of an Authorizer to use on this method (required when C(authorization_type) is 'CUSTOM').  |
| None | api_key_required |   no  |  False  | |  Specifies if an api key is required  |
| None | method_responses |   no  |  []  | |  List of dictionaries specifying mapping of response parameters to be passed back to the caller.  This section is required when C(state) is 'present'.  |
| method_responses | status_code |   no  |    | |  The status code used to map the method response  |
| method_responses | response_params |   no  |  []  | |  List of dictionaries defining header fields that are available in the integration response  |
| method_responses.<br />response_params | is_required |   yes  |  | |  Specifies if the field is required or not  |
| method_responses.<br />response_params | name |   yes  |  | |  A unique name for this response parameter  |
| method_responses | response_models |   no  |  []  | |  List of dictionaries that specify Model resources used for the response's content type.  |
| method_responses.<br />response_models | model |   no  |  Empty  | <ul> <li>Empty</li>  <li>Error</li> </ul> |  Type of the model  |
| method_responses.<br />response_models | content_type |   yes  |  | |  The type of the content for this model (e.g. application/json)  |
| None | method_integration |   no  |  {}  | |  Dictionary of parameters that specify how and to which resource API Gateway should map requests. This is required when C(state) is 'present'.  |
| method_integration | integration_type |   no  |  AWS  | <ul> <li>AWS</li>  <li>MOCK</li>  <li>HTTP</li>  <li>HTTP_PROXY</li>  <li>AWS_PROXY</li> </ul> |  The type of method integration  |
| method_integration | cache_namespace |   no  |    | |  Specifies input cache namespace  |
| method_integration | uri |   no  |    | |  The URI of the integration input.  This field is required when C(integration_type) is 'HTTP', 'AWS_PROXY', or 'AWS'.  |
| method_integration | request_templates |   no  |  []  | |  List of dictionaries that represent Velocity templates that are applied to the request payload.  |
| method_integration.<br />request_templates | content_type |   yes  |  | |  The type of the content for this template (e.g. application/json)  |
| method_integration.<br />request_templates | template |   yes  |  | |  The template to apply  |
| method_integration | content_handling |   no  |    | <ul> <li></li>  <li>convert_to_binary</li>  <li>convert_to_text</li> </ul> |  Specifies how to handle request payload content type conversions  |
| method_integration | http_method |   no  |  POST  | <ul> <li>POST</li>  <li>GET</li>  <li>PUT</li> </ul> |  Method used by the integration.  This is required when C(integration_type) is 'HTTP', 'AWS_PROXY', or 'AWS'.  |
| method_integration | integration_params |   no  |  []  | |  List of dictionaries that represent parameters passed from the method request to the back end.  |
| method_integration.<br />integration_params | name |   yes  |  | |  A unique name for this request parameter  |
| method_integration.<br />integration_params | value |   yes  |  | |  The value to assign to the parameter  |
| method_integration.<br />integration_params | location |   yes  |  | <ul> <li>querystring</li>  <li>path</li>  <li>header</li> </ul> |  Where in the request to find the parameter  |
| method_integration | credentials |   no  |    | |  If present, use these credentials for the integration  |
| method_integration | passthrough_behavior |   no  |  when_no_templates  | <ul> <li>when_no_templates</li>  <li>when_no_match</li>  <li>never</li> </ul> |  Specifies the pass-through behaving for incoming requests based on the Content-Type header in the request and the available mapping templates specified in C(request_templates).  |
| method_integration | uses_caching |   no  |  False  | |  Flag that indicates if this method uses caching.  Specifying false ensures that caching is disabled for the method if it is otherwise enabled .  |
| method_integration | cache_key_parameters |   no  |  []  | |  Specifies input cache key parameters  |


 
#### <a id="apigw_method-examples"></a>Examples

```
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


```


#### <a id="apigw_method-notes"></a>Notes

- This module is a beast in that it's covering four separate APIs for the four API Gateway stages

- Arguments are presented in a non-idiomatic manner -- arguments are grouped under dictionaries in order to better organize arguments to the four separate stages

- While the majority of the Method, Method Integration, Method Response, and Integration Response APIs are covered, there are likely gaps.  Issues and PRs are welcome.

- This module requires that you have boto and boto3 installed and that your credentials are created or stored in a way that is compatible (see U(https://boto3.readthedocs.io/en/latest/guide/quickstart.html#configuration)).


---


## <a id="apigw_stage"></a>apigw_stage
An Ansible module to update or remove an apigateway Stage

  * [Synopsis](#apigw_stage-synopsis)
  * [Options](#apigw_stage-options)
  * [Examples](#apigw_stage-examples)
  * [Notes](#apigw_stage-notes)

#### <a id="apigw_stage-synopsis"></a>Synopsis
* Updates or removes API Gateway Stage resources
* Only processes 'replace' patches for updates

#### <a id="apigw_stage-options"></a>Options

| Parent | Parameter     | required    | default  | choices    | comments |
|--------| ------------- |-------------| ---------|----------- |--------- |
| None | name |   yes  |  | |  The name of the stage to deploy  |
| None | cache_cluster_size |   no  |    | <ul> <li>0.5</li>  <li>1.6</li>  <li>6.1</li>  <li>13.5</li>  <li>28.4</li>  <li>58.2</li>  <li>118</li>  <li>237</li> </ul> |  Specifies the size of the cache cluster for the Stage resource  |
| None | method_settings |   no  |  []  | |  List of dictionaries capturing methods to be patched  |
| method_settings | method_name |   yes  |  | |  Name of the method to be patched  |
| method_settings | method_verb |   yes  |  | <ul> <li>GET</li>  <li>PUT</li>  <li>POST</li>  <li>DELETE</li>  <li>HEAD</li>  <li>PATCH</li>  <li>OPTIONS</li> </ul> |  Verb of the method to be patched  |
| method_settings | caching_enabled |   no  |  False  | |  Flag indicating if caching should be enabled  |
| None | state |   no  |  present  | <ul> <li>present</li>  <li>absent</li> </ul> |  State of the stage resource  |
| None | rest_api_id |   yes  |  | |  The id of the parent rest api  |
| None | cache_cluster_enabled |   no  |    | |  Cache cluster setting for the Stage resource  |
| None | description |   no  |    | |  The description for the Stage resource to create  |


 
#### <a id="apigw_stage-examples"></a>Examples

```
- name: Test playbook for creating API GW Method resource
  hosts: localhost
  gather_facts: False
  tasks:
    - name: stage updatin'
      apigw_stage:
        rest_api_id: your_api_id
        name: dev
        description: 'This is a test of the emergency deployment system'
        method_settings:
          - method_name: /test
            method_verb: PUT
            caching_enabled: False
      register: stage

    - debug: var=stage

```


#### <a id="apigw_stage-notes"></a>Notes

- This module does not currently create stages, as these are a byproduct of executing deployments.

- This module requires that you have boto and boto3 installed and that your credentials are created or stored in a way that is compatible (see U(https://boto3.readthedocs.io/en/latest/guide/quickstart.html#configuration)).


---


## <a id="apigw_api_key"></a>apigw_api_key
Add, update, or remove ApiKey resources

  * [Synopsis](#apigw_api_key-synopsis)
  * [Options](#apigw_api_key-options)
  * [Examples](#apigw_api_key-examples)
  * [Notes](#apigw_api_key-notes)

#### <a id="apigw_api_key-synopsis"></a>Synopsis
* Create if no ApiKey resource is found matching the provided name
* Delete ApiKey resource matching the provided name
* Updates I(enabled) and I(description)

#### <a id="apigw_api_key-options"></a>Options

| Parent | Parameter     | required    | default  | choices    | comments |
|--------| ------------- |-------------| ---------|----------- |--------- |
| None | name |   yes  |  | |  The domain name of the ApiKey resource on which to operate  |
| None | generate_distinct_id |   no  |  False  | |  Specifies whether key identifier is distinct from created apikey value  |
| None | enabled |   no  |  False  | |  Can ApiKey be used by called  |
| None | value |   no  |    | |  Value of the api key. Required for create.  |
| None | state |   no  |  present  | <ul> <li>present</li>  <li>absent</li> </ul> |  Should api_key exist or not  |
| None | description |   no  |    | |  ApiKey description  |


 
#### <a id="apigw_api_key-examples"></a>Examples

```
---
- hosts: localhost
  gather_facts: False
  tasks:
  - name: api key creation
    apigw_api_key:
      name: testkey5000
      description: 'this is an awesome test'
      enabled: True
      value: 'notthegreatestkeyintheworld:justatribute'
      state: present
    register: apikey

  - debug: var=apikey

```


#### <a id="apigw_api_key-notes"></a>Notes

- While it is possible via the boto api to update the ApiKey's name, this module does not support this functionality since it searches for the ApiKey's id by its name.

- This module requires that you have boto and boto3 installed and that your credentials are created or stored in a way that is compatible (see U(https://boto3.readthedocs.io/en/latest/guide/quickstart.html#configuration)).


---


## <a id="apigw_resource"></a>apigw_resource
Add or remove Resource resources

  * [Synopsis](#apigw_resource-synopsis)
  * [Options](#apigw_resource-options)
  * [Examples](#apigw_resource-examples)
  * [Notes](#apigw_resource-notes)

#### <a id="apigw_resource-synopsis"></a>Synopsis
* An Ansible module to add or remove Resource resources for AWS API Gateway.

#### <a id="apigw_resource-options"></a>Options

| Parent | Parameter     | required    | default  | choices    | comments |
|--------| ------------- |-------------| ---------|----------- |--------- |
| None | state |   no  |  present  | <ul> <li>present</li>  <li>absent</li> </ul> |  Determine whether to assert if resource should exist or not  |
| None | name |   yes  |  | |  The name of the resource on which to operate  |
| None | rest_api_id |   yes  |  | |  The id of the parent rest api  |


 
#### <a id="apigw_resource-examples"></a>Examples

```
- name: Add resource to Api Gateway
  hosts: localhost
  gather_facts: False
  connection: local
  tasks:
    - name: Create resource
      apigw_resource:
        name: '/thing/{param}/awesomeness'
        rest_api_id: 'abcd1234'
        state: present
      register: resource

    - name: debug
      debug: var=resource

- name: Rest api from Api Gateway
  hosts: localhost
  gather_facts: False
  connection: local
  tasks:
    - name: Delete resource
      apigw_rest_api:
        name: '/thing/not-awesome'
        rest_api_id: 'abcd1234'
        state: absent
      register: resource

    - name: debug
      debug: var=resource

```


#### <a id="apigw_resource-notes"></a>Notes

- This module requires that you have boto and boto3 installed and that your credentials are created or stored in a way that is compatible (see U(https://boto3.readthedocs.io/en/latest/guide/quickstart.html#configuration)).


---


## <a id="apigw_model"></a>apigw_model
Add or remove models

  * [Synopsis](#apigw_model-synopsis)
  * [Options](#apigw_model-options)
  * [Examples](#apigw_model-examples)
  * [Notes](#apigw_model-notes)

#### <a id="apigw_model-synopsis"></a>Synopsis
* An Ansible module to add or remove models for AWS API Gateway.

#### <a id="apigw_model-options"></a>Options

| Parent | Parameter     | required    | default  | choices    | comments |
|--------| ------------- |-------------| ---------|----------- |--------- |
| None | state |   no  |  present  | <ul> <li>present</li>  <li>absent</li> </ul> |  Determine whether to assert if resource should exist or not  |
| None | description | no | "" | | The description of the model. |
| None | schema | no | | | The schema for the model. This is required if state is present. If content_type is application/json, this should be a JSON schema draft 4 model. |
| None | content_type | no | | | The content-type for the model. This is required if state is present. |
| None | name |   yes  |  | | Determine whether to assert if model should exist or not. |
| None | rest_api_id |   yes  |  | |  The id of the parent rest api.  |


 
#### <a id="apigw_model-examples"></a>Examples

```
- name: Add model
  hosts: localhost
  gather_facts: False
  connection: local
  tasks:
    - name: Create resource
      apigw_model:
        name: 'Model'
        rest_api_id: 'abcd1234'
        content_type: 'application/json'
        schema: '{}'
        description: 'Description for the model'
        state: present
      register: resource

    - name: debug
      debug: var=resource

- name: Delete model
  hosts: localhost
  gather_facts: False
  connection: local
  tasks:
    - name: Delete resource
      apigw_rest_api:
        name: 'Model'
        rest_api_id: 'abcd1234'
        state: absent
      register: resource

    - name: debug
      debug: var=resource

```


#### <a id="apigw_model-notes"></a>Notes
- Even though the docs say that schema is required for create model, I could not find an example where you did not have to pass in schema.
- This module requires that you have boto and boto3 installed and that your credentials are created or stored in a way that is compatible (see U(https://boto3.readthedocs.io/en/latest/guide/quickstart.html#configuration)).


---
Created by Network to Code, LLC
For:
2015
