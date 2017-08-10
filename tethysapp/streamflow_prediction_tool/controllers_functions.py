# -*- coding: utf-8 -*-
"""controllers_functions.py

    This module contains functions that act like controllers,
    are used in controllers, but are just functions.

    Author: Alan D. Snow, 2017
    License: BSD 3-Clause
"""
import os

import pandas as pd
import xarray

from django.shortcuts import render

from .app import StreamflowPredictionTool as app
from .controllers_validators import (validate_historical_data,
                                     validate_rivid_info,
                                     validate_watershed_info)
from .exception_handling import (InvalidData, NotFoundError, SettingsError,
                                 rivid_exception_handler)

from .functions import (ecmwf_find_most_current_files,
                        get_ecmwf_valid_forecast_folder_list,
                        M3_TO_FT3)
from .model import DataStore, GeoServer, Watershed, WatershedGroup


def get_ecmwf_avaialable_dates(request):
    """
    Finds a list of directories with valid data and
    returns dates in select2 format
    """
    path_to_rapid_output = app.get_custom_setting('ecmwf_forecast_folder')
    if not os.path.exists(path_to_rapid_output):
        raise SettingsError('Location of ECMWF forecast files faulty. '
                            'Please check settings.')

    # get/check information from AJAX request
    watershed_name, subbasin_name = validate_watershed_info(request.GET)

    # find/check current output datasets
    path_to_watershed_files = \
        os.path.join(path_to_rapid_output,
                     "{0}-{1}".format(watershed_name, subbasin_name))

    if not os.path.exists(path_to_watershed_files):
        raise NotFoundError('ECMWF forecast for %s (%s).'
                            % (watershed_name, subbasin_name))

    output_directories = \
        get_ecmwf_valid_forecast_folder_list(path_to_watershed_files, ".nc")

    if len(output_directories) <= 0:
        raise NotFoundError('Recent ECMWF forecasts for %s, %s.'
                            % (watershed_name, subbasin_name))

    return output_directories


def get_ecmwf_forecast_statistics(request):
    """
    Returns the statistics for the 52 member forecast
    """
    path_to_rapid_output = app.get_custom_setting('ecmwf_forecast_folder')
    if not os.path.exists(path_to_rapid_output):
        raise SettingsError('Location of ECMWF forecast files faulty. '
                            'Please check settings.')

    # get/check information from AJAX request
    get_info = request.GET
    watershed_name, subbasin_name = validate_watershed_info(get_info)
    river_id = validate_rivid_info(get_info)
    units = get_info.get('units')

    forecast_folder = get_info.get('forecast_folder')
    if not forecast_folder:
        raise InvalidData('Missing value for forecast_folder.')

    stat_type = get_info.get('stat_type')
    if stat_type is None:
        stat_type = ""

    # find/check current output datasets
    path_to_output_files = \
        os.path.join(path_to_rapid_output,
                     "{0}-{1}".format(watershed_name, subbasin_name))
    forecast_nc_list, start_date = \
        ecmwf_find_most_current_files(path_to_output_files, forecast_folder)
    if not forecast_nc_list or not start_date:
        raise NotFoundError('ECMWF forecast for %s (%s).'
                            % (watershed_name, subbasin_name))
    # combine 52 ensembles
    qout_datasets = []
    ensemble_index_list = []
    with rivid_exception_handler("ECMWF Forecast", river_id):
        for forecast_nc in forecast_nc_list:
            ensemble_index_list.append(
                int(os.path.basename(forecast_nc)[:-3].split("_")[-1])
            )
            qout_datasets.append(
                xarray.open_dataset(forecast_nc, autoclose=True)
                      .sel(rivid=river_id).Qout
            )

    merged_ds = xarray.concat(qout_datasets,
                              pd.Index(ensemble_index_list, name='ensemble'))

    return_dict = {}
    if stat_type == 'high_res' or not stat_type:
        # extract the high res ensemble & time
        try:
            return_dict['high_res'] = merged_ds.sel(ensemble=52).dropna('time')
        except IndexError:
            pass

    if stat_type != 'high_res' or not stat_type:
        # analyze data to get statistic bands
        merged_ds = merged_ds.dropna('time')

        if stat_type == 'mean' or 'std' in stat_type or not stat_type:
            return_dict['mean'] = merged_ds.mean(dim='ensemble')
            std_ar = merged_ds.std(dim='ensemble')
            if stat_type == 'std_dev_range_upper' or not stat_type:
                return_dict['std_dev_range_upper'] = \
                    return_dict['mean'] + std_ar
            if stat_type == 'std_dev_range_lower' or not stat_type:
                return_dict['std_dev_range_lower'] = \
                    return_dict['mean'] - std_ar
        if stat_type == "min" or not stat_type:
            return_dict['min'] = merged_ds.min(dim='ensemble')
        if stat_type == "max" or not stat_type:
            return_dict['max'] = merged_ds.max(dim='ensemble')

    for key in list(return_dict):
        if units == 'english':
            # convert m3/s to ft3/s
            return_dict[key] *= M3_TO_FT3
        # convert to pandas series
        return_dict[key] = return_dict[key].to_dataframe().Qout

    return return_dict


def get_return_period_dict(request):
    """
    Returns return period data as dictionary for a river ID in a watershed
    """
    units = request.GET.get('units')
    return_period_file, river_id =\
        validate_historical_data(request.GET,
                                 "return_period*.nc",
                                 "Return Period")[:2]

    # get information from dataset
    return_period_data = {}
    with rivid_exception_handler('return period', river_id):
        with xarray.open_dataset(return_period_file) \
                as return_period_nc:
            rpd = return_period_nc.sel(rivid=river_id)
            if units == 'english':
                rpd['max_flow'] *= M3_TO_FT3
                rpd['return_period_20'] *= M3_TO_FT3
                rpd['return_period_10'] *= M3_TO_FT3
                rpd['return_period_2'] *= M3_TO_FT3

            return_period_data["max"] = str(rpd.max_flow.values)
            return_period_data["twenty"] = str(rpd.return_period_20.values)
            return_period_data["ten"] = str(rpd.return_period_10.values)
            return_period_data["two"] = str(rpd.return_period_2.values)

    return return_period_data


def get_return_period_ploty_info(request, datetime_start, datetime_end):
    """
    Get shapes and annotations for plotly plot
    """
    # Return Period Section
    return_period_data = get_return_period_dict(request)
    return_max = float(return_period_data["max"])
    return_20 = float(return_period_data["twenty"])
    return_10 = float(return_period_data["ten"])
    return_2 = float(return_period_data["two"])

    # plotly info section
    shapes = [
         # return 20 band
         dict(
             type='rect',
             xref='x',
             yref='y',
             x0=datetime_start,
             y0=return_20,
             x1=datetime_end,
             y1=return_max,
             line=dict(width=0),
             fillcolor='rgba(128, 0, 128, 0.3)',
         ),
         # return 10 band
         dict(
             type='rect',
             xref='x',
             yref='y',
             x0=datetime_start,
             y0=return_10,
             x1=datetime_end,
             y1=return_20,
             line=dict(width=0),
             fillcolor='rgba(255, 0, 0, 0.3)',
         ),
         # return 2 band
         dict(
             type='rect',
             xref='x',
             yref='y',
             x0=datetime_start,
             y0=return_2,
             x1=datetime_end,
             y1=return_10,
             line=dict(width=0),
             fillcolor='rgba(255, 255, 0, 0.3)',
         ),
    ]
    annotations = [
        # return max
        dict(
            x=datetime_end,
            y=return_max,
            xref='x',
            yref='y',
            text='Max. ({:.1f})'.format(return_max),
            showarrow=False,
            xanchor='left',
        ),
        # return 20 band
        dict(
            x=datetime_end,
            y=return_20,
            xref='x',
            yref='y',
            text='20-yr ({:.1f})'.format(return_20),
            showarrow=False,
            xanchor='left',
        ),
        # return 10 band
        dict(
            x=datetime_end,
            y=return_10,
            xref='x',
            yref='y',
            text='10-yr ({:.1f})'.format(return_10),
            showarrow=False,
            xanchor='left',
        ),
        # return 2 band
        dict(
            x=datetime_end,
            y=return_2,
            xref='x',
            yref='y',
            text='2-yr ({:.1f})'.format(return_2),
            showarrow=False,
            xanchor='left',
        ),
    ]

    return shapes, annotations


def render_manage_data_store_pages(request, html_file):
    """
    Generate management pages for data_stores.
    """
    # initialize session
    session_maker = app.get_persistent_store_database('main_db',
                                                      as_sessionmaker=True)
    session = session_maker()

    data_stores = session.query(DataStore) \
                         .filter(DataStore.id > 1) \
                         .order_by(DataStore.name) \
                         .all()

    context = {
        'data_stores': data_stores,
    }

    table_html = \
        render(request,
               'streamflow_prediction_tool/{}'.format(html_file),
               context)
    # in order to close the session, the request needed to be rendered first
    session.close()

    return table_html


def render_manage_geoserver_pages(request, html_file):
    """
    Generates managemement pages for GeoServers.
    """
    # initialize session
    session_maker = app.get_persistent_store_database('main_db',
                                                      as_sessionmaker=True)
    session = session_maker()
    geoservers = session.query(GeoServer) \
                        .order_by(GeoServer.name, GeoServer.url) \
                        .all()
    context = {
        'geoservers': geoservers,
    }

    session.close()

    return render(request,
                  'streamflow_prediction_tool/{}'.format(html_file),
                  context)


def render_manage_watershed_groups_pages(request, html_file):
    """
    Generates management pages for WatershedGroups
    """
    # initialize session
    session_maker = app.get_persistent_store_database('main_db',
                                                      as_sessionmaker=True)
    session = session_maker()
    watershed_groups = session.query(WatershedGroup) \
                              .order_by(WatershedGroup.name) \
                              .all()

    watersheds = session.query(Watershed) \
        .order_by(Watershed.watershed_name,
                  Watershed.subbasin_name) \
        .all()

    context = {
        'watershed_groups': watershed_groups,
        'watersheds': watersheds,
    }

    page_html = \
        render(request,
               'streamflow_prediction_tool/{}'.format(html_file),
               context)
    session.close()

    return page_html
