from django.http import JsonResponse, Http404
from django.shortcuts import render_to_response
from django.contrib.auth import authenticate, login
from rest_framework.decorators import api_view
import json
import datetime as dt

from .controllers_ajax import ecmwf_get_hydrograph, era_interim_get_hydrograph

@api_view(['GET'])
def get_waterml(request):
    """
	Controller that will show the data in WaterML 1.1 format
	"""
    watershed_name = request.GET['watershed_name']
    subbasin_name = request.GET['subbasin_name']
    reach_id = request.GET['reach_id']
    stat = request.GET['stat_type']

    formatted_stat = {'high_res': 'High Resolution', 'mean': 'Mean', 'outer_range_lower': 'Outer Lower Range',
                      'outer_range_upper': 'Outer Upper Range', 'std_dev_range_lower': 'Standard Deviation Lower Range',
                      'std_dev_range_upper': 'Standard Deviation Upper Range'}

    try:
        data = ecmwf_get_hydrograph(request)
        data_dict = json.loads(data.content)

        time_series = []
        if stat in ('high_res', 'mean', 'outer_range_lower', 'std_dev_range_lower'):
            stat_mod = stat.replace('_lower', '').replace('_upper', '')
            startdate = dt.datetime.fromtimestamp(data_dict[stat_mod][0][0] / 1e3).strftime('%Y-%m-%d %H:%M:%S')
            for pair in data_dict[stat_mod]:
                date = dt.datetime.fromtimestamp(pair[0]/1e3)
                formatted_date = date.strftime('%Y-%m-%dT%H:%M:%S')
                time_series.append({'date': formatted_date, 'val': pair[1]})

        elif stat in ('outer_range_upper', 'std_dev_range_upper'):
            stat_mod = stat.replace('_lower', '').replace('_upper', '')
            startdate = dt.datetime.fromtimestamp(data_dict[stat_mod][0][0] / 1e3).strftime('%Y-%m-%d %H:%M:%S')
            for pair in data_dict[stat_mod]:
                date = dt.datetime.fromtimestamp(pair[0] / 1e3)
                formatted_date = date.strftime('%Y-%m-%dT%H:%M:%S')
                time_series.append({'date': formatted_date, 'val': pair[2]})

        context = {
            'config': watershed_name,
            'comid': reach_id,
            'stat': formatted_stat[stat],
            'startdate': startdate,
            'site_name': watershed_name + ' ' + subbasin_name,
            'units': {'name': 'Flow', 'short': 'm^3/s', 'long': 'Cubic meters per Second'},
            'time_series': time_series,
            'Source': 'ECMWF GloFAS forecast',
            'host': 'https://%s' % request.get_host(),
        }

        xmlResponse = render_to_response('streamflow_prediction_tool/waterml.xml', context)
        xmlResponse['Content-Type'] = 'application/xml'

        return xmlResponse
    except Exception as e:
        print str(e)
        raise Http404('An error occurred. Please verify parameters.')

@api_view(['GET'])
def get_historic_data(request):
    """
	Controller that will show the historic data in WaterML 1.1 format
	"""
    watershed_name = request.GET['watershed_name']
    subbasin_name = request.GET['subbasin_name']
    reach_id = request.GET['reach_id']

    try:
        data = era_interim_get_hydrograph(request)
        data_dict = json.loads(data.content)
        historic_data = data_dict['era_interim']

        time_series = []
        if "success" in data_dict.keys():
            startdate = dt.datetime.fromtimestamp(historic_data['series'][0][0] / 1e3).strftime('%Y-%m-%d %H:%M:%S')
            for pair in historic_data['series']:
                date = dt.datetime.fromtimestamp(pair[0]/1e3)
                formatted_date = date.strftime('%Y-%m-%dT%H:%M:%S')
                time_series.append({'date': formatted_date, 'val': pair[1]})
        else:
            raise Http404('Historic data is not available for this area.')

        context = {
            'config': watershed_name,
            'comid': reach_id,
            'stat': 'Historic Data',
            'startdate': startdate,
            'site_name': watershed_name + ' ' + subbasin_name,
            'units': {'name': 'Flow', 'short': 'm^3/s', 'long': 'Cubic meters per Second'},
            'time_series': time_series,
            'source': 'ECMWF ERA Interim data',
            'host': 'https://%s' % request.get_host(),
        }

        xmlResponse = render_to_response('streamflow_prediction_tool/waterml.xml', context)
        xmlResponse['Content-Type'] = 'application/xml'

        return xmlResponse
    except Exception as e:
        print str(e)
        raise Http404('An error occurred. Please verify parameters.')
