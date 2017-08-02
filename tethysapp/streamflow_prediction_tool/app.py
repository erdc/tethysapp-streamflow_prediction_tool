# -*- coding: utf-8 -*-
##
##  app.py
##  streamflow_prediction_tool
##
##  Created by Alan D. Snow.
##  Copyright © 2015-2016 Alan D. Snow. All rights reserved.
##  License: BSD 3-Clause
from uuid import uuid5, NAMESPACE_DNS
from datetime import datetime

from tethys_sdk.base import TethysAppBase, url_map_maker
from tethys_sdk.app_settings import CustomSetting, PersistentStoreDatabaseSetting


class StreamflowPredictionTool(TethysAppBase):
    """
    Tethys app class for streamflow_prediction_tool.
    """

    name = 'Streamflow Prediction Tool'
    index = 'streamflow_prediction_tool:home'
    icon = 'streamflow_prediction_tool/images/logo.png'
    package = 'streamflow_prediction_tool'
    root_url = 'streamflow-prediction-tool'
    color = '#34495e'
    description = 'Provides 15-day streamflow predicted estimates by using ' \
                  'ECMWF (ecmwf.int) runoff predictions routed with the RAPID ' \
                  '(rapid-hub.org) program. Return period estimates ' \
                  'and warning flags aid in determining the severity.'
    enable_feedback = False
    feedback_emails = []
        
    def url_maps(self):
        """
        Add controllers
        """
        UrlMap = url_map_maker(self.root_url)

        url_maps = (UrlMap(name='home',
                           url='streamflow-prediction-tool',
                           controller='streamflow_prediction_tool.controllers.home'),
                    UrlMap(name='map',
                           url='streamflow-prediction-tool/map',
                           controller='streamflow_prediction_tool.controllers.map'),
                    UrlMap(name='get_ecmwf_reach_statistical_hydrograph_ajax',
                           url='streamflow-prediction-tool/map/ecmwf-get-hydrograph',
                           controller='streamflow_prediction_tool.controllers_ajax.ecmwf_get_hydrograph'),
                    UrlMap(name='get_era_interim_reach_hydrograph_ajax',
                           url='streamflow-prediction-tool/map/era-interim-get-hydrograph',
                           controller='streamflow_prediction_tool.controllers_ajax.era_interim_get_hydrograph'),
                    UrlMap(name='get_era_interim_csv_ajax',
                           url='streamflow-prediction-tool/map/era-interim-get-csv',
                           controller='streamflow_prediction_tool.controllers_ajax.era_interim_get_csv'),
                    UrlMap(name='get_warning_points_ajax',
                           url='streamflow-prediction-tool/map/get-warning-points',
                           controller='streamflow_prediction_tool.controllers_ajax.generate_warning_points'),
                    UrlMap(name='ecmf_get_avaialable_dates_ajax',
                           url='streamflow-prediction-tool/map/ecmwf-get-avaialable-dates',
                           controller='streamflow_prediction_tool.controllers_ajax.ecmwf_get_avaialable_dates'),
                    UrlMap(name='get_seasonal_streamflow',
                           url='streamflow-prediction-tool/map/get_seasonal_streamflow',
                           controller='streamflow_prediction_tool.controllers_ajax.get_seasonal_streamflow'),
                    UrlMap(name='add-watershed',
                           url='streamflow-prediction-tool/add-watershed',
                           controller='streamflow_prediction_tool.controllers.add_watershed'),
                    UrlMap(name='add-watershed-ajax',
                           url='streamflow-prediction-tool/add-watershed/submit',
                           controller='streamflow_prediction_tool.controllers_ajax.watershed_add'),
                    UrlMap(name='add-watershed-ecmwf-rapid-files-ajax',
                           url='streamflow-prediction-tool/add-watershed/upload_ecmwf_rapid',
                           controller='streamflow_prediction_tool.controllers_ajax.watershed_ecmwf_rapid_file_upload'),
                    UrlMap(name='add-watershed-update-ajax',
                           url='streamflow-prediction-tool/add-watershed/update',
                           controller='streamflow_prediction_tool.controllers_ajax.watershed_update'),
                    UrlMap(name='add-watershed-delete-ajax',
                           url='streamflow-prediction-tool/add-watershed/delete',
                           controller='streamflow_prediction_tool.controllers_ajax.watershed_delete'),
                    UrlMap(name='manage-watersheds',
                           url='streamflow-prediction-tool/manage-watersheds',
                           controller='streamflow_prediction_tool.controllers.manage_watersheds'),
                    UrlMap(name='manage-watersheds-table',
                           url='streamflow-prediction-tool/manage-watersheds/table',
                           controller='streamflow_prediction_tool.controllers.manage_watersheds_table'),
                    UrlMap(name='manage-watersheds-edit',
                           url='streamflow-prediction-tool/manage-watersheds/edit',
                           controller='streamflow_prediction_tool.controllers.edit_watershed'),
                    UrlMap(name='manage-watershed-ecmwf-rapid-files-ajax',
                           url='streamflow-prediction-tool/manage-watersheds/upload_ecmwf_rapid',
                           controller='streamflow_prediction_tool.controllers_ajax.watershed_ecmwf_rapid_file_upload'),
                    UrlMap(name='delete-watershed',
                           url='streamflow-prediction-tool/manage-watersheds/delete',
                           controller='streamflow_prediction_tool.controllers_ajax.watershed_delete'),
                    UrlMap(name='update-watershed',
                           url='streamflow-prediction-tool/manage-watersheds/submit',
                           controller='streamflow_prediction_tool.controllers_ajax.watershed_update'),
                    UrlMap(name='add-geoserver',
                           url='streamflow-prediction-tool/add-geoserver',
                           controller='streamflow_prediction_tool.controllers.add_geoserver'),
                    UrlMap(name='add-geoserver-ajax',
                           url='streamflow-prediction-tool/add-geoserver/submit',
                           controller='streamflow_prediction_tool.controllers_ajax.geoserver_add'),
                    UrlMap(name='manage-geoservers',
                           url='streamflow-prediction-tool/manage-geoservers',
                           controller='streamflow_prediction_tool.controllers.manage_geoservers'),
                    UrlMap(name='manage-geoservers-table',
                           url='streamflow-prediction-tool/manage-geoservers/table',
                           controller='streamflow_prediction_tool.controllers.manage_geoservers_table'),
                    UrlMap(name='update-geoservers-ajax',
                           url='streamflow-prediction-tool/manage-geoservers/submit',
                           controller='streamflow_prediction_tool.controllers_ajax.geoserver_update'),
                    UrlMap(name='delete-geoserver-ajax',
                           url='streamflow-prediction-tool/manage-geoservers/delete',
                           controller='streamflow_prediction_tool.controllers_ajax.geoserver_delete'),
                    UrlMap(name='add-data-store',
                           url='streamflow-prediction-tool/add-data-store',
                           controller='streamflow_prediction_tool.controllers.add_data_store'),
                    UrlMap(name='add-data-store-ajax',
                           url='streamflow-prediction-tool/add-data-store/submit',
                           controller='streamflow_prediction_tool.controllers_ajax.data_store_add'),
                    UrlMap(name='manage-data-stores',
                           url='streamflow-prediction-tool/manage-data-stores',
                           controller='streamflow_prediction_tool.controllers.manage_data_stores'),
                    UrlMap(name='manage-data-stores-table',
                           url='streamflow-prediction-tool/manage-data-stores/table',
                           controller='streamflow_prediction_tool.controllers.manage_data_stores_table'),
                    UrlMap(name='update-data-store-ajax',
                           url='streamflow-prediction-tool/manage-data-stores/submit',
                           controller='streamflow_prediction_tool.controllers_ajax.data_store_update'),
                    UrlMap(name='delete-data-store-ajax',
                           url='streamflow-prediction-tool/manage-data-stores/delete',
                           controller='streamflow_prediction_tool.controllers_ajax.data_store_delete'),
                    UrlMap(name='add-watershed-group',
                           url='streamflow-prediction-tool/add-watershed-group',
                           controller='streamflow_prediction_tool.controllers.add_watershed_group'),
                    UrlMap(name='add-watershed-group-ajax',
                           url='streamflow-prediction-tool/add-watershed-group/submit',
                           controller='streamflow_prediction_tool.controllers_ajax.watershed_group_add'),
                    UrlMap(name='manage-watershed-groups',
                           url='streamflow-prediction-tool/manage-watershed-groups',
                           controller='streamflow_prediction_tool.controllers.manage_watershed_groups'),
                    UrlMap(name='manage-watershed-groups-table',
                           url='streamflow-prediction-tool/manage-watershed-groups/table',
                           controller='streamflow_prediction_tool.controllers.manage_watershed_groups_table'),
                    UrlMap(name='update-watershed-group-ajax',
                           url='streamflow-prediction-tool/manage-watershed-groups/submit',
                           controller='streamflow_prediction_tool.controllers_ajax.watershed_group_update'),
                    UrlMap(name='delete-watershed-group-ajax',
                           url='streamflow-prediction-tool/manage-watershed-groups/delete',
                           controller='streamflow_prediction_tool.controllers_ajax.watershed_group_delete'),
                    UrlMap(name='getting-started',
                           url='streamflow-prediction-tool/getting-started',
                           controller='streamflow_prediction_tool.controllers.getting_started'),
                    UrlMap(name='publications',
                           url='streamflow-prediction-tool/publications',
                           controller='streamflow_prediction_tool.controllers.publications'),
                    UrlMap(name='waterml',
                           url='streamflow-prediction-tool/api/GetWaterML',
                           controller='streamflow_prediction_tool.api.get_waterml'),
                    UrlMap(name='era_interim',
                           url='streamflow-prediction-tool/api/GetHistoricData',
                           controller='streamflow_prediction_tool.api.get_historic_data'),
                    UrlMap(name='return_periods',
                           url='streamflow-prediction-tool/api/GetReturnPeriods',
                           controller='streamflow_prediction_tool.api.get_return_periods'),
                    UrlMap(name='return_periods',
                           url='streamflow-prediction-tool/api/GetAvailableDates',
                           controller='streamflow_prediction_tool.api.get_available_dates'),
                    UrlMap(name='watershed_list',
                           url='streamflow-prediction-tool/api/GetWatersheds',
                           controller='streamflow_prediction_tool.api.get_watershed_list'),
                    UrlMap(name='warning_points',
                           url='streamflow-prediction-tool/api/GetWarningPoints',
                           controller='streamflow_prediction_tool.api.get_warning_points'),
        )
        return url_maps

    def persistent_store_settings(self):
        """
        Define Persistent Store Settings.
        """
        ps_settings = (
            PersistentStoreDatabaseSetting(
                name='main_db',
                description='primary database',
                initializer='streamflow_prediction_tool.init_stores.init_main_db',
                required=True
            ),
        )

        return ps_settings

    def custom_settings(self):
        """
        Custom app settings.
        """
        custom_settings = (
            CustomSetting(
                name='app_instance_id',
                type=CustomSetting.TYPE_STRING,
                description='Unique identifier for this instance of the app.',
                value=uuid5(NAMESPACE_DNS, '%s%s' % ("spt", datetime.now())),
                required=True
            ),
            CustomSetting(
                name='ecmwf_forecast_folder',
                type=CustomSetting.TYPE_STRING,
                description='Server directory path to ECMWF forecasts.',
                required=True
            ),
            CustomSetting(
                name='historical_folder',
                type=CustomSetting.TYPE_STRING,
                description=('Server directory path to historical streamflow, '
                             'return period, and seasonal files.'),
                required=True
            ),
        )

        return custom_settings