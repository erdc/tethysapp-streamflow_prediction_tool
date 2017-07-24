# -*- coding: utf-8 -*-
##
##  controllers.py
##  streamflow_prediction_tool
##
##  Created by Alan D. Snow, Curtis Rae, Shawn Crawley.
##  Copyright © 2015-2016 Alan D Snow, Curtis Rae, Shawn Crawley. All rights reserved.
##  License: BSD 3-Clause

#from glob import glob
import json
import os
#from datetime import datetime, timedelta

#django imports
from django.contrib.auth.decorators import user_passes_test, login_required
from django.shortcuts import render
#tethys imports
from tethys_sdk.gizmos import (Button, MessageBox, SelectInput, 
                               TextInput, ToggleSwitch)

#local imports
#from spt_dataset_manager.dataset_manager import GeoServerDatasetManager
from .app import StreamflowPredictionTool as app
from .model import (BaseLayer, DataStore, DataStoreType, Geoserver,
                    MainSettings, Watershed, WatershedGroup)
from .functions import (ecmwf_get_valid_forecast_folder_list,
                        format_watershed_title,
                        redirect_with_message,
                        user_permission_test)

@login_required
def home(request):
    """
    Controller for the app home page.
    """
    #get the base layer information
    session_maker = app.get_persistent_store_database('main_db', as_sessionmaker=True)
    session = session_maker()
    #Query DB for settings
    watersheds  = session.query(Watershed) \
                            .order_by(Watershed.watershed_name,
                                      Watershed.subbasin_name) \
                             .all()
    watershed_list = []
    for watershed in watersheds:
        watershed_list.append(("%s (%s)" % (watershed.watershed_name, watershed.subbasin_name),
                               watershed.id))
    watershed_groups = []
    groups  = session.query(WatershedGroup).order_by(WatershedGroup.name).all()
    session.close()
    for group in groups:
        watershed_groups.append((group.name,group.id))
    
    watershed_select = SelectInput(display_text='Select Watershed(s)',
                                   name='watershed_select',
                                   options=watershed_list,
                                   multiple=True,)
                                   
    watershed_group_select = SelectInput(display_text='Select Watershed Group(s)',
                                         name='watershed_group_select',
                                         options=watershed_groups,
                                         multiple=True,)
    context = {
                'watershed_select' : watershed_select,
                'watersheds_length': len(watersheds),
                'watershed_group_select' : watershed_group_select,
                'watershed_group_length': len(groups),
              }

    return render(request, 'streamflow_prediction_tool/home.html', context)

@login_required
def map(request):
    """
    Controller for the app map page.
    """
    if request.method == 'GET':
        #-------------------------------------------------------------------------------
        #HELPER FUNCTIONS
        #-------------------------------------------------------------------------------        
        def find_add_attribute_ci(attribute, layer_attributes, contained_attributes):
            """
            Case insensitive attribute search and add
            """
            for layer_attribute in layer_attributes:    
                if layer_attribute.lower() == attribute.lower():
                    contained_attributes.append(layer_attribute)
                    return True
            return False

        def get_watershed_layers_info(watershed_list):
            """
            This gets the information about the watershed layers
            """
            layers_info = []
            boundary_exists = False
            gage_exists = False
            ahps_station_exists = False
            historical_flood_map_exists = False            
            #add layer urls to list and add their navigation items as well
            for watershed in watershed_list:
                ecmwf_watershed_name = watershed.ecmwf_data_store_watershed_name if \
                                       watershed.ecmwf_data_store_watershed_name else watershed.watershed_name
                ecmwf_subbasin_name = watershed.ecmwf_data_store_subbasin_name if \
                                       watershed.ecmwf_data_store_subbasin_name else watershed.subbasin_name
                # (get geoserver info)
                #get wms/api url
                geoserver_wms_url = watershed.geoserver.url
                geoserver_api_url = watershed.geoserver.url
                if watershed.geoserver.url.endswith('/geoserver/rest'):
                    geoserver_wms_url = "%s/ows" % "/".join(watershed.geoserver.url.split("/")[:-1])
                elif watershed.geoserver.url.endswith('/geoserver'):
                    geoserver_wms_url = "%s/ows" % watershed.geoserver.url
                    geoserver_api_url = "%s/rest" % watershed.geoserver.url
                    
                geoserver_info = {'watershed': watershed.watershed_clean_name, 
                                  'subbasin': watershed.subbasin_clean_name,
                                  'ecmwf_watershed' : ecmwf_watershed_name,
                                  'ecmwf_subbasin' : ecmwf_subbasin_name,
                                  'geoserver_url': geoserver_wms_url,
                                  'title' : format_watershed_title(watershed.watershed_name,
                                                                   watershed.subbasin_name),
                                  'id' : watershed.id,
                                  }
                
                #LOAD DRAINAGE LINE
                layer_attributes = json.loads(watershed.geoserver_drainage_line_layer.attribute_list)
                missing_attributes = []
                contained_attributes = []
                #check required attributes
                #necessary_attributes = ['COMID','watershed', 'subbasin', 'wwatershed','wsubbasin']
                
                #check COMID/HydroID attribute
                if not find_add_attribute_ci('COMID', layer_attributes, contained_attributes):
                    if not find_add_attribute_ci('HydroID', layer_attributes, contained_attributes):
                        missing_attributes.append('COMID or HydroID')
                
                #check ECMWF watershed/subbasin attributes
                if not find_add_attribute_ci('watershed', layer_attributes, contained_attributes) \
                or not find_add_attribute_ci('subbasin', layer_attributes, contained_attributes):
                    missing_attributes.append('watershed')
                    missing_attributes.append('subbasin')
                    
                #check WRF-Hydro watershed/subbasin attributes
                if not find_add_attribute_ci('wwatershed', layer_attributes, contained_attributes) \
                or not find_add_attribute_ci('wsubbasin', layer_attributes, contained_attributes):
                    missing_attributes.append('wwatershed')
                    missing_attributes.append('wsubbasin')
                    
                #check optional attributes
                optional_attributes = ['usgs_id', 'nws_id', 'hydroserve']
                for optional_attribute in optional_attributes:
                    find_add_attribute_ci(optional_attribute, layer_attributes, contained_attributes)
                    
                geoserver_info['drainage_line'] = {'name': watershed.geoserver_drainage_line_layer.name,
                                                   'geojson': watershed.geoserver_drainage_line_layer.wfs_url,
                                                   'latlon_bbox': json.loads(watershed.geoserver_drainage_line_layer.latlon_bbox),
                                                   'projection': watershed.geoserver_drainage_line_layer.projection,
                                                   'contained_attributes': contained_attributes,
                                                   'missing_attributes': missing_attributes,
                                                   }
                #check if needed attribute is there to perfrom query based rendering of layer
                query_attribute = []
                if find_add_attribute_ci('Natur_Flow', layer_attributes, query_attribute):
                    geoserver_info['drainage_line']['geoserver_method'] = "natur_flow_query"
                    geoserver_info['drainage_line']['geoserver_query_attribute'] = query_attribute[0]
                elif find_add_attribute_ci('RiverOrder', layer_attributes, query_attribute):
                    geoserver_info['drainage_line']['geoserver_method'] = "river_order_query"
                    geoserver_info['drainage_line']['geoserver_query_attribute'] = query_attribute[0]
                else:
                    geoserver_info['drainage_line']['geoserver_method'] = "simple"
                
                if watershed.geoserver_boundary_layer:
                    #LOAD BOUNDARY
                    geoserver_info['boundary'] = {'name': watershed.geoserver_boundary_layer.name,
                                                  'latlon_bbox': json.loads(watershed.geoserver_boundary_layer.latlon_bbox),
                                                  'projection': watershed.geoserver_boundary_layer.projection,
                                                  }
                    boundary_exists = True
                if watershed.geoserver_gage_layer:
                    #LOAD GAGE
                    geoserver_info['gage'] = {'name': watershed.geoserver_gage_layer.name,
                                              'latlon_bbox': json.loads(watershed.geoserver_gage_layer.latlon_bbox),
                                              'projection': watershed.geoserver_gage_layer.projection,
                                              }
                    gage_exists = True
    
                if watershed.geoserver_ahps_station_layer:
                    #LOAD AHPS STATION
                    geoserver_info['ahps_station'] = {'name': watershed.geoserver_ahps_station_layer.name,
                                                      'geojson': watershed.geoserver_ahps_station_layer.wfs_url,
                                                      'latlon_bbox': json.loads(watershed.geoserver_ahps_station_layer.latlon_bbox),
                                                      'projection': watershed.geoserver_ahps_station_layer.projection,
                                                      }
                    ahps_station_exists = True                                  
                if watershed.geoserver_historical_flood_map_layer:
                    #LOAD HISTORICAL FLOOD MAP
                    geoserver_info['historical_flood_map'] = {'name': watershed.geoserver_historical_flood_map_layer.name,
                                                              'latlon_bbox': json.loads(watershed.geoserver_historical_flood_map_layer.latlon_bbox),
                                                              'projection': watershed.geoserver_historical_flood_map_layer.projection,
                                                              }
                    historical_flood_map_exists = True

                if geoserver_info:                
                    layers_info.append(geoserver_info)
                
            return layers_info, boundary_exists, gage_exists, historical_flood_map_exists, ahps_station_exists

        #get/check information from AJAX request
        post_info = request.GET
        watershed_ids = post_info.getlist('watershed_select')
        group_ids = post_info.getlist('watershed_group_select')
        
        if not watershed_ids and not group_ids:
            #send them home
            msg = "No watershed or watershed group selected. Please select one to proceed."
            return redirect_with_message(request, "..", msg, severity="WARNING")

        session_maker = app.get_persistent_store_database('main_db', as_sessionmaker=True)
        session = session_maker()

        #get base layer info
        main_settings  = session.query(MainSettings).order_by(MainSettings.id).first()
        base_layer = main_settings.base_layer
        path_to_ecmwf_rapid_output = main_settings.ecmwf_rapid_prediction_directory
        
        watershed_list = []
        watershed_layers_info_array = []
        watershed_group_info_array = []
        flood_map_date_selectors = []
        available_forecast_dates = []

        if watershed_ids:
            watersheds  = session.query(Watershed) \
                            .order_by(Watershed.watershed_name,
                                      Watershed.subbasin_name) \
                            .filter(Watershed.id.in_(watershed_ids)) \
                            .all()
            
            for watershed in watersheds:
                watershed_list.append(("%s (%s)" % (watershed.watershed_name, watershed.subbasin_name),
                                       "%s:%s" % (watershed.watershed_clean_name, watershed.subbasin_clean_name)))
                #find/check current output datasets    
                path_to_watershed_files = os.path.join(path_to_ecmwf_rapid_output, "{0}-{1}".format(watershed.ecmwf_data_store_watershed_name, 
                                                                                                    watershed.ecmwf_data_store_subbasin_name))
                if path_to_watershed_files and os.path.exists(path_to_watershed_files):                                                                                  
                    available_forecast_dates = available_forecast_dates + ecmwf_get_valid_forecast_folder_list(path_to_watershed_files, ".txt")

            watershed_layers_info_array = get_watershed_layers_info(watersheds)[0]

            for watershed_layers_info in watershed_layers_info_array:
                valid_date_list = []
                flood_map_info = watershed_layers_info.get('predicted_flood_maps')
                if flood_map_info:
                    geoserver_info_list = flood_map_info.get('geoserver_info_list')
                    if geoserver_info_list:
                        for geoserver_info in geoserver_info_list:
                            if not geoserver_info.get('error'):
                                valid_date_list.append((geoserver_info.get('forecast_timestamp'),
                                                        geoserver_info.get('forecast_directory')))
                    if valid_date_list:
                        flood_map_date_selectors.append({
                                                        'name': 'flood_map_select',
                                                        'options': valid_date_list,
                                                        'placeholder': 'Select Forecast Date',
                                                        'original' : True,
                                                        'classes' : "flood_map_select"
                                                       })
                    else:
                        flood_map_date_selectors.append(None)
                        
        elif group_ids:
            for group_id in group_ids:
                try:
                    int(group_id)
                except TypeError, ValueError:
                    #send them home
                    msg = "Invalid Watershed Group ID: {0}".format(group_id)
                    return redirect_with_message(request, "..", msg, severity="ERROR")
                    
                watershed_group  = session.query(WatershedGroup).get(group_id)
                
                layers_info, boundary_exists, gage_exists, historical_flood_map_exists, ahps_station_exists =\
                    get_watershed_layers_info(watershed_group.watersheds)
                
                watershed_group_info_array.append({'group_id' : group_id,
                                                   'group_name' : watershed_group.name,
                                                   'watershed_layers_info' : layers_info,
                                                   'boundary_exists' : boundary_exists,
                                                   'gage_exists' : gage_exists,
                                                   'historical_flood_map_exists' : historical_flood_map_exists,
                                                   'ahps_station_exists' : ahps_station_exists,
                                                  })

                for watershed in watershed_group.watersheds:
                    watershed_list.append(("%s (%s)" % (watershed.watershed_name, watershed.subbasin_name),
                                           "%s:%s" % (watershed.watershed_clean_name, watershed.subbasin_clean_name)))
                                           
                    #find/check current output datasets    
                    path_to_watershed_files = os.path.join(path_to_ecmwf_rapid_output, "{0}-{1}".format(watershed.ecmwf_data_store_watershed_name, 
                                                                                                        watershed.ecmwf_data_store_subbasin_name))
                    if path_to_watershed_files and os.path.exists(path_to_watershed_files):                                                                                  
                        available_forecast_dates = available_forecast_dates + ecmwf_get_valid_forecast_folder_list(path_to_watershed_files, ".txt")


        #set up the inputs            
        watershed_select = SelectInput(display_text='Select Watershed',
                                       name='watershed_select',
                                       options=watershed_list,)
        warning_point_date_select = None
        warning_point_start_folder = None                               
        if available_forecast_dates:
            available_forecast_dates = sorted(available_forecast_dates, key=lambda k: k['id'], reverse=True)
            warning_point_start_folder = available_forecast_dates[0]['id']
            available_forecast_date_select_input = []
            for available_forecast_date in available_forecast_dates:
                next_row_info = (available_forecast_date['text'], available_forecast_date['id'])
                if next_row_info not in available_forecast_date_select_input:
                    available_forecast_date_select_input.append(next_row_info)
            warning_point_date_select = SelectInput(display_text='Select Forecast Date',
                                                    name='warning_point_date_select',
                                                    options=available_forecast_date_select_input,)
                                       
        units_toggle_switch = ToggleSwitch(display_text='Units',
                                           name='units-toggle',
                                           on_label='Metric',
                                           off_label='English',
                                           initial=True,)

        ecmwf_toggle_switch = ToggleSwitch(display_text="ECMWF",
                                           name='ecmwf-toggle',
                                           on_style='success',
                                           initial=True,)

        wrf_toggle_switch =  ToggleSwitch(display_text="WRF-Hydro",
                                          name='wrf-toggle',
                                          on_style='warning',
                                          initial=False,)

     
        base_layer_info = {
                            'name': base_layer.name,
                            'api_key':base_layer.api_key,
                          }
                          
        context = {
                    'watershed_layers_info_array_json' : json.dumps(watershed_layers_info_array),
                    'watershed_layers_info_array': watershed_layers_info_array,
                    'watershed_group_info_array_json': json.dumps(watershed_group_info_array),
                    'watershed_group_info_array': watershed_group_info_array,
                    'warning_point_start_folder': warning_point_start_folder,
                    'base_layer_info' : json.dumps(base_layer_info),
                    'watershed_select' : watershed_select,
                    'warning_point_date_select' : warning_point_date_select,
                    'units_toggle_switch' : units_toggle_switch,
                    'ecmwf_toggle_switch' : ecmwf_toggle_switch,
                    'wrf_toggle_switch' : wrf_toggle_switch,
                    'flood_map_date_selectors' : flood_map_date_selectors,
                    'flood_map_date_selectors_len' : len(flood_map_date_selectors)
                  }
        rendered_request = render(request, 'streamflow_prediction_tool/map.html', context)
        session.close()
        return rendered_request
    #send home
    msg = 'Invalid Request Method.'
    return redirect_with_message(request, "..", msg, severity="WARNING")


@user_passes_test(user_permission_test)
def settings(request):
    """
    Controller for the app settings page.
    """
    
    session_maker = app.get_persistent_store_database('main_db', as_sessionmaker=True)
    session = session_maker()
    # Query DB for base layers
    base_layers = session.query(BaseLayer).all()
    base_layer_list = []
    base_layer_api_keys = {}
    for base_layer in base_layers:
        base_layer_list.append((base_layer.name, base_layer.id))
        base_layer_api_keys[base_layer.id] = base_layer.api_key

    #Query DB for settings
    main_settings  = session.query(MainSettings).order_by(MainSettings.id).first()

    base_layer_select_input = SelectInput(display_text='Select a Base Layer',
                                          name='base-layer-select',
                                          multiple=False,
                                          options=base_layer_list,
                                          initial=main_settings.base_layer.name,)

    base_layer_api_key_input = TextInput(display_text='Base Layer API Key',
                                         name='api-key-input',
                                         placeholder='e.g.: a1b2c3-d4e5d6-f7g8h9',
                                         icon_append='glyphicon glyphicon-lock',
                                         initial=main_settings.base_layer.api_key,)
              
    ecmwf_rapid_directory_input = TextInput(display_text='Server Folder Location of ECMWF-RAPID files',
                                            name='ecmwf-rapid-location-input',
                                            placeholder='e.g.: /home/username/work/rapid/ecmwf_output',
                                            icon_append='glyphicon glyphicon-folder-open',
                                            initial=main_settings.ecmwf_rapid_prediction_directory,)

    era_interim_rapid_directory_input = TextInput(display_text='Server Folder Location of ERA Interim RAPID files',
                                                  name='era-interim-rapid-location-input',
                                                  placeholder='e.g.: /home/username/work/rapid/era_interim',
                                                  icon_append='glyphicon glyphicon-folder-open',
                                                  initial=main_settings.era_interim_rapid_directory,)
              
    wrf_hydro_rapid_directory_input = TextInput(display_text='Server Folder Location of WRF-Hydro RAPID files',
                                                name='wrf-hydro-rapid-location-input',
                                                placeholder='e.g.: /home/username/work/rapid/wrf_output',
                                                icon_append='glyphicon glyphicon-folder-open',
                                                initial=main_settings.wrf_hydro_rapid_prediction_directory,)
              
    submit_button = Button(display_text='Submit',
                           name='submit-changes-settings',
                           attributes={'id':'submit-changes-settings'},)
              
    context = {
                'base_layer_select_input': base_layer_select_input,
                'base_layer_api_key_input': base_layer_api_key_input,
                'ecmwf_rapid_input': ecmwf_rapid_directory_input,
                'era_interim_rapid_input': era_interim_rapid_directory_input,
                'wrf_hydro_rapid_input':wrf_hydro_rapid_directory_input,
                'submit_button': submit_button,
                'base_layer_api_keys': json.dumps(base_layer_api_keys),
                'app_instance_id': main_settings.app_instance_id,
              }
    session.close()
    
    return render(request, 'streamflow_prediction_tool/settings.html', context)


@user_passes_test(user_permission_test)
def add_watershed(request):
    """
    Controller for the app add_watershed page.
    """
    #initialize session
    session_maker = app.get_persistent_store_database('main_db', as_sessionmaker=True)
    session = session_maker()

    watershed_name_input = TextInput(display_text='Watershed Display Name',
                                     name='watershed-name-input',
                                     placeholder='e.g.: Magdalena',
                                     icon_append='glyphicon glyphicon-home',
                                     )
              
    subbasin_name_input = TextInput(display_text='Subbasin Display Name',
                                    name='subbasin-name-input',
                                    placeholder='e.g.: El Banco',
                                    icon_append='glyphicon glyphicon-tree-deciduous',
                                    )
    # Query DB for data stores
    data_stores = session.query(DataStore).all()
    data_store_list = []
    for data_store in data_stores:
        data_store_list.append(("%s (%s)" % (data_store.name, data_store.api_endpoint),
                                 data_store.id))

    data_store_select = SelectInput(display_text='Select a Data Store',
                                    name='data-store-select',
                                    options=data_store_list,)
              
    ecmwf_data_store_watershed_name_input = TextInput(display_text='ECMWF Watershed Data Store Name',
                                                      name='ecmwf-data-store-watershed-name-input',
                                                      placeholder='e.g.: magdalena',
                                                      icon_append='glyphicon glyphicon-home',)
              
    ecmwf_data_store_subbasin_name_input = TextInput(display_text='ECMWF Subbasin Data Store Name',
                                                     name='ecmwf-data-store-subbasin-name-input',
                                                     placeholder='e.g.: el_banco',
                                                     icon_append='glyphicon glyphicon-tree-deciduous',)

    wrf_hydro_data_store_watershed_name_input = TextInput(display_text='WRF-Hydro Watershed Data Store Name',
                                                          name='wrf-hydro-data-store-watershed-name-input',
                                                          placeholder='e.g.: nfie_wrfhydro_conus',
                                                          icon_append='glyphicon glyphicon-home',)
              
    wrf_hydro_data_store_subbasin_name_input = TextInput(display_text='WRF-Hydro Subbasin Data Store Name',
                                                         name='wrf-hydro-data-store-subbasin-name-input',
                                                         placeholder='e.g.: nfie_wrfhydro_conus',
                                                         icon_append='glyphicon glyphicon-tree-deciduous')

    # Query DB for geoservers
    geoservers = session.query(Geoserver).all()
    geoserver_list = []
    for geoserver in geoservers:
        geoserver_list.append(( "%s (%s)" % (geoserver.name, geoserver.url), 
                               geoserver.id))
    session.close()
    if geoserver_list:
        geoserver_select = SelectInput(display_text='Select a Geoserver',
                                       name='geoserver-select',
                                       options=geoserver_list,)
    else:
        geoserver_select = None
                                   
    geoserver_drainage_line_input = TextInput(display_text='Geoserver Drainage Line Layer',
                                              name='geoserver-drainage-line-input',
                                              placeholder='e.g.: erfp:streams',
                                              icon_append='glyphicon glyphicon-link')
              
    geoserver_boundary_input = TextInput(display_text='Geoserver Boundary Layer (Optional)',
                                         name='geoserver-boundary-input',
                                         placeholder='e.g.: erfp:boundary',
                                         icon_append='glyphicon glyphicon-link')
              
    geoserver_gage_input = TextInput(display_text='Geoserver Gage Layer  (Optional)',
                                     name='geoserver-gage-input',
                                     placeholder='e.g.: erfp:gage',
                                     icon_append='glyphicon glyphicon-link')

    geoserver_historical_flood_map_input = TextInput(display_text='Geoserver Historical Flood Map Layer Group (Optional)',
                                                     name='geoserver-historical-flood-map-input',
                                                     placeholder='e.g.: erfp:historical_flood_map',
                                                     icon_append='glyphicon glyphicon-link')

    geoserver_ahps_station_input = TextInput(display_text='Geoserver AHPS Station Layer  (Optional)',
                                             name='geoserver-ahps-station-input',
                                             placeholder='e.g.: erfp:ahps-station',
                                             icon_append='glyphicon glyphicon-link')
              
    shp_upload_toggle_switch = ToggleSwitch(display_text='Upload Shapefile?',
                                            name='shp-upload-toggle',
                                            on_label='Yes',
                                            off_label='No',
                                            on_style='success',
                                            off_style='danger',
                                            initial=True,)

    add_button = Button(display_text='Add Watershed',
                        icon='glyphicon glyphicon-plus',
                        style='success',
                        name='submit-add-watershed',
                        attributes={'id':'submit-add-watershed'},)

    context = {
                'watershed_name_input': watershed_name_input,
                'subbasin_name_input': subbasin_name_input,
                'data_store_select': data_store_select,
                'ecmwf_data_store_watershed_name_input': ecmwf_data_store_watershed_name_input,
                'ecmwf_data_store_subbasin_name_input': ecmwf_data_store_subbasin_name_input,
                'wrf_hydro_data_store_watershed_name_input': wrf_hydro_data_store_watershed_name_input,
                'wrf_hydro_data_store_subbasin_name_input': wrf_hydro_data_store_subbasin_name_input,
                'geoserver_select': geoserver_select,
                'geoserver_drainage_line_input': geoserver_drainage_line_input,
                'geoserver_boundary_input': geoserver_boundary_input,
                'geoserver_gage_input': geoserver_gage_input,
                'geoserver_historical_flood_map_input': geoserver_historical_flood_map_input,
                'geoserver_ahps_station_input': geoserver_ahps_station_input,
                'shp_upload_toggle_switch': shp_upload_toggle_switch,
                'add_button': add_button,
              }

    return render(request, 'streamflow_prediction_tool/add_watershed.html', context)


@user_passes_test(user_permission_test)
def manage_watersheds(request):        
    """
    Controller for the app manage_watersheds page.
    """
    #initialize session
    session_maker = app.get_persistent_store_database('main_db', as_sessionmaker=True)
    session = session_maker()
    num_watersheds = session.query(Watershed).count()
    session.close()
    edit_modal = MessageBox(name='edit_watershed_modal',
                            title='Edit Watershed',
                            message='Loading ...',
                            dismiss_button='Nevermind',
                            affirmative_button='Save Changes',
                            affirmative_attributes='id=edit_modal_submit',
                            width=500)
    context = {
        'initial_page': 0,
        'num_watersheds': num_watersheds,
        'edit_modal' : edit_modal
    }

    return render(request, 'streamflow_prediction_tool/manage_watersheds.html', context)

@user_passes_test(user_permission_test)
def manage_watersheds_table(request):
    """
    Controller for the app manage_watersheds page.
    """
    #initialize session
    session_maker = app.get_persistent_store_database('main_db', as_sessionmaker=True)
    session = session_maker()

    # Query DB for watersheds
    RESULTS_PER_PAGE = 5
    page = int(request.GET.get('page'))

    watersheds = session.query(Watershed) \
                        .order_by(Watershed.watershed_name,
                                  Watershed.subbasin_name) \
                        .all()[(page * RESULTS_PER_PAGE):((page + 1)*RESULTS_PER_PAGE)]

    session.close()

    shp_upload_toggle_switch = ToggleSwitch(name='shp-upload-toggle',
                                            on_label='Yes',
                                            off_label='No',
                                            on_style='success',
                                            off_style='danger',
                                            initial=False,)
                                            
    prev_button = Button(display_text='Previous',
                         name='prev_button',
                         attributes={'class' :'nav_button'})

    next_button = Button(display_text='Next',
                         name='next_button',
                         attributes={'class':'nav_button'})

    context = {
                'watersheds': watersheds,
                'shp_upload_toggle_switch': shp_upload_toggle_switch,
                'prev_button': prev_button,
                'next_button': next_button,
              }

    return render(request, 'streamflow_prediction_tool/manage_watersheds_table.html', context)

@user_passes_test(user_permission_test)
def edit_watershed(request):
    """
    Controller for the app manage_watersheds page.
    """
    if request.method == 'GET':
        get_info = request.GET
        #get/check information from AJAX request
        watershed_id = get_info.get('watershed_id')

        #initialize session
        session_maker = app.get_persistent_store_database('main_db', as_sessionmaker=True)
        session = session_maker()
        #get desired watershed
        watershed  = session.query(Watershed).get(watershed_id)

        watershed_name_input = TextInput(display_text='Watershed Name',
                                         name='watershed-name-input',
                                         placeholder='e.g.: magdalena',
                                         icon_append='glyphicon glyphicon-home',
                                         initial=watershed.watershed_name,)

        subbasin_name_input = TextInput(display_text='Subbasin Name',
                                        name='subbasin-name-input',
                                        placeholder='e.g.: el_banco',
                                        icon_append='glyphicon glyphicon-tree-deciduous',
                                        initial=watershed.subbasin_name,)

        # Query DB for data stores
        data_stores = session.query(DataStore).all()
        data_store_list = []
        for data_store in data_stores:
            data_store_list.append(("%s (%s)" % (data_store.name, data_store.api_endpoint),
                                     data_store.id))

        data_store_select = SelectInput(display_text='Select a Data Store',
                                        name='data-store-select',
                                        options=data_store_list,
                                        initial=["%s (%s)" % (watershed.data_store.name, watershed.data_store.api_endpoint)],)

        ecmwf_data_store_watershed_name_input = TextInput(display_text='ECMWF Watershed Data Store Name',
                                                          name='ecmwf-data-store-watershed-name-input',
                                                          placeholder='e.g.: magdalena',
                                                          icon_append='glyphicon glyphicon-home',
                                                          initial=watershed.ecmwf_data_store_watershed_name,)
                  
        ecmwf_data_store_subbasin_name_input = TextInput(display_text='ECMWF Subbasin Data Store Name',
                                                         name='ecmwf-data-store-subbasin-name-input',
                                                         placeholder='e.g.: el_banco',
                                                         icon_append='glyphicon glyphicon-tree-deciduous',
                                                         initial=watershed.ecmwf_data_store_subbasin_name,)
    
        wrf_hydro_data_store_watershed_name_input = TextInput(display_text='WRF-Hydro Watershed Data Store Name',
                                                              name='wrf-hydro-data-store-watershed-name-input',
                                                              placeholder='e.g.: magdalena',
                                                              icon_append='glyphicon glyphicon-home',
                                                              initial=watershed.wrf_hydro_data_store_watershed_name,)
                  
        wrf_hydro_data_store_subbasin_name_input = TextInput(display_text='WRF-Hydro Subbasin Data Store Name',
                                                             name='wrf-hydro-data-store-subbasin-name-input',
                                                             placeholder='e.g.: el_banco',
                                                             icon_append='glyphicon glyphicon-tree-deciduous',
                                                             initial=watershed.wrf_hydro_data_store_subbasin_name,)
                                                             
       # Query DB for geoservers
        geoservers = session.query(Geoserver).all()
        geoserver_list = []
        for geoserver in geoservers:
            geoserver_list.append(( "%s (%s)" % (geoserver.name, geoserver.url),
                                   geoserver.id))

        geoserver_select= SelectInput(display_text='Select a Geoserver',
                                      name='geoserver-select',
                                      options=geoserver_list,
                                      initial=["%s (%s)" % (watershed.geoserver.name, watershed.geoserver.url)],)

        geoserver_drainage_line_input = TextInput(display_text='Geoserver Drainage Line Layer',
                                                  name='geoserver-drainage-line-input',
                                                  placeholder='e.g.: erfp:streams',
                                                  icon_append='glyphicon glyphicon-link',
                                                  initial=watershed.geoserver_drainage_line_layer.name if watershed.geoserver_drainage_line_layer else "",)
                                                  
        geoserver_boundary_input = TextInput(display_text='Geoserver Boundary Layer (Optional)',
                                              name='geoserver-boundary-input',
                                              placeholder='e.g.: erfp:boundary',
                                              icon_append='glyphicon glyphicon-link',
                                              initial=watershed.geoserver_boundary_layer.name if watershed.geoserver_boundary_layer else "",)
                                              
        geoserver_gage_input = TextInput(display_text='Geoserver Gage Layer (Optional)',
                                         name='geoserver-gage-input',
                                         placeholder='e.g.: erfp:gage',
                                         icon_append='glyphicon glyphicon-link',
                                         initial=watershed.geoserver_gage_layer.name if watershed.geoserver_gage_layer else "",)
                                         
        geoserver_historical_flood_map_input = TextInput(display_text='Geoserver Historical Flood Map Layer Group (Optional)',
                                                         name='geoserver-historical-flood-map-input',
                                                         placeholder='e.g.: erfp:historical_flood_map',
                                                         icon_append='glyphicon glyphicon-link',
                                                         initial=watershed.geoserver_historical_flood_map_layer.name if watershed.geoserver_historical_flood_map_layer else "",)

        geoserver_ahps_station_input = TextInput(display_text='Geoserver AHPS Station Layer (Optional)',
                                                 name='geoserver-ahps-station-input',
                                                 placeholder='e.g.: erfp:ahps-station',
                                                 icon_append='glyphicon glyphicon-link',
                                                 initial=watershed.geoserver_ahps_station_layer.name if watershed.geoserver_ahps_station_layer else "",)

        shp_upload_toggle_switch = ToggleSwitch(display_text='Upload Shapefile?',
                                                name='shp-upload-toggle',
                                                on_label='Yes',
                                                off_label='No',
                                                on_style='success',
                                                off_style='danger',
                                                initial=False,)

        add_button = Button(display_text='Add Watershed',
                            icon='glyphicon glyphicon-plus',
                            style='success',
                            name='submit-add-watershed',
                            attributes={'id':'submit-add-watershed'},)

        context = {
                    'watershed_name_input': watershed_name_input,
                    'subbasin_name_input': subbasin_name_input,
                    'data_store_select': data_store_select,
                    'ecmwf_data_store_watershed_name_input': ecmwf_data_store_watershed_name_input,
                    'ecmwf_data_store_subbasin_name_input': ecmwf_data_store_subbasin_name_input,
                    'wrf_hydro_data_store_watershed_name_input': wrf_hydro_data_store_watershed_name_input,
                    'wrf_hydro_data_store_subbasin_name_input': wrf_hydro_data_store_subbasin_name_input,
                    'geoserver_select': geoserver_select,
                    'geoserver_drainage_line_input': geoserver_drainage_line_input,
                    'geoserver_boundary_input': geoserver_boundary_input,
                    'geoserver_gage_input': geoserver_gage_input,
                    'geoserver_historical_flood_map_input': geoserver_historical_flood_map_input,
                    'geoserver_ahps_station_input': geoserver_ahps_station_input,
                    'shp_upload_toggle_switch': shp_upload_toggle_switch,
                    'add_button': add_button,
                    'watershed' : watershed,
                  }
        page_html = render(request, 'streamflow_prediction_tool/edit_watershed.html', context)
        session.close()

        return page_html

@user_passes_test(user_permission_test)
def add_data_store(request):        
    """
    Controller for the app add_data_store page.
    """
    #initialize session
    session_maker = app.get_persistent_store_database('main_db', as_sessionmaker=True)
    session = session_maker()

    data_store_name_input = TextInput(display_text='Data Store Server Name',
                                      name='data-store-name-input',
                                      placeholder='e.g.: My CKAN Server',
                                      icon_append='glyphicon glyphicon-tag',)

    # Query DB for data store types
    data_store_types = session.query(DataStoreType).filter(DataStoreType.id>1).all()
    data_store_type_list = []
    for data_store_type in data_store_types:
        data_store_type_list.append((data_store_type.human_readable_name, 
                                     data_store_type.id))

    session.close()

    data_store_type_select_input = SelectInput(display_text='Data Store Type',
                                               name='data-store-type-select',
                                               options=data_store_type_list,
                                               initial=data_store_type_list[0][0],)

    data_store_endpoint_input = TextInput(display_text='Data Store API Endpoint',
                                          name='data-store-endpoint-input',
                                          placeholder='e.g.: http://ciwweb.chpc.utah.edu/api/3/action',
                                          icon_append='glyphicon glyphicon-cloud-download',)

    data_store_owner_org_input = TextInput(display_text='Data Store Owner Organization',
                                           name='data-store-owner_org-input',
                                           placeholder='e.g.: byu',
                                           icon_append='glyphicon glyphicon-home',)

    add_button = Button(display_text='Add Data Store',
                        icon='glyphicon glyphicon-plus',
                        style='success',
                        name='submit-add-data-store',
                        attributes={'id':'submit-add-data-store'},)

    context = {
                'data_store_name_input': data_store_name_input,
                'data_store_type_select_input': data_store_type_select_input,
                'data_store_endpoint_input': data_store_endpoint_input,
                'data_store_owner_org_input': data_store_owner_org_input,
                'add_button': add_button,
              }
              
    return render(request, 'streamflow_prediction_tool/add_data_store.html', context)

@user_passes_test(user_permission_test)
def manage_data_stores(request):        
    """
    Controller for the app manage_data_stores page.
    """
    #initialize session
    session_maker = app.get_persistent_store_database('main_db', as_sessionmaker=True)
    session = session_maker()
    num_data_stores = session.query(DataStore).count() - 1
    session.close()
    context = {
                'initial_page': 0,
                'num_data_stores': num_data_stores,
              }
              
    return render(request, 'streamflow_prediction_tool/manage_data_stores.html', context)

@user_passes_test(user_permission_test)
def manage_data_stores_table(request):
    """
    Controller for the app manage_data_stores page.
    """
    #initialize session
    session_maker = app.get_persistent_store_database('main_db', as_sessionmaker=True)
    session = session_maker()
    RESULTS_PER_PAGE = 5
    page = int(request.GET.get('page'))

    # Query DB for data store types
    data_stores = session.query(DataStore) \
                        .filter(DataStore.id>1) \
                        .order_by(DataStore.name) \
                        .all()[(page * RESULTS_PER_PAGE):((page + 1)*RESULTS_PER_PAGE)]

    prev_button = Button(display_text='Previous',
                         name='prev_button',
                         attributes={'class':'nav_button'},)

    next_button = Button(display_text='Next',
                         name='next_button',
                         attributes={'class':'nav_button'},)

    context = {
                'prev_button' : prev_button,
                'next_button': next_button,
                'data_stores': data_stores,
              }

    table_html = render(request, 'streamflow_prediction_tool/manage_data_stores_table.html', context)
    #in order to close the session, the request needed to be rendered first
    session.close()

    return table_html

@user_passes_test(user_permission_test)
def add_geoserver(request):        
    """
    Controller for the app add_geoserver page.
    """
    geoserver_name_input = TextInput(display_text='Geoserver Name',
                                     name='geoserver-name-input',
                                     placeholder='e.g.: My Geoserver',
                                     icon_append='glyphicon glyphicon-tag',)

    geoserver_url_input = TextInput(display_text='Geoserver Url',
                                    name='geoserver-url-input',
                                    placeholder='e.g.: http://felek.cns.umass.edu:8080/geoserver',
                                    icon_append='glyphicon glyphicon-cloud-download')
              
    geoserver_username_input = TextInput(display_text='Geoserver Username',
                                         name='geoserver-username-input',
                                         placeholder='e.g.: admin',
                                         icon_append='glyphicon glyphicon-user',)
        
    add_button = Button(display_text='Add Geoserver',
                        icon='glyphicon glyphicon-plus',
                        style='success',
                        name='submit-add-geoserver',
                        attributes={'id':'submit-add-geoserver'},)

    context = {
                'geoserver_name_input': geoserver_name_input,
                'geoserver_url_input': geoserver_url_input,
                'geoserver_username_input': geoserver_username_input,
                'add_button': add_button,
              }
              
    return render(request, 'streamflow_prediction_tool/add_geoserver.html', context)
 
@user_passes_test(user_permission_test)
def manage_geoservers(request):        
    """
    Controller for the app manage_geoservers page.
    """
    #initialize session
    session_maker = app.get_persistent_store_database('main_db', as_sessionmaker=True)
    session = session_maker()
    num_geoservers = session.query(Geoserver).count()
    session.close()

    context = {
                'initial_page': 0,
                'num_geoservers': num_geoservers,
              }

    return render(request, 'streamflow_prediction_tool/manage_geoservers.html', context)

@user_passes_test(user_permission_test)
def manage_geoservers_table(request):
    """
    Controller for the app manage_geoservers page.
    """
    #initialize session
    session_maker = app.get_persistent_store_database('main_db', as_sessionmaker=True)
    session = session_maker()
    RESULTS_PER_PAGE = 5
    page = int(request.GET.get('page'))

    # Query DB for data store types
    geoservers = session.query(Geoserver)\
                        .order_by(Geoserver.name, Geoserver.url) \
                        .all()[(page * RESULTS_PER_PAGE):((page + 1)*RESULTS_PER_PAGE)]

    prev_button = Button(display_text='Previous',
                         name='prev_button',
                         attributes={'class':'nav_button'},)

    next_button = Button(display_text='Next',
                         name='next_button',
                         attributes={'class':'nav_button'},)

    context = {
                'prev_button' : prev_button,
                'next_button': next_button,
                'geoservers': geoservers,
              }

    session.close()

    return render(request, 'streamflow_prediction_tool/manage_geoservers_table.html', context)

@user_passes_test(user_permission_test)
def add_watershed_group(request):        
    """
    Controller for the app add_watershed_group page.
    """
    watershed_group_name_input = TextInput(display_text='Watershed Group Name',
                                           name='watershed-group-name-input',
                                           placeholder='e.g.: My Watershed Group',
                                           icon_append='glyphicon glyphicon-tag',)
 
    #initialize session
    session_maker = app.get_persistent_store_database('main_db', as_sessionmaker=True)
    session = session_maker()
    #Query DB for settings
    watersheds  = session.query(Watershed) \
                        .order_by(Watershed.watershed_name,
                                  Watershed.subbasin_name) \
                        .all()
    watershed_list = []
    for watershed in watersheds:
        watershed_list.append(("%s (%s)" % \
                              (watershed.watershed_name, watershed.subbasin_name),
                              watershed.id))
                              
    session.close()
    
    watershed_select = SelectInput(display_text='Select Watershed(s) to Add to Group',
                                   name='watershed_select',
                                   options=watershed_list,
                                   multiple=True,)
 
    add_button = Button(display_text='Add Watershed Group',
                        icon='glyphicon glyphicon-plus',
                        style='success',
                        name='submit-add-watershed-group',
                        attributes={'id':'submit-add-watershed-group'},)

    context = {
                'watershed_group_name_input': watershed_group_name_input,
                'watershed_select': watershed_select,
                'add_button': add_button,
              }
    return render(request, 'streamflow_prediction_tool/add_watershed_group.html', context)
 
@user_passes_test(user_permission_test)
def manage_watershed_groups(request):        
    """
    Controller for the app manage_watershed_groups page.
    """
    #initialize session
    session_maker = app.get_persistent_store_database('main_db', as_sessionmaker=True)
    session = session_maker()
    num_watershed_groups = session.query(WatershedGroup).count()
    session.close()
    context = {
                'initial_page': 0,
                'num_watershed_groups': num_watershed_groups,
              }
    return render(request, 'streamflow_prediction_tool/manage_watershed_groups.html', context)

@user_passes_test(user_permission_test)
def manage_watershed_groups_table(request):
    """
    Controller for the app manage_watershed_groups page.
    """
    #initialize session
    session_maker = app.get_persistent_store_database('main_db', as_sessionmaker=True)
    session = session_maker()
    RESULTS_PER_PAGE = 5
    page = int(request.GET.get('page'))

    # Query DB for data store types
    watershed_groups = session.query(WatershedGroup)\
                                .order_by(WatershedGroup.name) \
                                .all()[(page * RESULTS_PER_PAGE):((page + 1)*RESULTS_PER_PAGE)]

    watersheds = session.query(Watershed) \
                        .order_by(Watershed.watershed_name,
                                  Watershed.subbasin_name)\
                        .all()


    prev_button = Button(display_text='Previous',
                         name='prev_button',
                         attributes={'class':'nav_button'},)

    next_button = Button(display_text='Next',
                         name='next_button',
                         attributes={'class':'nav_button'},)

    context = {
                'prev_button' : prev_button,
                'next_button': next_button,
                'watershed_groups': watershed_groups,
                'watersheds' : watersheds,
              }
    table_html = render(request, 'streamflow_prediction_tool/manage_watershed_groups_table.html', context)
    session.close()

    return table_html
    
@user_passes_test(user_permission_test)
def getting_started(request):
    """
    Controller for the app getting started page.
    """
   
    return render(request, 'streamflow_prediction_tool/getting_started.html', {})

@login_required
def publications(request):
    """
    Controller for the app publications page.
    """
   
    return render(request, 'streamflow_prediction_tool/publications.html', {})