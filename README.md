# api-gateway-ansible
Ansible modules for managing AWS API Gateway resources

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
will cause the under-test resource to be pointed to 'qa' when deployed.

## How Do I Work Around This?

At this time, the simplest way to work around this is to create a REST API
resource for each environment, with each environment containing a single
stage.  There are probably nifty and creative ways to use stage variables --
be creative!
