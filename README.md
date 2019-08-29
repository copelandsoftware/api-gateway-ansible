# api-gateway-ansible
Ansible modules for managing AWS API Gateway resources

# Library Notes

## Non-idiomatic Documentation/Argument Specs

As the APIs covered by this library are, in some cases, very complex, the
modules in this library use nested dictionaries and lists of dictionaries
to better organize arguments.  This requires a non-standard approach to
produce usable documentation, which is included as WEBDOCS.md in the repo.

## API Coverage

Currently, the following resources are completely or partially covered:

- API Key
- Authorizer
- Base Path Mapping
- Deployment
- Domain Name
- Method (including all four stages)
- Resource
- REST API
- Stage
- Usage Plan
- Usage Plan Key
- Models

## Gaps

- Pagination is not covered for any API.  For situations where many items
  are possible (e.g. Resource), the API calls to list all resources have
  been hard-coded to the maximum response size.
- Updates/Patches represent a subset of all possible operations.  While
  coverage is generally robust, there are a few exceptions that are not
  covered, and those should be noted in the docs and modules.

## Other Notes

- There is some goofiness with handling None/Empty String arguments to work
  around a possible templating bug in Ansible that causes an argument like
  the following -- `"{{ undefined_thing | default(None) }}"` -- to be passed
  into the module as an empty string instead of the expected NoneType.  This
  required a great deal of ugliness and hacking since empty string is
  sometimes a valid argument.
- At this time, I have no plans to try to get this included with Ansible.
  Not only would the non-standard argument spec likely cause problems,
  I expect that development will be ongoing.
- Issues and PRs are welcome!  Tests are expected with any code changes.

## How to run the tests
`python -m unittest discovery tests/`

# DANGER WILL ROBINSON!!!

This module is not for you if:
- You use multiple stages within your rest API
AND
- Your method integrations point to different endpoints in each stage

## Why?

This module is designed to allow granular, idempotent interaction with API
Gateway resources.  This is great if you want to make isolated changes to
your Resource and Method resources, but it falls apart when a Deployment
resource is created since the deployment resource pushes to a stage the current
state of all resources.  E.g. if you're pushing to a 'dev' stage but you've
recently been testing a change in your 'qa' environment, the deploy operation
will cause the under-test resource to be pointed to 'qa' when deployed (while
everything else remains pointed to 'dev').

## How Do I Work Around This?

At this time, the simplest way to work around this is to create a REST API
resource for each environment, with each environment containing a single
stage.  There are probably crafty workarounds using stage variables --
be creative and share your results!
