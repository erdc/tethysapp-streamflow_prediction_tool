# -*- coding: utf-8 -*-
"""controllers_ajax.py

    Created by Alan D. Snow, Curtis Rae, Shawn Crawley 2015.
    License: BSD 3-Clause
"""
from csv import writer as csv_writer
import datetime
from json import load as json_load
import os

import numpy as np
import pandas as pd
import plotly.graph_objs as go
import scipy.stats as sp
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import ObjectDeletedError
import xarray

# django imports
from django.contrib.auth.decorators import user_passes_test, login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST

# tethys imports
from tethys_sdk.gizmos import PlotlyView
from tethys_dataset_services.engines import CkanDatasetEngine

# local imports
from spt_dataset_manager.dataset_manager import (GeoServerDatasetManager,
                                                 RAPIDInputDatasetManager)

from .exception_handling import (DatabaseError, GeoServerError, InvalidData,
                                 NotFoundError, SettingsError, UploadError,
                                 exceptions_to_http_status,
                                 rivid_exception_handler)

from .app import StreamflowPredictionTool as app
from .controllers_functions import (get_ecmwf_avaialable_dates,
                                    get_ecmwf_forecast_statistics,
                                    get_historic_streamflow_series,
                                    get_return_period_dict,
                                    get_return_period_ploty_info)
from .controllers_validators import (validate_historical_data,
                                     validate_watershed_info)
from .functions import (delete_from_database,
                        format_name,
                        get_units_title,
                        handle_uploaded_file,
                        update_geoserver_layer,
                        user_permission_test,
                        M3_TO_FT3)

from .model import DataStore, GeoServer, Watershed, WatershedGroup


@require_POST
@user_passes_test(user_permission_test)
@exceptions_to_http_status
def data_store_add(request):
    """
    Controller for adding a data store.
    """
    # get/check information from AJAX request
    data_store_name = request.POST.get('data_store_name')
    data_store_owner_org = request.POST.get('data_store_owner_org')
    data_store_type_id = request.POST.get('data_store_type_id')
    data_store_endpoint = request.POST.get('data_store_endpoint')
    data_store_api_key = request.POST.get('data_store_api_key')

    if not (data_store_name or data_store_type_id or data_store_endpoint
            or data_store_api_key):
        raise InvalidData("Request missing data.")

    # initialize session
    session_maker = app.get_persistent_store_database('main_db',
                                                      as_sessionmaker=True)
    session = session_maker()

    # check to see if duplicate exists
    num_similar_data_stores = session.query(DataStore) \
        .filter(
        or_(
            DataStore.name == data_store_name,
            DataStore.api_endpoint == data_store_endpoint
        )
    ) \
        .count()

    if num_similar_data_stores > 0:
        session.close()
        raise DatabaseError(
            "A data store with the same name or api endpoint exists.")

    # check if data store info is valid
    dataset_engine = CkanDatasetEngine(endpoint=data_store_endpoint,
                                       apikey=data_store_api_key)
    result = dataset_engine.list_datasets()
    if not result or "success" not in result:
        session.close()
        raise InvalidData("Data Store Credentials Invalid. "
                          "Password incorrect; "
                          "Endpoint must end in \"api/3/action\"")

    # add Data Store
    session.add(
        DataStore(
            name=data_store_name,
            owner_org=data_store_owner_org,
            data_store_type_id=data_store_type_id,
            api_endpoint=data_store_endpoint,
            api_key=data_store_api_key
        )
    )

    session.commit()
    session.close()

    return JsonResponse({'success': "Data Store Sucessfully Added!"})


@require_POST
@user_passes_test(user_permission_test)
@exceptions_to_http_status
def data_store_delete(request):
    """
    Controller for deleting a data store.
    """
    # get/check information from AJAX request
    data_store_id = request.POST.get('data_store_id')

    if int(data_store_id) == 1:
        raise DatabaseError("Cannot change this data store.")

    # initialize session
    session_maker = \
        app.get_persistent_store_database('main_db',
                                          as_sessionmaker=True)
    session = session_maker()
    try:
        # update data store
        data_store = session.query(DataStore).get(data_store_id)
        session.delete(data_store)
        session.commit()
    except IntegrityError:
        session.close()
        raise DatabaseError(
            "This data store is connected with a watershed!"
            "Must remove connection to delete."
        )

    session.close()
    return JsonResponse({'success': "Data Store Sucessfully Deleted!"})


@require_POST
@user_passes_test(user_permission_test)
@exceptions_to_http_status
def data_store_update(request):
    """
    Controller for updating a data store.
    """
    # get/check information from AJAX request
    data_store_id = request.POST.get('data_store_id')
    data_store_name = request.POST.get('data_store_name')
    data_store_owner_org = request.POST.get('data_store_owner_org')
    data_store_api_endpoint = request.POST.get('data_store_api_endpoint')
    data_store_api_key = request.POST.get('data_store_api_key')

    if int(data_store_id) == 1:
        raise DatabaseError("Cannot change this data store.")

    # initialize session
    session_maker = app.get_persistent_store_database('main_db',
                                                      as_sessionmaker=True)
    session = session_maker()
    # check to see if duplicate exists
    num_similar_data_stores = session.query(DataStore) \
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
        raise DatabaseError(
            "A data store with the same name or api endpoint exists.")

    # check if data store info is valid
    dataset_engine = \
        CkanDatasetEngine(endpoint=data_store_api_endpoint,
                          apikey=data_store_api_key)
    result = dataset_engine.list_datasets()

    if not result or "success" not in result:
        session.close()
        raise InvalidData("Data store credentials invalid. "
                          "Endpoint must end in \"api/3/action\"")

    # update data store
    data_store = session.query(DataStore).get(data_store_id)
    data_store.name = data_store_name
    data_store.owner_org = data_store_owner_org
    data_store.api_endpoint = data_store_api_endpoint
    data_store.api_key = data_store_api_key
    session.commit()
    session.close()
    return JsonResponse({'success': "Data store sucessfully updated!"})


@require_POST
@user_passes_test(user_permission_test)
@exceptions_to_http_status
def geoserver_add(request):
    """
    Controller for adding a geoserver.
    """
    # get/check information from AJAX request
    geoserver_name = request.POST.get('geoserver_name')
    geoserver_url = request.POST.get('geoserver_url')
    geoserver_username = request.POST.get('geoserver_username')
    geoserver_password = request.POST.get('geoserver_password')

    # check data
    if not geoserver_name or not geoserver_url or not \
            geoserver_username or not geoserver_password:
        raise InvalidData("Missing input data.")

    # validate geoserver credentials
    app_instance_id = app.get_custom_setting('app_instance_id')
    try:
        geoserver_manager = \
            GeoServerDatasetManager(engine_url=geoserver_url.strip(),
                                    username=geoserver_username.strip(),
                                    password=geoserver_password.strip(),
                                    app_instance_id=app_instance_id)
    except Exception as ex:
        raise GeoServerError(str(ex))

    # initialize session
    session_maker = app.get_persistent_store_database('main_db',
                                                      as_sessionmaker=True)
    session = session_maker()

    # check to see if duplicate exists
    num_similar_geoservers = session.query(GeoServer) \
        .filter(
        or_(
            GeoServer.name == geoserver_name,
            GeoServer.url == geoserver_manager.engine_url
        )
    ) \
        .count()
    if num_similar_geoservers > 0:
        session.close()
        raise DatabaseError("A geoserver with the same name or url exists.")

    # add GeoServer
    session.add(
        GeoServer(
            name=geoserver_name.strip(),
            url=geoserver_manager.engine_url,
            username=geoserver_username.strip(),
            password=geoserver_password.strip()
        )
    )

    session.commit()
    session.close()
    return JsonResponse({'success': "GeoServer Sucessfully Added!"})


@require_POST
@user_passes_test(user_permission_test)
@exceptions_to_http_status
def geoserver_delete(request):
    """
    Controller for deleting a geoserver.
    """
    # get/check information from AJAX request
    geoserver_id = request.POST.get('geoserver_id')

    # initialize session
    session_maker = app.get_persistent_store_database('main_db',
                                                      as_sessionmaker=True)
    session = session_maker()
    try:
        # delete geoserver
        try:
            geoserver = session.query(GeoServer).get(geoserver_id)
        except ObjectDeletedError:
            session.close()
            raise DatabaseError("The geoserver to delete does not exist.")

        session.delete(geoserver)
        session.commit()
    except IntegrityError:
        session.close()
        raise DatabaseError("This geoserver is connected with a watershed! "
                            "Must remove connection to delete.")

    session.close()
    return JsonResponse({'success': "GeoServer sucessfully deleted!"})


@require_POST
@user_passes_test(user_permission_test)
@exceptions_to_http_status
def geoserver_update(request):
    """
    Controller for updating a geoserver.
    """
    # get/check information from AJAX request
    geoserver_id = request.POST.get('geoserver_id')
    geoserver_name = request.POST.get('geoserver_name')
    geoserver_url = request.POST.get('geoserver_url')
    geoserver_username = request.POST.get('geoserver_username')
    geoserver_password = request.POST.get('geoserver_password')
    # check data
    if not geoserver_id or not geoserver_name or not geoserver_url or not \
            geoserver_username or not geoserver_password:
        raise InvalidData("Missing geoserver request input data.")
    # make sure id is id
    try:
        int(geoserver_id)
    except ValueError:
        raise InvalidData('GeoServer id is faulty.')

    if int(geoserver_id) == 1:
        raise InvalidData("Cannot change this geoserver.")

    # validate geoserver credentials
    app_instance_id = app.get_custom_setting('app_instance_id')
    try:
        geoserver_manager = \
            GeoServerDatasetManager(engine_url=geoserver_url.strip(),
                                    username=geoserver_username.strip(),
                                    password=geoserver_password.strip(),
                                    app_instance_id=app_instance_id)
    except Exception as ex:
        return GeoServerError(str(ex))

    # initialize session
    session_maker = app.get_persistent_store_database('main_db',
                                                      as_sessionmaker=True)
    session = session_maker()
    # check to see if duplicate exists
    num_similar_geoservers = session.query(GeoServer) \
        .filter(
        or_(GeoServer.name == geoserver_name,
            GeoServer.url == geoserver_manager.engine_url)
    ) \
        .filter(GeoServer.id != geoserver_id) \
        .count()

    if num_similar_geoservers > 0:
        session.close()
        raise DatabaseError("A geoserver with the same name or url exists.")

    # update geoserver
    try:
        geoserver = session.query(GeoServer).get(geoserver_id)
    except ObjectDeletedError:
        session.close()
        raise DatabaseError("The geoserver to update does not exist.")

    geoserver.name = geoserver_name.strip()
    geoserver.url = geoserver_manager.engine_url
    geoserver.username = geoserver_username.strip()
    geoserver.password = geoserver_password.strip()
    session.commit()
    session.close()
    return JsonResponse({'success': "GeoServer sucessfully updated!"})


@require_GET
@login_required
@exceptions_to_http_status
def ecmwf_get_avaialable_dates(request):
    """
    Finds a list of directories with valid data and
    returns dates in select2 format
    """
    output_directories = get_ecmwf_avaialable_dates(request)

    return JsonResponse({
        "success": "Data analysis complete!",
        "output_directories": output_directories,
    })


@require_GET
@login_required
@exceptions_to_http_status
def get_ecmwf_hydrograph_plot(request):
    """
    Retrieves 52 ECMWF ensembles analysis with min., max., avg., std. dev.
    as a plotly hydrograph plot.
    """
    # retrieve statistics
    forecast_statistics, watershed_name, subbasin_name, river_id, units = \
        get_ecmwf_forecast_statistics(request)

    # ensure lower std dev values limited by the min
    std_dev_lower_df = \
        forecast_statistics['std_dev_range_lower']
    std_dev_lower_df[std_dev_lower_df < forecast_statistics['min']] =\
        forecast_statistics['min']

    # ----------------------------------------------
    # Chart Section
    # ----------------------------------------------
    datetime_start = forecast_statistics['mean'].index[0]
    datetime_end = forecast_statistics['mean'].index[-1]

    avg_series = go.Scatter(
        name='Mean',
        x=forecast_statistics['mean'].index,
        y=forecast_statistics['mean'].values,
        line=dict(
            color='blue',
        )
    )

    max_series = go.Scatter(
        name='Max',
        x=forecast_statistics['max'].index,
        y=forecast_statistics['max'].values,
        fill='tonexty',
        mode='lines',
        line=dict(
            color='rgb(152, 251, 152)',
            width=0,
        )
    )

    min_series = go.Scatter(
        name='Min',
        x=forecast_statistics['min'].index,
        y=forecast_statistics['min'].values,
        fill=None,
        mode='lines',
        line=dict(
            color='rgb(152, 251, 152)',
        )
    )

    std_dev_lower_series = go.Scatter(
        name='Std. Dev. Lower',
        x=std_dev_lower_df.index,
        y=std_dev_lower_df.values,
        fill='tonexty',
        mode='lines',
        line=dict(
            color='rgb(152, 251, 152)',
            width=0,
        )
    )

    std_dev_upper_series = go.Scatter(
        name='Std. Dev. Upper',
        x=forecast_statistics['std_dev_range_upper'].index,
        y=forecast_statistics['std_dev_range_upper'].values,
        fill='tonexty',
        mode='lines',
        line=dict(
            width=0,
            color='rgb(34, 139, 34)',
        )
    )

    plot_series = [min_series,
                   std_dev_lower_series,
                   std_dev_upper_series,
                   max_series,
                   avg_series]

    if 'high_res' in forecast_statistics:
        plot_series.append(go.Scatter(
            name='HRES',
            x=forecast_statistics['high_res'].index,
            y=forecast_statistics['high_res'].values,
            line=dict(
                color='black',
            )
        ))

    try:
        return_shapes, return_annotations = \
            get_return_period_ploty_info(request, datetime_start, datetime_end)
    except NotFoundError:
        return_annotations = []
        return_shapes = []

    layout = go.Layout(
        title="Forecast<br><sub>{0} ({1}): {2}</sub>".format(
            watershed_name, subbasin_name, river_id),
        xaxis=dict(
            title='Date',
        ),
        yaxis=dict(
            title='Streamflow ({}<sup>3</sup>/s)'
                  .format(get_units_title(units))
        ),
        shapes=return_shapes,
        annotations=return_annotations
    )

    chart_obj = PlotlyView(
        go.Figure(data=plot_series,
                  layout=layout)
    )

    context = {
        'gizmo_object': chart_obj,
    }

    return render(request,
                  'streamflow_prediction_tool/gizmo_ajax.html',
                  context)


@require_GET
@login_required
@exceptions_to_http_status
def get_forecast_streamflow_csv(request):
    """
    Retrieve the forecasted streamflow as CSV
    """
    # retrieve statistics
    forecast_statistics, watershed_name, subbasin_name, river_id, units = \
        get_ecmwf_forecast_statistics(request)

    # prepare to write response for CSV
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = \
        'attachment; filename=forecasted_streamflow_{0}_{1}_{2}.csv' \
        .format(watershed_name,
                subbasin_name,
                river_id)

    writer = csv_writer(response)
    forecast_df = pd.DataFrame(forecast_statistics)
    column_names = (forecast_df.columns.values +
                    [' ({}3/s)'.format(get_units_title(units))]
                    ).tolist()

    writer.writerow(['datetime'] + column_names)

    for row_data in forecast_df.itertuples():
        writer.writerow(row_data)

    return response


@require_GET
@login_required
@exceptions_to_http_status
def generate_warning_points(request):
    """
    Controller for getting warning points for user on map
    """
    path_to_ecmwf_rapid_output = \
        app.get_custom_setting('ecmwf_forecast_folder')
    path_to_era_interim_data = app.get_custom_setting('historical_folder')
    if not os.path.exists(path_to_ecmwf_rapid_output) \
            or not os.path.exists(path_to_era_interim_data):
        raise SettingsError('Location of ECMWF forecast and historical files '
                            'faulty. Please check settings.')

    # get/check information from AJAX request
    get_info = request.GET
    watershed_name, subbasin_name = validate_watershed_info(get_info)
    return_period = get_info.get('return_period')
    forecast_folder = get_info.get('forecast_folder')
    if not return_period:
        return InvalidData('Missing return_period parameter ...')

    try:
        return_period = int(return_period)
    except (TypeError, ValueError):
        return InvalidData('Invalid return period.')

    path_to_output_files = \
        os.path.join(path_to_ecmwf_rapid_output,
                     "{0}-{1}".format(watershed_name, subbasin_name))

    # attempt to find forecast folder for watershed
    if not forecast_folder:
        if not os.path.exists(path_to_output_files):
            raise NotFoundError('No forecasts found ...')

        directory_list = \
            sorted([d for d in os.listdir(path_to_output_files)
                    if os.path.isdir(os.path.join(path_to_output_files, d))],
                   reverse=True)
        if directory_list:
            forecast_folder = directory_list[0]

    if not forecast_folder:
        raise NotFoundError('No forecasts found with {0} return period '
                            'warning points.'.format(return_period))

    # get warning points to load in
    if return_period == 20:
        warning_points_file = os.path.join(path_to_output_files,
                                           forecast_folder,
                                           "return_20_points.geojson")
    elif return_period == 10:
        warning_points_file = os.path.join(path_to_output_files,
                                           forecast_folder,
                                           "return_10_points.geojson")
    elif return_period == 2:
        warning_points_file = os.path.join(path_to_output_files,
                                           forecast_folder,
                                           "return_2_points.geojson")
    else:
        raise InvalidData('Invalid return period.')

    if not os.path.exists(warning_points_file):
        raise NotFoundError('Warning points file.')

    with open(warning_points_file, 'rb') as infile:
        warning_points = json_load(infile)

    return JsonResponse(warning_points)


@require_GET
@login_required
@exceptions_to_http_status
def get_historic_data_csv(request):
    """""
    Returns ERA Interim data as csv
    """""
    # get information from GET request
    units = request.GET.get('units')

    river_id, watershed_name, subbasin_name =\
        validate_historical_data(request.GET)[1:]

    qout_data = get_historic_streamflow_series(request)

    # prepare to write response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = \
        'attachment; filename=historic_streamflow_{0}_{1}_{2}.csv' \
        .format(watershed_name,
                subbasin_name,
                river_id)

    writer = csv_writer(response)

    writer.writerow(['datetime', 'streamflow ({}3/s)'
                                 .format(get_units_title(units))])

    for row_data in qout_data.iteritems():
        writer.writerow(row_data)

    return response


@require_GET
@login_required
@exceptions_to_http_status
def get_return_periods(request):
    """""
    Returns return period data for river ID
    """""
    return_period_data = get_return_period_dict(request)

    return JsonResponse({
        'success': "ERA-Interim data analysis complete!",
        'return_period': return_period_data
    })


@require_GET
@login_required
@exceptions_to_http_status
def get_historical_hydrograph(request):
    """""
    Returns ERA Interim hydrograph
    """""
    units = request.GET.get('units')
    historical_data_file, river_id, watershed_name, subbasin_name =\
        validate_historical_data(request.GET)

    with rivid_exception_handler('ERA Interim', river_id):
        with xarray.open_dataset(historical_data_file) as qout_nc:
            # get information from dataset
            qout_data = qout_nc.sel(rivid=river_id).Qout
            qout_values = qout_data.values
            qout_time = qout_data.time.values

    if units == 'english':
        # convert m3/s to ft3/s
        qout_values *= M3_TO_FT3

    # ----------------------------------------------
    # Chart Section
    # ----------------------------------------------
    qout_time = pd.to_datetime(qout_time)
    era_series = go.Scatter(
        name='ERA Interim',
        x=qout_time,
        y=qout_values,
    )

    return_shapes, return_annotations = \
        get_return_period_ploty_info(request, qout_time[0], qout_time[-1])

    layout = go.Layout(
        title="Historical Streamflow<br><sub>{0} ({1}): {2}</sub>".format(
            watershed_name, subbasin_name, river_id),
        xaxis=dict(
            title='Date',
        ),
        yaxis=dict(
            title='Streamflow ({}<sup>3</sup>/s)'
                  .format(get_units_title(units))
        ),
        shapes=return_shapes,
        annotations=return_annotations
    )

    chart_obj = PlotlyView(
        go.Figure(data=[era_series],
                  layout=layout)
    )

    context = {
        'gizmo_object': chart_obj,
    }

    return render(request,
                  'streamflow_prediction_tool/gizmo_ajax.html',
                  context)


@require_GET
@login_required
@exceptions_to_http_status
def get_daily_seasonal_streamflow_chart(request):
    """
    Returns daily seasonal streamflow chart for unique river ID
    """
    units = request.GET.get('units')
    seasonal_data_file, river_id, watershed_name, subbasin_name =\
        validate_historical_data(request.GET,
                                 "seasonal_average*.nc",
                                 "Seasonal Average")

    with rivid_exception_handler('Seasonal Average', river_id):
        with xarray.open_dataset(seasonal_data_file) as seasonal_nc:
            seasonal_data = seasonal_nc.sel(rivid=river_id)
            base_date = datetime.datetime(2017, 1, 1)
            day_of_year = \
                [base_date + datetime.timedelta(days=ii)
                 for ii in range(seasonal_data.dims['day_of_year'])]
            season_avg = seasonal_data.average_flow.values
            season_std = seasonal_data.std_dev_flow.values

            season_avg[season_avg < 0] = 0

            avg_plus_std = season_avg + season_std
            avg_min_std = season_avg - season_std

            avg_plus_std[avg_plus_std < 0] = 0
            avg_min_std[avg_min_std < 0] = 0

    if units == 'english':
        # convert from m3/s to ft3/s
        season_avg *= M3_TO_FT3
        avg_plus_std *= M3_TO_FT3
        avg_min_std *= M3_TO_FT3

    # generate chart
    avg_scatter = go.Scatter(
        name='Average',
        x=day_of_year,
        y=season_avg,
        line=dict(
            color='#0066ff'
        )
    )

    std_plus_scatter = go.Scatter(
        name='Std. Dev. Upper',
        x=day_of_year,
        y=avg_plus_std,
        fill=None,
        mode='lines',
        line=dict(
            color='#98fb98'
        )
    )

    std_min_scatter = go.Scatter(
        name='Std. Dev. Lower',
        x=day_of_year,
        y=avg_min_std,
        fill='tonexty',
        mode='lines',
        line=dict(
            color='#98fb98',
        )
    )

    layout = go.Layout(
        title="Daily Seasonal Streamflow<br>"
              "<sub>{0} ({1}): {2}</sub>"
              .format(watershed_name, subbasin_name, river_id),
        xaxis=dict(
            title='Day of Year',
            tickformat="%b"),
        yaxis=dict(
            title='Streamflow ({}<sup>3</sup>/s)'
                  .format(get_units_title(units)))
    )

    chart_obj = PlotlyView(
        go.Figure(data=[std_plus_scatter,
                        std_min_scatter,
                        avg_scatter],
                  layout=layout)
    )

    context = {
        'gizmo_object': chart_obj,
    }

    return render(request,
                  'streamflow_prediction_tool/gizmo_ajax.html',
                  context)


@require_GET
@login_required
@exceptions_to_http_status
def get_monthly_seasonal_streamflow_chart(request):
    """""
    Returns monthly seasonal streamflow chart for unique river ID
    """""
    historical_data_file, river_id, watershed_name, subbasin_name =\
        validate_historical_data(request.GET)
    units = request.GET.get('units')

    with rivid_exception_handler('ERA Interim', river_id):
        with xarray.open_dataset(historical_data_file) as qout_nc:
            # get information from dataset
            qout_data = qout_nc.sel(rivid=river_id).Qout.to_dataframe().Qout
            monthly_qout_data = qout_data.groupby(qout_data.index.month)

            min_series = monthly_qout_data.min().values
            max_series = monthly_qout_data.max().values
            avg_series = monthly_qout_data.mean().values
            std_series = monthly_qout_data.std().values
            std_plus_series = avg_series + std_series

    if units == 'english':
        min_series *= M3_TO_FT3
        max_series *= M3_TO_FT3
        avg_series *= M3_TO_FT3
        std_plus_series *= M3_TO_FT3

    months_arr = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul',
                  'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    # generate chart
    max_scatter = go.Scatter(
        name='Max.',
        x=months_arr,
        y=max_series,
        fill='tonexty',
        mode='lines',
        line=dict(
            color='rgb(204, 204, 204)'
        )
    )

    std_plus_scatter = go.Scatter(
        name='Std. Dev. Upper',
        x=months_arr,
        y=std_plus_series,
        fill='tonexty',
        mode='lines',
        line=dict(
            color='#98fb98'
        )
    )

    avg_scatter = go.Scatter(
        name='Average',
        x=months_arr,
        y=avg_series,
        line=dict(
            color='#0066ff'
        )
    )

    min_scatter = go.Scatter(
        name='Min.',
        x=months_arr,
        y=min_series,
        fill=None,
        mode='lines',
        line=dict(
            color='#ff6600'
        )
    )

    layout = go.Layout(
        title="Monthly Seasonal Streamflow<br>"
              "<sub>{0} ({1}): {2}</sub>"
              .format(watershed_name, subbasin_name, river_id),
        xaxis=dict(
            title='Month',
            tickformat="%b"),
        yaxis=dict(
            title='Streamflow ({}<sup>3</sup>/s)'
                  .format(get_units_title(units)))
    )

    chart_obj = PlotlyView(
        go.Figure(data=[min_scatter,
                        std_plus_scatter,
                        max_scatter,
                        avg_scatter],
                  layout=layout)
    )

    context = {
        'gizmo_object': chart_obj,
    }

    return render(request,
                  'streamflow_prediction_tool/gizmo_ajax.html',
                  context)


@require_GET
@login_required
@exceptions_to_http_status
def get_flow_duration_curve(request):
    """
    Generate flow duration curve for hydrologic time series data

    Based on: http://earthpy.org/flow.html
    """
    historical_data_file, river_id, watershed_name, subbasin_name = \
        validate_historical_data(request.GET)
    units = request.GET.get('units')

    with rivid_exception_handler('ERA Interim', river_id):
        with xarray.open_dataset(historical_data_file) as qout_nc:
            # get information from dataset
            qout_data = qout_nc.sel(rivid=river_id).Qout.to_dataframe().Qout

    sorted_daily_avg = np.sort(qout_data.values)[::-1]

    # ranks data from smallest to largest
    ranks = len(sorted_daily_avg) - sp.rankdata(sorted_daily_avg,
                                                method='average')

    # calculate probability of each rank
    prob = [100*(ranks[i] / (len(sorted_daily_avg) + 1))
            for i in range(len(sorted_daily_avg))]

    if units == 'english':
        # convert from m3/s to ft3/s
        sorted_daily_avg *= M3_TO_FT3

    flow_duration_sc = go.Scatter(
        x=prob,
        y=sorted_daily_avg,
    )

    layout = go.Layout(title="Flow-Duration Curve<br><sub>{0} ({1}): {2}</sub>"
                             .format(watershed_name, subbasin_name, river_id),
                       xaxis=dict(
                           title='Exceedance Probability (%)',),
                       yaxis=dict(
                           title='Streamflow ({}<sup>3</sup>/s)'
                                 .format(get_units_title(units)),
                           type='log',
                           autorange=True),
                       showlegend=False)

    chart_obj = PlotlyView(
        go.Figure(data=[flow_duration_sc],
                  layout=layout)
    )

    context = {
        'gizmo_object': chart_obj,
    }

    return render(request,
                  'streamflow_prediction_tool/gizmo_ajax.html',
                  context)


@require_POST
@user_passes_test(user_permission_test)
@exceptions_to_http_status
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
    if not (watershed_name or subbasin_name or data_store_id or geoserver_id
            or watershed_clean_name or subbasin_clean_name):
        raise InvalidData('Request input missing data ...')

    # make sure ids are ids
    try:
        int(data_store_id)
        int(geoserver_id)
    except ValueError:
        raise InvalidData('One or more ids are faulty.')

    # check ECMWF inputs
    ecmwf_rapid_input_resource_id = ""

    data_store_watershed_name = \
        format_name(post_info.get('ecmwf_data_store_watershed_name'))
    data_store_subbasin_name = \
        format_name(post_info.get('ecmwf_data_store_subbasin_name'))

    if not data_store_watershed_name \
            or not data_store_subbasin_name:
        raise InvalidData("Must have an ECMWF watershed and subbasin name "
                          "to continue.")

    # initialize session
    session_maker = app.get_persistent_store_database('main_db',
                                                      as_sessionmaker=True)
    session = session_maker()

    # check to see if duplicate exists
    num_similar_watersheds = session.query(Watershed) \
        .filter(Watershed.watershed_clean_name == watershed_clean_name) \
        .filter(Watershed.subbasin_clean_name == subbasin_clean_name) \
        .count()
    if num_similar_watersheds > 0:
        session.close()
        raise DatabaseError("A watershed with the same name exists.")

    # validate geoserver inputs
    if not drainage_line_shp_file and not geoserver_drainage_line_layer_name:
        session.close()
        raise InvalidData('Missing geoserver drainage line.')

    # get desired geoserver
    try:
        geoserver = session.query(GeoServer).get(geoserver_id)
    except ObjectDeletedError:
        session.close()
        raise DatabaseError("The geoserver does not exist.")
    try:
        app_instance_id = app.get_custom_setting('app_instance_id')
        geoserver_manager = \
            GeoServerDatasetManager(engine_url=geoserver.url,
                                    username=geoserver.username,
                                    password=geoserver.password,
                                    app_instance_id=app_instance_id)
    except Exception as ex:
        session.close()
        return GeoServerError(str(ex))

    # GEOSERVER UPLOAD
    # check geoserver input before upload
    if drainage_line_shp_file:
        geoserver_drainage_line_layer_name = \
            "%s-%s-%s" % (watershed_clean_name, subbasin_clean_name,
                          'drainage_line')
        # check shapefles
        try:
            geoserver_manager \
                .check_shapefile_input_files(drainage_line_shp_file)
        except Exception as ex:
            session.close()
            raise UploadError('Drainage Line layer - %s.' % ex)

    # UPLOAD DRAINAGE LINE
    try:
        geoserver_drainage_line_layer = \
            update_geoserver_layer(None,
                                   geoserver_drainage_line_layer_name,
                                   drainage_line_shp_file,
                                   geoserver_manager,
                                   session,
                                   layer_required=True)
    except Exception as ex:
        session.close()
        raise UploadError("Drainage Line layer error updating -  %s" % ex)

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
        raise UploadError("Boundary layer error updating - %s" % ex)

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
        raise UploadError("Gage layer error updating - %s" % ex)

    # UPDATE HISTORICAL FLOOD MAP LAYER GROUP
    try:
        geoserver_hist_flood_map_layer = \
            update_geoserver_layer(None,
                                   geoserver_historical_flood_map_layer_name,
                                   None,
                                   geoserver_manager,
                                   session,
                                   layer_required=False,
                                   is_layer_group=True)
    except Exception as ex:
        session.close()
        raise UploadError("Historical Flood Map layer error updating - %s"
                          % ex)

    # UPDATE AHPS STATION
    try:
        geoserver_ahps_station_layer = \
            update_geoserver_layer(
                None,
                geoserver_ahps_station_layer_name,
                None,
                geoserver_manager,
                session,
                layer_required=False
            )
    except Exception as ex:
        session.close()
        raise UploadError("AHPS Station layer error updating - %s" % ex)

    # add watershed
    watershed = Watershed(
        watershed_name=watershed_name.strip(),
        subbasin_name=subbasin_name.strip(),
        watershed_clean_name=watershed_clean_name,
        subbasin_clean_name=subbasin_clean_name,
        data_store_id=data_store_id,
        ecmwf_rapid_input_resource_id=ecmwf_rapid_input_resource_id,
        ecmwf_data_store_watershed_name=data_store_watershed_name.strip(),
        ecmwf_data_store_subbasin_name=data_store_subbasin_name.strip(),
        geoserver_id=geoserver_id,
        geoserver_drainage_line_layer=geoserver_drainage_line_layer,
        geoserver_boundary_layer=geoserver_boundary_layer,
        geoserver_gage_layer=geoserver_gage_layer,
        geoserver_historical_flood_map_layer=geoserver_hist_flood_map_layer,
        geoserver_ahps_station_layer=geoserver_ahps_station_layer,
    )

    session.add(watershed)
    session.commit()

    # get watershed_id
    response = {
        'success': "Watershed Sucessfully Added!",
        'watershed_id': watershed.id,
        'geoserver_drainage_line_layer': geoserver_drainage_line_layer.name
        if geoserver_drainage_line_layer
        else geoserver_drainage_line_layer_name,
    }
    session.close()

    return JsonResponse(response)


@require_POST
@user_passes_test(user_permission_test)
@exceptions_to_http_status
def watershed_ecmwf_rapid_file_upload(request):
    """
    Controller AJAX for uploading RAPID input files for a watershed.
    """
    watershed_id = request.POST.get('watershed_id')
    ecmwf_rapid_input_file = request.FILES.get('ecmwf_rapid_input_file')

    # make sure id is int
    try:
        int(watershed_id)
    except (TypeError, ValueError):
        raise InvalidData('Watershed ID is invalid ...')

    if not ecmwf_rapid_input_file:
        raise InvalidData("Missing ecmwf_rapid_input_file ...")

    # initialize session
    session_maker = app.get_persistent_store_database('main_db',
                                                      as_sessionmaker=True)
    session = session_maker()
    watershed = session.query(Watershed).get(watershed_id)

    if int(watershed.data_store_id) == 1:
        session.close()
        raise InvalidData("Not allowed to upload to the local data store ...")

    # Upload file to Data Store Server

    # temporarily upload to Tethys Plarform server
    tmp_file_location = \
        os.path.join(os.path.dirname(os.path.realpath(__file__)),
                     'workspaces', 'app_workspace')

    ecmwf_rapid_input_zip = \
        "%s-%s-rapid.zip" % (watershed.ecmwf_data_store_watershed_name,
                             watershed.ecmwf_data_store_subbasin_name)
    local_file_path = os.path.join(tmp_file_location,
                                   ecmwf_rapid_input_zip)

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
        raise UploadError('Problem uploading ECMWF-RAPID dataset to CKAN ...')

    # delete local file
    try:
        os.remove(local_file_path)
    except OSError:
        pass

    # update watershed
    watershed.ecmwf_rapid_input_resource_id = resource_info['result']['id']
    session.commit()
    session.close()
    return JsonResponse({'success': 'ECMWF-RAPID input upload success!'})


@require_POST
@user_passes_test(user_permission_test)
@exceptions_to_http_status
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
        raise InvalidData('Watershed ID is faulty ...')

    if not watershed_id:
        raise InvalidData('Cannot delete this watershed ...')
    # initialize session
    session_maker = app.get_persistent_store_database('main_db',
                                                      as_sessionmaker=True)
    session = session_maker()
    # get watershed to delete
    try:
        watershed = session.query(Watershed).get(watershed_id)
    except ObjectDeletedError:
        raise DatabaseError("The watershed to delete does not exist ...")

    delete_from_database(session, watershed)
    # NOTE: CASCADE removes associated geoserver layers

    # delete watershed from database
    session.commit()
    session.close()

    return JsonResponse({'success': "Watershed sucessfully deleted!"})


@require_POST
@user_passes_test(user_permission_test)
@exceptions_to_http_status
def watershed_update(request):
    """
    Controller for updating a watershed.
    """
    post_info = request.POST
    # get/check information from AJAX request
    watershed_id = post_info.get('watershed_id')
    watershed_name, subbasin_name = validate_watershed_info(post_info,
                                                            clean_name=False)
    watershed_clean_name = format_name(watershed_name)
    subbasin_clean_name = format_name(subbasin_name)
    data_store_id = post_info.get('data_store_id')
    geoserver_id = post_info.get('geoserver_id')

    # REQUIRED TO HAVE drainage_line from one of these
    # layer names
    geoserver_drainage_line_layer_name = post_info.get(
        'geoserver_drainage_line_layer')
    geoserver_boundary_layer_name = post_info.get('geoserver_boundary_layer')
    geoserver_gage_layer_name = post_info.get('geoserver_gage_layer')
    geoserver_historical_flood_map_layer_name = post_info.get(
        'geoserver_historical_flood_map_layer')
    geoserver_ahps_station_layer_name = post_info.get(
        'geoserver_ahps_station_layer')
    # shape files
    drainage_line_shp_file = request.FILES.getlist('drainage_line_shp_file')
    boundary_shp_file = request.FILES.getlist('boundary_shp_file')
    gage_shp_file = request.FILES.getlist('gage_shp_file')
    ahps_station_shp_file = request.FILES.getlist('ahps_station_shp_file')
    # CHECK INPUT
    # check if variables exist
    if not (watershed_id or data_store_id or geoserver_id
            or watershed_clean_name or subbasin_clean_name):
        raise InvalidData('Request input missing data.')

    # make sure ids are ids
    try:
        int(watershed_id)
        int(data_store_id)
        int(geoserver_id)
    except (TypeError, ValueError):
        raise InvalidData('One or more ids are faulty.')

    # initialize session
    session_maker = app.get_persistent_store_database('main_db',
                                                      as_sessionmaker=True)
    session = session_maker()
    # check to see if duplicate exists
    num_similar_watersheds = session.query(Watershed) \
        .filter(Watershed.watershed_clean_name == watershed_clean_name) \
        .filter(Watershed.subbasin_clean_name == subbasin_clean_name) \
        .filter(Watershed.id != watershed_id) \
        .count()
    if num_similar_watersheds > 0:
        session.close()
        raise DatabaseError("A watershed with the same name exists ...")

    # get desired watershed
    try:
        watershed = session.query(Watershed).get(watershed_id)
    except ObjectDeletedError:
        session.close()
        raise DatabaseError("The watershed to update does not exist ...")
    # get desired geoserver
    try:
        geoserver = session.query(GeoServer).get(geoserver_id)
    except ObjectDeletedError:
        session.close()
        raise DatabaseError("The geoserver does not exist ...")

    # check ecmwf inputs
    ecmwf_data_store_watershed_name = format_name(
        post_info.get('ecmwf_data_store_watershed_name'))
    ecmwf_data_store_subbasin_name = format_name(
        post_info.get('ecmwf_data_store_subbasin_name'))

    if not ecmwf_data_store_watershed_name \
            or not ecmwf_data_store_subbasin_name:
        session.close()
        raise InvalidData("Must have an ECMWF watershed/subbasin name "
                          "to continue")

    # GEOSERVER SECTION
    # remove old geoserver files if geoserver changed
    if int(geoserver_id) != watershed.geoserver_id:
        # remove old geoserver files
        watershed.delete_geoserver_files()

    # validate geoserver inputs
    if not drainage_line_shp_file and not geoserver_drainage_line_layer_name:
        session.close()
        raise InvalidData('Missing geoserver drainage line.')

    try:
        app_instance_id = app.get_custom_setting('app_instance_id')
        geoserver_manager = \
            GeoServerDatasetManager(engine_url=geoserver.url,
                                    username=geoserver.username,
                                    password=geoserver.password,
                                    app_instance_id=app_instance_id)
    except Exception as ex:
        session.close()
        raise GeoServerError(str(ex))

    # check geoserver input before upload
    if drainage_line_shp_file:
        geoserver_drainage_line_layer_name = "%s-%s-%s" % (
            watershed_clean_name, subbasin_clean_name, 'drainage_line')
        # check permissions to upload file
        if watershed.geoserver_drainage_line_layer:
            if not watershed.geoserver_drainage_line_layer.uploaded and \
                    watershed.geoserver_drainage_line_layer.name \
                    == geoserver_manager.get_layer_name(
                    geoserver_drainage_line_layer_name):
                session.close()
                raise PermissionDenied('You do not have permissions to '
                                       'overwrite the drainage line layer ...')

        # check shapefles
        try:
            geoserver_manager.check_shapefile_input_files(
                drainage_line_shp_file)
        except Exception as ex:
            session.close()
            raise UploadError('Drainage Line - %s.' % ex)

    if boundary_shp_file:
        geoserver_boundary_layer_name = "%s-%s-%s" % (
            watershed_clean_name, subbasin_clean_name, 'boundary')
        # check permissions to upload file
        if watershed.geoserver_boundary_layer:
            if not watershed.geoserver_boundary_layer.uploaded and \
                    watershed.geoserver_boundary_layer.name == \
                    geoserver_manager.get_layer_name(
                        geoserver_boundary_layer_name):
                session.close()
                raise PermissionDenied('You do not have permissions to '
                                       'overwrite the boundary layer ...')

        # check shapefiles
        try:
            geoserver_manager.check_shapefile_input_files(boundary_shp_file)
        except Exception as ex:
            session.close()
            raise UploadError('Boundary - %s.' % ex)

    if gage_shp_file:
        geoserver_gage_layer_name = "%s-%s-%s" % (
            watershed_clean_name, subbasin_clean_name, 'gage')
        # check permissions to upload file
        if watershed.geoserver_gage_layer:
            if not watershed.geoserver_gage_layer.uploaded and \
                    watershed.geoserver_gage_layer.name == \
                    geoserver_manager.get_layer_name(
                        geoserver_gage_layer_name):
                session.close()
                raise PermissionDenied('You do not have permissions to '
                                       'overwrite the gage layer ...')

        # check shapefiles
        try:
            geoserver_manager.check_shapefile_input_files(gage_shp_file)
        except Exception as ex:
            session.close()
            raise UploadError('Gage - %s.' % ex)

    if ahps_station_shp_file:
        geoserver_ahps_station_layer_name = "%s-%s-%s" % (
            watershed_clean_name, subbasin_clean_name, 'ahps_station')
        # check permissions to upload file
        if watershed.geoserver_ahps_station_layer:
            if not watershed.geoserver_ahps_station_layer.uploaded and \
                    watershed.geoserver_ahps_station_layer.name == \
                    geoserver_manager.get_layer_name(
                        geoserver_ahps_station_layer_name):
                session.close()
                raise PermissionDenied('You do not have permissions to '
                                       'overwrite the AHPS station layer ...')

        # check shapefiles
        try:
            geoserver_manager\
                .check_shapefile_input_files(ahps_station_shp_file)
        except Exception as ex:
            session.close()
            raise UploadError('AHPS Station - %s.' % ex)

    # UPDATE DRAINAGE LINE
    try:
        watershed.geoserver_drainage_line_layer = \
            update_geoserver_layer(
                watershed.geoserver_drainage_line_layer,
                geoserver_drainage_line_layer_name,
                drainage_line_shp_file,
                geoserver_manager,
                session,
                layer_required=True
            )
    except Exception as ex:
        session.close()
        raise UploadError("Drainage Line layer update - %s" % ex)

    # UPDATE Boundary
    try:
        watershed.geoserver_boundary_layer = \
            update_geoserver_layer(
                watershed.geoserver_boundary_layer,
                geoserver_boundary_layer_name,
                boundary_shp_file,
                geoserver_manager,
                session,
                layer_required=False
            )
    except Exception as ex:
        session.close()
        raise UploadError("Boundary layer update - %s" % ex)

    # UPDATE GAGE
    try:
        watershed.geoserver_gage_layer = \
            update_geoserver_layer(
                watershed.geoserver_gage_layer,
                geoserver_gage_layer_name,
                gage_shp_file,
                geoserver_manager,
                session,
                layer_required=False
            )
    except Exception as ex:
        session.close()
        raise UploadError("Gage layer update - %s" % ex)

    # UPDATE HISTORICAL FLOOD MAP LAYER GROUP
    try:
        watershed.geoserver_historical_flood_map_layer = \
            update_geoserver_layer(
                watershed.geoserver_historical_flood_map_layer,
                geoserver_historical_flood_map_layer_name,
                None,
                geoserver_manager,
                session,
                layer_required=False,
                is_layer_group=True
            )
    except Exception as ex:
        session.close()
        raise UploadError("Historical Flood Map layer update - %s" % ex)

    # UPDATE AHPS STATION
    try:
        watershed.geoserver_ahps_station_layer = update_geoserver_layer(
            watershed.geoserver_ahps_station_layer,
            geoserver_ahps_station_layer_name,
            ahps_station_shp_file,
            geoserver_manager,
            session,
            layer_required=False)
    except Exception as ex:
        session.close()
        raise UploadError("AHPS Station layer update - %s" % ex)

    # remove old prediction files if watershed/subbasin name changed
    if (ecmwf_data_store_watershed_name !=
            watershed.ecmwf_data_store_watershed_name or
            ecmwf_data_store_subbasin_name !=
            watershed.ecmwf_data_store_subbasin_name):
        watershed.delete_prediction_files()
        # remove RAPID input files on CKAN if exists
        try:
            watershed.delete_rapid_input_ckan()
        except Exception as ex:
            session.close()
            raise InvalidData("Invalid CKAN instance %s. "
                              "Cannot delete RAPID input files on CKAN: %s"
                              % (watershed.data_store.api_endpoint, ex))

    # remove CKAN files on old CKAN instance
    if watershed.data_store_id != data_store_id:
        # remove RAPID input files on CKAN if exists
        try:
            watershed.delete_rapid_input_ckan()
        except Exception as ex:
            session.close()
            raise InvalidData("Invalid CKAN instance %s. "
                              "Cannot delete RAPID input files on CKAN: %s"
                              % (watershed.data_store.api_endpoint, ex))

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
        'geoserver_drainage_line_layer':
        watershed.geoserver_drainage_line_layer.name
            if watershed.geoserver_drainage_line_layer else "",
        'geoserver_boundary_layer': watershed.geoserver_boundary_layer.name
            if watershed.geoserver_boundary_layer else "",
        'geoserver_gage_layer': watershed.geoserver_gage_layer.name
            if watershed.geoserver_gage_layer else "",
        'geoserver_historical_flood_map_layer':
        watershed.geoserver_historical_flood_map_layer.name
            if watershed.geoserver_historical_flood_map_layer else "",
        'geoserver_ahps_station_layer':
        watershed.geoserver_ahps_station_layer.name
            if watershed.geoserver_ahps_station_layer else "",
    }

    # update database
    session.commit()
    session.close()

    return JsonResponse(response)


@require_POST
@user_passes_test(user_permission_test)
@exceptions_to_http_status
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
        raise InvalidData("Missing watershed group name and/or group ids ...")

    # initialize session
    session_maker = app.get_persistent_store_database('main_db',
                                                      as_sessionmaker=True)
    session = session_maker()

    # check to see if duplicate exists
    num_similar_watershed_groups = session.query(WatershedGroup) \
        .filter(WatershedGroup.name == watershed_group_name) \
        .count()
    if num_similar_watershed_groups > 0:
        session.close()
        raise DatabaseError("A watershed group with the same name.")

    # add Watershed Group
    group = WatershedGroup(name=watershed_group_name)

    # update watersheds
    watersheds = session.query(Watershed) \
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
@exceptions_to_http_status
def watershed_group_delete(request):
    """
    Controller for deleting a watershed group.
    """
    # get/check information from AJAX request
    post_info = request.POST
    watershed_group_id = post_info.get('watershed_group_id')

    if not watershed_group_id:
        raise InvalidData("Missing watershed group id ...")

    # initialize session
    session_maker = app.get_persistent_store_database('main_db',
                                                      as_sessionmaker=True)
    session = session_maker()
    # get watershed group to delete
    watershed_group = session.query(WatershedGroup).get(watershed_group_id)

    # delete watershed group from database
    session.delete(watershed_group)
    session.commit()
    session.close()

    return JsonResponse({
        'success': "Watershed group sucessfully deleted!"
    })


@require_POST
@user_passes_test(user_permission_test)
@exceptions_to_http_status
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

    if not (watershed_group_id or watershed_group_name or
            watershed_group_watershed_ids):
        raise InvalidData("Watershed group input data missing ...")

    # initialize session
    session_maker = app.get_persistent_store_database('main_db',
                                                      as_sessionmaker=True)
    session = session_maker()
    # check to see if duplicate exists
    num_similar_watershed_groups = session.query(WatershedGroup) \
        .filter(WatershedGroup.name == watershed_group_name) \
        .filter(WatershedGroup.id != watershed_group_id) \
        .count()

    if num_similar_watershed_groups > 0:
        session.close()
        raise DatabaseError("A watershed group with the same name exists.")

    # get watershed group
    watershed_group = session.query(WatershedGroup).get(watershed_group_id)
    watershed_group.name = watershed_group_name

    # find new watersheds
    new_watersheds = session.query(Watershed) \
        .filter(Watershed.id.in_(watershed_group_watershed_ids)) \
        .all()

    # update watersheds in group
    watershed_group.watersheds = new_watersheds

    session.commit()
    session.close()
    return JsonResponse({
        'success': "Watershed group successfully updated."
    })
