#Push CloudFront logs to Elasticsearch with Lambda and S3 (WIP)

Lambda function to ingest and push CloudFront logs that have been placed on S3.

##Prerequisites
* Admin Acess to: AWS S3, Elasticsearch, Lambda, IAM
* aws cli
* python 2.7+
* boto3
* virtualenv
* jq

##AWS Setup
###IAM
* create the lambda IAM role
```
aws iam create-role --role-name lambda-cloudfront-log-ingester --assume-role-policy-document="$(cat policies/trust-policy.json|jq -c '.' )"
```
* modify the role so that it can assume itself for STS token generation
```
aws iam update-assume-role-policy --policy-document="$(cat policies/trust-policy-mod.json|jq -c '.')" --role-name lambda-cloudfront-log-ingester
```
###S3
* create the bucket where the lambda function config will be stored
```
aws s3 mb s3://lambda-cloudfront-log-ingester-config --region eu-west-1
```
* create the bucket where lambda function deployment zip will be stored
```
aws s3 mb s3://lambda-cloudfront-log-ingester --region eu-west-1
```
###Elasticsearch
Permissions policy should allow calls from the lamda role, however in my case I have this open to the domain.

##Local setup
```
pip install virtualenv boto3
```
* clone the repo
```
 git clone https://github.com/dbnegative/lambda-cloudfront-log-ingester
 cd lambda-cloudfront-log-ingester
```
* setup the build enviroment
```
deploy-wrapper.py setup
```
* amend the config.json with your own settings
```
{
    "es_host": "YOUR AWS ES ENDPOINT ",
    "es_region": "eu-west-1",
    "es_connection_timeout": 60,
    "es_bulk_timeout": "60s",
    "es_bulk_chunk_size": 1000, 
    "sts_role_arn": "YOUR LAMBDA ROLE ARN",
    "sts_session_name": "lambdastsassume",
    "es_mapping": {
        "mappings": {
            "logs": {
                "properties": {
                    "host-header": {
                        "type": "string",
                        "index": "not_analyzed"
                    },
                    "ip": {
                        "type": "string",
                        "index": "not_analyzed"
                    },
                    "host": {
                        "type": "string",
                        "index": "not_analyzed"
                    },
                    "uri-stem": {
                        "type": "string",
                        "index": "not_analyzed"
                    }
                }
            }
        }
    }
}
```
#Deploy-wrapper.py usage
```
Deploy and manipulate lambda function

positional arguments:
  {promote,deploy,config,clean,setup}
                        [CMDS...]
    promote             promote <source enviroment> version to <target
                        enviroment>
    deploy              deploy function to s3
    config              deploy config to s3
    clean               clean local build enviroment
    setup               create local build enviroment

optional arguments:
  -h, --help            show this help message and exit
```

##TODO
* aws policy files
* improve instructions aka this file
