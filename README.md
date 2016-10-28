#Push CloudFront logs to Elasticsearch with Lambda and S3 (WIP)

Lambda function to ingest and push CloudFront logs that have been placed on S3.

##Prerequisites
* AWS account
* AWS acccess key and secret
* python 2.7+
* boto3
* virtualenv

```
pip install virtualenv boto3
```
##Setup
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
