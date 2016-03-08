# -*- coding: utf-8 -*-
##
##  load_datasets.py
##  streamflow_prediction_tool
##
##  Created by Alan D. Snow.
##  Copyright © 2015-2016 Alan D. Snow. All rights reserved.
##  License: BSD 2-Clause

import os
from shutil import rmtree

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tethys_apps.settings")
#local imports
from tethys_apps.tethysapp.streamflow_prediction_tool.model import (MainSettings, 
                                                                    mainSessionMaker, 
                                                                    Watershed)
                                                   
from spt_dataset_manager.dataset_manager import (ECMWFRAPIDDatasetManager,
                                                 GeoServerDatasetManager,
                                                 WRFHydroHRRRDatasetManager)
                                                  
def download_single_watershed_ecmwf_data(watershed, 
                                         ecmwf_rapid_prediction_directory,
                                         app_instance_id):
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
            
            if watershed.geoserver_id > 1 and app_instance_id and watershed.geoserver_search_for_flood_map:
                try:
                    #get geoserver engine
                    geoserver_manager = GeoServerDatasetManager(engine_url=watershed.geoserver.url,
                                                                username=watershed.geoserver.username,
                                                                password=watershed.geoserver.password,
                                                                app_instance_id=app_instance_id)
                    #remove old geoserver layers
                    flood_map_layer_name_beginning = "%s-%s-floodmap-" % (watershed.ecmwf_data_store_watershed_name,
                                                                          watershed.ecmwf_data_store_subbasin_name)
                    geoserver_directories = sorted([d for d in os.listdir(path_to_predicitons) \
                                        if os.path.isdir(os.path.join(path_to_predicitons, d))],
                                         reverse=True)[7:]
                    for geoserver_directory in geoserver_directories:
                        layer_name = geoserver_manager.get_layer_name("%s%s" % (flood_map_layer_name_beginning, geoserver_directory))
                        print "Deleting geoserver layer group:", layer_name
                        #TODO: CHECK IF EXISTS BEFORE REMOVING
                        geoserver_manager.purge_remove_geoserver_layer_group(layer_name)
                except Exception as ex:
                    print ex
                    pass

def download_single_watershed_wrf_hydro_data(watershed, 
                                             wrf_hydro_rapid_prediction_directory):
    """
    Loads single watersheds WRF-Hydro datasets from data store
    """
    if wrf_hydro_rapid_prediction_directory \
        and os.path.exists(wrf_hydro_rapid_prediction_directory) \
        and watershed.wrf_hydro_data_store_watershed_name \
        and watershed.wrf_hydro_data_store_subbasin_name:
        #get data engine
        data_store = watershed.data_store
        if 'ckan' == data_store.data_store_type.code_name:
            #get dataset managers
            data_manager = WRFHydroHRRRDatasetManager(data_store.api_endpoint,
                                                      data_store.api_key)
            #load current datasets
            data_manager.download_recent_resource(watershed.wrf_hydro_data_store_watershed_name, 
                                                  watershed.wrf_hydro_data_store_subbasin_name,
                                                  wrf_hydro_rapid_prediction_directory)
    
        path_to_predicitons = os.path.join(wrf_hydro_rapid_prediction_directory, 
                                           "{0}-{1}".format(watershed.wrf_hydro_data_store_watershed_name, 
                                                            watershed.wrf_hydro_data_store_subbasin_name)
                                          )
    
        if os.path.exists(path_to_predicitons):
            #remove oldest datasets if more than 24 exist
            try:
                prediction_files = sorted(os.listdir(path_to_predicitons), 
                                                reverse=True)[24:]
                for prediction_file in prediction_files:
                    rmtree(os.path.join(path_to_predicitons, prediction_file))
            except OSError:
                pass


def load_datasets():
    """
    Loads ECMWF prediction datasets from data store for all watersheds
    """
    session = mainSessionMaker()
    main_settings  = session.query(MainSettings).order_by(MainSettings.id).first()

    ecmwf_rapid_prediction_directory = main_settings.ecmwf_rapid_prediction_directory
    if ecmwf_rapid_prediction_directory and os.path.exists(ecmwf_rapid_prediction_directory):
        for watershed in session.query(Watershed).all():
            download_single_watershed_ecmwf_data(watershed, 
                                                 ecmwf_rapid_prediction_directory, 
                                                 main_settings.app_instance_id)
    else:
        print "ECMWF prediction location invalid. Please set to continue."
        
    wrf_hydro_rapid_prediction_directory = main_settings.wrf_hydro_rapid_prediction_directory
    if wrf_hydro_rapid_prediction_directory and \
        os.path.exists(wrf_hydro_rapid_prediction_directory):
        for watershed in session.query(Watershed).all():
            download_single_watershed_wrf_hydro_data(watershed, 
                                                     wrf_hydro_rapid_prediction_directory)
    else:
        print "WRF-Hydro prediction location invalid. Please set to continue."

def load_watershed(watershed):
    """
    Loads prediction datasets from data store for one watershed
    """
    session = mainSessionMaker()
    main_settings  = session.query(MainSettings).order_by(MainSettings.id).first()

    if main_settings.ecmwf_rapid_prediction_directory and \
        os.path.exists(main_settings.ecmwf_rapid_prediction_directory):
            
        download_single_watershed_ecmwf_data(watershed, 
                                             main_settings.ecmwf_rapid_prediction_directory,
                                             main_settings.app_instance_id)
    else:
        print "ECMWF prediction location invalid. Please set to continue."

    if main_settings.wrf_hydro_rapid_prediction_directory and \
        os.path.exists(main_settings.wrf_hydro_rapid_prediction_directory):
            
        download_single_watershed_wrf_hydro_data(watershed, 
                                                 main_settings.wrf_hydro_rapid_prediction_directory)
    else:
        print "WRF-Hydro prediction location invalid. Please set to continue."
    
        
if __name__ == "__main__":
    load_datasets()
    #engine_url = 'https://ckan.test'
    #api_key = ':SDKLFGNSD:L-sfl;jgn'
    """    
    #ECMWF
    er_manager = ECMWFRAPIDDatasetManager(engine_url, api_key)
    er_manager.download_prediction_dataset(watershed='philippines', 
                                            subbasin='luzon', 
                                            date_string='20151214.0', 
                                            extract_directory='/home/alan/work/rapid-io/output/philippines-luzon')
    """
    """
    #WRF-Hydro
    wr_manager = WRFHydroHRRRDatasetManager(engine_url, api_key)
    wr_manager.download_prediction_resource(watershed='usa', 
                                            subbasin='usa', 
                                            date_string='20150405T2300Z', 
                                            extract_directory='/home/alan/tethysdev/tethysapp-erfp_tool/wrf_hydro_rapid_predictions/usa')
    """ 
