#!/bin/bash
BUILD_SCRIPT=$(readlink -f $0)
# Absolute path this script is in.
BUILD_DIR=$(dirname ${BUILD_SCRIPT})
ROOT_DIR=${BUILD_DIR}/..
src_install_file="scripts/install.sh"
dst_install_file="dist/cmlxztp_install.sh"
version_file="lib/cmlxztp/version.py"

export cmlxztp_ver=$1
export cmlxztp_rel=$2

if [ "${cmlxztp_ver}" == "" ] || [ "${cmlxztp_rel}" == "" ]; then
    echo "missing version or release!"
    echo "usage: $0 <version> <release>"
    exit 1
fi


function prepare_build()
{
    rm -rf dist MANIFEST
    mkdir dist
    cp ${src_install_file} ${dst_install_file}
    cp -f "${version_file}.in" ${version_file}
    sed -i "s,@CMLXZTP_VER@,${cmlxztp_ver},g" "${version_file}"
    sed -i "s,@CMLXZTP_REL@,${cmlxztp_rel},g" "${version_file}"
    sed -i "s,@CMLXZTP_VER@,${cmlxztp_ver},g" ${dst_install_file}
}

function post_build()
{
    rm -f ${install_file}
}

function main()
{
    pushd ${ROOT_DIR} > /dev/null
    prepare_build
    PYTHONPATH=lib python setup.py sdist --format=gztar
    #post_build
    popd > /dev/null
}

main