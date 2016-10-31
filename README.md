#Push CloudFront logs to Elasticsearch with Lambda and S3

Lambda function to ingest and push CloudFront logs that have been placed on S3.

![Alt text](/diagram.png?raw=true "Layout")

##Things to know before starting:
This function pulls the cloudfront .gz log files from S3 and creates a dict of all log lines. It all also strips the time/date and merge's them into a new timestamp field. The dict is written using the Elasticsearch client via the bulk api. 

New elasticsearch index's are created for each day. PLEASE MAKE SURE YOU HAVE INDEX CLEANING POLICY IN PLACE! 
I have created a custom index map scheme that works for me. Please change to suite your needs. 

The deploy-wrapper.sh is generic and can be used for other functions. All settings can be changed in the deployment-config.json file in the config folder. 

* I'm not a python expert so pull requests welcome!!
* AWS Elasticsearch is a pain to connect to. You need to auth all your requests with an AWSAuthRequest
* My default lambda settings are not finely tuned - however they are working for me - YMMV
* Always use aliases when working with LAMBDA in prod - trust me...
 
##Prerequisites
* Admin Acess to: AWS S3, Elasticsearch, Lambda, IAM
* aws cli
* python 2.7+
* boto3
* virtualenv
* jq

##Setup
###IAM
* create the lambda IAM role
```
aws iam create-role --role-name lambda-cloudfront-log-ingester --assume-role-policy-document="$(cat policies/trust-policy.json|jq -c '.' )"
```
* modify the role so that it can assume itself for STS token generation
```
aws iam update-assume-role-policy --policy-document="$(cat policies/trust-policy-mod.json|jq -c '.')" --role-name lambda-cloudfront-log-ingester
```
* Add custom policy to allow access to S3, Elasticsearch, Cloudwatch Logs,
```
TODO ;)
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
* Create 4 folders to hold config files for different deployment stages thorugh the AWS S3 console:
```
$LATEST
DEV
STAGE
PROD
```
###Elasticsearch
Permissions policy should allow calls from the lamda role, however in my case I have this open to the domain.
You will need to get your ES endpoint URL


* install needed python dep's
```
pip install virtualenv boto3
```
* clone the repo
```
 git clone https://github.com/dbnegative/lambda-cloudfront-log-ingester
 cd lambda-cloudfront-log-ingester
```
* edit the config/deployment-config.json if needed. 
```
{
"S3_CONFIG_BUCKET":"lambda-cloudfront-log-ingester-config",
"LAMBDA_DEPLOY_BUCKET": "lambda-cloudfront-log-ingester",
"CONFIG_FILE":"config.json",
"LAMBDA_FUNC_NAME" :"cloudfront-log-ingester",
"LAMBDA_HANDLER":"lambda_function.lambda_handler",
"LAMBDA_ROLE_ARN":"arn:aws:iam::<YOURAWSACCOUNTID>:role/lambda-cloudfront-log-ingester",
"LAMBDA_TIMEOUT":"300",
"LAMBDA_MEMORY_SIZE":"512"
}
```
* setup the build enviroment
```
deploy-wrapper.py setup
```
* edit the config/config.json with your own settings, at the minimum the following:
```
    "es_host": "YOUR AWS ES ENDPOINT ",
    "es_region": "eu-west-1",
    "sts_role_arn": "YOUR LAMBDA ROLE ARN",
    "sts_session_name": "lambdastsassume",
```
* create the initial version of the function using the deploy-wrapper.sh
```
deploy-wrapper.py init
```
* create 3 lambda alias for continous deploments and tests 
```
aws lambda create-alias --name DEV --function-name lambda-cloudfront-log-ingester --function-version=1
aws lambda create-alias --name STAGE --function-name lambda-cloudfront-log-ingester --function-version=1
aws lambda create-alias --name PROD --function-name lambda-cloudfront-log-ingester --function-version=1
```
* create s3 trigger on PROD alias. You can now deploy and test to DEV and STAGE without affecting your production version
  1. go to the lambda console
  2. select the lambda-cloudfront-log-ingester fucntion
  3. press the "Qualifiers" button and select the PROD alias
  4. select the "Triggers" tab
  5. add an S3 trigger
  6. set the bucket to where your cloudfront logs sit
  7. set the event to "Object Create (All) - Put"
  8. enable the trigger and save

* deploying a new build to DEV alias
```
deploy-wrapper.py deploy --env DEV
```
* promoting that version to STAGE alias
```
deploy-wrapper.py promote DEV STAGE
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
    init                creates the base lambda function
    clean               clean local build enviroment
    setup               create local build enviroment

optional arguments:
  -h, --help            show this help message and exit
```

##TODO
* aws policy files - S3, ELASTICSEARCH, LOG 
* improve instructions aka this file
