#!/bin/bash

# VirtualEnv vars
VENV="_venv"
VENV_LIBS=${VENV}/lib/python2.7/site-packages
BASE=`pwd`

#Build Vars
NOW=`date`
SUFFIX=`date -j -f "%a %b %d %T %Z %Y" "${NOW}" "+%s"`
PACKAGE_NAME="cloudfront-log-ingester-${SUFFIX}"
SERVICE_FILE="lambda_function.py"
BUILDLOG="${BASE}/build-${SUFFIX}.log"

function cleanup {
    echo "Destroying environment...."
    rm -rf ./${VENV}
    rm -rf ./*.zip 
    rm -rf ./*.log 
}

function setup { # ->  Creates a new vurtual python enviroment
    echo "[+] Creating environment \n [$NOW]"  >> ${BUILDLOG}
    cd ${BASE} 
    virtualenv ${VENV}  >> ${BUILDLOG}
    source ${VENV}/bin/activate  >> ${BUILDLOG}
    pip install elasticsearch  >> ${BUILDLOG}
    pip install aws_requests_auth  >> ${BUILDLOG}
    mkdir ${VENV}/dist  >> ${BUILDLOG}
}

function build {
    # -> Packages lambda function into acceptable ZIP format
    echo "[+] Building Lambda package at ${BASE}/${PACKAGE_NAME}.zip [$NOW]"  >> ${BUILDLOG}
    rm -rf ${VENV}/dist/*  >> ${BUILDLOG}
    cp -R ${VENV_LIBS}/* ${VENV}/dist/  >> ${BUILDLOG}
    cp ${SERVICE_FILE} ${VENV}/dist/  >> ${BUILDLOG}
    cd ${VENV}/dist && zip -r ${BASE}/${PACKAGE_NAME}.zip *  >> ${BUILDLOG}
    echo "${PACKAGE_NAME}.zip"
}

usage="$(basename "$0") [-h] [-bcs] -- Build Lambda Function

where:
    -h  show this help text
    -b  build
    -c  cleanup
    -s  setup"

while getopts ':hbsc' option; do
  case "$option" in
    h) echo "$usage"
       exit
       ;;
    b) build
       ;;
    c) cleanup
       ;;
    s) setup
       ;;

  esac
done
shift $((OPTIND - 1))