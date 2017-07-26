# -*- coding: utf-8 -*-
##
##  load_datasets.py
##  streamflow_prediction_tool
##
##  Created by Alan D. Snow, 2015
##  License: BSD 3-Clause

import os
from shutil import rmtree

from spt_dataset_manager.dataset_manager import ECMWFRAPIDDatasetManager

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tethys_portal.settings")

# local imports
from tethys_apps.tethysapp.streamflow_prediction_tool.model import Watershed
from tethys_apps.tethysapp.streamflow_prediction_tool.app \
    import StreamflowPredictionTool as app


def download_single_watershed_ecmwf_data(watershed,
                                         ecmwf_rapid_prediction_directory):
    """
    Loads single watersheds ECMWF datasets from data store
    """
    if ecmwf_rapid_prediction_directory \
        and os.path.exists(ecmwf_rapid_prediction_directory) \
        and watershed.ecmwf_data_store_watershed_name \
        and watershed.ecmwf_data_store_subbasin_name:
            
        #get data engine
        data_store = watershed.data_store
        if 'ckan' == data_store.data_store_type.code_name:
            #get dataset managers
            data_manager = ECMWFRAPIDDatasetManager(data_store.api_endpoint,
                                                    data_store.api_key)    
            #load current datasets
            data_manager.download_recent_resource(watershed.ecmwf_data_store_watershed_name, 
                                                  watershed.ecmwf_data_store_subbasin_name,
                                                  ecmwf_rapid_prediction_directory)
    
        path_to_predicitons = os.path.join(ecmwf_rapid_prediction_directory,
                                           "{0}-{1}".format(watershed.ecmwf_data_store_watershed_name, 
                                                            watershed.ecmwf_data_store_subbasin_name) 
                                           )

        if os.path.exists(path_to_predicitons):
            prediction_directories = sorted(os.listdir(path_to_predicitons), 
                                            reverse=True)[14:]
            #remove oldest datasets if more than 14 exist
            try:
                for prediction_directory in prediction_directories:
                    rmtree(os.path.join(path_to_predicitons, prediction_directory))
            except OSError:
                pass


def load_datasets():
    """
    Loads ECMWF prediction datasets from data store for all watersheds
    """
    session_maker = app.get_persistent_store_database('main_db', as_sessionmaker=True)
    session = session_maker()

    app_instance_id = app.get_custom_setting('app_instance_id')
    ecmwf_rapid_prediction_directory = app.get_custom_setting('ecmwf_forecast_folder')
    if ecmwf_rapid_prediction_directory and os.path.exists(ecmwf_rapid_prediction_directory):
        for watershed in session.query(Watershed).all():
            download_single_watershed_ecmwf_data(watershed, 
                                                 ecmwf_rapid_prediction_directory, 
                                                 app_instance_id)
    else:
        print("ECMWF prediction location invalid. Please set to continue.")
        
    session.close()


def load_watershed(watershed):
    """
    Loads prediction datasets from data store for one watershed
    """
    session_maker = app.get_persistent_store_database('main_db', as_sessionmaker=True)
    session = session_maker()

    app_instance_id = app.get_custom_setting('app_instance_id')
    ecmwf_rapid_prediction_directory = app.get_custom_setting('ecmwf_forecast_folder')

    if ecmwf_rapid_prediction_directory and \
        os.path.exists(ecmwf_rapid_prediction_directory):
            
        download_single_watershed_ecmwf_data(watershed, 
                                             ecmwf_rapid_prediction_directory,
                                             app_instance_id)
    else:
        print("ECMWF prediction location invalid. Please set to continue.")

    session.close()
