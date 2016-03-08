#Streamflow Prediction Tool App
*tethysapp-streamflow_prediction_tool*

**This app is created to run in the Teyths Platform programming environment.
See: https://github.com/CI-WATER/tethys and http://docs.tethys.ci-water.org**

*This app requires you to have the ECMWF AutoRAPID preprocessing completed 
separately. See: https://github.com/erdc-cm/spt_ecmwf_autorapid_process*

##Prerequisites:
- Tethys Platform v1.3 (CKAN, PostgresQL, GeoServer)
- RAPIDpy (Python package).

###Install RAPIDpy:
For instructions, go to: https://github.com/erdc-cm/RAPIDpy.

Note: Before installing RAPIDpy into your python site-packages,
activate your Tethys python environment:

```
$ . /usr/lib/tethys/bin/activate
```

##Installation:
Clone the app into the directory you want:
```
$ git clone https://github.com/erdc-cm/tethysapp-streamflow_prediction_tool.git
$ cd tethysapp-streamflow_prediction_tool
$ git submodule init
$ git submodule update
```
Then install the app in Tethys Platform.

###Installation for App Development:
```
$ . /usr/lib/tethys/bin/activate
$ cd tethysapp-streamflow_prediction_tool
$ python setup.py develop
$ tethys syncstores erfp_tool
```
###Installation for Production:
```
$ . /usr/lib/tethys/bin/activate
$ cd tethysapp-streamflow_prediction_tool
$ python setup.py install
$ tethys syncstores streamflow_prediction_tool
$ tethys manage collectstatic
```
Restart the Apache Server:
See: http://docs.tethys.ci-water.org/en/1.1.0/production/installation.html#enable-site-and-restart-apache

##Updating the App:
Update the local repository and Tethys Platform instance.
```
$ . /usr/lib/tethys/bin/activate
$ cd tethysapp-streamflow_prediction_tool
$ git pull
$ git submodule update
```
Reset the database if changes are made to the database (this will delete your old database and regenerate a new app instance id):
```
$ tethys syncstores streamflow_prediction_tool -r
```
Restart the Apache Server:
See: http://tethys-platform.readthedocs.org/en/1.0.0/production.html#enable-site-and-restart-apache

# Troubleshooting
## ImportError: No module named packages.urllib3.poolmanager
```
$ pip install pip --upgrade
```
Restart your terminal
```
$ pip install requests --upgrade
```
## Crontab Errors
Check if your server has crontab permissions:
Ex:
```
# su -s /bin/bash apache
bash-4.2$ crontab -e
You (apache) are not allowed to use this program (crontab)
See crontab(1) for more information
```
If not, add the permissions in the cron.allow file.
```
# echo apache >>/etc/cron.allow
```
## SELinux
If you are using a drive/folder not associated with your normal apache server locations, you may need to set SELinux to allow it. In this example, I am using a folder named /tethys
```
# semanage fcontext -a -t httpd_sys_content_t '/tethys(/.*)?'
# restorecon -Rv /tethys
```
