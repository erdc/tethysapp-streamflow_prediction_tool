********************************************
Setup: Web Application
********************************************
*tethysapp-streamflow\_prediction\_tool*

|License (3-Clause BSD)|

|DOI|

*This app requires you to have the ECMWF AutoRAPID preprocessing
completed separately. See:*

- :doc:`gis-stream_network_generation`
- :doc:`gis-ecmwf_rapid_input_generation`
- :doc:`historical_lsm_process`
- :doc:`forecast_framework`

Publications:
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

-  Tethys Platform 2.0 (CKAN, PostgresQL, GeoServer): See:
   http://docs.tethysplatform.org
-  RAPIDpy (Python package).
-  Geoserver needs CORS enabled.

.. note::
    Before installing the Streamflow Prediction Tool, RAPIDpy,
    or the spt_dataset_manager, activate your Tethys Platform
    python environment::

            $ t

Install RAPIDpy:
~~~~~~~~~~~~~~~~

For instructions, go to: https://github.com/erdc-cm/RAPIDpy.

Install spt_dataset_manager:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For instructions, go to: https://github.com/erdc-cm/spt_dataset_manager.


Installation:
-------------

Clone the app into the directory you want:

::

    $ git clone https://github.com/erdc-cm/tethysapp-streamflow_prediction_tool.git
    $ cd tethysapp-streamflow_prediction_tool

Then install the app in Tethys Platform.

Source Code Setup:
~~~~~~~~~~~~~~~~~~


A. App Development:
^^^^^^^^^^^^^^^^^^^

::

    $ t
    (tethys) $ cd tethysapp-streamflow_prediction_tool
    (tethys) $ python setup.py develop

B. Production:
^^^^^^^^^^^^^^
See: http://docs.tethysplatform.org/en/stable/installation/production/app_installation.html

::

    $ t
    (tethys) $ cd tethysapp-streamflow_prediction_tool
    (tethys) $ python setup.py install
    (tethys) $ tethys syncstores streamflow_prediction_tool
    (tethys) $ tethys manage collectall
    (tethys) $ tethys_server_own

Restart the server.
See: http://docs.tethysplatform.org/en/stable/installation/production/app_installation.html#restart-uwsgi-and-nginx


Configure App Settings:
~~~~~~~~~~~~~~~~~~~~~~~
Go to _"http://localhost:8000/admin/tethys_apps/tethysapp/" and select 'Streamflow Prediciton Tool'. Update required settings.

Setup the Database:
~~~~~~~~~~~~~~~~~~~
::

    $ t
    (tethys) $ tethys syncstores streamflow_prediction_tool


Updating the App:
-----------------

Update the local repository and Tethys Platform instance.

::

    $ t
    (tethys) $ cd tethysapp-streamflow_prediction_tool
    (tethys) $ git pull
    (tethys) $ tethys_server_own

Reset the database if changes are made to the database (this will delete
your old database):

::

    $ tethys syncstores streamflow_prediction_tool -r

The last step is to restart the server.
See: http://docs.tethysplatform.org/en/stable/installation/production/app_installation.html#restart-uwsgi-and-nginx


Crontab Errors
~~~~~~~~~~~~~~

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
~~~~~~~

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
