# -*- coding: utf-8 -*-
"""controllers.py

    Created by Alan D. Snow, Curtis Rae, Shawn Crawley. 2015-2017
    License: BSD 3-Clause
"""
import json
import os

# django imports
from django.contrib.auth.decorators import user_passes_test, login_required
from django.views.decorators.http import require_GET
from django.shortcuts import render
# tethys imports
from tethys_sdk.gizmos import (Button, MessageBox, SelectInput,
                               TextInput, ToggleSwitch)

# local imports
from .app import StreamflowPredictionTool as app
from .controllers_functions import (render_manage_data_store_pages,
                                    render_manage_geoserver_pages,
                                    render_manage_watershed_groups_pages)
from .model import (DataStore, DataStoreType, GeoServer,
                    Watershed, WatershedGroup)
from .functions import (get_ecmwf_valid_forecast_folder_list,
                        format_watershed_title,
                        redirect_with_message,
                        user_permission_test,
                        get_sorted_watershed_list)


@require_GET
@login_required
def home(request):
    """
    Controller for the app home page.
    """
    # get the base layer information
    session_maker = app.get_persistent_store_database('main_db',
                                                      as_sessionmaker=True)
    session = session_maker()

    watersheds = session.query(Watershed) \
        .order_by(Watershed.watershed_name,
                  Watershed.subbasin_name) \
        .all()
    watershed_list = []
    for watershed in watersheds:
        watershed_list.append((
            "%s (%s)" % (watershed.watershed_name, watershed.subbasin_name),
            watershed.id
        ))
    watershed_groups = []
    groups = session.query(WatershedGroup).order_by(WatershedGroup.name).all()
    session.close()
    for group in groups:
        watershed_groups.append((group.name, group.id))

    watershed_select = SelectInput(display_text='Select Watershed(s)',
                                   name='watershed_select',
                                   options=watershed_list,
                                   multiple=True)

    watershed_group_select = \
        SelectInput(display_text='Select Watershed Group(s)',
                    name='watershed_group_select',
                    options=watershed_groups,
                    multiple=True)
    context = {
        'watershed_select': watershed_select,
        'watersheds_length': len(watersheds),
        'watershed_group_select': watershed_group_select,
        'watershed_group_length': len(groups),
    }

    return render(request, 'streamflow_prediction_tool/home.html', context)


@require_GET
@login_required
def app_map(request):
    """
    Controller for the app map page.
    """

    # -------------------------------------------------------------------------
    # HELPER FUNCTIONS
    # -------------------------------------------------------------------------
    def find_add_attribute_ci(attribute, layer_attributes,
                              contained_attributes):
        """
        Case insensitive attribute search and add
        """
        for layer_attribute in layer_attributes:
            if layer_attribute.lower() == attribute.lower():
                contained_attributes.append(layer_attribute)
                return True
        return False

    def get_watershed_layers_info(a_watershed_list):
        """
        This gets the information about the watershed layers
        """
        a_layers_info = []
        a_boundary_exists = False
        a_gage_exists = False
        a_ahps_station_exists = False
        a_historical_flood_map_exists = False
        # add layer urls to list and add their navigation items as well
        for a_watershed in a_watershed_list:
            ecmwf_watershed_name = a_watershed.ecmwf_data_store_watershed_name\
                if a_watershed.ecmwf_data_store_watershed_name \
                else a_watershed.watershed_name
            ecmwf_subbasin_name = a_watershed.ecmwf_data_store_subbasin_name \
                if a_watershed.ecmwf_data_store_subbasin_name \
                else a_watershed.subbasin_name
            # (get geoserver info)
            # get wms/api url
            geoserver_wms_url = a_watershed.geoserver.url
            if a_watershed.geoserver.url.endswith('/geoserver/rest'):
                geoserver_wms_url = \
                    "%s/ows" % "/".join(
                        a_watershed.geoserver.url.split("/")[:-1]
                    )
            elif a_watershed.geoserver.url.endswith('/geoserver'):
                geoserver_wms_url = "%s/ows" % a_watershed.geoserver.url

            a_geoserver_info = {
                'watershed': a_watershed.watershed_clean_name,
                'subbasin': a_watershed.subbasin_clean_name,
                'ecmwf_watershed': ecmwf_watershed_name,
                'ecmwf_subbasin': ecmwf_subbasin_name,
                'geoserver_url': geoserver_wms_url,
                'title': format_watershed_title(a_watershed.watershed_name,
                                                a_watershed.subbasin_name),
                'id': a_watershed.id,
            }

            # LOAD DRAINAGE LINE
            layer_attributes = \
                json.loads(a_watershed.geoserver_drainage_line_layer
                           .attribute_list)
            missing_attributes = []
            contained_attributes = []
            # check required attributes
            # necessary_attributes = ['COMID','watershed', 'subbasin',
            # 'wwatershed','wsubbasin']

            # check COMID/HydroID attribute
            if not find_add_attribute_ci('COMID', layer_attributes,
                                         contained_attributes):
                if not find_add_attribute_ci('HydroID', layer_attributes,
                                             contained_attributes):
                    missing_attributes.append('COMID or HydroID')

            # check ECMWF watershed/subbasin attributes
            if not find_add_attribute_ci('watershed', layer_attributes,
                                         contained_attributes) \
                    or not find_add_attribute_ci('subbasin', layer_attributes,
                                                 contained_attributes):
                missing_attributes.append('watershed')
                missing_attributes.append('subbasin')

            # check optional attributes
            optional_attributes = ['usgs_id', 'nws_id', 'hydroserve']
            for optional_attribute in optional_attributes:
                find_add_attribute_ci(optional_attribute, layer_attributes,
                                      contained_attributes)

            a_geoserver_info['drainage_line'] = {
                'name': a_watershed.geoserver_drainage_line_layer.name,
                'geojson': a_watershed.geoserver_drainage_line_layer.wfs_url,
                'latlon_bbox': json.loads(
                    a_watershed.geoserver_drainage_line_layer.latlon_bbox
                ),
                'projection': a_watershed.geoserver_drainage_line_layer
                                         .projection,
                'contained_attributes': contained_attributes,
                'missing_attributes': missing_attributes,
            }
            # check if needed attribute is there to perfrom
            # query based rendering of layer
            query_attribute = []
            if find_add_attribute_ci('Natur_Flow', layer_attributes,
                                     query_attribute):
                a_geoserver_info['drainage_line']['geoserver_method'] = \
                    "natur_flow_query"
                a_geoserver_info['drainage_line'][
                    'geoserver_query_attribute'] = query_attribute[0]
            elif find_add_attribute_ci('RiverOrder', layer_attributes,
                                       query_attribute):
                a_geoserver_info['drainage_line']['geoserver_method'] = \
                    "river_order_query"
                a_geoserver_info['drainage_line']['geoserver_query_attribute']\
                    = query_attribute[0]
            else:
                a_geoserver_info['drainage_line']['geoserver_method'] \
                    = "simple"

            if a_watershed.geoserver_boundary_layer:
                # LOAD BOUNDARY
                a_geoserver_info['boundary'] = {
                    'name': a_watershed.geoserver_boundary_layer.name,
                    'latlon_bbox': json.loads(
                        a_watershed.geoserver_boundary_layer.latlon_bbox
                    ),
                    'projection': a_watershed.geoserver_boundary_layer
                                             .projection,
                }
                a_boundary_exists = True
            if a_watershed.geoserver_gage_layer:
                # LOAD GAGE
                a_geoserver_info['gage'] = {
                    'name': a_watershed.geoserver_gage_layer.name,
                    'latlon_bbox':
                        json.loads(
                            a_watershed.geoserver_gage_layer.latlon_bbox),
                    'projection': a_watershed.geoserver_gage_layer.projection,
                }
                a_gage_exists = True

            if a_watershed.geoserver_ahps_station_layer:
                # LOAD AHPS STATION
                a_geoserver_info['ahps_station'] = {
                    'name': a_watershed.geoserver_ahps_station_layer
                                       .name,
                    'geojson': a_watershed.geoserver_ahps_station_layer
                                          .wfs_url,
                    'latlon_bbox': json.loads(
                        a_watershed.geoserver_ahps_station_layer
                                   .latlon_bbox
                    ),
                    'projection':
                        a_watershed.geoserver_ahps_station_layer
                                   .projection,
                }
                a_ahps_station_exists = True
            if a_watershed.geoserver_historical_flood_map_layer:
                # LOAD HISTORICAL FLOOD MAP
                a_geoserver_info['historical_flood_map'] = {
                    'name': a_watershed.geoserver_historical_flood_map_layer
                                       .name,
                    'latlon_bbox': json.loads(
                        a_watershed.geoserver_historical_flood_map_layer
                                   .latlon_bbox
                    ),
                    'projection':
                        a_watershed.geoserver_historical_flood_map_layer
                                   .projection,
                }
                a_historical_flood_map_exists = True

            if a_geoserver_info:
                a_layers_info.append(a_geoserver_info)

        return a_layers_info, a_boundary_exists, a_gage_exists, \
            a_historical_flood_map_exists, a_ahps_station_exists

    # get/check information from AJAX request
    post_info = request.GET
    watershed_ids = post_info.getlist('watershed_select')
    group_ids = post_info.getlist('watershed_group_select')

    if not watershed_ids and not group_ids:
        # send them home
        msg = "No watershed or watershed group selected. " \
              "Please select one to proceed."
        return redirect_with_message(request, "..", msg, severity="WARNING")

    session_maker = app.get_persistent_store_database('main_db',
                                                      as_sessionmaker=True)
    session = session_maker()

    # get base layer info
    path_to_ecmwf_rapid_output = \
        app.get_custom_setting('ecmwf_forecast_folder')

    watershed_list = []
    watershed_layers_info_array = []
    watershed_group_info_array = []
    flood_map_date_selectors = []
    available_forecast_dates = []

    if watershed_ids:
        watersheds = session.query(Watershed) \
            .order_by(Watershed.watershed_name,
                      Watershed.subbasin_name) \
            .filter(Watershed.id.in_(watershed_ids)) \
            .all()

        for watershed in watersheds:
            watershed_list.append((
                "%s (%s)" % (watershed.watershed_name,
                             watershed.subbasin_name),
                "%s:%s" % (watershed.watershed_clean_name,
                           watershed.subbasin_clean_name)
            ))
            # find/check current output datasets
            path_to_watershed_files = \
                os.path.join(
                    path_to_ecmwf_rapid_output,
                    "{0}-{1}".format(watershed.ecmwf_data_store_watershed_name,
                                     watershed.ecmwf_data_store_subbasin_name))
            if path_to_watershed_files and \
                    os.path.exists(path_to_watershed_files):
                available_forecast_dates = \
                    available_forecast_dates + \
                    get_ecmwf_valid_forecast_folder_list(
                        path_to_watershed_files, ".geojson")

        watershed_layers_info_array = get_watershed_layers_info(watersheds)[0]

        for watershed_layers_info in watershed_layers_info_array:
            valid_date_list = []
            flood_map_info = watershed_layers_info.get('predicted_flood_maps')
            if flood_map_info:
                geoserver_info_list = flood_map_info.get('geoserver_info_list')
                if geoserver_info_list:
                    for geoserver_info in geoserver_info_list:
                        if not geoserver_info.get('error'):
                            valid_date_list.append((
                                geoserver_info.get('forecast_timestamp'),
                                geoserver_info.get('forecast_directory')
                            ))
                if valid_date_list:
                    flood_map_date_selectors.append({
                        'name': 'flood_map_select',
                        'options': valid_date_list,
                        'placeholder': 'Select Forecast Date',
                        'original': True,
                        'classes': "flood_map_select",
                    })
                else:
                    flood_map_date_selectors.append(None)

    elif group_ids:
        for group_id in group_ids:
            try:
                int(group_id)
            except (TypeError, ValueError):
                # send them home
                msg = "Invalid Watershed Group ID: {0}".format(group_id)
                return redirect_with_message(request, "..", msg,
                                             severity="ERROR")

            watershed_group = session.query(WatershedGroup).get(group_id)

            layers_info, boundary_exists, gage_exists, \
                historical_flood_map_exists, ahps_station_exists = \
                get_watershed_layers_info(watershed_group.watersheds)

            watershed_group_info_array.append({
                'group_id': group_id,
                'group_name': watershed_group.name,
                'watershed_layers_info': layers_info,
                'boundary_exists': boundary_exists,
                'gage_exists': gage_exists,
                'historical_flood_map_exists': historical_flood_map_exists,
                'ahps_station_exists': ahps_station_exists,
            })

            for watershed in watershed_group.watersheds:
                watershed_list.append((
                    "%s (%s)" % (watershed.watershed_name,
                                 watershed.subbasin_name),
                    "%s:%s" % (watershed.watershed_clean_name,
                               watershed.subbasin_clean_name)
                ))

                # find/check current output datasets
                path_to_watershed_files = \
                    os.path.join(path_to_ecmwf_rapid_output,
                                 "{0}-{1}".format(
                                     watershed.ecmwf_data_store_watershed_name,
                                     watershed.ecmwf_data_store_subbasin_name)
                                 )
                if path_to_watershed_files and \
                        os.path.exists(path_to_watershed_files):
                    available_forecast_dates = \
                        available_forecast_dates + \
                        get_ecmwf_valid_forecast_folder_list(
                            path_to_watershed_files, ".geojson")

    # set up the inputs
    watershed_select = SelectInput(display_text='Select Watershed',
                                   name='watershed_select',
                                   options=watershed_list, )
    warning_point_date_select = None
    warning_point_forecast_folder = ""
    if available_forecast_dates:
        available_forecast_dates = sorted(available_forecast_dates,
                                          key=lambda k: k['id'], reverse=True)
        warning_point_forecast_folder = available_forecast_dates[0]['id']
        forecast_date_select_input = []
        for available_forecast_date in available_forecast_dates:
            next_row_info = (available_forecast_date['text'],
                             available_forecast_date['id'])
            if next_row_info not in forecast_date_select_input:
                forecast_date_select_input.append(next_row_info)

        warning_point_date_select = \
            SelectInput(display_text='Select Forecast Date',
                        name='warning_point_date_select',
                        options=forecast_date_select_input)

    units_toggle_switch = ToggleSwitch(display_text='Units:',
                                       name='units-toggle',
                                       on_label='Metric',
                                       off_label='English',
                                       size='mini',
                                       initial=True, )

    context = {
        'watershed_layers_info_array_json':
            json.dumps(watershed_layers_info_array),
        'watershed_layers_info_array': watershed_layers_info_array,
        'watershed_group_info_array_json':
            json.dumps(watershed_group_info_array),
        'watershed_group_info_array': watershed_group_info_array,
        'warning_point_forecast_folder': warning_point_forecast_folder,
        'base_layer_info': json.dumps({'name': 'esri'}),
        'watershed_select': watershed_select,
        'warning_point_date_select': warning_point_date_select,
        'units_toggle_switch': units_toggle_switch,
        'flood_map_date_selectors': flood_map_date_selectors,
        'flood_map_date_selectors_len': len(flood_map_date_selectors)
    }
    rendered_request = \
        render(request, 'streamflow_prediction_tool/map.html', context)
    session.close()
    return rendered_request


@require_GET
@user_passes_test(user_permission_test)
def add_watershed(request):
    """
    Controller for the app add_watershed page.
    """
    # initialize session
    session_maker = app.get_persistent_store_database('main_db',
                                                      as_sessionmaker=True)
    session = session_maker()

    watershed_name_input = \
        TextInput(display_text='Watershed Display Name',
                  name='watershed-name-input',
                  placeholder='e.g.: Magdalena',
                  icon_append='glyphicon glyphicon-home')

    subbasin_name_input = \
        TextInput(display_text='Subbasin Display Name',
                  name='subbasin-name-input',
                  placeholder='e.g.: El Banco',
                  icon_append='glyphicon glyphicon-tree-deciduous')

    # Query DB for data stores
    data_stores = session.query(DataStore).all()
    data_store_list = []
    for data_store in data_stores:
        data_store_list.append(("%s (%s)" % (data_store.name,
                                             data_store.api_endpoint),
                                data_store.id))

    data_store_select = SelectInput(display_text='Select a Data Store',
                                    name='data-store-select',
                                    options=data_store_list, )

    data_store_watershed_name_input = \
        TextInput(display_text='ECMWF Watershed Data Store Name',
                  name='ecmwf-data-store-watershed-name-input',
                  placeholder='e.g.: magdalena',
                  icon_append='glyphicon glyphicon-home')

    data_store_subbasin_name_input = \
        TextInput(display_text='ECMWF Subbasin Data Store Name',
                  name='ecmwf-data-store-subbasin-name-input',
                  placeholder='e.g.: el_banco',
                  icon_append='glyphicon glyphicon-tree-deciduous')

    # Query DB for geoservers
    geoservers = session.query(GeoServer).all()
    geoserver_list = []
    for geoserver in geoservers:
        geoserver_list.append(("%s (%s)" % (geoserver.name, geoserver.url),
                               geoserver.id))
    session.close()
    if geoserver_list:
        geoserver_select = SelectInput(display_text='Select a GeoServer',
                                       name='geoserver-select',
                                       options=geoserver_list, )
    else:
        geoserver_select = None

    geoserver_drainage_line_input = \
        TextInput(display_text='GeoServer Drainage Line Layer',
                  name='geoserver-drainage-line-input',
                  placeholder='e.g.: erfp:streams',
                  icon_append='glyphicon glyphicon-link')

    geoserver_boundary_input = \
        TextInput(display_text='GeoServer Boundary Layer (Optional)',
                  name='geoserver-boundary-input',
                  placeholder='e.g.: erfp:boundary',
                  icon_append='glyphicon glyphicon-link')

    geoserver_gage_input = \
        TextInput(display_text='GeoServer Gage Layer  (Optional)',
                  name='geoserver-gage-input',
                  placeholder='e.g.: erfp:gage',
                  icon_append='glyphicon glyphicon-link')

    geoserver_hist_flood_input = \
        TextInput(display_text='GeoServer Historical Flood Map '
                               'Layer Group (Optional)',
                  name='geoserver-historical-flood-map-input',
                  placeholder='e.g.: erfp:historical_flood_map',
                  icon_append='glyphicon glyphicon-link')

    geoserver_ahps_station_input = \
        TextInput(display_text='GeoServer AHPS Station Layer (Optional)',
                  name='geoserver-ahps-station-input',
                  placeholder='e.g.: erfp:ahps-station',
                  icon_append='glyphicon glyphicon-link')

    shp_upload_toggle_switch = ToggleSwitch(display_text='Upload Shapefile?',
                                            name='shp-upload-toggle',
                                            on_label='Yes',
                                            off_label='No',
                                            on_style='success',
                                            off_style='danger',
                                            initial=True, )

    add_button = Button(display_text='Add Watershed',
                        icon='glyphicon glyphicon-plus',
                        style='success',
                        name='submit-add-watershed',
                        attributes={'id': 'submit-add-watershed'}, )

    context = {
        'watershed_name_input': watershed_name_input,
        'subbasin_name_input': subbasin_name_input,
        'data_store_select': data_store_select,
        'data_store_watershed_name_input':
            data_store_watershed_name_input,
        'data_store_subbasin_name_input':
            data_store_subbasin_name_input,
        'geoserver_select': geoserver_select,
        'geoserver_drainage_line_input': geoserver_drainage_line_input,
        'geoserver_boundary_input': geoserver_boundary_input,
        'geoserver_gage_input': geoserver_gage_input,
        'geoserver_historical_flood_map_input':
            geoserver_hist_flood_input,
        'geoserver_ahps_station_input': geoserver_ahps_station_input,
        'shp_upload_toggle_switch': shp_upload_toggle_switch,
        'add_button': add_button,
    }

    return render(request, 'streamflow_prediction_tool/add_watershed.html',
                  context)


@user_passes_test(user_permission_test)
def manage_watersheds(request):
    """
    Controller for the app manage_watersheds page.
    """
    edit_modal = MessageBox(name='edit_watershed_modal',
                            title='Edit Watershed',
                            message='Loading ...',
                            dismiss_button='Nevermind',
                            affirmative_button='Save Changes',
                            affirmative_attributes='id=edit_modal_submit',
                            width=500)

    context = {
        'watersheds': get_sorted_watershed_list(),
        'edit_modal': edit_modal,
    }

    return render(request, 'streamflow_prediction_tool/manage_watersheds.html',
                  context)


@require_GET
@user_passes_test(user_permission_test)
def manage_watersheds_table(request):
    """
    Controller for the app manage_watersheds page.
    """
    shp_upload_toggle_switch = ToggleSwitch(name='shp-upload-toggle',
                                            on_label='Yes',
                                            off_label='No',
                                            on_style='success',
                                            off_style='danger',
                                            initial=False, )

    context = {
        'watersheds': get_sorted_watershed_list(),
        'shp_upload_toggle_switch': shp_upload_toggle_switch,
    }

    return render(request,
                  'streamflow_prediction_tool/manage_watersheds_table.html',
                  context)


@require_GET
@user_passes_test(user_permission_test)
def edit_watershed(request):
    """
    Controller for the app manage_watersheds page.
    """
    # get/check information from AJAX request
    watershed_id = request.GET.get('watershed_id')

    # initialize session
    session_maker = app.get_persistent_store_database('main_db',
                                                      as_sessionmaker=True)
    session = session_maker()
    # get desired watershed
    watershed = session.query(Watershed).get(watershed_id)

    watershed_name_input = \
        TextInput(display_text='Watershed Name',
                  name='watershed-name-input',
                  placeholder='e.g.: magdalena',
                  icon_append='glyphicon glyphicon-home',
                  initial=watershed.watershed_name)

    subbasin_name_input = \
        TextInput(display_text='Subbasin Name',
                  name='subbasin-name-input',
                  placeholder='e.g.: el_banco',
                  icon_append='glyphicon glyphicon-tree-deciduous',
                  initial=watershed.subbasin_name)

    # Query DB for data stores
    data_stores = session.query(DataStore).all()
    data_store_list = []
    for data_store in data_stores:
        data_store_list.append((
            "%s (%s)" % (data_store.name, data_store.api_endpoint),
            data_store.id
        ))

    data_store_select = \
        SelectInput(display_text='Select a Data Store',
                    name='data-store-select',
                    options=data_store_list,
                    initial=["%s (%s)" % (watershed.data_store.name,
                                          watershed.data_store.api_endpoint)])

    data_store_watershed_name_input = \
        TextInput(display_text='ECMWF Watershed Data Store Name',
                  name='ecmwf-data-store-watershed-name-input',
                  placeholder='e.g.: magdalena',
                  icon_append='glyphicon glyphicon-home',
                  initial=watershed.ecmwf_data_store_watershed_name)

    data_store_subbasin_name_input = \
        TextInput(display_text='ECMWF Subbasin Data Store Name',
                  name='ecmwf-data-store-subbasin-name-input',
                  placeholder='e.g.: el_banco',
                  icon_append='glyphicon glyphicon-tree-deciduous',
                  initial=watershed.ecmwf_data_store_subbasin_name)

    # Query DB for geoservers
    geoservers = session.query(GeoServer).all()
    geoserver_list = []
    for geoserver in geoservers:
        geoserver_list.append(("%s (%s)" % (geoserver.name, geoserver.url),
                               geoserver.id))

    geoserver_select = SelectInput(display_text='Select a GeoServer',
                                   name='geoserver-select',
                                   options=geoserver_list,
                                   initial=["%s (%s)" %
                                            (watershed.geoserver.name,
                                             watershed.geoserver.url)])

    geoserver_drainage_line_input = TextInput(
        display_text='GeoServer Drainage Line Layer',
        name='geoserver-drainage-line-input',
        placeholder='e.g.: erfp:streams',
        icon_append='glyphicon glyphicon-link',
        initial=watershed.geoserver_drainage_line_layer.name
                    if watershed.geoserver_drainage_line_layer else "")

    geoserver_boundary_input = TextInput(
        display_text='GeoServer Boundary Layer (Optional)',
        name='geoserver-boundary-input',
        placeholder='e.g.: erfp:boundary',
        icon_append='glyphicon glyphicon-link',
        initial=watershed.geoserver_boundary_layer.name
                    if watershed.geoserver_boundary_layer else "")

    geoserver_gage_input = TextInput(
        display_text='GeoServer Gage Layer (Optional)',
        name='geoserver-gage-input',
        placeholder='e.g.: erfp:gage',
        icon_append='glyphicon glyphicon-link',
        initial=watershed.geoserver_gage_layer.name
                    if watershed.geoserver_gage_layer else "")

    geoserver_hist_flood_input = TextInput(
        display_text='GeoServer Historical Flood Map Layer Group (Optional)',
        name='geoserver-historical-flood-map-input',
        placeholder='e.g.: erfp:historical_flood_map',
        icon_append='glyphicon glyphicon-link',
        initial=watershed.geoserver_historical_flood_map_layer.name
                    if watershed.geoserver_historical_flood_map_layer else "")

    geoserver_ahps_station_input = TextInput(
        display_text='GeoServer AHPS Station Layer (Optional)',
        name='geoserver-ahps-station-input',
        placeholder='e.g.: erfp:ahps-station',
        icon_append='glyphicon glyphicon-link',
        initial=watershed.geoserver_ahps_station_layer.name
                    if watershed.geoserver_ahps_station_layer else "")

    shp_upload_toggle_switch = ToggleSwitch(display_text='Upload Shapefile?',
                                            name='shp-upload-toggle',
                                            on_label='Yes',
                                            off_label='No',
                                            on_style='success',
                                            off_style='danger',
                                            initial=False)

    add_button = Button(display_text='Add Watershed',
                        icon='glyphicon glyphicon-plus',
                        style='success',
                        name='submit-add-watershed',
                        attributes={'id': 'submit-add-watershed'}, )

    context = {
        'watershed_name_input': watershed_name_input,
        'subbasin_name_input': subbasin_name_input,
        'data_store_select': data_store_select,
        'data_store_watershed_name_input':
            data_store_watershed_name_input,
        'data_store_subbasin_name_input':
            data_store_subbasin_name_input,
        'geoserver_select': geoserver_select,
        'geoserver_drainage_line_input': geoserver_drainage_line_input,
        'geoserver_boundary_input': geoserver_boundary_input,
        'geoserver_gage_input': geoserver_gage_input,
        'geoserver_historical_flood_map_input':
            geoserver_hist_flood_input,
        'geoserver_ahps_station_input': geoserver_ahps_station_input,
        'shp_upload_toggle_switch': shp_upload_toggle_switch,
        'add_button': add_button,
        'watershed': watershed,
    }
    page_html = render(request,
                       'streamflow_prediction_tool/edit_watershed.html',
                       context)
    session.close()

    return page_html


@require_GET
@user_passes_test(user_permission_test)
def add_data_store(request):
    """
    Controller for the app add_data_store page.
    """
    # initialize session
    session_maker = app.get_persistent_store_database('main_db',
                                                      as_sessionmaker=True)
    session = session_maker()

    data_store_name_input = TextInput(display_text='Data Store Server Name',
                                      name='data-store-name-input',
                                      placeholder='e.g.: My CKAN Server',
                                      icon_append='glyphicon glyphicon-tag')

    # Query DB for data store types
    data_store_types = session.query(DataStoreType).filter(
        DataStoreType.id > 1).all()
    data_store_type_list = []
    for data_store_type in data_store_types:
        data_store_type_list.append((data_store_type.human_readable_name,
                                     data_store_type.id))

    session.close()

    data_store_type_select_input = \
        SelectInput(display_text='Data Store Type',
                    name='data-store-type-select',
                    options=data_store_type_list,
                    initial=data_store_type_list[0][0])

    data_store_endpoint_input = TextInput(
        display_text='Data Store API Endpoint',
        name='data-store-endpoint-input',
        placeholder='e.g.: http://ciwweb.chpc.utah.edu/api/3/action',
        icon_append='glyphicon glyphicon-cloud-download')

    data_store_owner_org_input = TextInput(
        display_text='Data Store Owner Organization',
        name='data-store-owner_org-input',
        placeholder='e.g.: byu',
        icon_append='glyphicon glyphicon-home')

    add_button = Button(display_text='Add Data Store',
                        icon='glyphicon glyphicon-plus',
                        style='success',
                        name='submit-add-data-store',
                        attributes={'id': 'submit-add-data-store'})

    context = {
        'data_store_name_input': data_store_name_input,
        'data_store_type_select_input': data_store_type_select_input,
        'data_store_endpoint_input': data_store_endpoint_input,
        'data_store_owner_org_input': data_store_owner_org_input,
        'add_button': add_button,
    }

    return render(request, 'streamflow_prediction_tool/add_data_store.html',
                  context)


@require_GET
@user_passes_test(user_permission_test)
def manage_data_stores(request):
    """
    Controller for the app manage_data_stores page.
    """
    return render_manage_data_store_pages(request, 'manage_data_stores.html')


@require_GET
@user_passes_test(user_permission_test)
def manage_data_stores_table(request):
    """
    Controller for the app manage_data_stores page.
    """
    return render_manage_data_store_pages(request,
                                          'manage_data_stores_table.html')


@require_GET
@user_passes_test(user_permission_test)
def add_geoserver(request):
    """
    Controller for the app add_geoserver page.
    """
    geoserver_name_input = TextInput(display_text='GeoServer Name',
                                     name='geoserver-name-input',
                                     placeholder='e.g.: My GeoServer',
                                     icon_append='glyphicon glyphicon-tag')

    geoserver_url_input = \
        TextInput(display_text='GeoServer Url',
                  name='geoserver-url-input',
                  placeholder='e.g.: http://localhost:8181/geoserver',
                  icon_append='glyphicon glyphicon-cloud-download')

    geoserver_username_input = \
        TextInput(display_text='GeoServer Username',
                  name='geoserver-username-input',
                  placeholder='e.g.: admin',
                  icon_append='glyphicon glyphicon-user')

    add_button = Button(display_text='Add GeoServer',
                        icon='glyphicon glyphicon-plus',
                        style='success',
                        name='submit-add-geoserver',
                        attributes={'id': 'submit-add-geoserver'})

    context = {
        'geoserver_name_input': geoserver_name_input,
        'geoserver_url_input': geoserver_url_input,
        'geoserver_username_input': geoserver_username_input,
        'add_button': add_button,
    }

    return render(request, 'streamflow_prediction_tool/add_geoserver.html',
                  context)


@require_GET
@user_passes_test(user_permission_test)
def manage_geoservers(request):
    """
    Controller for the app manage_geoservers page.
    """
    return render_manage_geoserver_pages(request, 'manage_geoservers.html')


@require_GET
@user_passes_test(user_permission_test)
def manage_geoservers_table(request):
    """
    Controller for the app manage_geoservers page.
    """
    return render_manage_geoserver_pages(request,
                                         'manage_geoservers_table.html')


@require_GET
@user_passes_test(user_permission_test)
def add_watershed_group(request):
    """
    Controller for the app add_watershed_group page.
    """
    watershed_group_name_input = \
        TextInput(display_text='Watershed Group Name',
                  name='watershed-group-name-input',
                  placeholder='e.g.: My Watershed Group',
                  icon_append='glyphicon glyphicon-tag')

    # initialize session
    session_maker = app.get_persistent_store_database('main_db',
                                                      as_sessionmaker=True)
    session = session_maker()
    # Query DB for settings
    watersheds = session.query(Watershed) \
        .order_by(Watershed.watershed_name,
                  Watershed.subbasin_name) \
        .all()
    watershed_list = []
    for watershed in watersheds:
        watershed_list.append(("%s (%s)" %
                               (watershed.watershed_name,
                                watershed.subbasin_name),
                               watershed.id))

    session.close()

    watershed_select = SelectInput(
        display_text='Select Watershed(s) to Add to Group',
        name='watershed_select',
        options=watershed_list,
        multiple=True, )

    add_button = Button(display_text='Add Watershed Group',
                        icon='glyphicon glyphicon-plus',
                        style='success',
                        name='submit-add-watershed-group',
                        attributes={'id': 'submit-add-watershed-group'})

    context = {
        'watershed_group_name_input': watershed_group_name_input,
        'watershed_select': watershed_select,
        'add_button': add_button,
    }
    return render(request,
                  'streamflow_prediction_tool/add_watershed_group.html',
                  context)


@require_GET
@user_passes_test(user_permission_test)
def manage_watershed_groups(request):
    """
    Controller for the app manage_watershed_groups page.
    """
    return render_manage_watershed_groups_pages(request,
                                                'manage_watershed_groups.html')


@require_GET
@user_passes_test(user_permission_test)
def manage_watershed_groups_table(request):
    """
    Controller for the app manage_watershed_groups page.
    """
    return render_manage_watershed_groups_pages(
        request, 'manage_watershed_groups_table.html')


@require_GET
@user_passes_test(user_permission_test)
def getting_started(request):
    """
    Controller for the app getting started page.
    """

    return render(request, 'streamflow_prediction_tool/getting_started.html',
                  {})


@require_GET
@login_required
def publications(request):
    """
    Controller for the app publications page.
    """

    return render(request, 'streamflow_prediction_tool/publications.html', {})
