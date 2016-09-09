********************************************
Setup: Web Application
********************************************
*tethysapp-streamflow\_prediction\_tool*

|License (3-Clause BSD)|

|DOI|

*This app requires you to have the ECMWF AutoRAPID preprocessing
completed separately. See:*

.. toctree::
    :maxdepth: 1

    gis-stream_network_generation.rst
    gis-ecmwf_rapid_input_generation.rst
    historical_lsm_process.rst
    forecast_framework.rst

How it works:
-------------

Snow, Alan D., Scott D. Christensen, Nathan R. Swain, E. James Nelson,
Daniel P. Ames, Norman L. Jones, Deng Ding, Nawajish S. Noman, Cedric H.
David, Florian Pappenberger, and Ervin Zsoter, 2016. A High-Resolution
National-Scale Hydrologic Forecast System from a Global Ensemble Land
Surface Model. *Journal of the American Water Resources Association
(JAWRA)* 1-15, DOI: 10.1111/1752-1688.12434. 
http://onlinelibrary.wiley.com/doi/10.1111/1752-1688.12434/abstract

Snow, Alan Dee, "A New Global Forecasting Model to Produce
High-Resolution Stream Forecasts" (2015). All Theses and Dissertations.
Paper 5272. http://scholarsarchive.byu.edu/etd/5272

Prerequisites:
--------------

-  Tethys Platform v1.4 (CKAN, PostgresQL, GeoServer): See:
   http://docs.tethysplatform.org/en/1.4.0/
-  RAPIDpy (Python package).
-  Geoserver needs CORS enabled.

Install RAPIDpy:
~~~~~~~~~~~~~~~~

For instructions, go to: https://github.com/erdc-cm/RAPIDpy.

Note: Before installing RAPIDpy into your python site-packages, activate
your Tethys python environment:

::

    $ . /usr/lib/tethys/bin/activate

Installation:
-------------

Clone the app into the directory you want:

::

    $ git clone https://github.com/erdc-cm/tethysapp-streamflow_prediction_tool.git
    $ cd tethysapp-streamflow_prediction_tool
    $ git submodule init
    $ git submodule update

Then install the app in Tethys Platform.

Installation for App Development:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

    $ . /usr/lib/tethys/bin/activate
    $ cd tethysapp-streamflow_prediction_tool
    $ python setup.py develop
    $ tethys syncstores streamflow_prediction_tool

Installation for Production:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

    $ . /usr/lib/tethys/bin/activate
    $ cd tethysapp-streamflow_prediction_tool
    $ python setup.py install
    $ tethys syncstores streamflow_prediction_tool
    $ tethys manage collectstatic

Restart the Apache Server: See:
http://docs.tethysplatform.org/en/1.3.0/production/installation.html#enable-site-and-restart-apache

Updating the App:
-----------------

Update the local repository and Tethys Platform instance.

::

    $ . /usr/lib/tethys/bin/activate
    $ cd tethysapp-streamflow_prediction_tool
    $ git pull
    $ git submodule update

Reset the database if changes are made to the database (this will delete
your old database and regenerate a new app instance id):

::

    $ tethys syncstores streamflow_prediction_tool -r

Restart the Apache Server: See:
http://docs.tethysplatform.org/en/1.3.0/production/installation.html#enable-site-and-restart-apache

Troubleshooting
===============

ImportError: No module named packages.urllib3.poolmanager
---------------------------------------------------------

::

    $ pip install pip --upgrade

Restart your terminal

::

    $ pip install requests --upgrade

Crontab Errors
--------------

Check if your server has crontab permissions: Ex:

::

    # su -s /bin/bash apache
    bash-4.2$ crontab -e
    You (apache) are not allowed to use this program (crontab)
    See crontab(1) for more information

If not, add the permissions in the cron.allow file.

::

    # echo apache >>/etc/cron.allow

SELinux
-------

If you are using a drive/folder not associated with your normal apache
server locations, you may need to set SELinux to allow it. In this
example, I am using a folder named /tethys

::

    # semanage fcontext -a -t httpd_sys_content_t '/tethys(/.*)?'
    # restorecon -Rv /tethys

.. |License (3-Clause BSD)| image:: https://img.shields.io/badge/license-BSD%203--Clause-yellow.svg
   :target: https://github.com/erdc-cm/tethysapp-streamflow_prediction_tool/blob/master/LICENSE
.. |DOI| image:: https://zenodo.org/badge/19918/erdc-cm/tethysapp-streamflow_prediction_tool.svg
   :target: https://zenodo.org/badge/latestdoi/19918/erdc-cm/tethysapp-streamflow_prediction_tool
