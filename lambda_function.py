import csv
import gzip
import boto3
import json
from datetime import datetime
from elasticsearch import Elasticsearch, RequestsHttpConnection
from elasticsearch import helpers
from aws_requests_auth.aws_auth import AWSRequestsAuth

################################################
#GLOBAL vars
################################################
fieldnames = (
    'logdate', #this gets stripped and merged into a new timestamp field
    'logtime', #this gets stripped and merged into a new timestamp field
    'edge-location', 
    'src-bytes',  
    'ip', 
    'method', 
    'host', 
    'uri-stem', 
    'status', 
    'referer',
    'user-agent',
    'uri-query',
    'cookie',
    'edge-result-type',
    'edge-request-id',
    'host-header',
    'protocol',
    'resp-bytes',
    'time-taken'
    'forwarded-for',
    'ssl-protocol',
    'ssl-cipher',
    'edge-response-result-type'
    )


config_bucket='lambda-cf-es-config'
config_file='config.json'

################################################
#Genarate auth request to connect AWS ES
def sts_auth(config):
    sts = boto3.client('sts')
    creds = sts.assume_role(RoleArn=config['sts_role_arn'], RoleSessionName=config['sts_session_name'])

    auth = AWSRequestsAuth(aws_access_key=creds['Credentials']['AccessKeyId'],
                       aws_secret_access_key=creds['Credentials']['SecretAccessKey'],
                       aws_host=config['es_host'],
                       aws_region=config['es_region'],
                       aws_service='es',
                       aws_token=creds['Credentials']['SessionToken']
                       )
    return auth

#Parse the log file into a dict
def parse_log(filename): 
    idx = 1
    recordset = []
    with gzip.open(filename) as f:
        result = csv.DictReader(f,fieldnames=fieldnames ,dialect="excel-tab")
        for row in result:
            #skip header rows
            if idx > 2:
                date = row.pop('logdate')      
                row['timestamp'] = datetime.strptime(date+" "+row.pop('logtime'),'%Y-%m-%d %H:%M:%S').isoformat() 
                record = {
                "_index": "cloudfrontlog-"+date,
                "_type": "logs",
                "_source": row
                }
                recordset.append(record)
            idx = idx+1      
    return recordset
    
#Write the data set to ES
def write_bulk(recordset, es):
    print("Writing data to ES")
    resp = helpers.bulk(es, recordset,chunk_size=1000) 
    return resp

def load_config():
    config = ''
    s3 = boto3.client('s3')
    #set the file path
    file_path = '/tmp/config.json'
    
    #download the gzip log from s3
    s3.download_file(config_bucket, config_file, file_path)

    with open(file_path) as f:
        config = json.load(f)
    
    return config

#invoke Lambda
def lambda_handler(event, context):

    config = load_config()
    #create ES connection with sts auth file
    es = Elasticsearch(host=config['es_host'],
                   port=80,
                   connection_class=RequestsHttpConnection,
                   http_auth=sts_auth(config)
                   )
    # create a s3 boto client
    s3 = boto3.client('s3')
    
    # attribute bucket and file name/path to variables
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']
    
    #set the file path
    file_path = '/tmp/cflogfile.gz'
    
    #download the gzip log from s3
    s3.download_file(bucket, key, file_path)

    #parse the log
    rs = parse_log('/tmp/cflogfile.gz')

    #write the dict to ES
    resp = write_bulk(rs, es)
    print resp
