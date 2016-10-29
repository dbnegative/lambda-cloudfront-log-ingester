'''
Lambda fucnction to ingest CLoudfront logs from S3 and bulk insert
them into Elasticsearch. This lambda function needs to do a STS
assume role in order to create an AWSAUTHREQUEST inorder to connect
to the elastic search cluster

Author: Jason Witting
Version: 0.1

Copyright (c) 2016 Jason Witting

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the Software
is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
 all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED
, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF
CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE
OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
'''
import csv
import gzip
import json
from datetime import datetime

import boto3
from elasticsearch import Elasticsearch, RequestsHttpConnection
from elasticsearch import helpers
from aws_requests_auth.aws_auth import AWSRequestsAuth

# Global vars
FIELDNAMES = (
    'logdate',  # this gets stripped and merged into a new timestamp field
    'logtime',  # this gets stripped and merged into a new timestamp field
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


# config_bucket='lambda-cf-es-config'
CONFIG_BUCKET = 'lambda-cloudfront-log-ingester-config'
# config s3 location and filename
CONFIG_FILE = 'config.json'


def sts_auth(config):
    '''Genarate auth request to connect AWS ES '''
    sts = boto3.client('sts')

    creds = sts.assume_role(
        RoleArn=config['sts_role_arn'], RoleSessionName=config['sts_session_name'])

    auth = AWSRequestsAuth(aws_access_key=creds['Credentials']['AccessKeyId'],
                           aws_secret_access_key=creds['Credentials']['SecretAccessKey'],
                           aws_host=config['es_host'],
                           aws_region=config['es_region'],
                           aws_service='es',
                           aws_token=creds['Credentials']['SessionToken'])
    return auth


def parse_log(filename):
    '''Parse the log file into a dict'''
    # init
    idx = 1
    recordset = []

    with gzip.open(filename) as data:

        result = csv.DictReader(data, fieldnames=FIELDNAMES, dialect="excel-tab")

        for row in result:
            # skip header rows - cruft
            if idx > 2:
                # cloudfront events are logged to the second only, date and time are seperate
                # fields which we remove and merge into a new timestamp field
                date = row.pop('logdate')
                row['timestamp'] = datetime.strptime(
                    date + " " + row.pop('logtime'), '%Y-%m-%d %H:%M:%S').isoformat()
                # add to new record dict
                record = {
                    "_index": "cloudfrontlog-" + date,
                    "_type": "logs",
                    "_source": row
                }
                # append to recordset
                recordset.append(record)
            idx = idx + 1

    return recordset


def write_bulk(record_set, es_client, config):
    ''' Write the data set to ES, chunk size has been increased to improve performance '''
    print "Writing data to ES"
    resp = helpers.bulk(es_client,
                        record_set,
                        chunk_size=config['es_bulk_chunk_size'],
                        timeout=config['es_bulk_timeout'])
    return resp


def load_config(context):
    '''Load config file from S3'''
    config = ''

    # Check version
    function_name = context.function_name
    alias = context.invoked_function_arn.split(':').pop()

    if function_name == alias:
        alias = '$LATEST'
        print "No Version Set - Default to $LATEST"

    s3_client = boto3.client('s3')

    # set the file path
    file_path = '/tmp/config.json'

    # download the gzip log from s3
    s3_client.download_file(CONFIG_BUCKET, alias + "/" + CONFIG_FILE, file_path)

    with open(file_path) as f:
        config = json.load(f)

    print "Succesfully loaded config file"
    return config


def lambda_handler(event, context):
    '''Invoke Lambda '''
    # load config from json file in s3 bucket
    config = load_config(context)

    # create ES connection with sts auth file
    es_client = Elasticsearch(host=config['es_host'],
                              port=80,
                              connection_class=RequestsHttpConnection,
                              http_auth=sts_auth(config),
                              timeout=config['es_connection_timeout'])

    # create new index with custom mappings from config, ignore if it's already created
    # new index will be created for everyday YMV
    suffix = datetime.strftime(datetime.now(), '%Y-%m-%d')
    resp = es_client.indices.create(index="cloudfrontlog-" +
                                    suffix, body=config['es_mapping'],
                                    ignore=400)
    print resp

    # create a s3 boto client
    s3_client = boto3.client('s3')

    # split bucket and filepath to variables
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']

    # set the file path
    file_path = '/tmp/cflogfile.gz'

    # download the gzip log from s3
    s3_client.download_file(bucket, key, file_path)

    # parse the log
    record_set = parse_log('/tmp/cflogfile.gz')

    # write the dict to ES
    resp = write_bulk(record_set, es_client, config)
    print resp
