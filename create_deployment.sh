#!/bin/bash
WORKINGDIR=~/workspace/lambdacloudfront/
LAMBDAFUNC="CloudFrontLogs-S3-ES"
S3CONFIG="lambda-cf-es-config"
CONFIGFILE="config.json"

DT=`date`
SUFFIX=`date -j -f "%a %b %d %T %Z %Y" "${DT}" "+%s"`
FILENAME=bundle-${SUFFIX}.zip
rm -rf bundle*

echo "Creating Deployment Zipfile: ${FILENAME}"
zip ${FILENAME} lambda_function.py > /dev/null
cd venv/lib/python2.7/site-packages/
zip -r ../../../../${FILENAME} * > /dev/null
cd ${WORKINGDIR}

echo "Uploading Config File To S3"
aws s3 cp ${WORKINGDIR}$CONFIGFILE s3://${S3CONFIG}/ > /dev/null

echo "Uploading ${FILENAME}"
aws lambda update-function-code --function-name ${LAMBDAFUNC} --zip-file fileb://${WORKINGDIR}${FILENAME}

