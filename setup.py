"""
@copyright:
    Copyright (C) Mellanox Technologies Ltd. 2016-2017. ALL RIGHTS RESERVED.

    This software product is a proprietary product of Mellanox Technologies
    Ltd. (the "Company") and all right, title, and interest in and to the
    software product, including all associated intellectual property rights,
    are and shall remain exclusively with the Company.

    This software product is governed by the End User License Agreement
    provided with the software product.

@author: Samer Deeb
@date:   Oct 2, 2017
"""
import os
import sys

try:
    from setuptools import setup, find_packages
    from setuptools.command.install_lib import install_lib as InstallLib
except ImportError:
    print("cmlxztp now needs setuptools in order to build. Install it using"
          " your package manager (usually python-setuptools) or via pip (pip"
          " install setuptools).")
    sys.exit(1)

sys.path.insert(0, os.path.abspath('lib'))
from cmlxztp import version as NV

curr_ver = NV.CMLXZTP_VER
curr_rel = NV.CMLXZTP_REL


def _get_conf_files():
    content = os.listdir('conf')
    return ['conf/%s' % file_name for file_name in content]


class install_lib(InstallLib):
    """
    This class overwrite setuptools install_lib class implementation
    """

    def run(self):
        """
        remove the .py files from the destination folder
        """
        InstallLib.run(self)
        outfiles = self.install()
        for file_name in outfiles:
            if file_name.endswith(".py"):
                os.remove(file_name)

    def get_outputs(self):
        """Return the list of files that would be installed and
        remove the .py files from that list
        """
        output = InstallLib.get_outputs(self)
        outputs_without_py = [file_name for file_name in output
                              if not file_name.endswith(".py")]
        return outputs_without_py


with open('README.rst', 'r') as f:
    long_description = f.read()

with open('requirements.txt') as requirements_file:
    install_requirements = requirements_file.read().splitlines()
    if not install_requirements:
        print("Unable to read requirements from the requirements.txt file"
              "That indicates this copy of the source code is incomplete.")
        sys.exit(2)

setup(name='cmlxztp',
      version=curr_ver,
      description='NEO Cumulus ZTP Manager',
      long_description=long_description,
      url='http://www.mellanox.com/content/pages.php?pg='
          'products_dyn&product_family=100&menu_section=55',
      author='Samer Deeb',
      author_email='samerd@mellanox.com',
      packages=find_packages('lib'),
      package_dir={'': 'lib'},
      data_files=[('/etc/logrotate.d', ['conf/cmlxztp']),
                  ('/etc/cmlxztp', _get_conf_files()),
                  ('/var/lib/cmlxztp/data', []), ],
      scripts=["scripts/cmlxztp", 'scripts/cmlxztp_uninstall.sh'],
      install_requires=install_requirements,
      cmdclass={'install_lib': install_lib})
