import os
from setuptools import setup, find_packages
from tethys_apps.app_installation import custom_develop_command, custom_install_command

### Apps Definition ###
app_package = 'streamflow_prediction_tool'
release_package = 'tethysapp-' + app_package
app_class = 'streamflow_prediction_tool.app:StreamflowPredictionTool'
app_package_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tethysapp', app_package)
### Python Dependencies ###
dependencies = ['netCDF4', 'numpy', 'python-crontab', 'requests', 'sqlalchemy']

setup(
    name=release_package,
    version='1.0.0',
    description='Display streamflow from ECMWF predicted runoff routed with RAPID. Also, floodmaping with AutoRoute is available.',
    long_description='',
    keywords='',
    author='Alan Snow',
    author_email='alan.d.snow@usace.army.mil',
    url='127.0.0.1',
    license='MIT',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    namespace_packages=['tethysapp', 'tethysapp.' + app_package],
    include_package_data=True,
    zip_safe=False,
    install_requires=dependencies,
    cmdclass={
        'install': custom_install_command(app_package, app_package_dir, dependencies),
        'develop': custom_develop_command(app_package, app_package_dir, dependencies)
    }
)
