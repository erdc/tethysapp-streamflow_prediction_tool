# -*- coding: utf-8 -*-
"""app.py

    Created by Alan D. Snow.
    License: BSD 3-Clause
"""
from uuid import uuid5, NAMESPACE_DNS
from datetime import datetime

from tethys_sdk.base import TethysAppBase, url_map_maker
from tethys_sdk.app_settings import (CustomSetting,
                                     PersistentStoreDatabaseSetting)


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
    description = ('Provides 15-day streamflow predicted estimates by using '
                   'ECMWF (ecmwf.int) runoff predictions routed with the RAPID'
                   ' (rapid-hub.org) program. Return period estimates '
                   'and warning flags aid in determining the severity.')
    enable_feedback = False
    feedback_emails = []

    def url_maps(self):
        """
        Add controllers
        """
        url_map = url_map_maker(self.root_url)

        return (
            url_map(name='home',
                    url='streamflow-prediction-tool',
                    controller='streamflow_prediction_tool.controllers.home'),
            url_map(name='map',
                    url='streamflow-prediction-tool/map',
                    controller='streamflow_prediction_tool.controllers'
                               '.app_map'),
            url_map(name='get_ecmwf_hydrograph_plot_ajax',
                    url='streamflow-prediction-tool/map/'
                        'get-ecmwf-hydrograph-plot',
                    controller='streamflow_prediction_tool.controllers_ajax'
                               '.get_ecmwf_hydrograph_plot'),
            url_map(name='get_return_periods_ajax',
                    url='streamflow-prediction-tool/map/'
                        'get-return-periods',
                    controller='streamflow_prediction_tool.controllers_ajax'
                               '.get_return_periods'),
            url_map(name='get_historic_data_csv_ajax',
                    url='streamflow-prediction-tool/map/get-historic-data-csv',
                    controller='streamflow_prediction_tool.controllers_ajax'
                               '.get_historic_data_csv'),
            url_map(name='get_historical_hydrograph_ajax',
                    url='streamflow-prediction-tool/map/'
                        'get-historical-hydrograph',
                    controller='streamflow_prediction_tool.controllers_ajax'
                               '.get_historical_hydrograph'),
            url_map(name='get_forecast_streamflow_ajax',
                    url='streamflow-prediction-tool/map/'
                        'get-forecast-streamflow-csv',
                    controller='streamflow_prediction_tool.controllers_ajax'
                               '.get_forecast_streamflow_csv'),
            url_map(name='get_flow_duration_curve_ajax',
                    url='streamflow-prediction-tool/map/'
                        'get-flow-duration-curve',
                    controller='streamflow_prediction_tool.controllers_ajax'
                               '.get_flow_duration_curve'),
            url_map(name='get_warning_points_ajax',
                    url='streamflow-prediction-tool/map/get-warning-points',
                    controller='streamflow_prediction_tool.controllers_ajax'
                               '.generate_warning_points'),
            url_map(name='ecmf_get_avaialable_dates_ajax',
                    url='streamflow-prediction-tool/map/'
                        'ecmwf-get-avaialable-dates',
                    controller='streamflow_prediction_tool.controllers_ajax'
                               '.ecmwf_get_avaialable_dates'),
            url_map(name='get_daily_seasonal_streamflow_chart',
                    url='streamflow-prediction-tool/map/'
                        'get-daily-seasonal-streamflow-chart',
                    controller='streamflow_prediction_tool.controllers_ajax'
                               '.get_daily_seasonal_streamflow_chart'),
            url_map(name='get_monthly_seasonal_streamflow_chart',
                    url='streamflow-prediction-tool/map/'
                        'get-monthly-seasonal-streamflow-chart',
                    controller='streamflow_prediction_tool.controllers_ajax'
                               '.get_monthly_seasonal_streamflow_chart'),
            url_map(name='add-watershed',
                    url='streamflow-prediction-tool/add-watershed',
                    controller='streamflow_prediction_tool.controllers'
                               '.add_watershed'),
            url_map(name='add-watershed-ajax',
                    url='streamflow-prediction-tool/add-watershed/submit',
                    controller='streamflow_prediction_tool'
                               '.controllers_ajax.watershed_add'),
            url_map(name='add-watershed-ecmwf-rapid-files-ajax',
                    url='streamflow-prediction-tool/add-watershed/'
                        'upload_ecmwf_rapid',
                    controller='streamflow_prediction_tool.controllers_ajax'
                               '.watershed_ecmwf_rapid_file_upload'),
            url_map(name='add-watershed-update-ajax',
                    url='streamflow-prediction-tool/add-watershed/update',
                    controller='streamflow_prediction_tool.controllers_ajax'
                               '.watershed_update'),
            url_map(name='add-watershed-delete-ajax',
                    url='streamflow-prediction-tool/add-watershed/delete',
                    controller='streamflow_prediction_tool'
                               '.controllers_ajax.watershed_delete'),
            url_map(name='manage-watersheds',
                    url='streamflow-prediction-tool/manage-watersheds',
                    controller='streamflow_prediction_tool.controllers'
                               '.manage_watersheds'),
            url_map(name='manage-watersheds-table',
                    url='streamflow-prediction-tool/manage-watersheds/table',
                    controller='streamflow_prediction_tool.controllers'
                               '.manage_watersheds_table'),
            url_map(name='manage-watersheds-edit',
                    url='streamflow-prediction-tool/manage-watersheds/edit',
                    controller='streamflow_prediction_tool.controllers'
                               '.edit_watershed'),
            url_map(name='manage-watershed-ecmwf-rapid-files-ajax',
                    url='streamflow-prediction-tool/manage-watersheds/'
                        'upload_ecmwf_rapid',
                    controller='streamflow_prediction_tool.controllers_ajax'
                               '.watershed_ecmwf_rapid_file_upload'),
            url_map(name='delete-watershed',
                    url='streamflow-prediction-tool/manage-watersheds/delete',
                    controller='streamflow_prediction_tool.controllers_ajax'
                               '.watershed_delete'),
            url_map(name='update-watershed',
                    url='streamflow-prediction-tool/manage-watersheds/submit',
                    controller='streamflow_prediction_tool.controllers_ajax'
                               '.watershed_update'),
            url_map(name='add-geoserver',
                    url='streamflow-prediction-tool/add-geoserver',
                    controller='streamflow_prediction_tool.controllers'
                               '.add_geoserver'),
            url_map(name='add-geoserver-ajax',
                    url='streamflow-prediction-tool/add-geoserver/submit',
                    controller='streamflow_prediction_tool.controllers_ajax'
                               '.geoserver_add'),
            url_map(name='manage-geoservers',
                    url='streamflow-prediction-tool/manage-geoservers',
                    controller='streamflow_prediction_tool.controllers'
                               '.manage_geoservers'),
            url_map(name='manage-geoservers-table',
                    url='streamflow-prediction-tool/manage-geoservers/table',
                    controller='streamflow_prediction_tool.controllers'
                               '.manage_geoservers_table'),
            url_map(name='update-geoservers-ajax',
                    url='streamflow-prediction-tool/manage-geoservers/submit',
                    controller='streamflow_prediction_tool.controllers_ajax'
                               '.geoserver_update'),
            url_map(name='delete-geoserver-ajax',
                    url='streamflow-prediction-tool/manage-geoservers/delete',
                    controller='streamflow_prediction_tool.controllers_ajax'
                               '.geoserver_delete'),
            url_map(name='add-data-store',
                    url='streamflow-prediction-tool/add-data-store',
                    controller='streamflow_prediction_tool.controllers'
                               '.add_data_store'),
            url_map(name='add-data-store-ajax',
                    url='streamflow-prediction-tool/add-data-store/submit',
                    controller='streamflow_prediction_tool.controllers_ajax'
                               '.data_store_add'),
            url_map(name='manage-data-stores',
                    url='streamflow-prediction-tool/manage-data-stores',
                    controller='streamflow_prediction_tool.controllers'
                               '.manage_data_stores'),
            url_map(name='manage-data-stores-table',
                    url='streamflow-prediction-tool/manage-data-stores/table',
                    controller='streamflow_prediction_tool.controllers'
                               '.manage_data_stores_table'),
            url_map(name='update-data-store-ajax',
                    url='streamflow-prediction-tool/manage-data-stores/submit',
                    controller='streamflow_prediction_tool'
                               '.controllers_ajax.data_store_update'),
            url_map(name='delete-data-store-ajax',
                    url='streamflow-prediction-tool/manage-data-stores/delete',
                    controller='streamflow_prediction_tool'
                               '.controllers_ajax.data_store_delete'),
            url_map(name='add-watershed-group',
                    url='streamflow-prediction-tool/add-watershed-group',
                    controller='streamflow_prediction_tool.controllers'
                               '.add_watershed_group'),
            url_map(name='add-watershed-group-ajax',
                    url='streamflow-prediction-tool/add-watershed-group/'
                        'submit',
                    controller='streamflow_prediction_tool.controllers_ajax'
                               '.watershed_group_add'),
            url_map(name='manage-watershed-groups',
                    url='streamflow-prediction-tool/manage-watershed-groups',
                    controller='streamflow_prediction_tool.controllers'
                               '.manage_watershed_groups'),
            url_map(name='manage-watershed-groups-table',
                    url='streamflow-prediction-tool/manage-watershed-groups/'
                        'table',
                    controller='streamflow_prediction_tool.controllers'
                               '.manage_watershed_groups_table'),
            url_map(name='update-watershed-group-ajax',
                    url='streamflow-prediction-tool/manage-watershed-groups/'
                        'submit',
                    controller='streamflow_prediction_tool.controllers_ajax'
                               '.watershed_group_update'),
            url_map(name='delete-watershed-group-ajax',
                    url='streamflow-prediction-tool/manage-watershed-groups/'
                        'delete',
                    controller='streamflow_prediction_tool.controllers_ajax'
                               '.watershed_group_delete'),
            url_map(name='getting-started',
                    url='streamflow-prediction-tool/getting-started',
                    controller='streamflow_prediction_tool.controllers'
                               '.getting_started'),
            url_map(name='publications',
                    url='streamflow-prediction-tool/publications',
                    controller='streamflow_prediction_tool.controllers'
                               '.publications'),
            url_map(name='waterml',
                    url='streamflow-prediction-tool/api/GetForecast',
                    controller='streamflow_prediction_tool.controllers_api'
                               '.get_ecmwf_forecast'),
            url_map(name='era_interim',
                    url='streamflow-prediction-tool/api/GetHistoricData',
                    controller='streamflow_prediction_tool.controllers_api'
                               '.get_historic_data'),
            url_map(name='return_periods',
                    url='streamflow-prediction-tool/api/GetReturnPeriods',
                    controller='streamflow_prediction_tool.controllers_api'
                               '.get_return_periods_api'),
            url_map(name='return_periods',
                    url='streamflow-prediction-tool/api/GetAvailableDates',
                    controller='streamflow_prediction_tool.controllers_api'
                               '.get_available_dates'),
            url_map(name='watershed_list',
                    url='streamflow-prediction-tool/api/GetWatersheds',
                    controller='streamflow_prediction_tool.controllers_api'
                               '.get_watershed_list'),
            url_map(name='warning_points',
                    url='streamflow-prediction-tool/api/GetWarningPoints',
                    controller='streamflow_prediction_tool.controllers_api'
                               '.get_warning_points'),
        )

    def persistent_store_settings(self):
        """
        Define Persistent Store Settings.
        """
        return (
            PersistentStoreDatabaseSetting(
                name='main_db',
                description='primary database',
                initializer='streamflow_prediction_tool'
                            '.init_stores.init_main_db',
                required=True
            ),
        )

    def custom_settings(self):
        """
        Custom app settings.
        """
        return (
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
