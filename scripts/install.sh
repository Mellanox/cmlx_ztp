INSTALL_SCRIPT=$(readlink -f $0)
PKG_DIR=$(dirname ${INSTALL_SCRIPT})
pushd ${PKG_DIR} > /dev/null
pip install cmlxztp-@CMLXZTP_VER@.tar.gz --no-binary cmlxztp
popd > /dev/null