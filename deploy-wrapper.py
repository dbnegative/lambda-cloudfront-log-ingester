#!/usr/local/bin/python
'''
Deployment and build script to manage build and deploy lamda functions
Author: Jason Witting
Version: 0.1
'''

import argparse
import json
import logging
import subprocess
import sys

import boto3

BASE_DIR = subprocess.check_output(['pwd']).strip('\n')
BUILD_SCRIPT = BASE_DIR + '/' + 'build.sh'

CONFIG_FILE = 'config/deployment-config.json'

# setup logger
LOGGER = logging.getLogger('DEPLOY')
LOGGER.setLevel(logging.DEBUG)
STDOUT_LOG_HANDLER = logging.StreamHandler(sys.stdout)
STDOUT_LOG_HANDLER.setLevel(logging.INFO)

FORMATTER = logging.Formatter('\
[%(asctime)s] \
[%(levelname)s] \
[%(name)s] %(message)s')

STDOUT_LOG_HANDLER.setFormatter(FORMATTER)
LOGGER.addHandler(STDOUT_LOG_HANDLER)


def load_config(filename):
    '''loads the script config variables'''
    config = ''
    with open(filename) as f:
        config = json.load(f)
    return config


def create_deployment_bundle():
    '''create lambda deployment zip file and return name'''

    pkg = subprocess.check_output([BUILD_SCRIPT, '-b']).strip('\n')
    LOGGER.info("Created deployment bundle: " + pkg)
    return pkg


def publish_s3(filename, bucket, key):
    '''
    push files to s3

    args:
    filename - (string) the file to publish to s3
    bucket - (string) s3 bucket
    key - (string) s3 object key
    '''
    s3 = boto3.client('s3')
    with open(filename, 'rb') as data:
        s3.upload_fileobj(data, bucket, key)
    LOGGER.info("Uploaded " + filename + " to S3://" + bucket)


def upate_config(env, lambda_config_file, config):
    '''
    push config file to specific env folder on s3

    args:
    env - (string) the enviroment to push to i.e DEV, STAGE, PROD
    file - (string) the config.json file which contains the lambda
                 config
    '''
    return publish_s3(lambda_config_file,
                      config['S3_CONFIG_BUCKET'],
                      env + '/' +
                      lambda_config_file)


def update_lamda_alias(alias, version, function_name, description=''):
    '''
    update lambda alias to specified version
    returns the entire response as a JSON string

    args:
    alias - (string) name of the lambda alias to update
    version - (string) version number of lambda alias to point to
    function_name - the lamda function name

    opt args:
    description - description of the function
    '''
    aws_lambda = boto3.client('lambda')
    resp = aws_lambda.update_alias(
        FunctionName=function_name,
        Name=alias,
        FunctionVersion=version,
        Description=description
    )
    LOGGER.info("Updated Alias: " +
                alias +
                " to version: " +
                version)
    return resp


def publish_lambda(function_name, bucket, key):
    '''
    publish lambda function and return version number
    returns a version number as a string

    args:
    function_name - (string) the function name
    bucket - (string) the s3 bucket NameError
    key - (string) the s3 object key
    '''
    aws_lambda = boto3.client('lambda')
    resp = aws_lambda.update_function_code(
        FunctionName=function_name,
        S3Bucket=bucket,
        S3Key=key,
        Publish=True
    )
    LOGGER.info("Published verison: " + resp['Version'])
    return resp['Version']


def get_alias_version(alias, function_name):
    '''
    version number associated with alias
    returns the version number as a string

    args:
    alias - (string) the lambda alias to query
    function_name - (string) the lambda function name
    '''
    aws_lambda = boto3.client('lambda')
    response = aws_lambda.get_alias(
        FunctionName=function_name,
        Name=alias
    )
    return response['FunctionVersion']


def promote_version(source, target, config):
    '''
    promote version tied to an alias to another enviroment(alias)
    returns the entire reponse as JSON string

    args:
    source - (string) the source alias from which to get version
    target - (string) the target alias to set the version to
    '''
    resp = ''
    version = get_alias_version(source, config['LAMBDA_FUNC_NAME'])

    print("promote " + source +
          " version: " + version + " to " +
          target + " (Y/N):")

    reply = raw_input().strip('\n').upper()

    if reply == 'Y':
        LOGGER.info('Updating Alias: ' + source +
                    ' to version: ' + version)
        resp = update_lamda_alias(target, version, config['LAMBDA_FUNC_NAME'])
        LOGGER.debug(resp)
    return resp


def main():
    '''
    main method
    '''

    config = load_config(CONFIG_FILE)

    parser = argparse.ArgumentParser(
        description='Deploy and manipulate lambda function')
    subparsers = parser.add_subparsers(
        dest='subparsers_name', help="[CMDS...]")

    parser_promote = subparsers.add_parser(
        'promote', help='promote <source enviroment>  \
        version to <target enviroment>')
    parser_promote.add_argument('source', choices=['DEV', 'STAGE', 'PROD'],
                                help='the source enviroment')
    parser_promote.add_argument('target', choices=['DEV', 'STAGE', 'PROD'],
                                help='the target enviroment')

    parser_deploy = subparsers.add_parser(
        'deploy', help='deploy function to s3')
    parser_deploy.add_argument(
        '--env', choices=['DEV', 'STAGE', 'PROD'],
        help='the target enviroment')

    parser_config = subparsers.add_parser('config',
                                          help='deploy config to s3')
    parser_config.add_argument('env',
                               choices=['DEV', 'STAGE', 'PROD'],
                               help='set config for specific enviroment')

    subparsers.add_parser(
        'clean', help='clean local build enviroment')

    subparsers.add_parser(
        'setup', help='create local build enviroment')

    args = parser.parse_args()

    # deploy
    if args.subparsers_name == 'deploy':
        pkg = create_deployment_bundle()
        publish_s3(pkg, config['LAMBDA_DEPLOY_BUCKET'], pkg.split('/').pop())

        LOGGER.info("Uploaded lambda zip:" + pkg.split('/').pop() +
                    " to S3://" + config['LAMBDA_DEPLOY_BUCKET'])

        version = publish_lambda(config['LAMBDA_FUNC_NAME'],
                                 config['LAMBDA_DEPLOY_BUCKET'],
                                 pkg.split('/').pop())

        if args.env:
            LOGGER.debug(update_lamda_alias(args.env, version,
                                            config['LAMBDA_FUNC_NAME'], description=''))

    # promote
    if args.subparsers_name == 'promote':
        LOGGER.debug(promote_version(args.source, args.target, config))

    # deploy
    if args.subparsers_name == 'config':
        LOGGER.debug(upate_config(args.env, BASE_DIR +
                                  "/" + config['CONFIG_FILE'], config))

    # clean
    if args.subparsers_name == 'clean':
        LOGGER.info(subprocess.check_output([BUILD_SCRIPT, '-c']).strip('\n'))

    # setup
    if args.subparsers_name == 'setup':
        LOGGER.info("creating build enviroment" +
                    subprocess.check_output([BUILD_SCRIPT, '-s']).strip('\n'))

# launch main
if __name__ == "__main__":
    main()
