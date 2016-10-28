#Push CloudFront logs to Elasticsearch with Lambda and S3

Lambda function to ingest and push CloudFront logs that have been placed on S3.

##Prerequisites
* python 2.7+
* boto3
* virtualenv
```
pip install virtualenv boto3
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
