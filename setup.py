"""
Setup script for the Streamflow Prediction Tool web application.

Author: Alan D. Snow, 2015-2017
License: BSD-3-Clause
"""
import os
import sys

from setuptools import setup, find_packages
from setuptools.command.develop import develop
from setuptools.command.install import install

from tethys_apps.app_installation import (custom_develop_command,
                                          custom_install_command)

# Apps Definition
APP_PACKAGE = 'streamflow_prediction_tool'
RELEASE_PACKAGE = 'tethysapp-' + APP_PACKAGE
APP_CLASS = 'streamflow_prediction_tool.app:StreamflowPredictionTool'
APP_PACKAGE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               'tethysapp',
                               APP_PACKAGE)
# App Packages
DEPENDENCIES = [
    'RAPIDpy',
    'python-crontab',
    'sqlalchemy',
]


def init_crontab():
    """
    Install crontab job for app
    """
    from crontab import CronTab

    local_directory = os.path.dirname(os.path.abspath(__file__))
    cron_command = '%s %s' % (sys.executable,
                              os.path.join(local_directory, 'tethysapp',
                                           'streamflow_prediction_tool',
                                           'load_datasets.py'))
    cron_manager = CronTab(user=True)
    cron_manager.remove_all(comment="spt-dataset-download")
    # create job to run every hour
    cron_job = cron_manager.new(command=cron_command,
                                comment="spt-dataset-download")
    cron_job.every(1).hours()

    # writes content to crontab
    cron_manager.write_to_user(user=True)


class PostDevelopCommand(develop):
    """Post-installation for development mode."""
    def run(self):
        custom_develop_command(
            APP_PACKAGE,
            APP_PACKAGE_DIR,
            DEPENDENCIES
        )
        init_crontab()
        develop.run(self)


class PostInstallCommand(install):
    """Post-installation for installation mode."""
    def run(self):
        custom_install_command(
            APP_PACKAGE,
            APP_PACKAGE_DIR,
            DEPENDENCIES
        )
        init_crontab()
        install.run(self)


setup(
    name=RELEASE_PACKAGE,
    version='1.0.5',
    description=('Provides 15-day streamflow predicted estimates by using '
                 'ECMWF (ecmwf.int) runoff predictions routed with the RAPID '
                 '(rapid-hub.org) program. Return period estimates '
                 'and warning flags aid in determining the severity.'),
    long_description='',
    keywords='ECMWF, RAPID, Streamflow Prediction, Forecast',
    author='Alan D. Snow',
    author_email='alan.d.snow@usace.army.mil',
    url='https://github.com/erdc-cm/tethysapp-streamflow_prediction_tool',
    license='BSD 3-Clause',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    namespace_packages=['tethysapp', 'tethysapp.' + APP_PACKAGE],
    include_package_data=True,
    extras_require={
        'tests': [
            'flake8',
            'pylint',
        ],
        'docs': [
            'sphinx',
            'sphinx_rtd_theme',
            'sphinxcontrib-napoleon',
        ]
    },
    zip_safe=False,
    install_requires=DEPENDENCIES,
    cmdclass={
        'install': PostInstallCommand,
        'develop': PostDevelopCommand,
    }
)
