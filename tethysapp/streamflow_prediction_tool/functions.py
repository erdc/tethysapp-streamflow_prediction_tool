import datetime
from glob import glob
import netCDF4 as NET
import numpy as np
import os
from pytz import utc
import re
from shutil import rmtree
from sqlalchemy import and_

#local import
from model import mainSessionMaker, MainSettings, Watershed
from spt_dataset_manager.dataset_manager import (CKANDatasetManager, 
                                                  GeoServerDatasetManager)

    
def delete_old_watershed_prediction_files(watershed, forecast="all"):
    """
    Removes old watershed prediction files from system if no other watershed has them
    """
    def delete_prediciton_files(main_folder_name, sub_folder_name, local_prediction_files_location):
        """
        Removes predicitons from folder and folder if not empty
        """
        prediciton_folder = os.path.join(local_prediction_files_location, 
                                         main_folder_name,
                                         sub_folder_name)
        #remove watersheds subbsasins folders/files
        if main_folder_name and sub_folder_name and \
        local_prediction_files_location and os.path.exists(prediciton_folder):
            
            #remove all prediction files from watershed/subbasin
            try:
                rmtree(prediciton_folder)
            except OSError:
                pass
            
            #remove watershed folder if no other subbasins exist
            try:
                os.rmdir(os.path.join(local_prediction_files_location, 
                                      main_folder_name))
            except OSError:
                pass
        
    #initialize session
    session = mainSessionMaker()
    main_settings  = session.query(MainSettings).order_by(MainSettings.id).first()
    forecast = forecast.lower()
    
    #Remove ECMWF Forecasta
    if forecast == "all" or forecast == "ecmwf":
        #Make sure that you don't delete if another watershed is using the
        #same predictions
        num_ecmwf_watersheds_with_forecast  = session.query(Watershed) \
            .filter(
                and_(
                    Watershed.ecmwf_data_store_watershed_name == watershed.ecmwf_data_store_watershed_name, 
                    Watershed.ecmwf_data_store_subbasin_name == watershed.ecmwf_data_store_subbasin_name
                )
            ) \
            .filter(Watershed.id != watershed.id) \
            .count()
        if num_ecmwf_watersheds_with_forecast <= 0:
            delete_prediciton_files(watershed.ecmwf_data_store_watershed_name, 
                                    watershed.ecmwf_data_store_subbasin_name, 
                                    main_settings.ecmwf_rapid_prediction_directory)
    
    #Remove WRF-Hydro Forecasts
    if forecast == "all" or forecast == "wrf_hydro":
        #Make sure that you don't delete if another watershed is using the
        #same predictions
        num_wrf_hydro_watersheds_with_forecast  = session.query(Watershed) \
            .filter(
                and_(
                    Watershed.wrf_hydro_data_store_watershed_name == watershed.wrf_hydro_data_store_watershed_name, 
                    Watershed.wrf_hydro_data_store_subbasin_name == watershed.wrf_hydro_data_store_subbasin_name
                )
            ) \
            .filter(Watershed.id != watershed.id) \
            .count()
        if num_wrf_hydro_watersheds_with_forecast <= 0:
            delete_prediciton_files(watershed.wrf_hydro_data_store_watershed_name, 
                                    watershed.wrf_hydro_data_store_subbasin_name, 
                                    main_settings.wrf_hydro_rapid_prediction_directory)
    
    session.close()
              

def delete_old_watershed_kml_files(watershed):
    """
    Removes old watershed kml files from system
    """
    old_kml_file_location = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                         'public','kml',watershed.folder_name)
    #remove old kml files on local server
    #drainange line
    try:
        if watershed.kml_drainage_line_layer:
            os.remove(os.path.join(old_kml_file_location, 
                                   watershed.kml_drainage_line_layer))
    except OSError:
        pass
    #catchment
    try:
        if watershed.kml_catchment_layer:
            os.remove(os.path.join(old_kml_file_location, 
                                   watershed.kml_catchment_layer))
    except OSError:
        pass
    #gage
    try:
        if watershed.kml_gage_layer:
            os.remove(os.path.join(old_kml_file_location, 
                                   watershed.kml_gage_layer))
    except OSError:
        pass
    #folder
    try:
        os.rmdir(old_kml_file_location)
    except OSError:
        pass

def delete_old_watershed_geoserver_files(watershed):
    """
    Removes old watershed geoserver files from system
    """
    #initialize session
    session = mainSessionMaker()
    main_settings  = session.query(MainSettings).order_by(MainSettings.id).first()
    
    #initialize geoserver manager
    geoserver_manager = GeoServerDatasetManager(engine_url=watershed.geoserver.url,
                                                username=watershed.geoserver.username,
                                                password=watershed.geoserver.password,
                                                app_instance_id=main_settings.app_instance_id)

    session.close()
    
    #delete layers which need to be deleted
    if watershed.geoserver_drainage_line_uploaded and watershed.geoserver_drainage_line_layer:
        geoserver_manager.purge_remove_geoserver_layer(watershed.geoserver_drainage_line_layer)
                                     
    if watershed.geoserver_catchment_uploaded and watershed.geoserver_catchment_layer:
        geoserver_manager.purge_remove_geoserver_layer(watershed.geoserver_catchment_layer)
                                     
    if watershed.geoserver_gage_uploaded and watershed.geoserver_gage_layer:
        geoserver_manager.purge_remove_geoserver_layer(watershed.geoserver_gage_layer)

    if watershed.geoserver_ahps_station_uploaded and watershed.geoserver_ahps_station_layer:
        geoserver_manager.purge_remove_geoserver_layer(watershed.geoserver_ahps_station_layer)
        

def delete_old_watershed_files(watershed, ecmwf_local_prediction_files_location,
                               wrf_hydro_local_prediction_files_location):
    """
    Removes old watershed files from system
    """
    #remove old kml files
    delete_old_watershed_kml_files(watershed)
    #remove old geoserver files
    delete_old_watershed_geoserver_files(watershed)
    #remove old ECMWF and WRF-Hydro prediction files
    delete_old_watershed_prediction_files(watershed, forecast="all")
    #remove RAPID input files on CKAN
    data_store = watershed.data_store
    if 'ckan' == data_store.data_store_type.code_name and watershed.ecmwf_rapid_input_resource_id:
        #get dataset managers
        data_manager = CKANDatasetManager(data_store.api_endpoint,
                                          data_store.api_key,
                                          "ecmwf"
                                          )
        data_manager.dataset_engine.delete_resource(watershed.ecmwf_rapid_input_resource_id)

def ecmwf_find_most_current_files(path_to_watershed_files, start_folder):
    """""
    Finds the current output from downscaled ECMWF forecasts
    """""
    if(start_folder=="most_recent"):
        if not os.path.exists(path_to_watershed_files):
            return None, None
        directories = sorted([d for d in os.listdir(path_to_watershed_files) \
                             if os.path.isdir(os.path.join(path_to_watershed_files, d))],
                             reverse=True)
    else:
        directories = [start_folder]
    for directory in directories:
        try:
            date = datetime.datetime.strptime(directory.split(".")[0],"%Y%m%d")
            time = directory.split(".")[-1]
            path_to_files = os.path.join(path_to_watershed_files, directory)
            if os.path.exists(path_to_files):
                basin_files = sorted(glob(os.path.join(path_to_files,"*.nc")), reverse=True)
                if len(basin_files)>0:
                    hour = int(time)/100
                    return basin_files, (date + datetime.timedelta(0,int(hour)*60*60)).replace(tzinfo=utc)
        except Exception as ex:
            print ex
            pass
    #there are no files found
    return None, None

def wrf_hydro_find_most_current_file(path_to_watershed_files, date_string):
    """""
    Finds the current output from downscaled WRF-Hydro forecasts
    """""
    if(date_string=="most_recent"):
        if not os.path.exists(path_to_watershed_files):
            return None
        prediction_files = sorted(glob(os.path.join(path_to_watershed_files,"*.nc")),
                                  reverse=True)
    else:
        #RapidResult_20150405T2300Z_CF.nc
        prediction_files = ["RapidResult_%s_CF.nc" % date_string]
    for prediction_file in prediction_files:
        try:
            path_to_file = os.path.join(path_to_watershed_files, prediction_file)
            if os.path.exists(path_to_file):
                return path_to_file
        except Exception as ex:
            print ex
            pass
    #there are no files found
    return None

def format_name(string):
    """
    Formats watershed name for code
    """
    if string:
        formatted_string = string.strip().replace(" ", "_").lower()
        formatted_string = re.sub(r'[^a-zA-Z0-9_-]', '', formatted_string)
        while formatted_string.startswith("-") or formatted_string.startswith("_"):
            formatted_string = formatted_string[1:]
    else:
        formatted_string = ""
    return formatted_string

def format_watershed_title(watershed, subbasin):
    """
    Formats title for watershed in navigation
    """
    max_length = 30
    watershed = watershed.strip()
    subbasin = subbasin.strip()
    watershed_length = len(watershed)
    if(watershed_length>max_length):
        return watershed[:max_length-1].strip() + "..."
    max_length -= watershed_length
    subbasin_length = len(subbasin)
    if(subbasin_length>max_length):
        return (watershed + " (" + subbasin[:max_length-3].strip() + " ...)")
    return (watershed + " (" + subbasin + ")")

def get_cron_command():
    """
    Gets cron command for downloading datasets
    """
    #/usr/lib/tethys/src/tethys_apps/tethysapp/erfp_tool/cron/load_datasets.py
    local_directory = os.path.dirname(os.path.abspath(__file__))
    delimiter = ""
    if "/" in local_directory:
        delimiter = "/"
    elif "\\" in local_directory:
        delimiter = "\\"
    virtual_env_path = ""
    if delimiter and local_directory:
        virtual_env_path = delimiter.join(local_directory.split(delimiter)[:-4])
        command = '%s %s' % (os.path.join(virtual_env_path,'bin','python'), 
                              os.path.join(local_directory, 'load_datasets.py'))
        return command
    else:
        return None

def get_reach_index(reach_id, prediction_file, guess_index=None):
    """
    Gets the index of the reach from the COMID 
    """
    data_nc = NET.Dataset(prediction_file, mode="r")
    com_ids = data_nc.variables['COMID'][:]
    data_nc.close()
    try:
        if guess_index:
            if int(reach_id) == int(com_ids[int(guess_index)]):
                return int(guess_index)
    except Exception as ex:
        print ex
        pass
    
    try:
        reach_index = np.where(com_ids==int(reach_id))[0][0]
    except Exception as ex:
        print ex
        reach_index = None
        pass
    return reach_index                

def get_comids_in_lookup_comid_list(search_reach_id_list, lookup_reach_id_list):
    """
    Gets the subset comid_index_list, reordered_comid_list from the netcdf file
    """
    try:
        #get where comids are in search_list
        search_reach_indices_list = np.where(np.in1d(search_reach_id_list, lookup_reach_id_list))[0]
    except Exception as ex:
        print ex

    return search_reach_indices_list, lookup_reach_id_list[search_reach_indices_list]

def get_subbasin_list(file_path):
    """
    Gets a list of subbasins in the watershed
    """
    subbasin_list = []
    drainage_line_kmls = glob(os.path.join(file_path, '*drainage_line.kml'))
    for drainage_line_kml in drainage_line_kmls:
        subbasin_name = "-".join(os.path.basename(drainage_line_kml).split("-")[:-1])
        if subbasin_name not in subbasin_list:
            subbasin_list.append(subbasin_name)
    catchment_kmls = glob(os.path.join(file_path, '*catchment.kml'))
    for catchment_kml in catchment_kmls:
        subbasin_name = "-".join(os.path.basename(catchment_kml).split("-")[:-1])
        if subbasin_name not in subbasin_list:
            subbasin_list.append(subbasin_name)
    subbasin_list.sort()
    return subbasin_list
   
def handle_uploaded_file(f, file_path, file_name):
    """
    Uploads file to specified path
    """
    #remove old file if exists
    try:
        os.remove(os.path.join(file_path, file_name))
    except OSError:
        pass
    #make directory
    if not os.path.exists(file_path):
        os.mkdir(file_path)
    #upload file    
    with open(os.path.join(file_path,file_name), 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)

def user_permission_test(user):
    """
    User needs to be superuser or staff
    """
    return user.is_superuser or user.is_staff