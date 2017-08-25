"""
Setup script for the Streamflow Prediction Tool web application.

Author: Alan D. Snow, 2015-2017
License: BSD-3-Clause
"""
# pylint: disable=attribute-defined-outside-init,no-self-use
import os
import sys

from setuptools import setup, find_packages
from setuptools import Command

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
    'xarray',
    'netcdf4',
    'numpy',
    'pandas',
    'python-crontab',
    'pytz',
    'scipy',
    'sqlalchemy',
    'tethys_dataset_services',
]


def _path_to_download_script():
    """Returns path to SPT download script"""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        'tethysapp',
                        'streamflow_prediction_tool',
                        'spt_download_forecasts.py')


def install_spt_crontab(tethys_home_dir):
    """
    Install crontab job for SPT app
    """
    from crontab import CronTab

    if not tethys_home_dir:
        tethys_home_dir = os.environ['TETHYS_HOME']

    manage_scrip_path = os.path.join(tethys_home_dir,
                                     'src', 'manage.py')

    cron_command = '%s %s %s' % (sys.executable,
                                 manage_scrip_path,
                                 'spt_download_forecasts')
    cron_manager = CronTab(user=True)
    cron_manager.remove_all(comment="spt-dataset-download")
    # create job to run every hour
    cron_job = cron_manager.new(command=cron_command,
                                comment="spt-dataset-download")
    cron_job.every(1).hours()

    # writes content to crontab
    cron_manager.write_to_user(user=True)


def setup_download_command(tethys_home_dir):
    """
    Create symbolic link to command file
    to tethys command directory
    """
    if not tethys_home_dir:
        tethys_home_dir = os.environ['TETHYS_HOME']

    spt_download_script = _path_to_download_script()
    path_to_tethys_command = \
        os.path.join(tethys_home_dir,
                     'src',
                     'tethys_apps',
                     'management',
                     'commands',
                     os.path.basename(spt_download_script))

    os.symlink(spt_download_script, path_to_tethys_command)


class SetupCrontabCommand(Command):
    """Custom command for initializing crontab."""
    description = "Custom command to setup cron job that downloads data " \
                  "for the Streamflow Prediction Tool"
    user_options = [
        ('tethys-home=', None, 'Path to directory above source code '
                               'for Tethys Platform '
                               '(e.g. /home/frank/tethys).'),
    ]

    def initialize_options(self):
        """Set default values for options."""
        self.tethys_home = None

    def finalize_options(self):
        """Post-process options."""
        return

    def run(self):
        """Run command."""
        install_spt_crontab(self.tethys_home)
        setup_download_command(self.tethys_home)


setup(
    name=RELEASE_PACKAGE,
    version='1.1.0',
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
        'install': custom_install_command(
            APP_PACKAGE,
            APP_PACKAGE_DIR,
            DEPENDENCIES
        ),
        'develop': custom_develop_command(
            APP_PACKAGE,
            APP_PACKAGE_DIR,
            DEPENDENCIES
        ),
        'cron': SetupCrontabCommand,
    }
)
