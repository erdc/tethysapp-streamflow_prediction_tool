from tethys_apps.base import TethysAppBase, url_map_maker
from tethys_apps.base import PersistentStore

class StreamflowPredictionTool(TethysAppBase):
    """
    Tethys app class for streamflow_prediction_tool.
    """

    name = 'Streamflow Prediction Tool'
    index = 'streamflow_prediction_tool:home'
    icon = 'streamflow_prediction_tool/images/logo.png'
    package = 'streamflow_prediction_tool'
    root_url = 'spt'
    color = '#34495e'
        
    def url_maps(self):
        """
        Add controllers
        """
        UrlMap = url_map_maker(self.root_url)

        url_maps = (UrlMap(name='home',
                           url='spt',
                           controller='streamflow_prediction_tool.controllers.home'),
                    UrlMap(name='map',
                           url='spt/map',
                           controller='streamflow_prediction_tool.controllers.map'),
                    UrlMap(name='get_ecmwf_reach_statistical_hydrograph_ajax',
                           url='spt/map/ecmwf-get-hydrograph',
                           controller='streamflow_prediction_tool.controllers_ajax.ecmwf_get_hydrograph'),
                    UrlMap(name='get_era_interim_reach_hydrograph_ajax',
                           url='spt/map/era-interim-get-hydrograph',
                           controller='streamflow_prediction_tool.controllers_ajax.era_interim_get_hydrograph'),
                    UrlMap(name='get_warning_points_ajax',
                           url='spt/map/get-warning-points',
                           controller='streamflow_prediction_tool.controllers_ajax.generate_warning_points'),
                    UrlMap(name='get_wrf_hydro_reach_hydrograph_ajax',
                           url='spt/map/wrf-hydro-get-hydrograph',
                           controller='streamflow_prediction_tool.controllers_ajax.wrf_hydro_get_hydrograph'),
                    UrlMap(name='ecmf_get_avaialable_dates_ajax',
                           url='spt/map/ecmwf-get-avaialable-dates',
                           controller='streamflow_prediction_tool.controllers_ajax.ecmwf_get_avaialable_dates'),
                    UrlMap(name='wrf_hydro_get_avaialable_dates_ajax',
                           url='spt/map/wrf-hydro-get-avaialable-dates',
                           controller='streamflow_prediction_tool.controllers_ajax.wrf_hydro_get_avaialable_dates'),
                    UrlMap(name='settings',
                           url='spt/settings',
                           controller='streamflow_prediction_tool.controllers.settings'),
                    UrlMap(name='update_settings_ajax',
                           url='spt/settings/update',
                           controller='streamflow_prediction_tool.controllers_ajax.settings_update'),
                    UrlMap(name='add-watershed',
                           url='spt/add-watershed',
                           controller='streamflow_prediction_tool.controllers.add_watershed'),
                    UrlMap(name='add-watershed-ajax',
                           url='spt/add-watershed/submit',
                           controller='streamflow_prediction_tool.controllers_ajax.watershed_add'),
                    UrlMap(name='add-watershed-ecmwf-rapid-files-ajax',
                           url='spt/add-watershed/upload_ecmwf_rapid',
                           controller='streamflow_prediction_tool.controllers_ajax.watershed_ecmwf_rapid_file_upload'),
                    UrlMap(name='add-watershed-update-ajax',
                           url='spt/add-watershed/update',
                           controller='streamflow_prediction_tool.controllers_ajax.watershed_update'),
                    UrlMap(name='add-watershed-delete-ajax',
                           url='spt/add-watershed/delete',
                           controller='streamflow_prediction_tool.controllers_ajax.watershed_delete'),
                    UrlMap(name='manage-watersheds',
                           url='spt/manage-watersheds',
                           controller='streamflow_prediction_tool.controllers.manage_watersheds'),
                    UrlMap(name='manage-watersheds-table',
                           url='spt/manage-watersheds/table',
                           controller='streamflow_prediction_tool.controllers.manage_watersheds_table'),
                    UrlMap(name='manage-watersheds-edit',
                           url='spt/manage-watersheds/edit',
                           controller='streamflow_prediction_tool.controllers.edit_watershed'),
                    UrlMap(name='manage-watershed-ecmwf-rapid-files-ajax',
                           url='spt/manage-watersheds/upload_ecmwf_rapid',
                           controller='streamflow_prediction_tool.controllers_ajax.watershed_ecmwf_rapid_file_upload'),
                    UrlMap(name='delete-watershed',
                           url='spt/manage-watersheds/delete',
                           controller='streamflow_prediction_tool.controllers_ajax.watershed_delete'),
                    UrlMap(name='update-watershed',
                           url='spt/manage-watersheds/submit',
                           controller='streamflow_prediction_tool.controllers_ajax.watershed_update'),
                    UrlMap(name='add-geoserver',
                           url='spt/add-geoserver',
                           controller='streamflow_prediction_tool.controllers.add_geoserver'),
                    UrlMap(name='add-geoserver-ajax',
                           url='spt/add-geoserver/submit',
                           controller='streamflow_prediction_tool.controllers_ajax.geoserver_add'),
                    UrlMap(name='manage-geoservers',
                           url='spt/manage-geoservers',
                           controller='streamflow_prediction_tool.controllers.manage_geoservers'),
                    UrlMap(name='manage-geoservers-table',
                           url='spt/manage-geoservers/table',
                           controller='streamflow_prediction_tool.controllers.manage_geoservers_table'),
                    UrlMap(name='update-geoservers-ajax',
                           url='spt/manage-geoservers/submit',
                           controller='streamflow_prediction_tool.controllers_ajax.geoserver_update'),
                    UrlMap(name='delete-geoserver-ajax',
                           url='spt/manage-geoservers/delete',
                           controller='streamflow_prediction_tool.controllers_ajax.geoserver_delete'),
                    UrlMap(name='add-data-store',
                           url='spt/add-data-store',
                           controller='streamflow_prediction_tool.controllers.add_data_store'),
                    UrlMap(name='add-data-store-ajax',
                           url='spt/add-data-store/submit',
                           controller='streamflow_prediction_tool.controllers_ajax.data_store_add'),
                    UrlMap(name='manage-data-stores',
                           url='spt/manage-data-stores',
                           controller='streamflow_prediction_tool.controllers.manage_data_stores'),
                    UrlMap(name='manage-data-stores-table',
                           url='spt/manage-data-stores/table',
                           controller='streamflow_prediction_tool.controllers.manage_data_stores_table'),
                    UrlMap(name='update-data-store-ajax',
                           url='spt/manage-data-stores/submit',
                           controller='streamflow_prediction_tool.controllers_ajax.data_store_update'),
                    UrlMap(name='delete-data-store-ajax',
                           url='spt/manage-data-stores/delete',
                           controller='streamflow_prediction_tool.controllers_ajax.data_store_delete'),
                    UrlMap(name='add-watershed-group',
                           url='spt/add-watershed-group',
                           controller='streamflow_prediction_tool.controllers.add_watershed_group'),
                    UrlMap(name='add-watershed-group-ajax',
                           url='spt/add-watershed-group/submit',
                           controller='streamflow_prediction_tool.controllers_ajax.watershed_group_add'),
                    UrlMap(name='manage-watershed-groups',
                           url='spt/manage-watershed-groups',
                           controller='streamflow_prediction_tool.controllers.manage_watershed_groups'),
                    UrlMap(name='manage-watershed-groups-table',
                           url='spt/manage-watershed-groups/table',
                           controller='streamflow_prediction_tool.controllers.manage_watershed_groups_table'),
                    UrlMap(name='update-watershed-group-ajax',
                           url='spt/manage-watershed-groups/submit',
                           controller='streamflow_prediction_tool.controllers_ajax.watershed_group_update'),
                    UrlMap(name='delete-watershed-group-ajax',
                           url='spt/manage-watershed-groups/delete',
                           controller='streamflow_prediction_tool.controllers_ajax.watershed_group_delete'),
                    UrlMap(name='getting-started',
                           url='spt/getting-started',
                           controller='streamflow_prediction_tool.controllers.getting_started')
        )
        return url_maps
        
    def persistent_stores(self):
        """
        Add one or more persistent stores
        """
        stores = (PersistentStore(name='main_db',
                                  initializer='init_stores:init_main_db',
                                  spatial=False
                ),
        )

        return stores
