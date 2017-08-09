# -*- coding: utf-8 -*-
"""controllers_functions.py

    This module contains functions that validate request input
    for controllers.

    Author: Alan D. Snow, 2017
    License: BSD 3-Clause
"""
from glob import glob
import os

from .app import StreamflowPredictionTool as app
from .exception_handling import InvalidData, NotFoundError, SettingsError
from .functions import format_name


def validate_watershed_info(request_info, clean_name=True):
    """
    This function validates the input watershed and subbasin data for a request

    Returns
    -------
    watershed_name, subbasin_name
    """
    watershed_name = request_info['watershed_name'].strip() \
        if 'watershed_name' in request_info else None
    if watershed_name is None:
        raise InvalidData('Missing watershed_name parameter ....')

    subbasin_name = request_info['subbasin_name'].strip() \
        if 'subbasin_name' in request_info else None
    if subbasin_name is None:
        raise InvalidData('Missing subbasin_name parameter ....')

    if clean_name:
        return format_name(watershed_name), format_name(subbasin_name)
    return watershed_name, subbasin_name


def validate_rivid_info(request_info):
    """
    This function validates the input rivid data for a request

    Returns
    -------
    rivid
    """
    reach_id = request_info.get('reach_id')
    if reach_id is None:
        raise InvalidData('Missing reach_id parameter ....')

    # make sure reach id is integet
    try:
        reach_id = int(reach_id)
    except (TypeError, ValueError):
        raise InvalidData('Invalid value for reach_id {}.'.format(reach_id))

    return reach_id


def validate_historical_data(request_info, file_search_card="Qout*.nc",
                             dataset_name="ERA Interim"):
    """
    This function validates the request for historical data

    Returns
    -------
    historic_data_file, rivid
    """
    path_to_era_interim_data = app.get_custom_setting('historical_folder')
    if not os.path.exists(path_to_era_interim_data):
        raise SettingsError('Location of historical files faulty. '
                            'Please check settings.')

    # get information from request
    watershed_name, subbasin_name = validate_watershed_info(request_info)
    river_id = validate_rivid_info(request_info)

    # find/check current output datasets
    path_to_output_files = \
        os.path.join(path_to_era_interim_data,
                     "{0}-{1}".format(watershed_name, subbasin_name))
    historical_data_files = glob(os.path.join(path_to_output_files,
                                              file_search_card))
    if not historical_data_files:
        raise NotFoundError('{dataset_name} data for {watershed_name} '
                            '({subbasin_name}).'
                            .format(dataset_name=dataset_name,
                                    watershed_name=watershed_name,
                                    subbasin_name=subbasin_name))

    return historical_data_files[0], river_id, watershed_name, subbasin_name
