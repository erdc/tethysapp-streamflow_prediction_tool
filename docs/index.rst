.. Streamflow Prediction Tool documentation master file, created by
   sphinx-quickstart on Fri Jul 15 16:26:28 2016.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

********************************
Streamflow Prediction Tool 1.0.5
********************************

The Streamflow Prediction Tool provides 15-day streamflow 
predicted estimates by using the European Center for Medium 
Range Weather Forecasts (ecmwf.int) runoff predictions routed 
with the RAPID (rapid-hub.org) program. The connection between 
the predicted and hindcasted runoff are generated with GIS tools
both from Esri as well as from open source contributions. 
Return period estimates and warning flags aid in determining the severity.

Publications
============

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

Contents
========

.. toctree::
    :maxdepth: 2

    setup/gis-stream_network_generation.rst
    setup/gis-ecmwf_rapid_input_generation.rst
    setup/historical_lsm_process.rst
    setup/forecast_framework.rst
    setup/web_application.rst



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

