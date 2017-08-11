************
SPT REST API
************

A REST API is a web service or a set of methods that can be used to produce or access data without a web interface.
REST APIs use the http protocol to request data. Parameters are passed through a URL using a predetermined organization.
A REST API has been developed to provide access to the Streamflow Prediction Tool (SPT) forecasts without the need to
access the web app interface. This type of service facilitates integration of the SPT with third party web apps, and
the automation of forecast retrievals using programing languages like Python, or R. The available methods and a
description of how to use them are shown below.

GetForecast for Forecasts Statistics
====================================

+----------------+----------------------------------------------------------+---------------+
| Parameter      | Description                                              | Example       |
+================+==========================================================+===============+
| watershed_name | The name of watershed or main area of interest.          | Nepal         |
+----------------+----------------------------------------------------------+---------------+
| subbasin_name  | The name of the sub basin or sub area.                   | Central       |
+----------------+----------------------------------------------------------+---------------+
| reach_id       | The identifier for the stream reach.                     | 5             |
+----------------+----------------------------------------------------------+---------------+
| forecast_folder| The date of the forecast (YYYYMMDD.HHHH) [*]_. (Optional)| 20170110.1200 |
+----------------+----------------------------------------------------------+---------------+
|                | The selected forecast statistic. (high_res, mean,        |               |
|                |                                                          |               |
| stat_type      | std_dev_range_upper, std_dev_range_lower,                | mean          |
|                |                                                          |               |
|                | max, min).                                               |               |
+----------------+----------------------------------------------------------+---------------+
| units          | Set to 'english' to get ft3/s. (Optional)                | english       |
+----------------+----------------------------------------------------------+---------------+
| return_format  | Set to 'csv' to get csv file.  (Optional)                | csv           |
+----------------+----------------------------------------------------------+---------------+
.. [*] forecast_folder=most_recent will retrieve the most recent date available.

Example
-------

>>> import requests
>>> request_params = dict(watershed_name='Nepal', subbasin_name='Central', reach_id=5, forecast_folder='most_recent', stat_type='mean')
>>> request_headers = dict(Authorization='Token asdfqwer1234')
>>> res = requests.get('[HOST Portal]/apps/streamflow-prediction-tool/api/GetForecast/', params=request_params, headers=request_headers)

GetHistoricData (1980 - Present)
================================

+----------------+--------------------------------------------------+---------------+
| Parameter      | Description                                      | Example       |
+================+==================================================+===============+
| watershed_name | The name of watershed or main area of interest.  | Nepal         |
+----------------+--------------------------------------------------+---------------+
| subbasin_name  | The name of the sub basin or sub area.           | Central       |
+----------------+--------------------------------------------------+---------------+
| reach_id       | The identifier for the stream reach.             | 5             |
+----------------+--------------------------------------------------+---------------+
| units          | Set to 'english' to get ft3/s. (Optional)        | english       |
+----------------+--------------------------------------------------+---------------+
| return_format  | Set to 'csv' to get csv file.  (Optional)        | csv           |
+----------------+--------------------------------------------------+---------------+

Example
-------
>>> import requests
>>> request_params = dict(watershed_name='Nepal', subbasin_name='Central', reach_id=5)
>>> request_headers = dict(Authorization='Token asdfqwer1234')
>>> res = requests.get('[HOST Portal]/apps/streamflow-prediction-tool/api/GetHistoricData/', params=request_params, headers=request_headers)

GetReturnPeriods (2, 10, and 20 year return with historical max)
================================================================

+----------------+--------------------------------------------------+---------------+
| Parameter      | Description                                      | Example       |
+================+==================================================+===============+
| watershed_name | The name of watershed or main area of interest.  | Nepal         |
+----------------+--------------------------------------------------+---------------+
| subbasin_name  | The name of the sub basin or sub area.           | Central       |
+----------------+--------------------------------------------------+---------------+
| reach_id       | The identifier for the stream reach.             | 5             |
+----------------+--------------------------------------------------+---------------+
| units          | Set to 'english' to get ft3/s. (Optional)        | english       |
+----------------+--------------------------------------------------+---------------+

Example
-------
>>> import requests
>>> request_params = dict(watershed_name='Nepal', subbasin_name='Central', return_period=2)
>>> request_headers = dict(Authorization='Token asdfqwer1234')
>>> res = requests.get('[HOST Portal]/apps/streamflow-prediction-tool/api/GetReturnPeriods/', params=request_params, headers=request_headers)

GetAvailableDates
=================

+----------------+--------------------------------------------------+---------------+
| Parameter      | Description                                      | Example       |
+================+==================================================+===============+
| watershed_name | The name of watershed or main area of interest.  | Nepal         |
+----------------+--------------------------------------------------+---------------+
| subbasin_name  | The name of the sub basin or sub area.           | Central       |
+----------------+--------------------------------------------------+---------------+
| reach_id       | The identifier for the stream reach.             | 5             |
+----------------+--------------------------------------------------+---------------+

Example
-------
>>> import requests
>>> request_params = dict(watershed_name='Nepal', subbasin_name='Central', reach_id=5)
>>> request_headers = dict(Authorization='Token asdfqwer1234')
>>> res = requests.get('[HOST Portal]/apps/streamflow-prediction-tool/api/GetAvailableDates/', params=request_params, headers=request_headers)

GetWatersheds
=============

This method takes no parameters and returns a list of the available watersheds.

Example
-------
>>> import requests
>>> request_headers = dict(Authorization='Token asdfqwer1234')
>>> res = requests.get('[HOST Portal]/apps/streamflow-prediction-tool/api/GetWatersheds/', headers=request_headers)

GetWarningPoints
================

+----------------+------------------------------------------------------------+---------------+
| Parameter      | Description                                                | Example       |
+================+============================================================+===============+
| watershed_name | The name of watershed or main area of interest.            | Nepal         |
+----------------+------------------------------------------------------------+---------------+
| subbasin_name  | The name of the sub basin or sub area.                     | Central       |
+----------------+------------------------------------------------------------+---------------+
| return_period  | The return period that the warning is based on.            | (2,10, or 20) |
+----------------+------------------------------------------------------------+---------------+
| forecast_folder| The date of the forecast (YYYYMMDD.HHHH). (Optional [*]_)  | 20170110.1200 |
+----------------+------------------------------------------------------------+---------------+
.. [*] If you don't include forecast_folder, it will retrieve the most recent date available.

Example
-------
>>> import requests
>>> request_params = dict(watershed_name='Nepal', subbasin_name='Central', return_period=20, forecast_folder='20170802.0')
>>> request_headers = dict(Authorization='Token asdfqwer1234')
>>> res = requests.get('[HOST Portal]/apps/streamflow-prediction-tool/api/GetWarningPoints/', params=request_params, headers=request_headers)
