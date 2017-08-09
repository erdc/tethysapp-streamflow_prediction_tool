# -*- coding: utf-8 -*-
"""controllers_api.py

    Author: Michael Suffront & Alan D. Snow, 2017
    License: BSD 3-Clause
"""
import xarray

from django.http import JsonResponse
from django.shortcuts import render_to_response
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import api_view, authentication_classes

from .app import StreamflowPredictionTool as app
from .controllers_ajax import generate_warning_points
from .controllers_functions import (get_ecmwf_avaialable_dates,
                                    get_ecmwf_forecast_statistics,
                                    get_return_period_dict)
from .controllers_validators import validate_historical_data
from .exception_handling import (InvalidData, exceptions_to_http_status,
                                 rivid_exception_handler)
from .model import Watershed


@api_view(['GET'])
@authentication_classes((TokenAuthentication,))
@exceptions_to_http_status
def get_ecmwf_forecast(request):
    """
    Controller that will retrieve the ECMWF forecast data
    in WaterML 1.1 format
    """
    formatted_stat = {
        'high_res': 'High Resolution',
        'mean': 'Mean',
        'min': 'Min',
        'max': 'Max',
        'std_dev_range_lower': 'Standard Deviation Lower Range',
        'std_dev_range_upper': 'Standard Deviation Upper Range',
    }

    # retrieve statistics
    forecast_statistics = \
        get_ecmwf_forecast_statistics(request)

    # get information from request
    watershed_name = request.GET['watershed_name']
    subbasin_name = request.GET['subbasin_name']
    reach_id = request.GET['reach_id']

    try:
        stat = request.GET['stat_type']
    except KeyError:
        raise InvalidData('Missing value for stat_type ...')

    if stat not in formatted_stat:
        raise InvalidData('Invalid value for stat_type ...')

    forecast_data = forecast_statistics[stat].to_dataframe().Qout
    startdate = forecast_data.index[0].strftime('%Y-%m-%d %H:%M:%S')
    time_series = []
    for date, value in forecast_data.iteritems():
        time_series.append({
            'date': date.strftime('%Y-%m-%dT%H:%M:%S'),
            'val': value
        })

    context = {
        'config': watershed_name,
        'comid': reach_id,
        'stat': formatted_stat[stat],
        'startdate': startdate,
        'site_name': watershed_name + ' ' + subbasin_name,
        'units': {
            'name': 'Flow',
            'short': 'm^3/s',
            'long': 'Cubic meters per Second'
        },
        'time_series': time_series,
        'Source': 'ECMWF GloFAS forecast',
        'host': 'https://%s' % request.get_host(),
    }

    xml_response = \
        render_to_response('streamflow_prediction_tool/waterml.xml',
                           context)
    xml_response['Content-Type'] = 'application/xml'

    return xml_response


@api_view(['GET'])
@authentication_classes((TokenAuthentication,))
@exceptions_to_http_status
def get_historic_data(request):
    """
    Controller that will show the historic data in WaterML 1.1 format
    """
    historical_data_file, river_id, watershed_name, subbasin_name =\
        validate_historical_data(request.GET)

    with rivid_exception_handler("ERA Interim", river_id):
        with xarray.open_dataset(historical_data_file) as qout_nc:
            # get information from dataset
            qout_data = qout_nc.sel(rivid=river_id).Qout.to_dataframe().Qout
            startdate = qout_data.index[0].strftime('%Y-%m-%d %H:%M:%S')
            time_series = []
            for date, value in qout_data.iteritems():
                time_series.append({
                    'date': date.strftime('%Y-%m-%dT%H:%M:%S'),
                    'val': value
                })

    context = {
        'config': watershed_name,
        'comid': river_id,
        'stat': 'Historic Data',
        'startdate': startdate,
        'site_name': watershed_name + ' ' + subbasin_name,
        'units': {
            'name': 'Flow',
            'short': 'm^3/s',
            'long': 'Cubic meters per Second'
        },
        'time_series': time_series,
        'source': 'ECMWF ERA Interim data',
        'host': 'https://%s' % request.get_host(),
    }

    xml_response = \
        render_to_response('streamflow_prediction_tool/waterml.xml',
                           context)
    xml_response['Content-Type'] = 'application/xml'

    return xml_response


@api_view(['GET'])
@authentication_classes((TokenAuthentication,))
@exceptions_to_http_status
def get_return_periods_api(request):
    """
    Controller that will show the return period data in json format
    """
    return JsonResponse(get_return_period_dict(request), safe=False)


@api_view(['GET'])
@authentication_classes((TokenAuthentication,))
@exceptions_to_http_status
def get_available_dates(request):
    """
    Controller that will show the available
    forecast dates in a python list format
    """
    available_dates_raw = get_ecmwf_avaialable_dates(request)
    available_dates = []
    for pair in available_dates_raw:
        available_dates.append(pair["id"])
    available_dates = sorted(available_dates)

    return JsonResponse(available_dates, safe=False)


@api_view(['GET'])
@authentication_classes((TokenAuthentication,))
@exceptions_to_http_status
def get_watershed_list(request):  # pylint: disable=unused-argument
    """
    Controller that returns available watersheds.
    """
    session_maker = app.get_persistent_store_database('main_db',
                                                      as_sessionmaker=True)
    session = session_maker()

    watersheds = session.query(Watershed)\
                        .order_by(Watershed.watershed_name,
                                  Watershed.subbasin_name)\
                        .all()

    watershed_list = []
    for watershed in watersheds:
        watershed_list.append(
            (
                "%s (%s)" % (watershed.watershed_name,
                             watershed.subbasin_name),
                watershed.id
            )
        )

    if len(watershed_list) > 0:
        return JsonResponse(watershed_list, safe=False)
    return JsonResponse(["No watersheds found"], safe=False)


@api_view(['GET'])
@authentication_classes((TokenAuthentication,))
@exceptions_to_http_status
def get_warning_points(request):
    """
    Controller that will returned generated warning points in json format
    """
    return generate_warning_points(request)
