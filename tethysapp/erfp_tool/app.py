from tethys_apps.base import TethysAppBase, url_map_maker
from tethys_apps.base import PersistentStore

class ECMWFRAPIDFloodPredictionTool(TethysAppBase):
    """
    Tethys app class for ECMWF-RAPID Flood Prediction Tool.
    """

    name = 'Streamflow Prediction Tool'
    index = 'erfp_tool:home'
    icon = 'erfp_tool/images/logo.png'
    package = 'erfp_tool'
    root_url = 'erfp-tool'
    color = '#34495e'
        
    def url_maps(self):
        """
        Add controllers
        """
        UrlMap = url_map_maker(self.root_url)

        url_maps = (UrlMap(name='home',
                           url='erfp-tool',
                           controller='erfp_tool.controllers.home'),
                    UrlMap(name='map',
                           url='erfp-tool/map',
                           controller='erfp_tool.controllers.map'),
                    UrlMap(name='get_ecmwf_reach_statistical_hydrograph_ajax',
                           url='erfp-tool/map/ecmwf-get-hydrograph',
                           controller='erfp_tool.controllers_ajax.ecmwf_get_hydrograph'),
                    UrlMap(name='get_era_interim_reach_hydrograph_ajax',
                           url='erfp-tool/map/era-interim-get-hydrograph',
                           controller='erfp_tool.controllers_ajax.era_interim_get_hydrograph'),
                    UrlMap(name='get_warning_points_ajax',
                           url='erfp-tool/map/get-warning-points',
                           controller='erfp_tool.controllers_ajax.generate_warning_points'),
                    UrlMap(name='get_wrf_hydro_reach_hydrograph_ajax',
                           url='erfp-tool/map/wrf-hydro-get-hydrograph',
                           controller='erfp_tool.controllers_ajax.wrf_hydro_get_hydrograph'),
                    UrlMap(name='ecmf_get_avaialable_dates_ajax',
                           url='erfp-tool/map/ecmwf-get-avaialable-dates',
                           controller='erfp_tool.controllers_ajax.ecmwf_get_avaialable_dates'),
                    UrlMap(name='wrf_hydro_get_avaialable_dates_ajax',
                           url='erfp-tool/map/wrf-hydro-get-avaialable-dates',
                           controller='erfp_tool.controllers_ajax.wrf_hydro_get_avaialable_dates'),
                    UrlMap(name='settings',
                           url='erfp-tool/settings',
                           controller='erfp_tool.controllers.settings'),
                    UrlMap(name='update_settings_ajax',
                           url='erfp-tool/settings/update',
                           controller='erfp_tool.controllers_ajax.settings_update'),
                    UrlMap(name='add-watershed',
                           url='erfp-tool/add-watershed',
                           controller='erfp_tool.controllers.add_watershed'),
                    UrlMap(name='add-watershed-ajax',
                           url='erfp-tool/add-watershed/submit',
                           controller='erfp_tool.controllers_ajax.watershed_add'),
                    UrlMap(name='add-watershed-ecmwf-rapid-files-ajax',
                           url='erfp-tool/add-watershed/upload_ecmwf_rapid',
                           controller='erfp_tool.controllers_ajax.watershed_ecmwf_rapid_file_upload'),
                    UrlMap(name='add-watershed-update-ajax',
                           url='erfp-tool/add-watershed/update',
                           controller='erfp_tool.controllers_ajax.watershed_update'),
                    UrlMap(name='add-watershed-delete-ajax',
                           url='erfp-tool/add-watershed/delete',
                           controller='erfp_tool.controllers_ajax.watershed_delete'),
                    UrlMap(name='manage-watersheds',
                           url='erfp-tool/manage-watersheds',
                           controller='erfp_tool.controllers.manage_watersheds'),
                    UrlMap(name='manage-watersheds-table',
                           url='erfp-tool/manage-watersheds/table',
                           controller='erfp_tool.controllers.manage_watersheds_table'),
                    UrlMap(name='manage-watersheds-edit',
                           url='erfp-tool/manage-watersheds/edit',
                           controller='erfp_tool.controllers.edit_watershed'),
                    UrlMap(name='manage-watershed-ecmwf-rapid-files-ajax',
                           url='erfp-tool/manage-watersheds/upload_ecmwf_rapid',
                           controller='erfp_tool.controllers_ajax.watershed_ecmwf_rapid_file_upload'),
                    UrlMap(name='delete-watershed',
                           url='erfp-tool/manage-watersheds/delete',
                           controller='erfp_tool.controllers_ajax.watershed_delete'),
                    UrlMap(name='update-watershed',
                           url='erfp-tool/manage-watersheds/submit',
                           controller='erfp_tool.controllers_ajax.watershed_update'),
                    UrlMap(name='add-geoserver',
                           url='erfp-tool/add-geoserver',
                           controller='erfp_tool.controllers.add_geoserver'),
                    UrlMap(name='add-geoserver-ajax',
                           url='erfp-tool/add-geoserver/submit',
                           controller='erfp_tool.controllers_ajax.geoserver_add'),
                    UrlMap(name='manage-geoservers',
                           url='erfp-tool/manage-geoservers',
                           controller='erfp_tool.controllers.manage_geoservers'),
                    UrlMap(name='manage-geoservers-table',
                           url='erfp-tool/manage-geoservers/table',
                           controller='erfp_tool.controllers.manage_geoservers_table'),
                    UrlMap(name='update-geoservers-ajax',
                           url='erfp-tool/manage-geoservers/submit',
                           controller='erfp_tool.controllers_ajax.geoserver_update'),
                    UrlMap(name='delete-geoserver-ajax',
                           url='erfp-tool/manage-geoservers/delete',
                           controller='erfp_tool.controllers_ajax.geoserver_delete'),
                    UrlMap(name='add-data-store',
                           url='erfp-tool/add-data-store',
                           controller='erfp_tool.controllers.add_data_store'),
                    UrlMap(name='add-data-store-ajax',
                           url='erfp-tool/add-data-store/submit',
                           controller='erfp_tool.controllers_ajax.data_store_add'),
                    UrlMap(name='manage-data-stores',
                           url='erfp-tool/manage-data-stores',
                           controller='erfp_tool.controllers.manage_data_stores'),
                    UrlMap(name='manage-data-stores-table',
                           url='erfp-tool/manage-data-stores/table',
                           controller='erfp_tool.controllers.manage_data_stores_table'),
                    UrlMap(name='update-data-store-ajax',
                           url='erfp-tool/manage-data-stores/submit',
                           controller='erfp_tool.controllers_ajax.data_store_update'),
                    UrlMap(name='delete-data-store-ajax',
                           url='erfp-tool/manage-data-stores/delete',
                           controller='erfp_tool.controllers_ajax.data_store_delete'),
                    UrlMap(name='add-watershed-group',
                           url='erfp-tool/add-watershed-group',
                           controller='erfp_tool.controllers.add_watershed_group'),
                    UrlMap(name='add-watershed-group-ajax',
                           url='erfp-tool/add-watershed-group/submit',
                           controller='erfp_tool.controllers_ajax.watershed_group_add'),
                    UrlMap(name='manage-watershed-groups',
                           url='erfp-tool/manage-watershed-groups',
                           controller='erfp_tool.controllers.manage_watershed_groups'),
                    UrlMap(name='manage-watershed-groups-table',
                           url='erfp-tool/manage-watershed-groups/table',
                           controller='erfp_tool.controllers.manage_watershed_groups_table'),
                    UrlMap(name='update-watershed-group-ajax',
                           url='erfp-tool/manage-watershed-groups/submit',
                           controller='erfp_tool.controllers_ajax.watershed_group_update'),
                    UrlMap(name='delete-watershed-group-ajax',
                           url='erfp-tool/manage-watershed-groups/delete',
                           controller='erfp_tool.controllers_ajax.watershed_group_delete'),
                    UrlMap(name='getting-started',
                           url='erfp-tool/getting-started',
                           controller='erfp_tool.controllers.getting_started')
        )
        return url_maps
        
    def persistent_stores(self):
        """
        Add one or more persistent stores
        """
        stores = (PersistentStore(name='settings_db',
                                  initializer='init_stores:init_erfp_settings_db',
                                  spatial=False
                ),
        )

        return stores
