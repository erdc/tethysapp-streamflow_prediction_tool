# -*- coding: utf-8 -*-
"""controllers_ajax.py

    Created by Alan D. Snow, Curtis Rae, Shawn Crawley 2015.
    License: BSD 3-Clause
"""
from csv import writer as csv_writer
from glob import glob
from json import load as json_load
import netCDF4 as NET
import numpy as np
import os
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import ObjectDeletedError
from django.http import HttpResponse, JsonResponse, Http404
from RAPIDpy.dataset import RAPIDDataset
import xarray

# django imports
from django.contrib.auth.decorators import user_passes_test, login_required
from django.views.decorators.http import require_GET, require_POST

# tethys imports
from tethys_dataset_services.engines import CkanDatasetEngine

# local imports
from spt_dataset_manager.dataset_manager import (GeoServerDatasetManager,
                                                 RAPIDInputDatasetManager)

from .app import StreamflowPredictionTool as app
from .functions import (delete_from_database,
                        delete_rapid_input_ckan,
                        delete_old_watershed_prediction_files,
                        delete_old_watershed_files,
                        delete_old_watershed_geoserver_files,
                        ecmwf_find_most_current_files,
                        ecmwf_get_valid_forecast_folder_list,
                        ecmwf_get_forecast_statistics,
                        format_name,
                        handle_uploaded_file,
                        update_geoserver_layer,
                        user_permission_test)

from .model import (DataStore, Geoserver, Watershed, WatershedGroup)


@require_POST
@user_passes_test(user_permission_test)
def data_store_add(request):
    """
    Controller for adding a data store.
    """
    # get/check information from AJAX request
    post_info = request.POST
    data_store_name = post_info.get('data_store_name')
    data_store_owner_org = post_info.get('data_store_owner_org')
    data_store_type_id = post_info.get('data_store_type_id')
    data_store_endpoint = post_info.get('data_store_endpoint')
    data_store_api_key = post_info.get('data_store_api_key')

    if not data_store_name or not data_store_type_id or \
        not data_store_endpoint or not data_store_api_key:
        return JsonResponse({'error': "Request missing data."})

    # initialize session
    session_maker = app.get_persistent_store_database('main_db',
                                                      as_sessionmaker=True)
    session = session_maker()

    # check to see if duplicate exists
    num_similar_data_stores  = session.query(DataStore) \
        .filter(
            or_(
                DataStore.name == data_store_name,
                DataStore.api_endpoint == data_store_endpoint
            )
        ) \
        .count()
    if num_similar_data_stores > 0:
        return JsonResponse({
            'error': "A data store with the same name or api endpoint exists."
        })

    # check if data store info is valid
    try:
        dataset_engine = CkanDatasetEngine(endpoint=data_store_endpoint,
                                           apikey=data_store_api_key)
        result = dataset_engine.list_datasets()
        if not result or "success" not in result:
            return JsonResponse({
                'error': "Data Store Credentials Invalid. "
                         "Password incorrect; "
                         "Endpoint must end in \"api/3/action\""
            })
    except Exception, ex:
        return JsonResponse({ 'error': "%s" % ex })

    # add Data Store
    session.add(
        DataStore(name=data_store_name,
                  owner_org=data_store_owner_org,
                  data_store_type_id=data_store_type_id,
                  api_endpoint=data_store_endpoint,
                  api_key=data_store_api_key,
        )
    )

    session.commit()
    session.close()

    return JsonResponse({ 'success': "Data Store Sucessfully Added!" })


@require_POST
@user_passes_test(user_permission_test)
def data_store_delete(request):
    """
    Controller for deleting a data store.
    """
    # get/check information from AJAX request
    post_info = request.POST
    data_store_id = post_info.get('data_store_id')

    if int(data_store_id) != 1:
        try:
            # initialize session
            session_maker = app.get_persistent_store_database('main_db', as_sessionmaker=True)
            session = session_maker()
            # update data store
            data_store  = session.query(DataStore).get(data_store_id)
            session.delete(data_store)
            session.commit()
            session.close()
        except IntegrityError:
            return JsonResponse({ 'error': "This data store is connected with a watershed! Must remove connection to delete." })
        return JsonResponse({ 'success': "Data Store Sucessfully Deleted!" })
    return JsonResponse({ 'error': "Cannot change this data store." })


@require_POST
@user_passes_test(user_permission_test)
def data_store_update(request):
    """
    Controller for updating a data store.
    """
    # get/check information from AJAX request
    post_info = request.POST
    data_store_id = post_info.get('data_store_id')
    data_store_name = post_info.get('data_store_name')
    data_store_owner_org = post_info.get('data_store_owner_org')
    data_store_api_endpoint = post_info.get('data_store_api_endpoint')
    data_store_api_key = post_info.get('data_store_api_key')

    if int(data_store_id) != 1:
        # initialize session
        session_maker = app.get_persistent_store_database('main_db', as_sessionmaker=True)
        session = session_maker()
        # check to see if duplicate exists
        num_similar_data_stores  = session.query(DataStore) \
            .filter(
                or_(
                    DataStore.name == data_store_name,
                    DataStore.api_endpoint == data_store_api_endpoint
                )
            ) \
            .filter(DataStore.id != data_store_id) \
            .count()
        if num_similar_data_stores > 0:
            session.close()
            return JsonResponse({
                'error': "A data store with the same name "
                         "or api endpoint exists."
            })

        # check if data store info is valid
        try:
            dataset_engine = CkanDatasetEngine(endpoint=data_store_api_endpoint,
                                               apikey=data_store_api_key)
            result = dataset_engine.list_datasets()
            if not result or "success" not in result:
                return JsonResponse({
                    'error': "Data Store Credentials Invalid. "
                             "Endpoint must end in \"api/3/action\""
                })
        except Exception, ex:
            return JsonResponse({ 'error': "%s" % ex })

        # update data store
        data_store  = session.query(DataStore).get(data_store_id)
        data_store.name = data_store_name
        data_store.owner_org = data_store_owner_org
        data_store.api_endpoint= data_store_api_endpoint
        data_store.api_key = data_store_api_key
        session.commit()
        session.close()
        return JsonResponse({ 'success': "Data Store Sucessfully Updated!" })
    return JsonResponse({ 'error': "Cannot change this data store." })


@require_POST
@user_passes_test(user_permission_test)
def geoserver_add(request):
    """
    Controller for adding a geoserver.
    """
    # get/check information from AJAX request
    post_info = request.POST
    geoserver_name = post_info.get('geoserver_name')
    geoserver_url = post_info.get('geoserver_url')
    geoserver_username = post_info.get('geoserver_username')
    geoserver_password = post_info.get('geoserver_password')

    # check data
    if not geoserver_name or not geoserver_url or not \
        geoserver_username or not geoserver_password:
        return JsonResponse({ 'error': "Missing input data." })

    # initialize session
    session_maker = app.get_persistent_store_database('main_db', as_sessionmaker=True)
    session = session_maker()

    # validate geoserver credentials
    app_instance_id = app.get_custom_setting('app_instance_id')
    try:
        geoserver_manager = GeoServerDatasetManager(engine_url=geoserver_url.strip(),
                                                    username=geoserver_username.strip(),
                                                    password=geoserver_password.strip(),
                                                    app_instance_id=app_instance_id)
    except Exception as ex:
        return JsonResponse({'error' : "GeoServer Error: %s" % ex})

    # check to see if duplicate exists
    num_similar_geoservers  = session.query(Geoserver) \
        .filter(
            or_(
                Geoserver.name == geoserver_name,
                Geoserver.url == geoserver_manager.engine_url
            )
        ) \
        .count()
    if num_similar_geoservers > 0:
        session.close()
        return JsonResponse({
            'error': "A geoserver with the same name or url exists."
        })

    # add GeoServer
    session.add(
        Geoserver(name=geoserver_name.strip(),
                  url=geoserver_manager.engine_url,
                  username=geoserver_username.strip(),
                  password=geoserver_password.strip()
        )
    )

    session.commit()
    session.close()
    return JsonResponse({'success': "Geoserver Sucessfully Added!"})


@require_POST
@user_passes_test(user_permission_test)
def geoserver_delete(request):
    """
    Controller for deleting a geoserver.
    """
    # get/check information from AJAX request
    post_info = request.POST
    geoserver_id = post_info.get('geoserver_id')

    # initialize session
    session_maker = app.get_persistent_store_database('main_db', as_sessionmaker=True)
    session = session_maker()
    try:
        # delete geoserver
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


@require_POST
@user_passes_test(user_permission_test)
def geoserver_update(request):
    """
    Controller for updating a geoserver.
    """
    # get/check information from AJAX request
    post_info = request.POST
    geoserver_id = post_info.get('geoserver_id')
    geoserver_name = post_info.get('geoserver_name')
    geoserver_url = post_info.get('geoserver_url')
    geoserver_username = post_info.get('geoserver_username')
    geoserver_password = post_info.get('geoserver_password')
    # check data
    if not geoserver_id or not geoserver_name or not geoserver_url or not \
        geoserver_username or not geoserver_password:
        return JsonResponse({ 'error': "Missing input data." })
    # make sure id is id
    try:
        int(geoserver_id)
    except ValueError:
        return JsonResponse({'error' : 'Geoserver id is faulty.'})


    if int(geoserver_id) != 1:

        # initialize session
        session_maker = app.get_persistent_store_database('main_db', as_sessionmaker=True)
        session = session_maker()
        # validate geoserver credentials
        app_instance_id = app.get_custom_setting('app_instance_id')
        try:
            geoserver_manager = GeoServerDatasetManager(engine_url=geoserver_url.strip(),
                                                        username=geoserver_username.strip(),
                                                        password=geoserver_password.strip(),
                                                        app_instance_id=app_instance_id)
        except Exception as ex:
            return JsonResponse({'error' : "GeoServer Error: %s" % ex})

        # check to see if duplicate exists
        num_similar_geoservers  = session.query(Geoserver) \
          .filter(
                  or_(Geoserver.name == geoserver_name,
                      Geoserver.url == geoserver_manager.engine_url)
                  ) \
          .filter(Geoserver.id != geoserver_id) \
          .count()

        if num_similar_geoservers > 0:
            session.close()
            return JsonResponse({
                'error': "A geoserver with the same name or url exists."
            })

        # update geoserver
        try:
            geoserver = session.query(Geoserver).get(geoserver_id)
        except ObjectDeletedError:
            session.close()
            return JsonResponse({
                'error': "The geoserver to update does not exist."
            })

        geoserver.name = geoserver_name.strip()
        geoserver.url = geoserver_manager.engine_url
        geoserver.username = geoserver_username.strip()
        geoserver.password = geoserver_password.strip()
        session.commit()
        session.close()
        return JsonResponse({'success': "Geoserver sucessfully updated!"})
    return JsonResponse({'error': "Cannot change this geoserver."})


@require_GET
@login_required
def ecmwf_get_avaialable_dates(request):
    """""
    Finds a list of directories with valid data and 
    returns dates in select2 format
    """""
    path_to_rapid_output = app.get_custom_setting('ecmwf_forecast_folder')
    if not os.path.exists(path_to_rapid_output):
        return JsonResponse({
            'error' : 'Location of RAPID output files faulty. '
                      'Please check settings.'
        })

    # get/check information from AJAX request
    get_info = request.GET
    watershed_name = format_name(get_info['watershed_name']) \
        if 'watershed_name' in get_info else None
    subbasin_name = format_name(get_info['subbasin_name']) \
        if 'subbasin_name' in get_info else None
    if not watershed_name or not subbasin_name:
        return JsonResponse({'error' : 'ECMWF AJAX request input faulty'})

    # find/check current output datasets
    path_to_watershed_files = \
        os.path.join(path_to_rapid_output,
                     "{0}-{1}".format(watershed_name, subbasin_name))

    if not os.path.exists(path_to_watershed_files):
        return JsonResponse({
            'error' : 'ECMWF forecast for %s (%s) not found.'
                      % (watershed_name, subbasin_name)
        })

    output_directories = \
        ecmwf_get_valid_forecast_folder_list(path_to_watershed_files, ".nc")
    if len(output_directories)>0:
        return JsonResponse({
                    "success": "Data analysis complete!",
                    "output_directories": output_directories,
                })
    else:
        return JsonResponse({
            'error': 'Recent ECMWF forecasts for %s, %s not found.'
                     % (watershed_name, subbasin_name)
        })


@require_GET
@login_required
def ecmwf_get_hydrograph(request):
    """""
    Plots 52 ECMWF ensembles analysis with min., max., avg. ,std. dev.
    """""
    path_to_rapid_output = app.get_custom_setting('ecmwf_forecast_folder')
    if not os.path.exists(path_to_rapid_output):
        return JsonResponse({
            'error' : 'Location of RAPID output files faulty. '
                      'Please check settings.'
        })

    # get/check information from AJAX request
    get_info = request.GET
    watershed_name = format_name(get_info['watershed_name']) \
                        if 'watershed_name' in get_info else None
    subbasin_name = format_name(get_info['subbasin_name']) \
                        if 'subbasin_name' in get_info else None
    river_id = get_info.get('reach_id')
    start_folder = get_info.get('start_folder')
    if not river_id or not watershed_name or not subbasin_name \
            or not start_folder:
        return JsonResponse({'error' : 'ECMWF AJAX request input faulty.'})

    # make sure reach id is integet
    try:
        river_id = int(river_id)
    except (TypeError, ValueError):
        return JsonResponse({'error' : 'Invalid River ID %s.' % river_id})

    # find/check current output datasets
    path_to_output_files = \
        os.path.join(path_to_rapid_output,
                     "{0}-{1}".format(watershed_name, subbasin_name))
    forecast_nc_list, start_date = \
        ecmwf_find_most_current_files(path_to_output_files, start_folder)
    if not forecast_nc_list or not start_date:
        return JsonResponse(
            {'error' : 'ECMWF forecast for %s (%s) not found.'
                       % (watershed_name, subbasin_name)
             }
        )
    try:
        forecast_statistics = \
            ecmwf_get_forecast_statistics(forecast_nc_list, river_id)
    except IndexError:
        return JsonResponse({
            'error' : 'ECMWF River ID %s not found.'
                       % river_id
        })

    # extract the high res ensemble & time
    hres_return_data = None
    if 'high_res' in forecast_statistics:
        hres_time = (forecast_statistics['high_res']
                     .time.values.astype('int64')/1e6).tolist()
        hres_return_data = zip(hres_time, forecast_statistics['high_res']
                               .values.tolist())

    # analyze data to get statistic bands
    mean_ar = forecast_statistics['mean'].values.tolist()
    min_ar = forecast_statistics['min'].values.tolist()
    max_ar = forecast_statistics['max'].values.tolist()
    std_dev_range_upper = forecast_statistics['std_dev_range_upper']\
                              .values.tolist()
    std_dev_range_lower = forecast_statistics['std_dev_range_lower']\
                              .values.tolist()

    # conver time to miliseconds
    low_res_time = (forecast_statistics['mean']
                    .time.values.astype('int64')/1e6).tolist()

    # return JSON response with data
    return_data = {
        "mean": zip(low_res_time, mean_ar),
        "outer_range": zip(low_res_time, min_ar, max_ar),
        "std_dev_range": zip(low_res_time, std_dev_range_lower,
                             std_dev_range_upper),
        "success": "ECMWF Data analysis complete!"
    }
    if hres_return_data:
        return_data['high_res'] = hres_return_data
    return JsonResponse(return_data)


@require_GET
@login_required                     
def era_interim_get_hydrograph(request):
    """""
    Returns ERA Interim hydrograph
    """""
    path_to_era_interim_data = app.get_custom_setting('historical_folder')
    if not os.path.exists(path_to_era_interim_data):
        return JsonResponse({
            'error' : 'Location of ERA-Interim files faulty. '
                      'Please check settings.'
        })

    # get information from GET request
    get_info = request.GET
    watershed_name = format_name(get_info['watershed_name']) \
        if 'watershed_name' in get_info else None
    subbasin_name = format_name(get_info['subbasin_name']) \
        if 'subbasin_name' in get_info else None
    reach_id = get_info.get('reach_id')
    if not reach_id or not watershed_name or not subbasin_name:
        return JsonResponse({
            'error' : 'ERA Interim AJAX request input faulty.'
        })

    # make sure reach id is integet
    try:
        reach_id = int(reach_id)
    except (TypeError, ValueError):
        return JsonResponse({'error' : 'Invalid Reach ID %s.' % reach_id})

    # ----------------------------------------------
    # HISTORICAL DATA SECTION
    # ----------------------------------------------
    era_interim_return_data = {}
    # find/check current output datasets
    path_to_output_files = \
        os.path.join(path_to_era_interim_data,
                     "{0}-{1}".format(watershed_name, subbasin_name))
    historical_data_files = glob(os.path.join(path_to_output_files, "Qout*.nc"))
    if historical_data_files:
        try:
            # get/check the index of the reach
            with RAPIDDataset(historical_data_files[0]) as qout_nc:
                # get/check the index of the reach
                reach_index = qout_nc.get_river_index(reach_id)
                # get information from dataset
                data_values = qout_nc.get_qout_index(reach_index)
                time = [t*1000 for t in qout_nc.get_time_array()]
                era_interim_return_data['series'] = \
                    zip(time, data_values.tolist())
        except IndexError:
            era_interim_return_data['error'] = \
                'ERA Interim reach with ID: %s not found.' % reach_id
            pass
        except Exception:
            era_interim_return_data['error'] = \
                "Invalid ERA-Interim file ..."
            pass

    else:
        era_interim_return_data['error'] = \
            'ERA Interim data for %s (%s) not found.' \
            % (watershed_name, subbasin_name)

    # ----------------------------------------------
    # RETURN PERIOD SECTION
    # ----------------------------------------------
    return_period_return_data = {}
    return_period_files = glob(os.path.join(path_to_output_files,
                                            "return_period*.nc"))
    if return_period_files:

        return_period_file = return_period_files[0]
        # get/check the index of the reach
        error_found = False
        if not error_found:
            # get information from dataset
            try:
                with xarray.open_dataset(return_period_file) \
                        as return_period_nc:
                    rpd = return_period_nc.sel(rivid=reach_id)
                    return_period_return_data["max"] = str(rpd.max_flow.values)
                    return_period_return_data["twenty"] = \
                        str(rpd.return_period_20.values)
                    return_period_return_data["ten"] = \
                        str(rpd.return_period_10.values)
                    return_period_return_data["two"] = \
                        str(rpd.return_period_10.values)
            except IndexError:
                return_period_return_data['error'] = \
                    'Return period for reach with ID: %s not found.' \
                    % reach_id
                pass

            except Exception:
                return_period_return_data['error'] = \
                    "Invalid return period file"
                pass

    else:
        return_period_return_data['error'] = \
            'ERA Interim return period data for %s (%s) not found.' % \
            (watershed_name, subbasin_name)


    return JsonResponse({
        'success': "ERA-Interim data analysis complete!",
        'era_interim': era_interim_return_data,
        'return_period': return_period_return_data
    })


@require_GET
@login_required
def generate_warning_points(request):
    """
    Controller for getting warning points for user on map
    """
    path_to_ecmwf_rapid_output = app.get_custom_setting('ecmwf_forecast_folder')
    path_to_era_interim_data = app.get_custom_setting('historical_folder')
    if not os.path.exists(path_to_ecmwf_rapid_output) \
            or not os.path.exists(path_to_era_interim_data):
        return JsonResponse({
            'error' : 'Location of RAPID output files faulty. '
                      'Please check settings.'
        })

    # get/check information from AJAX request
    get_info = request.GET
    watershed_name = format_name(get_info['watershed_name']) \
        if 'watershed_name' in get_info else None
    subbasin_name = format_name(get_info['subbasin_name']) \
        if 'subbasin_name' in get_info else None
    return_period = get_info.get('return_period')
    forecast_folder = get_info.get('forecast_folder')
    if not watershed_name or not subbasin_name or not return_period:
        return JsonResponse({'error' : 'Warning point request input faulty.'})

    try:
        return_period = int(return_period)
    except (TypeError, ValueError):
        return JsonResponse({'error' : 'Invalid return period.'})

    path_to_output_files = \
        os.path.join(path_to_ecmwf_rapid_output,
                     "{0}-{1}".format(watershed_name, subbasin_name))

    # attempt to find forecast folder for watershed
    if not forecast_folder:
        if not os.path.exists(path_to_output_files):
            return JsonResponse({'error' : 'No files found for watershed.'})

        directory_list = \
            sorted([d for d in os.listdir(path_to_output_files) \
                    if os.path.isdir(os.path.join(path_to_output_files, d))],
                    reverse=True)
        if directory_list:
            forecast_folder = directory_list[0]

    if not forecast_folder:
        return JsonResponse({
            'error' : 'No forecasts found with {0} '
                      'return period warning points.'.format(return_period)
        })

    # get warning points to load in
    if return_period == 20:
        warning_points_file = os.path.join(path_to_output_files,forecast_folder,
                                           "return_20_points.txt")
    elif return_period == 10:
        warning_points_file = os.path.join(path_to_output_files,forecast_folder,
                                           "return_10_points.txt")
    elif return_period == 2:
        warning_points_file = os.path.join(path_to_output_files,forecast_folder,
                                           "return_2_points.txt")
    else:
        return JsonResponse({'error' : 'Invalid return period.'})

    if not os.path.exists(warning_points_file):
        return JsonResponse({'error' : 'Warning points file not found.'})

    with open(warning_points_file, 'rb') as infile:
        warning_points = json_load(infile)

    return JsonResponse({
        'success': "Warning Points Sucessfully Returned!",
        'warning_points' : warning_points,
    })


@require_GET
@login_required                     
def era_interim_get_csv(request):
    """""
    Returns ERA Interim data as csv
    """""
    path_to_era_interim_data = app.get_custom_setting('historical_folder')
    if not os.path.exists(path_to_era_interim_data):
        raise Http404('Location of ERA-Interim files faulty. '
                      'Please check settings.')

    # get information from GET request
    get_info = request.GET
    watershed_name = format_name(get_info['watershed_name']) \
        if 'watershed_name' in get_info else None
    subbasin_name = format_name(get_info['subbasin_name']) \
        if 'subbasin_name' in get_info else None
    reach_id = get_info.get('reach_id')
    daily = get_info.get('daily') if 'daily' in get_info else ''
    if not reach_id or not watershed_name or not subbasin_name:
        return JsonResponse({
            'error' : 'ERA Interim AJAX request input faulty.'
        })

    # make sure reach id is integet
    try:
        reach_id = int(reach_id)
    except (TypeError, ValueError):
        raise Http404('Invalid Reach ID %s.' % reach_id)

    # find/check current output datasets
    path_to_output_files = \
        os.path.join(path_to_era_interim_data,
                     "{0}-{1}".format(watershed_name, subbasin_name))
    historical_data_files = glob(os.path.join(path_to_output_files, "Qout*.nc"))
    if historical_data_files:
        try:
            # get/check the index of the reach
            with RAPIDDataset(historical_data_files[0]) as qout_nc:
                # get/check the index of the reach
                reach_index = qout_nc.get_river_index(reach_id)

                # get information from dataset
                response = HttpResponse(content_type='text/csv')
                response['Content-Disposition'] = \
                    'attachment; filename=streamflow_{0}_{1}_{2}.csv'\
                    .format(watershed_name,
                            subbasin_name,
                            reach_id)

                writer = csv_writer(response)
                writer.writerow(['datetime', 'streamflow (m3/s)'])
                if daily.lower() == 'true':
                    #return daily values
                    daily_time_index_array = \
                        qout_nc.get_daily_time_index_array()
                    data_values = \
                        qout_nc.get_daily_qout_index(reach_index,
                                                     daily_time_index_array)
                    datetime_array = \
                        qout_nc.get_time_array(return_datetime=True)
                    for index, daily_time_index in\
                            enumerate(daily_time_index_array):
                        writer.writerow([datetime_array[daily_time_index],
                                         data_values[index]])
                else:
                    #return raw data
                    data_values = qout_nc.get_qout_index(reach_index)
                    datetime_array = \
                        qout_nc.get_time_array(return_datetime=True)
                    for index, data_value in enumerate(data_values):
                        writer.writerow([datetime_array[index], data_value])

                return response

        except IndexError:
            raise Http404('ERA Interim reach with ID: %s not found.'
                          % reach_id)
        except Exception:
            raise Http404("Invalid ERA-Interim file ...")

    raise Http404('ERA Interim data for %s (%s) not found.'
                  % (watershed_name, subbasin_name))


@require_GET
@login_required                     
def get_seasonal_streamflow(request):
    """""
    Returns seasonal streamflow for unique river ID
    """""
    path_to_era_interim_data = app.get_custom_setting('historical_folder')
    if not os.path.exists(path_to_era_interim_data):
        raise Http404('Location of ERA-Interim files faulty. '
                      'Please check settings.')

    # get information from GET request
    get_info = request.GET
    watershed_name = format_name(get_info['watershed_name']) \
        if 'watershed_name' in get_info else None
    subbasin_name = format_name(get_info['subbasin_name']) if \
        'subbasin_name' in get_info else None
    reach_id = get_info.get('reach_id')
    if not reach_id or not watershed_name or not subbasin_name:
        return JsonResponse({
            'error' : 'ERA Interim AJAX request input faulty.'
        })

    # make sure reach id is integer
    try:
        reach_id = int(reach_id)
    except (TypeError, ValueError):
        raise Http404('Invalid Reach ID %s.' % reach_id)

    # find/check current output datasets
    path_to_output_files = \
        os.path.join(path_to_era_interim_data,
                     "{0}-{1}".format(watershed_name, subbasin_name))
    seasonal_data_files = glob(os.path.join(path_to_output_files,
                                            "seasonal_average*.nc"))
    if seasonal_data_files:
        try:
            seasonal_nc = NET.Dataset(seasonal_data_files[0])
            rivid_index = np.where(seasonal_nc.variables['rivid'][:]
                                   == reach_id)[0][0]

            season_avg = seasonal_nc.variables['average_flow'][rivid_index,:]
            season_std = seasonal_nc.variables['std_dev_flow'][rivid_index,:]

            avg_plus_std = season_avg + season_std
            avg_min_std = season_avg - season_std

            season_avg[season_avg < 0] = 0
            avg_plus_std[avg_plus_std <0] = 0
            avg_min_std[avg_min_std < 0] = 0

            return JsonResponse({
                'season_avg': season_avg.tolist(),
                'std_range': zip(avg_min_std.tolist(), avg_plus_std.tolist()),
            })

        except IndexError:
            raise Http404('Seasonal Average reach with ID: %s not found.'
                          % reach_id)
        except Exception as ex:
            raise Http404("Invalid Seasonal Average file ... {0}".format(ex))

    raise Http404('Seasonal Average data for %s (%s) not found.' %
                  (watershed_name, subbasin_name))

@require_POST
@user_passes_test(user_permission_test)
def watershed_add(request):
    """
    Controller for adding a watershed.
    """
    post_info = request.POST
    # get/check information from AJAX request
    watershed_name = post_info.get('watershed_name')
    subbasin_name = post_info.get('subbasin_name')
    watershed_clean_name = format_name(watershed_name)
    subbasin_clean_name = format_name(subbasin_name)
    data_store_id = post_info.get('data_store_id')
    geoserver_id = post_info.get('geoserver_id')
    # REQUIRED TO HAVE drainage_line from one of these
    # layer names
    geoserver_drainage_line_layer_name = \
        post_info.get('geoserver_drainage_line_layer')
    geoserver_boundary_layer_name = post_info.get('geoserver_boundary_layer')
    geoserver_gage_layer_name = post_info.get('geoserver_gage_layer')
    geoserver_historical_flood_map_layer_name = \
        post_info.get('geoserver_historical_flood_map_layer')
    geoserver_ahps_station_layer_name = \
        post_info.get('geoserver_ahps_station_layer')
    # shape files
    drainage_line_shp_file = request.FILES.getlist('drainage_line_shp_file')
    # CHECK DATA
    # make sure information exists
    if not watershed_name or not subbasin_name or not data_store_id \
        or not geoserver_id or not watershed_clean_name or not subbasin_clean_name:
        return JsonResponse({'error' : 'Request input missing data.'})
    # make sure ids are ids
    try:
        int(data_store_id)
        int(geoserver_id)
    except ValueError:
        return JsonResponse({'error' : 'One or more ids are faulty.'})

    # check ECMWF inputs
    ecmwf_rapid_input_resource_id = ""

    ecmwf_data_store_watershed_name = \
        format_name(post_info.get('ecmwf_data_store_watershed_name'))
    ecmwf_data_store_subbasin_name = \
        format_name(post_info.get('ecmwf_data_store_subbasin_name'))

    if not ecmwf_data_store_watershed_name \
            or not ecmwf_data_store_subbasin_name:
        return JsonResponse({
            'error' : "Must have an ECMWF watershed and "
                      "subbasin name to continue."
        })

    # initialize session
    session_maker = app.get_persistent_store_database('main_db',
                                                      as_sessionmaker=True)
    session = session_maker()

    # check to see if duplicate exists
    num_similar_watersheds  = session.query(Watershed) \
        .filter(Watershed.watershed_clean_name == watershed_clean_name) \
        .filter(Watershed.subbasin_clean_name == subbasin_clean_name) \
        .count()
    if num_similar_watersheds > 0:
        session.close()
        return JsonResponse({'error': "A watershed with the same name exists."})

    # validate geoserver inputs
    if not drainage_line_shp_file and not geoserver_drainage_line_layer_name:
        session.close()
        return JsonResponse({'error': 'Missing geoserver drainage line.'})

    # get desired geoserver
    try:
        geoserver  = session.query(Geoserver).get(geoserver_id)
    except ObjectDeletedError:
        session.close()
        return JsonResponse({'error': "The geoserver does not exist."})
    try:
        app_instance_id = app.get_custom_setting('app_instance_id')
        geoserver_manager = \
            GeoServerDatasetManager(engine_url=geoserver.url,
                                    username=geoserver.username,
                                    password=geoserver.password,
                                    app_instance_id=app_instance_id)
    except Exception as ex:
        session.close()
        return JsonResponse({'error': "GeoServer Error: %s" % ex})

    # GEOSERVER UPLOAD
    # check geoserver input before upload
    if drainage_line_shp_file:
        geoserver_drainage_line_layer_name = \
            "%s-%s-%s" % (watershed_clean_name, subbasin_clean_name,
                          'drainage_line')
        # check shapefles
        try:
            geoserver_manager\
                .check_shapefile_input_files(drainage_line_shp_file)
        except Exception as ex:
            session.close()
            return JsonResponse({
                'error' : 'Drainage Line layer upload error: %s.' % ex
            })

    # UPLOAD DRAINAGE LINE
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


    # UPDATE BOUNDARY
    try:
        geoserver_boundary_layer = \
            update_geoserver_layer(None,
                                   geoserver_boundary_layer_name,
                                   None,
                                   geoserver_manager,
                                   session,
                                   layer_required=False)
    except Exception as ex:
        session.close()
        return JsonResponse({'error' : "Boundary layer update error: %s" % ex})

    # UPDATE GAGE
    try:
        geoserver_gage_layer = \
            update_geoserver_layer(None,
                                   geoserver_gage_layer_name,
                                   None,
                                   geoserver_manager,
                                   session,
                                   layer_required=False)
    except Exception as ex:
        session.close()
        return JsonResponse({'error' : "Gage layer update error: %s" % ex})

    # UPDATE HISTORICAL FLOOD MAP LAYER GROUP
    try:
        geoserver_historical_flood_map_layer = \
            update_geoserver_layer(None,
                                   geoserver_historical_flood_map_layer_name,
                                   None,
                                   geoserver_manager,
                                   session,
                                   layer_required=False,
                                   is_layer_group=True)
    except Exception as ex:
        session.close()
        return JsonResponse({'error' : "Historical Flood Map layer update error: %s" % ex})

    # UPDATE AHPS STATION
    try:
        geoserver_ahps_station_layer = \
            update_geoserver_layer(None,
             geoserver_ahps_station_layer_name,
             None,
             geoserver_manager,
             session,
             layer_required=False)
    except Exception as ex:
        session.close()
        return JsonResponse({'error' : "AHPS Station layer update error: %s" % ex})

    # add watershed
    watershed = \
        Watershed(
            watershed_name=watershed_name.strip(),
            subbasin_name=subbasin_name.strip(),
            watershed_clean_name=watershed_clean_name,
            subbasin_clean_name=subbasin_clean_name,
            data_store_id=data_store_id,
            ecmwf_rapid_input_resource_id=ecmwf_rapid_input_resource_id,
            ecmwf_data_store_watershed_name=ecmwf_data_store_watershed_name.strip(),
            ecmwf_data_store_subbasin_name=ecmwf_data_store_subbasin_name.strip(),
            geoserver_id=geoserver_id,
            geoserver_drainage_line_layer=geoserver_drainage_line_layer,
            geoserver_boundary_layer=geoserver_boundary_layer,
            geoserver_gage_layer=geoserver_gage_layer,
            geoserver_historical_flood_map_layer=geoserver_historical_flood_map_layer,
            geoserver_ahps_station_layer=geoserver_ahps_station_layer,
        )

    session.add(watershed)
    session.commit()

    # get watershed_id
    response = {
                'success': "Watershed Sucessfully Added!",
                'watershed_id' : watershed.id,
                'geoserver_drainage_line_layer': geoserver_drainage_line_layer.name \
                    if geoserver_drainage_line_layer else geoserver_drainage_line_layer_name,
                }
    session.close()

    return JsonResponse(response)


@require_POST
@user_passes_test(user_permission_test)    
def watershed_ecmwf_rapid_file_upload(request):
    """
    Controller AJAX for uploading RAPID input files for a watershed.
    """
    watershed_id = request.POST.get('watershed_id')
    ecmwf_rapid_input_file = request.FILES.get('ecmwf_rapid_input_file')

    # make sure id is int
    try:
        int(watershed_id)
    except ValueError:
        return JsonResponse({'error' : 'Watershed ID need to be an integer.'})
    # initialize session
    session_maker = app.get_persistent_store_database('main_db',
                                                      as_sessionmaker=True)
    session = session_maker()
    watershed = session.query(Watershed).get(watershed_id)

    # Upload file to Data Store Server
    if int(watershed.data_store_id) > 1 and ecmwf_rapid_input_file:
        # temporarily upload to Tethys Plarform server
        tmp_file_location = \
            os.path.join(os.path.dirname(os.path.realpath(__file__)),
                         'workspaces', 'app_workspace')

        ecmwf_rapid_input_zip = \
            "%s-%s-rapid.zip" % (watershed.ecmwf_data_store_watershed_name,
                                 watershed.ecmwf_data_store_subbasin_name)
        local_file_path = os.path.join(tmp_file_location, ecmwf_rapid_input_zip)

        # delete local file
        try:
            os.remove(local_file_path)
        except OSError:
            pass

        handle_uploaded_file(ecmwf_rapid_input_file,
                             tmp_file_location,
                             ecmwf_rapid_input_zip)
        # upload file to CKAN server
        app_instance_id = app.get_custom_setting('app_instance_id')
        data_manager = \
            RAPIDInputDatasetManager(watershed.data_store.api_endpoint,
                                     watershed.data_store.api_key,
                                     "ecmwf",
                                     app_instance_id,
                                     watershed.data_store.owner_org)

        # remove RAPID input files on CKAN if exists
        if watershed.ecmwf_rapid_input_resource_id.strip():
            data_manager.dataset_engine.delete_resource(
                watershed.ecmwf_rapid_input_resource_id
            )

        # upload file to CKAN
        try:
            resource_info = \
                data_manager.upload_model_resource(
                    local_file_path,
                    watershed.ecmwf_data_store_watershed_name,
                    watershed.ecmwf_data_store_subbasin_name
                )
        except Exception:
            # delete local file
            try:
                os.remove(local_file_path)
            except OSError:
                pass
            session.close()
            return JsonResponse({
                'error' : 'Problem uploading ECMWF-RAPID dataset to CKAN.'
            })

        # delete local file
        try:
            os.remove(local_file_path)
        except OSError:
            pass

        # update watershed
        watershed.ecmwf_rapid_input_resource_id = resource_info['result']['id']
        session.commit()
    else:
        session.close()
        return JsonResponse({'error' : 'Watershed datastore ID or upload file invalid.'})
    session.close()
    return JsonResponse({'success' : 'ECMWF RAPID Input Upload Success!'})


@require_POST
@user_passes_test(user_permission_test)
def watershed_delete(request):
    """
    Controller for deleting a watershed.
    """
    # get/check information from AJAX request
    post_info = request.POST
    watershed_id = post_info.get('watershed_id')
    # make sure ids are ids
    try:
        int(watershed_id)
    except (TypeError, ValueError):
        return JsonResponse({'error' : 'Watershed id is faulty.'})

    if watershed_id:
        # initialize session
        session_maker = app.get_persistent_store_database('main_db',
                                                          as_sessionmaker=True)
        session = session_maker()
        # get watershed to delete
        try:
            watershed  = session.query(Watershed).get(watershed_id)
        except ObjectDeletedError:
            return JsonResponse({
                'error': "The watershed to delete does not exist."
            })

        # remove watershed geoserver, local prediction files, RAPID Input Files
        ecmwf_rapid_prediction_directory = \
            app.get_custom_setting('ecmwf_forecast_folder')

        delete_old_watershed_files(watershed)

        delete_from_database(session, watershed)
        # NOTE: CASCADE removes associated geoserver layers

        # delete watershed from database
        session.commit()
        session.close()

        return JsonResponse({'success': "Watershed sucessfully deleted!"})
    return JsonResponse({'error': "Cannot delete this watershed."})


@require_POST
@user_passes_test(user_permission_test)
def watershed_update(request):
    """
    Controller for updating a watershed.
    """
    post_info = request.POST
    # get/check information from AJAX request
    watershed_id = post_info.get('watershed_id')
    watershed_name = post_info.get('watershed_name')
    subbasin_name = post_info.get('subbasin_name')
    watershed_clean_name = format_name(watershed_name)
    subbasin_clean_name = format_name(subbasin_name)
    data_store_id = post_info.get('data_store_id')
    geoserver_id = post_info.get('geoserver_id')
    # REQUIRED TO HAVE drainage_line from one of these
    # layer names
    geoserver_drainage_line_layer_name = post_info.get('geoserver_drainage_line_layer')
    geoserver_boundary_layer_name = post_info.get('geoserver_boundary_layer')
    geoserver_gage_layer_name = post_info.get('geoserver_gage_layer')
    geoserver_historical_flood_map_layer_name = post_info.get('geoserver_historical_flood_map_layer')
    geoserver_ahps_station_layer_name = post_info.get('geoserver_ahps_station_layer')
    # shape files
    drainage_line_shp_file = request.FILES.getlist('drainage_line_shp_file')
    boundary_shp_file = request.FILES.getlist('boundary_shp_file')
    gage_shp_file = request.FILES.getlist('gage_shp_file')
    ahps_station_shp_file = request.FILES.getlist('ahps_station_shp_file')
    # CHECK INPUT
    # check if variables exist
    if not watershed_id or not watershed_name or not subbasin_name or not data_store_id \
        or not geoserver_id or not watershed_clean_name or not subbasin_clean_name:
        return JsonResponse({'error' : 'Request input missing data.'})
    # make sure ids are ids
    try:
        int(watershed_id)
        int(data_store_id)
        int(geoserver_id)
    except (TypeError, ValueError):
        return JsonResponse({'error' : 'One or more ids are faulty.'})

    # initialize session
    session_maker = app.get_persistent_store_database('main_db', as_sessionmaker=True)
    session = session_maker()
    # check to see if duplicate exists
    num_similar_watersheds  = session.query(Watershed) \
        .filter(Watershed.watershed_clean_name == watershed_clean_name) \
        .filter(Watershed.subbasin_clean_name == subbasin_clean_name) \
        .filter(Watershed.id != watershed_id) \
        .count()
    if num_similar_watersheds > 0:
        session.close()
        return JsonResponse({ 'error': "A watershed with the same name exists." })

    # get desired watershed
    try:
        watershed  = session.query(Watershed).get(watershed_id)
    except ObjectDeletedError:
        session.close()
        return JsonResponse({ 'error': "The watershed to update does not exist." })
    # get desired geoserver
    try:
        geoserver  = session.query(Geoserver).get(geoserver_id)
    except ObjectDeletedError:
        session.close()
        return JsonResponse({ 'error': "The geoserver does not exist." })


    # check ecmwf inputs
    ecmwf_data_store_watershed_name = format_name(post_info.get('ecmwf_data_store_watershed_name'))
    ecmwf_data_store_subbasin_name = format_name(post_info.get('ecmwf_data_store_subbasin_name'))

    if not ecmwf_data_store_watershed_name or not ecmwf_data_store_subbasin_name:
        session.close()
        return JsonResponse({'error' : "Must have an ECMWF watershed/subbasin name to continue" })

    # GEOSERVER SECTION
    # remove old geoserver files if geoserver changed
    if int(geoserver_id) != watershed.geoserver_id:
       # remove old geoserver files
       delete_old_watershed_geoserver_files(watershed)


    # validate geoserver inputs
    if not drainage_line_shp_file and not geoserver_drainage_line_layer_name:
        session.close()
        return JsonResponse({'error' : 'Missing geoserver drainage line.'})

    try:
        app_instance_id = app.get_custom_setting('app_instance_id')
        geoserver_manager = GeoServerDatasetManager(engine_url=geoserver.url,
                                                    username=geoserver.username,
                                                    password=geoserver.password,
                                                    app_instance_id=app_instance_id)
    except Exception as ex:
        session.close()
        return JsonResponse({'error' : "GeoServer Error: %s" % ex})

    # check geoserver input before upload
    if drainage_line_shp_file:
        geoserver_drainage_line_layer_name = "%s-%s-%s" % (watershed_clean_name, subbasin_clean_name, 'drainage_line')
        # check permissions to upload file
        if watershed.geoserver_drainage_line_layer:
            if not watershed.geoserver_drainage_line_layer.uploaded and \
                watershed.geoserver_drainage_line_layer.name == geoserver_manager.get_layer_name(geoserver_drainage_line_layer_name):
                session.close()
                return JsonResponse({'error' : 'You do not have permissions to overwrite the drainage line layer ...' })

        # check shapefles
        try:
            geoserver_manager.check_shapefile_input_files(drainage_line_shp_file)
        except Exception as ex:
            session.close()
            return JsonResponse({'error' : 'Drainage Line Error: %s.' % ex })

    if boundary_shp_file:
        geoserver_boundary_layer_name = "%s-%s-%s" % (watershed_clean_name, subbasin_clean_name, 'boundary')
        # check permissions to upload file
        if watershed.geoserver_boundary_layer:
            if not watershed.geoserver_boundary_layer.uploaded and \
                watershed.geoserver_boundary_layer.name == geoserver_manager.get_layer_name(geoserver_boundary_layer_name):
                session.close()
                return JsonResponse({'error' : 'You do not have permissions to overwrite the boundary layer ...' })

        # check shapefiles
        try:
            geoserver_manager.check_shapefile_input_files(boundary_shp_file)
        except Exception as ex:
            session.close()
            return JsonResponse({'error' : 'Boundary Error: %s.' % ex })

    if gage_shp_file:
        geoserver_gage_layer_name = "%s-%s-%s" % (watershed_clean_name, subbasin_clean_name, 'gage')
        # check permissions to upload file
        if watershed.geoserver_gage_layer:
            if not watershed.geoserver_gage_layer.uploaded and \
                watershed.geoserver_gage_layer.name == geoserver_manager.get_layer_name(geoserver_gage_layer_name):
                session.close()
                return JsonResponse({'error' : 'You do not have permissions to overwrite the gage layer ...' })

        # check shapefiles
        try:
            geoserver_manager.check_shapefile_input_files(gage_shp_file)
        except Exception as ex:
            session.close()
            return JsonResponse({'error' : 'Gage Error: %s.' % ex })

    if ahps_station_shp_file:
        geoserver_ahps_station_layer_name = "%s-%s-%s" % (watershed_clean_name, subbasin_clean_name, 'ahps_station')
        # check permissions to upload file
        if watershed.geoserver_ahps_station_layer:
            if not watershed.geoserver_ahps_station_layer.uploaded and \
                watershed.geoserver_ahps_station_layer.name == geoserver_manager.get_layer_name(geoserver_ahps_station_layer_name):
                session.close()
                return JsonResponse({'error' : 'You do not have permissions to overwrite the AHPS station layer ...' })

        # check shapefiles
        try:
            geoserver_manager.check_shapefile_input_files(ahps_station_shp_file)
        except Exception as ex:
            session.close()
            return JsonResponse({'error' : 'AHPS Station Error: %s.' % ex })

    # UPDATE DRAINAGE LINE
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


    # UPDATE Boundary
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

    # UPDATE GAGE
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

    # UPDATE HISTORICAL FLOOD MAP LAYER GROUP
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

    # UPDATE AHPS STATION
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

    # remove old prediction files if watershed/subbasin name changed
    if(ecmwf_data_store_watershed_name != watershed.ecmwf_data_store_watershed_name or
       ecmwf_data_store_subbasin_name != watershed.ecmwf_data_store_subbasin_name):
        delete_old_watershed_prediction_files(watershed)
        # remove RAPID input files on CKAN if exists
        try:
            delete_rapid_input_ckan(watershed)
        except Exception as ex:
            session.close()
            return JsonResponse({'error' : "Invalid CKAN instance %s. Cannot delete RAPID input files on CKAN: %s" \
                                            % (watershed.data_store.api_endpoint, ex)})


    # remove CKAN files on old CKAN instance
    if watershed.data_store_id != data_store_id:
        # remove RAPID input files on CKAN if exists
        try:
            delete_rapid_input_ckan(watershed)
        except Exception as ex:
            session.close()
            return JsonResponse({'error' : "Invalid CKAN instance %s. Cannot delete RAPID input files on CKAN: %s" \
                                            % (watershed.data_store.api_endpoint, ex)})

    # change watershed attributes
    watershed.watershed_name = watershed_name.strip()
    watershed.subbasin_name = subbasin_name.strip()
    watershed.watershed_clean_name = watershed_clean_name
    watershed.subbasin_clean_name = subbasin_clean_name
    watershed.data_store_id = data_store_id
    watershed.ecmwf_data_store_watershed_name = ecmwf_data_store_watershed_name
    watershed.ecmwf_data_store_subbasin_name = ecmwf_data_store_subbasin_name
    watershed.geoserver_id = geoserver_id


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

    # update database
    session.commit()
    session.close()

    return JsonResponse(response)


@require_POST
@user_passes_test(user_permission_test)
def watershed_group_add(request):
    """
    Controller for adding a watershed_group.
    """
    # get/check information from AJAX request
    post_info = request.POST
    watershed_group_name = post_info.get('watershed_group_name')
    watershed_group_watershed_ids = \
        post_info.getlist('watershed_group_watershed_ids[]')
    if not watershed_group_name or not watershed_group_watershed_ids:
        return JsonResponse({ 'error': 'AJAX request input faulty' })
    # initialize session
    session_maker = app.get_persistent_store_database('main_db',
                                                      as_sessionmaker=True)
    session = session_maker()

    # check to see if duplicate exists
    num_similar_watershed_groups  = session.query(WatershedGroup) \
        .filter(WatershedGroup.name == watershed_group_name) \
        .count()
    if num_similar_watershed_groups > 0:
        return JsonResponse({'error': "A watershed group with the same name."})

    # add Watershed Group
    group = WatershedGroup(name=watershed_group_name)

    # update watersheds
    watersheds  = session.query(Watershed) \
            .filter(Watershed.id.in_(watershed_group_watershed_ids)) \
            .all()
    for watershed in watersheds:
        group.watersheds.append(watershed)
    session.add(group)
    session.commit()
    session.close()

    return JsonResponse({'success': "Watershed group sucessfully added!"})


@require_POST
@user_passes_test(user_permission_test)
def watershed_group_delete(request):
    """
    Controller for deleting a watershed group.
    """
    # get/check information from AJAX request
    post_info = request.POST
    watershed_group_id = post_info.get('watershed_group_id')


    if watershed_group_id:
        # initialize session
        session_maker = app.get_persistent_store_database('main_db', as_sessionmaker=True)
        session = session_maker()
        # get watershed group to delete
        watershed_group  = session.query(WatershedGroup).get(watershed_group_id)

        # delete watershed group from database
        session.delete(watershed_group)
        session.commit()
        session.close()

        return JsonResponse({ 'success': "Watershed group sucessfully deleted!" })
    return JsonResponse({ 'error': "Cannot delete this watershed group." })


@require_POST
@user_passes_test(user_permission_test)
def watershed_group_update(request):
    """
    Controller for updating a watershed_group.
    """
    # get/check information from AJAX request
    post_info = request.POST
    watershed_group_id = post_info.get('watershed_group_id')
    watershed_group_name = post_info.get('watershed_group_name')
    watershed_group_watershed_ids = \
        post_info.getlist('watershed_group_watershed_ids[]')
    if watershed_group_id and watershed_group_name and \
            watershed_group_watershed_ids:
        # initialize session
        session_maker = app.get_persistent_store_database('main_db',
                                                          as_sessionmaker=True)
        session = session_maker()
        # check to see if duplicate exists
        num_similar_watershed_groups  = session.query(WatershedGroup) \
            .filter(WatershedGroup.name == watershed_group_name) \
            .filter(WatershedGroup.id != watershed_group_id) \
            .count()
        if num_similar_watershed_groups > 0:
            return JsonResponse({
                'error': "A watershed group with the same name exists."
            })

        # get watershed group
        watershed_group  = session.query(WatershedGroup).get(watershed_group_id)
        watershed_group.name = watershed_group_name
        # find new watersheds
        new_watersheds  = session.query(Watershed) \
                .filter(Watershed.id.in_(watershed_group_watershed_ids)) \
                .all()

        # remove old watersheds
        for watershed in watershed_group.watersheds:
            if watershed not in new_watersheds:
                watershed_group.watersheds.remove(watershed)

        # add new watersheds
        for watershed in new_watersheds:
            if watershed not in watershed_group.watersheds:
                watershed_group.watersheds.append(watershed)

        session.commit()
        session.close()
        return JsonResponse({
            'success': "Watershed group successfully updated."
        })
    return JsonResponse({'error': "Data missing for this watershed group."})
