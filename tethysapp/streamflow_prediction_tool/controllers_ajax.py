# -*- coding: utf-8 -*-
##
##  controllers_ajax.py
##  streamflow_prediction_tool
##
##  Created by Alan D. Snow, Curtis Rae, Shawn Crawley 2015.
##  Copyright © 2015-2016 Alan D Snow, Curtis Rae, Shawn Crawley. All rights reserved.
##  License: BSD 3-Clause

from crontab import CronTab
import datetime
from glob import glob
from json import load as json_load
import netCDF4 as NET
import numpy as np
import os
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import ObjectDeletedError
from django.http import JsonResponse
from RAPIDpy.dataset import RAPIDDataset


#django imports
from django.contrib.auth.decorators import user_passes_test, login_required

#tethys imports
from tethys_dataset_services.engines import CkanDatasetEngine

#local imports
from functions import (delete_from_database,
                       delete_old_watershed_prediction_files,
                       delete_old_watershed_files, 
                       delete_old_watershed_geoserver_files,
                       ecmwf_find_most_current_files,
                       ecmwf_get_valid_forecast_folder_list,
                       get_reach_index,
                       wrf_hydro_find_most_current_file,
                       format_name,
                       get_cron_command,
                       handle_uploaded_file,
                       update_geoserver_layer,
                       user_permission_test)

from model import (DataStore, Geoserver, MainSettings, 
                   mainSessionMaker, Watershed, WatershedGroup)

from spt_dataset_manager.dataset_manager import (GeoServerDatasetManager,
                                                 RAPIDInputDatasetManager)
                        
@user_passes_test(user_permission_test)
def data_store_add(request):
    """
    Controller for adding a data store.
    """
    if request.is_ajax() and request.method == 'POST':
        #get/check information from AJAX request
        post_info = request.POST
        data_store_name = post_info.get('data_store_name')
        data_store_type_id = post_info.get('data_store_type_id')
        data_store_endpoint = post_info.get('data_store_endpoint')
        data_store_api_key = post_info.get('data_store_api_key')
        
        if not data_store_name or not data_store_type_id or \
            not data_store_endpoint or not data_store_api_key:
            return JsonResponse({ 'error': "Request missing data." })
            
        #initialize session
        session = mainSessionMaker()
        
        #check to see if duplicate exists
        num_similar_data_stores  = session.query(DataStore) \
            .filter(
                or_(
                    DataStore.name == data_store_name, 
                    DataStore.api_endpoint == data_store_endpoint
                )
            ) \
            .count()
        if(num_similar_data_stores > 0):
            return JsonResponse({ 'error': "A data store with the same name or api endpoint exists." })
            
        #check if data store info is valid
        try:
            dataset_engine = CkanDatasetEngine(endpoint=data_store_endpoint, 
                                               apikey=data_store_api_key)    
            result = dataset_engine.list_datasets()
            if not result or "success" not in result:
                return JsonResponse({ 'error': "Data Store Credentials Invalid. Password incorrect; Endpoint must end in \"api/3/action\""})
        except Exception, ex:
            return JsonResponse({ 'error': "%s" % ex })
        
            
        #add Data Store
        session.add(DataStore(data_store_name, data_store_type_id, data_store_endpoint, data_store_api_key))
        session.commit()
        session.close()
        
        return JsonResponse({ 'success': "Data Store Sucessfully Added!" })

    return JsonResponse({ 'error': "A problem with your request exists." })

@user_passes_test(user_permission_test)
def data_store_delete(request):
    """
    Controller for deleting a data store.
    """
    if request.is_ajax() and request.method == 'POST':
        #get/check information from AJAX request
        post_info = request.POST
        data_store_id = post_info.get('data_store_id')
    
        if int(data_store_id) != 1:
            try:
                #initialize session
                session = mainSessionMaker()
                #update data store
                data_store  = session.query(DataStore).get(data_store_id)
                session.delete(data_store)
                session.commit()
                session.close()
            except IntegrityError:
                return JsonResponse({ 'error': "This data store is connected with a watershed! Must remove connection to delete." })
            return JsonResponse({ 'success': "Data Store Sucessfully Deleted!" })
        return JsonResponse({ 'error': "Cannot change this data store." })
    return JsonResponse({ 'error': "A problem with your request exists." })

@user_passes_test(user_permission_test)
def data_store_update(request):
    """
    Controller for updating a data store.
    """
    if request.is_ajax() and request.method == 'POST':
        #get/check information from AJAX request
        post_info = request.POST
        data_store_id = post_info.get('data_store_id')
        data_store_name = post_info.get('data_store_name')
        data_store_api_endpoint = post_info.get('data_store_api_endpoint')
        data_store_api_key = post_info.get('data_store_api_key')
    
        if int(data_store_id) != 1:
            #initialize session
            session = mainSessionMaker()
            #check to see if duplicate exists
            num_similar_data_stores  = session.query(DataStore) \
                .filter(
                    or_(
                        DataStore.name == data_store_name, 
                        DataStore.api_endpoint == data_store_api_endpoint
                    )
                ) \
                .filter(DataStore.id != data_store_id) \
                .count()
            if(num_similar_data_stores > 0):
                session.close()
                return JsonResponse({ 'error': "A data store with the same name or api endpoint exists." })

            #check if data store info is valid
            try:
                dataset_engine = CkanDatasetEngine(endpoint=data_store_api_endpoint, 
                                                   apikey=data_store_api_key)    
                result = dataset_engine.list_datasets()
                if not result or "success" not in result:
                    return JsonResponse({ 'error': "Data Store Credentials Invalid. Endpoint must end in \"api/3/action\""})
            except Exception, ex:
                return JsonResponse({ 'error': "%s" % ex })
                
            #update data store
            data_store  = session.query(DataStore).get(data_store_id)
            data_store.name = data_store_name
            data_store.api_endpoint= data_store_api_endpoint    
            data_store.api_key = data_store_api_key
            session.commit()
            session.close()
            return JsonResponse({ 'success': "Data Store Sucessfully Updated!" })
        return JsonResponse({ 'error': "Cannot change this data store." })
    return JsonResponse({ 'error': "A problem with your request exists." })

@user_passes_test(user_permission_test)
def geoserver_add(request):
    """
    Controller for adding a geoserver.
    """
    if request.is_ajax() and request.method == 'POST':
        #get/check information from AJAX request
        post_info = request.POST
        geoserver_name = post_info.get('geoserver_name')
        geoserver_url = post_info.get('geoserver_url')
        geoserver_username = post_info.get('geoserver_username')
        geoserver_password = post_info.get('geoserver_password')
    
        #check data
        if not geoserver_name or not geoserver_url or not \
            geoserver_username or not geoserver_password:
            return JsonResponse({ 'error': "Missing input data." })

        #initialize session
        session = mainSessionMaker()

        #validate geoserver credentials
        main_settings  = session.query(MainSettings).order_by(MainSettings.id).first()
        try:
            geoserver_manager = GeoServerDatasetManager(engine_url=geoserver_url.strip(),
                                                        username=geoserver_username.strip(),
                                                        password=geoserver_password.strip(),
                                                        app_instance_id=main_settings.app_instance_id)
        except Exception as ex:
            return JsonResponse({'error' : "GeoServer Error: %s" % ex})
        
        #check to see if duplicate exists
        num_similar_geoservers  = session.query(Geoserver) \
            .filter(
                or_(
                    Geoserver.name == geoserver_name, 
                    Geoserver.url == geoserver_manager.engine_url
                )
            ) \
            .count()
        if(num_similar_geoservers > 0):
            session.close()
            return JsonResponse({ 'error': "A geoserver with the same name or url exists." })
  
        #add Data Store
        session.add(Geoserver(geoserver_name.strip(), 
                              geoserver_manager.engine_url,
                              geoserver_username.strip(), 
                              geoserver_password.strip()
                              ))
        session.commit()
        session.close()
        return JsonResponse({ 'success': "Geoserver Sucessfully Added!" })

    return JsonResponse({ 'error': "A problem with your request exists." })

@user_passes_test(user_permission_test)
def geoserver_delete(request):
    """
    Controller for deleting a geoserver.
    """
    if request.is_ajax() and request.method == 'POST':
        #get/check information from AJAX request
        post_info = request.POST
        geoserver_id = post_info.get('geoserver_id')
    
        #initialize session
        session = mainSessionMaker()
        try:
            #delete geoserver
            try:
                geoserver = session.query(Geoserver).get(geoserver_id)
            except ObjectDeletedError:
                session.close()
                return JsonResponse({ 'error': "The geoserver to delete does not exist." })
            session.delete(geoserver)
            session.commit()
            session.close()
        except IntegrityError:
            session.close()
            return JsonResponse({ 'error': "This geoserver is connected with a watershed! Must remove connection to delete." })
        return JsonResponse({ 'success': "Geoserver sucessfully deleted!" })
    return JsonResponse({ 'error': "A problem with your request exists." })

@user_passes_test(user_permission_test)
def geoserver_update(request):
    """
    Controller for updating a geoserver.
    """
    if request.is_ajax() and request.method == 'POST':
        #get/check information from AJAX request
        post_info = request.POST
        geoserver_id = post_info.get('geoserver_id')
        geoserver_name = post_info.get('geoserver_name')
        geoserver_url = post_info.get('geoserver_url')
        geoserver_username = post_info.get('geoserver_username')
        geoserver_password = post_info.get('geoserver_password')
        #check data
        if not geoserver_id or not geoserver_name or not geoserver_url or not \
            geoserver_username or not geoserver_password:
            return JsonResponse({ 'error': "Missing input data." })
        #make sure id is id
        try:
            int(geoserver_id)
        except ValueError:
            return JsonResponse({'error' : 'Geoserver id is faulty.'})
            

        if int(geoserver_id) != 1:

            #initialize session
            session = mainSessionMaker()
            #validate geoserver credentials
            main_settings  = session.query(MainSettings).order_by(MainSettings.id).first()
            try:
                geoserver_manager = GeoServerDatasetManager(engine_url=geoserver_url.strip(),
                                                            username=geoserver_username.strip(),
                                                            password=geoserver_password.strip(),
                                                            app_instance_id=main_settings.app_instance_id)
            except Exception as ex:
                return JsonResponse({'error' : "GeoServer Error: %s" % ex})

            #check to see if duplicate exists
            num_similar_geoservers  = session.query(Geoserver) \
              .filter(
                      or_(Geoserver.name == geoserver_name,
                          Geoserver.url == geoserver_manager.engine_url)
                      ) \
              .filter(Geoserver.id != geoserver_id) \
              .count()
              
            if(num_similar_geoservers > 0):
                session.close()
                return JsonResponse({ 'error': "A geoserver with the same name or url exists." })

            #update geoserver
            try:
                geoserver = session.query(Geoserver).get(geoserver_id)
            except ObjectDeletedError:
                session.close()
                return JsonResponse({ 'error': "The geoserver to update does not exist." })
            
            geoserver.name = geoserver_name.strip()
            geoserver.url = geoserver_manager.engine_url    
            geoserver.username = geoserver_username.strip()    
            geoserver.password = geoserver_password.strip()    
            session.commit()
            session.close()
            return JsonResponse({ 'success': "Geoserver sucessfully updated!" })
        return JsonResponse({ 'error': "Cannot change this geoserver." })
    return JsonResponse({ 'error': "A problem with your request exists." })

@login_required    
def ecmwf_get_avaialable_dates(request):
    """""
    Finds a list of directories with valid data and returns dates in select2 format
    """""
    if request.method == 'GET':
        #Query DB for path to rapid output
        session = mainSessionMaker()
        main_settings  = session.query(MainSettings).order_by(MainSettings.id).first()
        session.close()

        path_to_rapid_output = main_settings.ecmwf_rapid_prediction_directory
        if not os.path.exists(path_to_rapid_output):
            return JsonResponse({'error' : 'Location of RAPID output files faulty. Please check settings.'})    
    
        #get/check information from AJAX request
        get_info = request.GET
        watershed_name = format_name(get_info['watershed_name']) if 'watershed_name' in get_info else None
        subbasin_name = format_name(get_info['subbasin_name']) if 'subbasin_name' in get_info else None
        if not watershed_name or not subbasin_name:
            return JsonResponse({'error' : 'ECMWF AJAX request input faulty'})
            
        #find/check current output datasets    
        path_to_watershed_files = os.path.join(path_to_rapid_output, "{0}-{1}".format(watershed_name, subbasin_name))

        if not os.path.exists(path_to_watershed_files):
            return JsonResponse({'error' : 'ECMWF forecast for %s (%s) not found.' % (watershed_name, subbasin_name) })
       
        output_directories = ecmwf_get_valid_forecast_folder_list(path_to_watershed_files, ".nc")
        if len(output_directories)>0:
            return JsonResponse({     
                        "success" : "Data analysis complete!",
                        "output_directories" : output_directories,                   
                    })
        else:
            return JsonResponse({'error' : 'Recent ECMWF forecasts for %s, %s not found.' % (watershed_name, subbasin_name)})

@login_required      
def wrf_hydro_get_avaialable_dates(request):
    """""
    Finds a list of directories with valid data and returns dates in select2 format
    """""
    if request.method == 'GET':
        #Query DB for path to rapid output
        session = mainSessionMaker()
        main_settings  = session.query(MainSettings).order_by(MainSettings.id).first()
        session.close()

        path_to_rapid_output = main_settings.wrf_hydro_rapid_prediction_directory
        if not os.path.exists(path_to_rapid_output):
            return JsonResponse({'error' : 'Location of WRF-Hydro RAPID output files faulty. Please check settings.'})

        #get/check information from AJAX request
        get_info = request.GET
        watershed_name = format_name(get_info['watershed_name']) if 'watershed_name' in get_info else None
        subbasin_name = format_name(get_info['subbasin_name']) if 'subbasin_name' in get_info else None
        if not watershed_name or not subbasin_name:
            return JsonResponse({'error' : 'AJAX request input faulty'})

        #find/check current output datasets
        path_to_watershed_files = os.path.join(path_to_rapid_output, "{0}-{1}".format(watershed_name, subbasin_name))

        if not os.path.exists(path_to_watershed_files):
            return JsonResponse({'error' : 'WRF-Hydro forecast for %s (%s) not found.' % (watershed_name, subbasin_name) })

        prediction_files = sorted([d for d in os.listdir(path_to_watershed_files) \
                                if not os.path.isdir(os.path.join(path_to_watershed_files, d))],
                                reverse=True)
        output_files = []
        directory_count = 0
        for prediction_file in prediction_files:
            date_string = prediction_file.split("_")[1]
            date = datetime.datetime.strptime(date_string,"%Y%m%dT%H%MZ")
            path_to_file = os.path.join(path_to_watershed_files, prediction_file)
            if os.path.exists(path_to_file):
                output_files.append({
                    'id' : date_string,
                    'text' : str(date)
                })
                directory_count += 1
                #limit number of directories
                if(directory_count>64):
                    break
        if len(output_files)>0:
            return JsonResponse({
                        "success" : "File search complete!",
                        "output_files" : output_files,
                    })
        else:
            return JsonResponse({'error' : 'Recent WRF-Hydro forecasts for %s (%s) not found.' % (watershed_name, subbasin_name)})

@login_required 
def ecmwf_get_hydrograph(request):
    """""
    Plots 52 ECMWF ensembles analysis with min., max., avg. ,std. dev.
    """""
    if request.method == 'GET':
        #Query DB for path to rapid output
        session = mainSessionMaker()
        main_settings  = session.query(MainSettings).order_by(MainSettings.id).first()
        session.close()
        path_to_rapid_output = main_settings.ecmwf_rapid_prediction_directory
        if not os.path.exists(path_to_rapid_output):
            return JsonResponse({'error' : 'Location of RAPID output files faulty. Please check settings.'})    
    
        #get/check information from AJAX request
        get_info = request.GET
        watershed_name = format_name(get_info['watershed_name']) if 'watershed_name' in get_info else None
        subbasin_name = format_name(get_info['subbasin_name']) if 'subbasin_name' in get_info else None
        reach_id = get_info.get('reach_id')
        start_folder = get_info.get('start_folder')
        if not reach_id or not watershed_name or not subbasin_name or not start_folder:
            return JsonResponse({'error' : 'ECMWF AJAX request input faulty.'})
    
        #make sure reach id is integet
        try:
            reach_id = int(reach_id)
        except TypeError, ValueError:
            return JsonResponse({'error' : 'Invalid Reach ID %s.' % reach_id})

        #find/check current output datasets
        path_to_output_files = os.path.join(path_to_rapid_output, "{0}-{1}".format(watershed_name, subbasin_name))
        basin_files, start_date = ecmwf_find_most_current_files(path_to_output_files, start_folder)
        if not basin_files or not start_date:
            return JsonResponse({'error' : 'ECMWF forecast for %s (%s) not found.' % (watershed_name, subbasin_name)})
    
        with RAPIDDataset(basin_files[0]) as qout_nc_example:
            #get/check the index of the reach
            try:
                reach_index = qout_nc_example.get_river_index(reach_id)
            except Exception:
                return JsonResponse({'error' : 'ECMWF reach with id: %s not found.' % reach_id})

            first_half_size = 40 #run 6-hr resolution for all
            if qout_nc_example.is_time_variable_valid():
                if qout_nc_example.size_time == 41 or qout_nc_example.size_time == 61:
                    #run at full resolution for high res and 6-hr for low res
                    first_half_size = 41
                elif qout_nc_example.size_time == 85 or qout_nc_example.size_time == 125:
                    #run at full resolution for all
                    first_half_size = 65


        #get information from datasets
        all_data_first_half = []
        all_data_second_half = []
        high_res_data = []
        low_res_time = []
        high_res_time = []
        for in_nc in basin_files:
            try:
                index_str = os.path.basename(in_nc)[:-3].split("_")[-1]
                index = int(index_str)

                #Get hydrograph data from ECMWF Ensemble
                with RAPIDDataset(in_nc) as qout_nc:
                    #get streamflow for reach
                    data_values = qout_nc.get_qout_index(reach_index)
    
                    if(index < 52):
                        #get time
                        if low_res_time == []:
                            low_res_time = [t*1000 for t in qout_nc.get_time_array(datetime_simulation_start=start_date,
                                                                                   simulation_time_step_seconds=6*60*60)]
                        all_data_first_half.append(data_values[:first_half_size])
                        all_data_second_half.append(data_values[first_half_size:])
                    if(index == 52):
                        high_res_time = [t*1000 for t in qout_nc.get_time_array(datetime_simulation_start=start_date,
                                                                                simulation_time_step_seconds=6*60*60)]
                        if first_half_size == 65:
                            #convert to 3hr-6hr
                            streamflow_1hr = data_values[:90:3]
                            # calculate time series of 6 hr data from 3 hr data
                            streamflow_3hr_6hr = data_values[90:]
                            # get the time series of 6 hr data
                            all_data_first_half.append(np.concatenate([streamflow_1hr, streamflow_3hr_6hr]))
                        elif qout_nc.size_time == 125:
                            #convert to 6hr
                            streamflow_1hr = data_values[:90:6]
                            # calculate time series of 6 hr data from 3 hr data
                            streamflow_3hr = data_values[90:109:2]
                            # get the time series of 6 hr data
                            streamflow_6hr = data_values[109:]
                            # concatenate all time series
                            all_data_first_half.append(np.concatenate([streamflow_1hr, streamflow_3hr, streamflow_6hr]))
                        else:
                            
                            all_data_first_half.append(data_values)
                        high_res_data = data_values
            except Exception, e:
                print e
                pass
        return_data = {}
        if low_res_time:
            #perform analysis on datasets
            all_data_first = np.array(all_data_first_half, dtype=np.float64)
            all_data_second = np.array(all_data_second_half, dtype=np.float64)
            #get mean
            mean_data_first = np.mean(all_data_first, axis=0)
            mean_data_second = np.mean(all_data_second, axis=0)
            mean_series = np.concatenate([mean_data_first,mean_data_second])
            #get std dev
            std_dev_first = np.std(all_data_first, axis=0)
            std_dev_second = np.std(all_data_second, axis=0)
            std_dev = np.concatenate([std_dev_first,std_dev_second])
            #get max
            max_data_first = np.amax(all_data_first, axis=0)
            max_data_second = np.amax(all_data_second, axis=0)
            max_series = np.concatenate([max_data_first,max_data_second])
            #get min
            min_data_first = np.amin(all_data_first, axis=0)
            min_data_second = np.amin(all_data_second, axis=0)
            min_series = np.concatenate([min_data_first,min_data_second])
            #mean plus std
            mean_plus_std = mean_series + std_dev
            #mean minus std
            mean_mins_std = (mean_series - std_dev).clip(min=0)
            #return results of analysis
            return_data["mean"] = zip(low_res_time, mean_series.tolist())
            return_data["outer_range"] = zip(low_res_time, min_series.tolist(), max_series.tolist())
            return_data["std_dev_range"] = zip(low_res_time, mean_mins_std.tolist(), mean_plus_std.tolist())
            if len(high_res_data) > 0:
                return_data["high_res"] = zip(high_res_time,high_res_data.tolist())
            return_data["success"] = "ECMWF Data analysis complete!"
        return_data["error"] = "Problem generating forecast."
        return JsonResponse(return_data)

@login_required                     
def era_interim_get_hydrograph(request):
    """""
    Returns ERA Interim hydrograph
    """""
    if request.method == 'GET':
        #Query DB for path to rapid output
        session = mainSessionMaker()
        main_settings  = session.query(MainSettings).order_by(MainSettings.id).first()
        session.close()
        path_to_era_interim_data = main_settings.era_interim_rapid_directory
        if not os.path.exists(path_to_era_interim_data):
            return JsonResponse({'error' : 'Location of ERA-Interim files faulty. Please check settings.'})

        #get information from GET request
        get_info = request.GET
        watershed_name = format_name(get_info['watershed_name']) if 'watershed_name' in get_info else None
        subbasin_name = format_name(get_info['subbasin_name']) if 'subbasin_name' in get_info else None
        reach_id = get_info.get('reach_id')
        if not reach_id or not watershed_name or not subbasin_name:
            return JsonResponse({'error' : 'ERA Interim AJAX request input faulty.'})

        #make sure reach id is integet
        try:
            reach_id = int(reach_id)
        except TypeError, ValueError:
            return JsonResponse({'error' : 'Invalid Reach ID %s.' % reach_id})
            
        #----------------------------------------------
        # HISTORICAL DATA SECTION
        #----------------------------------------------
        era_interim_return_data = {}
        #find/check current output datasets
        path_to_output_files = os.path.join(path_to_era_interim_data, "{0}-{1}".format(watershed_name, subbasin_name))
        historical_data_files = glob(os.path.join(path_to_output_files, "Qout*.nc"))
        if historical_data_files:
            try:
                #get/check the index of the reach
                with RAPIDDataset(historical_data_files[0]) as qout_nc:
                    error_found = False
                    #get/check the index of the reach
                    try:
                        reach_index = qout_nc.get_river_index(reach_id)
                    except Exception:
                        era_interim_return_data['error'] = 'ERA Interim reach with id: %s not found.' % reach_id
                        error_found = True
                        raise
    
                    if not error_found:
                        #get information from dataset
                        data_values = qout_nc.get_qout_index(reach_index)
                        time = [t*1000 for t in qout_nc.get_time_array()]
                        era_interim_return_data['series'] = zip(time, data_values.tolist())
            except Exception:
                era_interim_return_data['error'] = "Invalid ERA-Interim file ..."
                pass
                        
        
        else:
            era_interim_return_data['error'] = 'ERA Interim data for %s (%s) not found.' % (watershed_name, subbasin_name)

        #----------------------------------------------
        # RETURN PERIOD SECTION
        #----------------------------------------------
        return_period_return_data = {}
        return_period_files = glob(os.path.join(path_to_output_files, "return_period*.nc"))
        if return_period_files:
            
            return_period_file = return_period_files[0]
            #get/check the index of the reach
            error_found = False
            try:
                rp_reach_index = get_reach_index(return_period_file, reach_id)
            except Exception:
                return_period_return_data['error'] = 'Return period for reach with id: %s not found.' % reach_id
                error_found = True
                pass
                
            if not error_found:
                #get information from dataset
                try:
                    return_period_nc = NET.Dataset(return_period_file, mode="r")
                    rp_max = return_period_nc.variables['max_flow'][rp_reach_index]
                    rp_20 = return_period_nc.variables['return_period_20'][rp_reach_index]
                    rp_10 = return_period_nc.variables['return_period_10'][rp_reach_index]
                    rp_2 = return_period_nc.variables['return_period_2'][rp_reach_index]
                    return_period_nc.close()
                    return_period_return_data["max"] = str(rp_max)
                    return_period_return_data["twenty"] = str(rp_20)
                    return_period_return_data["ten"] = str(rp_10)
                    return_period_return_data["two"] = str(rp_2)
                except Exception:
                    return_period_nc.close()
                    return_period_return_data['error'] = "Invalid return period file"
                    pass
                    
        else:
            return_period_return_data['error'] = 'ERA Interim return period data for %s (%s) not found.' % (watershed_name, subbasin_name)


        return JsonResponse({ 'success' : "ERA-Interim data analysis complete!",
                              'era_interim' : era_interim_return_data,
                              'return_period' : return_period_return_data
                          })

        

@login_required 
def wrf_hydro_get_hydrograph(request):
    """""
    Returns WRF-Hydro hydrograph
    """""
    if request.method == 'GET':
        #Query DB for path to rapid output
        session = mainSessionMaker()
        main_settings  = session.query(MainSettings).order_by(MainSettings.id).first()
        session.close()
        path_to_rapid_output = main_settings.wrf_hydro_rapid_prediction_directory
        if not os.path.exists(path_to_rapid_output):
            return JsonResponse({'error' : 'Location of WRF-Hydro RAPID output files faulty. Please check settings.'})

        #get information from GET request
        get_info = request.GET
        watershed_name = format_name(get_info['watershed_name']) if 'watershed_name' in get_info else None
        subbasin_name = format_name(get_info['subbasin_name']) if 'subbasin_name' in get_info else None
        reach_id = get_info.get('reach_id')
        date_string = get_info.get('date_string')
        if not reach_id or not watershed_name or not subbasin_name or not date_string:
            return JsonResponse({'error' : 'WRF-Hydro AJAX request input faulty.'})
        #find/check current output datasets
        #20150405T2300Z
        path_to_output_files = os.path.join(path_to_rapid_output, "{0}-{1}".format(watershed_name, subbasin_name))
        forecast_file = wrf_hydro_find_most_current_file(path_to_output_files, date_string)
        if not forecast_file:
            return JsonResponse({'error' : 'WRF-Hydro forecast for %s (%s) not found.' % (watershed_name, subbasin_name)})

        #get information from dataset
        try:
            #get/check the index of the reach
            with RAPIDDataset(forecast_file) as qout_nc:
                error_found = False
                #get/check the index of the reach
                try:
                    reach_index = qout_nc.get_river_index(reach_id)
                except Exception:
                    return JsonResponse({'error' : 'WRF-Hydro reach with id: %s not found.' % reach_id})

                if not error_found:
                    #get information from dataset
                    data_values = qout_nc.get_qout_index(reach_index)
                    time = [t*1000 for t in qout_nc.get_time_array()]
        except Exception:
            return JsonResponse({'error' : "Invalid WRF-Hydro forecast file"})
            pass

        return JsonResponse({
                "success" : "WRF-Hydro data analysis complete!",
                "wrf_hydro" : zip(time, data_values.tolist()),
        })
        
@login_required
def generate_warning_points(request):
    """
    Controller for getting warning points for user on map
    """
    if request.method == 'GET':
        #Query DB for path to rapid output
        session = mainSessionMaker()
        main_settings  = session.query(MainSettings).order_by(MainSettings.id).first()
        session.close()
        path_to_ecmwf_rapid_output = main_settings.ecmwf_rapid_prediction_directory
        path_to_era_interim_data = main_settings.era_interim_rapid_directory
        if not os.path.exists(path_to_ecmwf_rapid_output) or not os.path.exists(path_to_era_interim_data):
            return JsonResponse({'error' : 'Location of RAPID output files faulty. Please check settings.'})    
    
        #get/check information from AJAX request
        get_info = request.GET
        watershed_name = format_name(get_info['watershed_name']) if 'watershed_name' in get_info else None
        subbasin_name = format_name(get_info['subbasin_name']) if 'subbasin_name' in get_info else None
        return_period = get_info.get('return_period')
        forecast_folder = get_info.get('forecast_folder')
        if not watershed_name or not subbasin_name or not return_period:
            return JsonResponse({'error' : 'Warning point request input faulty.'})
        
        try:
            return_period = int(return_period)
        except TypeError, ValueError:
            return JsonResponse({'error' : 'Invalid return period.'})
        
        path_to_output_files = os.path.join(path_to_ecmwf_rapid_output, "{0}-{1}".format(watershed_name, subbasin_name))
        if not forecast_folder:
            if os.path.exists(path_to_output_files):
    
                directory_list = sorted([d for d in os.listdir(path_to_output_files) \
                                        if os.path.isdir(os.path.join(path_to_output_files, d))],
                                        reverse=True)
                if directory_list:
                    forecast_folder = directory_list[0]
            else:
                return JsonResponse({'error' : 'No files found for watershed.'})
            
        if forecast_folder:
            if return_period == 20:
                #get warning points to load in
                warning_points_file = os.path.join(path_to_output_files,forecast_folder, "return_20_points.txt")
            elif return_period == 10:
                warning_points_file = os.path.join(path_to_output_files,forecast_folder, "return_10_points.txt")
            elif return_period == 2:
                warning_points_file = os.path.join(path_to_output_files,forecast_folder, "return_2_points.txt")
            else:
                return JsonResponse({'error' : 'Invalid return period.'})
        else:
            return JsonResponse({'error' : 'No forecasts found with {0} return period warning points.'.format(return_period)})
 
        warning_points = []
        if os.path.exists(warning_points_file):
            with open(warning_points_file, 'rb') as infile:
                warning_points = json_load(infile)
        else:
            return JsonResponse({'error' : 'Warning points file not found.'})
                
        return JsonResponse({ 'success': "Warning Points Sucessfully Returned!",
                             'warning_points' : warning_points,
                            })

@user_passes_test(user_permission_test)
def settings_update(request):
    """
    Controller for updating the settings.
    """
    if request.is_ajax() and request.method == 'POST':
        #get/check information from AJAX request
        post_info = request.POST
        base_layer_id = post_info.get('base_layer_id')
        api_key = post_info.get('api_key')
        ecmwf_rapid_prediction_directory = post_info.get('ecmwf_rapid_location')
        era_interim_rapid_directory = post_info.get('era_interim_rapid_location')
        wrf_hydro_rapid_prediction_directory = post_info.get('wrf_hydro_rapid_location')

        #update cron jobs
        try:
            cron_manager = CronTab(user=True)
            cron_manager.remove_all(comment="erfp-dataset-download")
            cron_command = get_cron_command()
            if cron_command:
                #create job to run every hour  
                cron_job = cron_manager.new(command=cron_command, 
                                            comment="erfp-dataset-download")
                cron_job.every(1).hours()
            else:
               JsonResponse({ 'error': "Location of virtual environment not found. No changes made." }) 
       
            #writes content to crontab
            cron_manager.write_to_user(user=True)
        except Exception:
            return JsonResponse({ 'error': "CRON setup error." })

        #initialize session
        session = mainSessionMaker()
        #update main settings
        main_settings  = session.query(MainSettings).order_by(MainSettings.id).first()
        main_settings.base_layer_id = base_layer_id
        main_settings.ecmwf_rapid_prediction_directory = ecmwf_rapid_prediction_directory    
        main_settings.era_interim_rapid_directory = era_interim_rapid_directory    
        main_settings.wrf_hydro_rapid_prediction_directory = wrf_hydro_rapid_prediction_directory    
        main_settings.base_layer.api_key = api_key
        session.commit()
        session.close()

        return JsonResponse({ 'success': "Settings Sucessfully Updated!" })

@user_passes_test(user_permission_test)    
def watershed_add(request):
    """
    Controller for adding a watershed.
    """
    if request.is_ajax() and request.method == 'POST':
        post_info = request.POST
        #get/check information from AJAX request
        watershed_name = post_info.get('watershed_name')
        subbasin_name = post_info.get('subbasin_name')
        watershed_clean_name = format_name(watershed_name)
        subbasin_clean_name = format_name(subbasin_name)
        data_store_id = post_info.get('data_store_id')
        geoserver_id = post_info.get('geoserver_id')
        geoserver_search_for_predicted_flood_map = post_info.get('geoserver_search_for_predicted_flood_map')
        #REQUIRED TO HAVE drainage_line from one of these
        #layer names
        geoserver_drainage_line_layer_name = post_info.get('geoserver_drainage_line_layer')
        geoserver_boundary_layer_name = post_info.get('geoserver_boundary_layer')
        geoserver_gage_layer_name = post_info.get('geoserver_gage_layer')
        geoserver_historical_flood_map_layer_name = post_info.get('geoserver_historical_flood_map_layer')
        geoserver_ahps_station_layer_name = post_info.get('geoserver_ahps_station_layer')
        #shape files
        drainage_line_shp_file = request.FILES.getlist('drainage_line_shp_file')
        geoserver_drainage_line_layer = None
        geoserver_boundary_layer = None
        geoserver_gage_layer = None
        geoserver_historical_flood_map_layer = None
        geoserver_ahps_station_layer = None
        #CHECK DATA
        #make sure information exists 
        if not watershed_name or not subbasin_name or not data_store_id \
            or not geoserver_id or not watershed_clean_name or not subbasin_clean_name:
            return JsonResponse({'error' : 'Request input missing data.'})
        #make sure ids are ids
        try:
            int(data_store_id)
            int(geoserver_id)
        except ValueError:
            return JsonResponse({'error' : 'One or more ids are faulty.'})
         
        #check ECMWF inputs
        ecmwf_ready = False
        ecmwf_rapid_input_resource_id = ""

        ecmwf_data_store_watershed_name = format_name(post_info.get('ecmwf_data_store_watershed_name'))
        ecmwf_data_store_subbasin_name = format_name(post_info.get('ecmwf_data_store_subbasin_name'))
        
        if not ecmwf_data_store_watershed_name or not ecmwf_data_store_subbasin_name:
            ecmwf_data_store_watershed_name = ""
            ecmwf_data_store_subbasin_name = ""
        else:
            ecmwf_ready = True
        
        #check wrf-hydro inputs
        wrf_hydro_ready = False
        wrf_hydro_data_store_watershed_name = format_name(post_info.get('wrf_hydro_data_store_watershed_name'))
        wrf_hydro_data_store_subbasin_name = format_name(post_info.get('wrf_hydro_data_store_subbasin_name'))
        
        if not wrf_hydro_data_store_watershed_name or not wrf_hydro_data_store_subbasin_name:
            wrf_hydro_data_store_watershed_name = ""
            wrf_hydro_data_store_subbasin_name = ""
        else:
            wrf_hydro_ready = True

        #need at least one to be OK to proceed
        if not ecmwf_ready and not wrf_hydro_ready:
            return JsonResponse({'error' : "Must have an ECMWF or WRF-Hydro watershed/subbasin name to continue." })

        #initialize session
        session = mainSessionMaker()
        main_settings  = session.query(MainSettings).order_by(MainSettings.id).first()

        #check to see if duplicate exists
        num_similar_watersheds  = session.query(Watershed) \
            .filter(Watershed.watershed_clean_name == watershed_clean_name) \
            .filter(Watershed.subbasin_clean_name == subbasin_clean_name) \
            .count()
        if(num_similar_watersheds > 0):
            session.close()
            return JsonResponse({ 'error': "A watershed with the same name exists." })

        #validate geoserver inputs
        if not drainage_line_shp_file and not geoserver_drainage_line_layer_name:
            session.close()
            return JsonResponse({'error' : 'Missing geoserver drainage line.'})
            
        #get desired geoserver
        try:
            geoserver  = session.query(Geoserver).get(geoserver_id)
        except ObjectDeletedError:
            session.close()
            return JsonResponse({ 'error': "The geoserver does not exist." })
        try:
            geoserver_manager = GeoServerDatasetManager(engine_url=geoserver.url,
                                                        username=geoserver.username,
                                                        password=geoserver.password,
                                                        app_instance_id=main_settings.app_instance_id)
        except Exception as ex:
            session.close()
            return JsonResponse({'error' : "GeoServer Error: %s" % ex})

        #GEOSERVER UPLOAD
        #check geoserver input before upload
        if drainage_line_shp_file:
            geoserver_drainage_line_layer_name = "%s-%s-%s" % (watershed_clean_name, subbasin_clean_name, 'drainage_line')
            #check shapefles
            try:
                geoserver_manager.check_shapefile_input_files(drainage_line_shp_file)
            except Exception as ex:
                session.close()
                return JsonResponse({'error' : 'Drainage Line layer upload error: %s.' % ex })

        #UPLOAD DRAINAGE LINE
        try:
            geoserver_drainage_line_layer = update_geoserver_layer(None, 
                                                                   geoserver_drainage_line_layer_name, 
                                                                   drainage_line_shp_file,
                                                                   geoserver_manager, 
                                                                   session, 
                                                                   layer_required=True)
        except Exception as ex:
            session.close()
            return JsonResponse({'error' : "Drainage Line layer update error: %s" % ex})
                

        #UPDATE BOUNDARY
        try:
            geoserver_boundary_layer = update_geoserver_layer(None, 
                                                              geoserver_boundary_layer_name, 
                                                              None,
                                                              geoserver_manager, 
                                                              session, 
                                                              layer_required=False)
        except Exception as ex:
            session.close()
            return JsonResponse({'error' : "Boundary layer update error: %s" % ex})

        #UPDATE GAGE
        try:
            geoserver_gage_layer = update_geoserver_layer(None, 
                                                          geoserver_gage_layer_name, 
                                                          None,
                                                          geoserver_manager, 
                                                          session, 
                                                          layer_required=False)
        except Exception as ex:
            session.close()
            return JsonResponse({'error' : "Gage layer update error: %s" % ex})

        #UPDATE HISTORICAL FLOOD MAP LAYER GROUP
        try:
            geoserver_historical_flood_map_layer = update_geoserver_layer(None, 
                                                                          geoserver_historical_flood_map_layer_name, 
                                                                          None,
                                                                          geoserver_manager, 
                                                                          session, 
                                                                          layer_required=False,
                                                                          is_layer_group=True)
        except Exception as ex:
            session.close()
            return JsonResponse({'error' : "Historical Flood Map layer update error: %s" % ex})

        #UPDATE AHPS STATION
        try:
            geoserver_ahps_station_layer = update_geoserver_layer(None, 
                                                                  geoserver_ahps_station_layer_name, 
                                                                  None,
                                                                  geoserver_manager, 
                                                                  session, 
                                                                  layer_required=False)
        except Exception as ex:
            session.close()
            return JsonResponse({'error' : "AHPS Station layer update error: %s" % ex})

        #add watershed
        watershed = Watershed(watershed_name.strip(), 
                              subbasin_name.strip(), 
                              watershed_clean_name, 
                              subbasin_clean_name, 
                              data_store_id, 
                              ecmwf_rapid_input_resource_id,
                              ecmwf_data_store_watershed_name.strip(),
                              ecmwf_data_store_subbasin_name.strip(),
                              wrf_hydro_data_store_watershed_name.strip(),
                              wrf_hydro_data_store_subbasin_name.strip(),
                              geoserver_id, 
                              geoserver_drainage_line_layer,
                              geoserver_boundary_layer,
                              geoserver_gage_layer,
                              geoserver_historical_flood_map_layer,
                              geoserver_ahps_station_layer,
                              geoserver_search_for_predicted_flood_map,
                              )
        session.add(watershed)
        session.commit()
        
        #get watershed_id
        response = {
                    'success': "Watershed Sucessfully Added!",
                    'watershed_id' : watershed.id,
                    'geoserver_drainage_line_layer': geoserver_drainage_line_layer.name if geoserver_drainage_line_layer else geoserver_drainage_line_layer_name,
                    }
        session.close()
        
        return JsonResponse(response)

    return JsonResponse({ 'error': "A problem with your request exists." })

@user_passes_test(user_permission_test)    
def watershed_ecmwf_rapid_file_upload(request):
    """
    Controller AJAX for uploading RAPID input files for a watershed.
    """
    if request.is_ajax() and request.method == 'POST':
        watershed_id = request.POST.get('watershed_id')
        ecmwf_rapid_input_file = request.FILES.get('ecmwf_rapid_input_file')

        #make sure id is int
        try:
            int(watershed_id)
        except ValueError:
            return JsonResponse({'error' : 'Watershed ID need to be an integer.'})
        #initialize session
        session = mainSessionMaker()
        watershed = session.query(Watershed).get(watershed_id)

        #Upload file to Data Store Server
        if int(watershed.data_store_id) > 1 and ecmwf_rapid_input_file:
            #temporarily upload to Tethys Plarform server
            tmp_file_location = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                             'tmp')

            ecmwf_rapid_input_zip = "%s-%s-rapid.zip" % (watershed.ecmwf_data_store_watershed_name, 
                                                         watershed.ecmwf_data_store_subbasin_name)
            handle_uploaded_file(ecmwf_rapid_input_file,
                                 tmp_file_location, 
                                 ecmwf_rapid_input_zip)
            #upload file to CKAN server
            main_settings  = session.query(MainSettings).order_by(MainSettings.id).first()
            #get dataset manager
            data_manager = RAPIDInputDatasetManager(watershed.data_store.api_endpoint,
                                                    watershed.data_store.api_key,
                                                    "ecmwf",
                                                    main_settings.app_instance_id)

            #remove RAPID input files on CKAN if exists
            if watershed.ecmwf_rapid_input_resource_id.strip():
                data_manager.dataset_engine.delete_resource(watershed.ecmwf_rapid_input_resource_id)

            #upload file to CKAN
            upload_file = os.path.join(tmp_file_location, ecmwf_rapid_input_zip)
            resource_info = data_manager.upload_model_resource(upload_file, 
                                                               watershed.ecmwf_data_store_watershed_name, 
                                                               watershed.ecmwf_data_store_subbasin_name)
            
            #update watershed
            watershed.ecmwf_rapid_input_resource_id = resource_info['result']['id']
            session.commit()
        else:
            session.close()
            return JsonResponse({'error' : 'Watershed datastore ID or upload file invalid.'})
        session.close()
        return JsonResponse({'success' : 'ECMWF RAPID Input Upload Success!'})

@user_passes_test(user_permission_test)
def watershed_delete(request):
    """
    Controller for deleting a watershed.
    """
    if request.is_ajax() and request.method == 'POST':
        #get/check information from AJAX request
        post_info = request.POST
        watershed_id = post_info.get('watershed_id')
        #make sure ids are ids
        try:
            int(watershed_id)
        except TypeError, ValueError:
            return JsonResponse({'error' : 'Watershed id is faulty.'})    
        
        if watershed_id:
            #initialize session
            session = mainSessionMaker()
            #get watershed to delete
            try:
                watershed  = session.query(Watershed).get(watershed_id)
            except ObjectDeletedError:
                return JsonResponse({ 'error': "The watershed to delete does not exist." })
                
            #remove watershed geoserver, local prediction files, RAPID Input Files
            main_settings  = session.query(MainSettings).order_by(MainSettings.id).first()
            delete_old_watershed_files(watershed, main_settings.ecmwf_rapid_prediction_directory,
                                       main_settings.wrf_hydro_rapid_prediction_directory)
                                       
                                       
            delete_from_database(session, watershed)
            #NOTE: CASCADE removes associated geoserver layers
            
            #delete watershed from database
            session.commit()
            session.close()

            return JsonResponse({ 'success': "Watershed sucessfully deleted!" })
        return JsonResponse({ 'error': "Cannot delete this watershed." })
    return JsonResponse({ 'error': "A problem with your request exists." })
    
@user_passes_test(user_permission_test)
def watershed_update(request):
    """
    Controller for updating a watershed.
    """
    if request.is_ajax() and request.method == 'POST':
        post_info = request.POST
        #get/check information from AJAX request
        watershed_id = post_info.get('watershed_id')
        watershed_name = post_info.get('watershed_name')
        subbasin_name = post_info.get('subbasin_name')
        watershed_clean_name = format_name(watershed_name)
        subbasin_clean_name = format_name(subbasin_name)
        data_store_id = post_info.get('data_store_id')
        geoserver_id = post_info.get('geoserver_id')
        geoserver_search_for_predicted_flood_map = post_info.get('geoserver_search_for_predicted_flood_map')
        #REQUIRED TO HAVE drainage_line from one of these
        #layer names
        geoserver_drainage_line_layer_name = post_info.get('geoserver_drainage_line_layer')
        geoserver_boundary_layer_name = post_info.get('geoserver_boundary_layer')
        geoserver_gage_layer_name = post_info.get('geoserver_gage_layer')
        geoserver_historical_flood_map_layer_name = post_info.get('geoserver_historical_flood_map_layer')
        geoserver_ahps_station_layer_name = post_info.get('geoserver_ahps_station_layer')
        #shape files
        drainage_line_shp_file = request.FILES.getlist('drainage_line_shp_file')
        boundary_shp_file = request.FILES.getlist('boundary_shp_file')
        gage_shp_file = request.FILES.getlist('gage_shp_file')
        ahps_station_shp_file = request.FILES.getlist('ahps_station_shp_file')
        #CHECK INPUT
        #check if variables exist
        if not watershed_id or not watershed_name or not subbasin_name or not data_store_id \
            or not geoserver_id or not watershed_clean_name or not subbasin_clean_name:
            return JsonResponse({'error' : 'Request input missing data.'})
        #make sure ids are ids
        try:
            int(watershed_id)
            int(data_store_id)
            int(geoserver_id)
        except TypeError, ValueError:
            return JsonResponse({'error' : 'One or more ids are faulty.'})

        #initialize session
        session = mainSessionMaker()
        #check to see if duplicate exists
        num_similar_watersheds  = session.query(Watershed) \
            .filter(Watershed.watershed_clean_name == watershed_clean_name) \
            .filter(Watershed.subbasin_clean_name == subbasin_clean_name) \
            .filter(Watershed.id != watershed_id) \
            .count()
        if(num_similar_watersheds > 0):
            session.close()
            return JsonResponse({ 'error': "A watershed with the same name exists." })
        
        #get desired watershed
        try:
            watershed  = session.query(Watershed).get(watershed_id)
        except ObjectDeletedError:
            session.close()
            return JsonResponse({ 'error': "The watershed to update does not exist." })
        #get desired geoserver
        try:
            geoserver  = session.query(Geoserver).get(geoserver_id)
        except ObjectDeletedError:
            session.close()
            return JsonResponse({ 'error': "The geoserver does not exist." })

            
        #make sure data store information is correct
        ecmwf_data_store_watershed_name = ""
        ecmwf_data_store_subbasin_name = ""
        wrf_hydro_data_store_watershed_name = ""
        wrf_hydro_data_store_subbasin_name = ""
        
        #check ecmwf inputs
        ecmwf_ready = False
        ecmwf_data_store_watershed_name = format_name(post_info.get('ecmwf_data_store_watershed_name'))
        ecmwf_data_store_subbasin_name = format_name(post_info.get('ecmwf_data_store_subbasin_name'))
        
        if not ecmwf_data_store_watershed_name or not ecmwf_data_store_subbasin_name:
            ecmwf_data_store_watershed_name = ""
            ecmwf_data_store_subbasin_name = ""
        else:
            ecmwf_ready = True
        
        #check wrf-hydro inputs
        wrf_hydro_ready = False
        wrf_hydro_data_store_watershed_name = format_name(post_info.get('wrf_hydro_data_store_watershed_name'))
        wrf_hydro_data_store_subbasin_name = format_name(post_info.get('wrf_hydro_data_store_subbasin_name'))
        
        if not wrf_hydro_data_store_watershed_name or not wrf_hydro_data_store_subbasin_name:
            wrf_hydro_data_store_watershed_name = ""
            wrf_hydro_data_store_subbasin_name = ""
        else:
            wrf_hydro_ready = True

        #need at least one to be OK to proceed
        if not ecmwf_ready and not wrf_hydro_ready:
            session.close()
            return JsonResponse({'error' : "Must have an ECMWF or WRF-Hydro watershed/subbasin name to continue" })

        main_settings  = session.query(MainSettings).order_by(MainSettings.id).first()
        
        #GEOSERVER SECTION
        #remove old geoserver files if geoserver changed
        if int(geoserver_id) != watershed.geoserver_id:
           #remove old geoserver files
           delete_old_watershed_geoserver_files(watershed)


        #validate geoserver inputs
        if not drainage_line_shp_file and not geoserver_drainage_line_layer_name:
            session.close()
            return JsonResponse({'error' : 'Missing geoserver drainage line.'})

        try:
            geoserver_manager = GeoServerDatasetManager(engine_url=geoserver.url,
                                                        username=geoserver.username,
                                                        password=geoserver.password,
                                                        app_instance_id=main_settings.app_instance_id)
        except Exception as ex:
            session.close()
            return JsonResponse({'error' : "GeoServer Error: %s" % ex})

        #check geoserver input before upload
        if drainage_line_shp_file:
            geoserver_drainage_line_layer_name = "%s-%s-%s" % (watershed_clean_name, subbasin_clean_name, 'drainage_line')
            #check permissions to upload file
            if watershed.geoserver_drainage_line_layer:
                if not watershed.geoserver_drainage_line_layer.uploaded and \
                    watershed.geoserver_drainage_line_layer.name == geoserver_manager.get_layer_name(geoserver_drainage_line_layer_name):
                    session.close()
                    return JsonResponse({'error' : 'You do not have permissions to overwrite the drainage line layer ...' })
                
            #check shapefles
            try:
                geoserver_manager.check_shapefile_input_files(drainage_line_shp_file)
            except Exception as ex:
                session.close()
                return JsonResponse({'error' : 'Drainage Line Error: %s.' % ex })
                
        if boundary_shp_file:
            geoserver_boundary_layer_name = "%s-%s-%s" % (watershed_clean_name, subbasin_clean_name, 'boundary')
            #check permissions to upload file
            if watershed.geoserver_boundary_layer:
                if not watershed.geoserver_boundary_layer.uploaded and \
                    watershed.geoserver_boundary_layer.name == geoserver_manager.get_layer_name(geoserver_boundary_layer_name):
                    session.close()
                    return JsonResponse({'error' : 'You do not have permissions to overwrite the boundary layer ...' })

            #check shapefiles
            try:
                geoserver_manager.check_shapefile_input_files(boundary_shp_file)
            except Exception as ex:
                session.close()
                return JsonResponse({'error' : 'Boundary Error: %s.' % ex })
                
        if gage_shp_file:
            geoserver_gage_layer_name = "%s-%s-%s" % (watershed_clean_name, subbasin_clean_name, 'gage')
            #check permissions to upload file
            if watershed.geoserver_gage_layer:
                if not watershed.geoserver_gage_layer.uploaded and \
                    watershed.geoserver_gage_layer.name == geoserver_manager.get_layer_name(geoserver_gage_layer_name):
                    session.close()
                    return JsonResponse({'error' : 'You do not have permissions to overwrite the gage layer ...' })

            #check shapefiles
            try:
                geoserver_manager.check_shapefile_input_files(gage_shp_file)
            except Exception as ex:
                session.close()
                return JsonResponse({'error' : 'Gage Error: %s.' % ex })
                
        if ahps_station_shp_file:
            geoserver_ahps_station_layer_name = "%s-%s-%s" % (watershed_clean_name, subbasin_clean_name, 'ahps_station')
            #check permissions to upload file
            if watershed.geoserver_ahps_station_layer:
                if not watershed.geoserver_ahps_station_layer.uploaded and \
                    watershed.geoserver_ahps_station_layer.name == geoserver_manager.get_layer_name(geoserver_ahps_station_layer_name):
                    session.close()
                    return JsonResponse({'error' : 'You do not have permissions to overwrite the AHPS station layer ...' })

            #check shapefiles
            try:
                geoserver_manager.check_shapefile_input_files(ahps_station_shp_file)
            except Exception as ex:
                session.close()
                return JsonResponse({'error' : 'AHPS Station Error: %s.' % ex })
        
        #UPDATE DRAINAGE LINE
        try:
            watershed.geoserver_drainage_line_layer = update_geoserver_layer(watershed.geoserver_drainage_line_layer, 
                                                                             geoserver_drainage_line_layer_name, 
                                                                             drainage_line_shp_file,
                                                                             geoserver_manager, 
                                                                             session, 
                                                                             layer_required=True)
        except Exception as ex:
            session.close()
            return JsonResponse({'error' : "Drainage Line layer update error: %s" % ex})
            

        #UPDATE Boundary
        try:
            watershed.geoserver_boundary_layer = update_geoserver_layer(watershed.geoserver_boundary_layer, 
                                                                        geoserver_boundary_layer_name, 
                                                                        boundary_shp_file,
                                                                        geoserver_manager, 
                                                                        session, 
                                                                        layer_required=False)
        except Exception as ex:
            session.close()
            return JsonResponse({'error' : "Boundary layer update error: %s" % ex})

        #UPDATE GAGE
        try:
            watershed.geoserver_gage_layer = update_geoserver_layer(watershed.geoserver_gage_layer, 
                                                                    geoserver_gage_layer_name, 
                                                                    gage_shp_file,
                                                                    geoserver_manager, 
                                                                    session, 
                                                                    layer_required=False)
        except Exception as ex:
            session.close()
            return JsonResponse({'error' : "Gage layer update error: %s" % ex})

        #UPDATE HISTORICAL FLOOD MAP LAYER GROUP
        try:
            watershed.geoserver_historical_flood_map_layer = update_geoserver_layer(watershed.geoserver_historical_flood_map_layer, 
                                                                                    geoserver_historical_flood_map_layer_name, 
                                                                                    None,
                                                                                    geoserver_manager, 
                                                                                    session, 
                                                                                    layer_required=False,
                                                                                    is_layer_group=True)
        except Exception as ex:
            session.close()
            return JsonResponse({'error' : "Historical Flood Map layer update error: %s" % ex})

        #UPDATE AHPS STATION
        try:
            watershed.geoserver_ahps_station_layer = update_geoserver_layer(watershed.geoserver_ahps_station_layer, 
                                                                            geoserver_ahps_station_layer_name, 
                                                                            ahps_station_shp_file,
                                                                            geoserver_manager, 
                                                                            session, 
                                                                            layer_required=False)
        except Exception as ex:
            session.close()
            return JsonResponse({'error' : "AHPS Station layer update error: %s" % ex})
            


        #remove old prediction files if watershed/subbasin name changed
        if(ecmwf_data_store_watershed_name != watershed.ecmwf_data_store_watershed_name or 
           ecmwf_data_store_subbasin_name != watershed.ecmwf_data_store_subbasin_name):
            delete_old_watershed_prediction_files(watershed,forecast="ecmwf")
            #remove RAPID input files on CKAN if exists
            if watershed.ecmwf_rapid_input_resource_id.strip() \
            and watershed.data_store.data_store_type_id>0:
                #get dataset manager
                try:
                    data_manager = RAPIDInputDatasetManager(watershed.data_store.api_endpoint,
                                                            watershed.data_store.api_key,
                                                            "ecmwf",
                                                            main_settings.app_instance_id)
                except Exception as ex:
                    session.close()
                    return JsonResponse({'error' : "Invalid CKAN instance %s. Cannot delete RAPID input files on CKAN: %s" \
                                                    % (watershed.data_store.api_endpoint, ex)})

                data_manager.dataset_engine.delete_resource(watershed.ecmwf_rapid_input_resource_id)
                watershed.ecmwf_rapid_input_resource_id = ""

        if(wrf_hydro_data_store_watershed_name != watershed.wrf_hydro_data_store_watershed_name or 
           wrf_hydro_data_store_subbasin_name != watershed.wrf_hydro_data_store_subbasin_name):
            delete_old_watershed_prediction_files(watershed, forecast="wrf_hydro")

        #change watershed attributes
        watershed.watershed_name = watershed_name.strip()
        watershed.subbasin_name = subbasin_name.strip()
        watershed.watershed_clean_name = watershed_clean_name
        watershed.subbasin_clean_name = subbasin_clean_name
        watershed.data_store_id = data_store_id
        watershed.ecmwf_data_store_watershed_name = ecmwf_data_store_watershed_name
        watershed.ecmwf_data_store_subbasin_name = ecmwf_data_store_subbasin_name
        watershed.wrf_hydro_data_store_watershed_name = wrf_hydro_data_store_watershed_name
        watershed.wrf_hydro_data_store_subbasin_name = wrf_hydro_data_store_subbasin_name
        watershed.geoserver_id = geoserver_id
        watershed.geoserver_search_for_predicted_flood_map = geoserver_search_for_predicted_flood_map
        
        
        response = {
                    'success': "Watershed sucessfully updated!", 
                    'geoserver_drainage_line_layer': watershed.geoserver_drainage_line_layer.name \
                                                     if watershed.geoserver_drainage_line_layer else "",
                    'geoserver_boundary_layer': watershed.geoserver_boundary_layer.name \
                                                 if watershed.geoserver_boundary_layer else "",
                    'geoserver_gage_layer': watershed.geoserver_gage_layer.name \
                                            if watershed.geoserver_gage_layer else "",
                    'geoserver_historical_flood_map_layer': watershed.geoserver_historical_flood_map_layer.name \
                                            if watershed.geoserver_historical_flood_map_layer else "",
                    'geoserver_ahps_station_layer': watershed.geoserver_ahps_station_layer.name \
                                                    if watershed.geoserver_ahps_station_layer else "",
                    }
        
        #update database
        session.commit()
        session.close()
        
        return JsonResponse(response)

    return JsonResponse({ 'error': "A problem with your request exists." })

@user_passes_test(user_permission_test)
def watershed_group_add(request):
    """
    Controller for adding a watershed_group.
    """
    if request.is_ajax() and request.method == 'POST':
        #get/check information from AJAX request
        post_info = request.POST
        watershed_group_name = post_info.get('watershed_group_name')
        watershed_group_watershed_ids = post_info.getlist('watershed_group_watershed_ids[]')
        if not watershed_group_name or not watershed_group_watershed_ids:
            return JsonResponse({ 'error': 'AJAX request input faulty' })
        #initialize session
        session = mainSessionMaker()
        
        #check to see if duplicate exists
        num_similar_watershed_groups  = session.query(WatershedGroup) \
            .filter(WatershedGroup.name == watershed_group_name) \
            .count()
        if(num_similar_watershed_groups > 0):
            return JsonResponse({ 'error': "A watershed group with the same name." })
            
        #add Watershed Group
        group = WatershedGroup(watershed_group_name)

        #update watersheds
        watersheds  = session.query(Watershed) \
                .filter(Watershed.id.in_(watershed_group_watershed_ids)) \
                .all()
        for watershed in watersheds:
            group.watersheds.append(watershed)
        session.add(group)
        session.commit()
        session.close()

        return JsonResponse({ 'success': "Watershed group sucessfully added!" })

    return JsonResponse({ 'error': "A problem with your request exists." })
    
@user_passes_test(user_permission_test)
def watershed_group_delete(request):
    """
    Controller for deleting a watershed group.
    """
    if request.is_ajax() and request.method == 'POST':
        #get/check information from AJAX request
        post_info = request.POST
        watershed_group_id = post_info.get('watershed_group_id')
    
        
        if watershed_group_id:
            #initialize session
            session = mainSessionMaker()
            #get watershed group to delete
            watershed_group  = session.query(WatershedGroup).get(watershed_group_id)
            
            #delete watershed group from database
            session.delete(watershed_group)
            session.commit()
            session.close()

            return JsonResponse({ 'success': "Watershed group sucessfully deleted!" })
        return JsonResponse({ 'error': "Cannot delete this watershed group." })
    return JsonResponse({ 'error': "A problem with your request exists." })
    
@user_passes_test(user_permission_test)
def watershed_group_update(request):
    """
    Controller for updating a watershed_group.
    """
    if request.is_ajax() and request.method == 'POST':
        #get/check information from AJAX request
        post_info = request.POST
        watershed_group_id = post_info.get('watershed_group_id')
        watershed_group_name = post_info.get('watershed_group_name')
        watershed_group_watershed_ids = post_info.getlist('watershed_group_watershed_ids[]')
        if watershed_group_id and watershed_group_name and watershed_group_watershed_ids:
            #initialize session
            session = mainSessionMaker()
            #check to see if duplicate exists
            num_similar_watershed_groups  = session.query(WatershedGroup) \
                .filter(WatershedGroup.name == watershed_group_name) \
                .filter(WatershedGroup.id != watershed_group_id) \
                .count()
            if(num_similar_watershed_groups > 0):
                return JsonResponse({ 'error': "A watershed group with the same name exists." })

            #get watershed group
            watershed_group  = session.query(WatershedGroup).get(watershed_group_id)
            watershed_group.name = watershed_group_name
            #find new watersheds
            new_watersheds  = session.query(Watershed) \
                    .filter(Watershed.id.in_(watershed_group_watershed_ids)) \
                    .all()

            #remove old watersheds
            for watershed in watershed_group.watersheds:
                if watershed not in new_watersheds:
                    watershed_group.watersheds.remove(watershed)
                
            #add new watersheds        
            for watershed in new_watersheds:
                if watershed not in watershed_group.watersheds:
                    watershed_group.watersheds.append(watershed)
            
            session.commit()
            session.close()
            return JsonResponse({ 'success': "Watershed group successfully updated." })
        return JsonResponse({ 'error': "Data missing for this watershed group." })
    return JsonResponse({ 'error': "A problem with your request exists." })
