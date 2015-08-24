# Put your persistent store models in this file
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Boolean, Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship, sessionmaker
from uuid import uuid5, NAMESPACE_DNS
from datetime import datetime
from .utilities import get_persistent_store_engine
# DB Engine, sessionmaker and base
settingsEngine = get_persistent_store_engine('settings_db')
SettingsSessionMaker = sessionmaker(bind=settingsEngine)
Base = declarative_base()

class MainSettings(Base):
    '''
    Main Settings SQLAlchemy DB Model
    '''
    __tablename__ = 'main_settings'

    # Columns
    id = Column(Integer, primary_key=True)
    base_layer_id = Column(Integer,ForeignKey('base_layer.id'))
    base_layer = relationship("BaseLayer")
    ecmwf_rapid_prediction_directory = Column(String)
    era_interim_rapid_directory = Column(String)
    wrf_hydro_rapid_prediction_directory = Column(String)
    app_instance_id = Column(String)

    def __init__(self, base_layer_id, ecmwf_rapid_prediction_directory, 
                 era_interim_rapid_directory, wrf_hydro_rapid_prediction_directory):

        self.base_layer_id = base_layer_id
        self.ecmwf_rapid_prediction_directory = ecmwf_rapid_prediction_directory
        self.era_interim_rapid_directory = era_interim_rapid_directory
        self.wrf_hydro_rapid_prediction_directory = wrf_hydro_rapid_prediction_directory
        self.app_instance_id = uuid5(NAMESPACE_DNS, '%s%s' % ("sfpt", datetime.now())).hex
        
class BaseLayer(Base):
    '''
    BaseLayer SQLAlchemy DB Model
    '''
    __tablename__ = 'base_layer'

    # Columns
    id = Column(Integer, primary_key=True)
    name = Column(String)
    api_key = Column(String)

    def __init__(self, name, api_key):
        self.name = name
        self.api_key = api_key

class DataStore(Base):
    '''
    DataStore SQLAlchemy DB Model
    '''
    __tablename__ = 'data_store'

    # Columns
    id = Column(Integer, primary_key=True)
    name = Column(String)
    data_store_type_id = Column(Integer,ForeignKey('data_store_type.id'))
    data_store_type = relationship("DataStoreType")
    api_endpoint = Column(String)
    api_key = Column(String)

    def __init__(self, server_name, data_store_type_id, api_endpoint, api_key):
        self.name = server_name
        self.data_store_type_id = data_store_type_id
        self.api_endpoint = api_endpoint
        self.api_key = api_key

class DataStoreType(Base):
    '''
    DataStoreType SQLAlchemy DB Model
    '''
    __tablename__ = 'data_store_type'

    # Columns
    id = Column(Integer, primary_key=True)
    code_name = Column(String)
    human_readable_name = Column(String)

    def __init__(self, code_name, human_readable_name):
        self.code_name = code_name
        self.human_readable_name = human_readable_name

class Geoserver(Base):
    '''
    Geoserver SQLAlchemy DB Model
    '''
    __tablename__ = 'geoserver'

    # Columns
    id = Column(Integer, primary_key=True)
    name = Column(String)
    url = Column(String)
    username = Column(String)
    password = Column(String)
    
    def __init__(self, name, url, username, password):
        self.name = name
        self.url = url
        self.username = username
        self.password = password

class Watershed(Base):
    '''
    Watershed SQLAlchemy DB Model
    '''
    __tablename__ = 'watershed'

    # Columns
    id = Column(Integer, primary_key=True)
    watershed_name = Column(String)
    subbasin_name = Column(String)
    folder_name = Column(String)
    file_name = Column(String)
    data_store_id = Column(Integer,ForeignKey('data_store.id'))
    data_store = relationship("DataStore")
    ecmwf_rapid_input_resource_id = Column(String)
    ecmwf_data_store_watershed_name = Column(String)
    ecmwf_data_store_subbasin_name = Column(String)
    wrf_hydro_data_store_watershed_name = Column(String)
    wrf_hydro_data_store_subbasin_name = Column(String)
    geoserver_id = Column(Integer,ForeignKey('geoserver.id'))
    geoserver = relationship("Geoserver")
    geoserver_drainage_line_layer = Column(String)
    geoserver_catchment_layer = Column(String)
    geoserver_gage_layer = Column(String)
    geoserver_ahps_station_layer = Column(String)
    geoserver_drainage_line_uploaded = Column(Boolean)
    geoserver_catchment_uploaded = Column(Boolean)
    geoserver_gage_uploaded = Column(Boolean)
    geoserver_ahps_station_uploaded = Column(Boolean)
    geoserver_search_for_flood_map = Column(Boolean)
    kml_drainage_line_layer = Column(String)
    kml_catchment_layer = Column(String)
    kml_gage_layer = Column(String)
    watershed_groups = relationship("WatershedGroup", 
                                    secondary='watershed_watershed_group_link')
                              
    def __init__(self, watershed_name, subbasin_name, folder_name, file_name,
                 data_store_id, ecmwf_rapid_input_resource_id, 
                 ecmwf_data_store_watershed_name, ecmwf_data_store_subbasin_name,
                 wrf_hydro_data_store_watershed_name, wrf_hydro_data_store_subbasin_name,
                 geoserver_id, geoserver_drainage_line_layer, geoserver_catchment_layer, 
                 geoserver_gage_layer, geoserver_ahps_station_layer,
                 geoserver_drainage_line_uploaded, geoserver_catchment_uploaded, 
                 geoserver_gage_uploaded, geoserver_ahps_station_uploaded, 
                 geoserver_search_for_flood_map, kml_drainage_line_layer, 
                 kml_catchment_layer, kml_gage_layer):

        self.watershed_name = watershed_name
        self.subbasin_name = subbasin_name
        self.folder_name = folder_name
        self.file_name = file_name
        self.data_store_id = data_store_id
        self.ecmwf_rapid_input_resource_id = ecmwf_rapid_input_resource_id
        self.ecmwf_data_store_watershed_name = ecmwf_data_store_watershed_name
        self.ecmwf_data_store_subbasin_name = ecmwf_data_store_subbasin_name
        self.wrf_hydro_data_store_watershed_name = wrf_hydro_data_store_watershed_name
        self.wrf_hydro_data_store_subbasin_name = wrf_hydro_data_store_subbasin_name
        self.geoserver_id = geoserver_id
        self.geoserver_drainage_line_layer = geoserver_drainage_line_layer
        self.geoserver_catchment_layer = geoserver_catchment_layer
        self.geoserver_gage_layer = geoserver_gage_layer
        self.geoserver_ahps_station_layer = geoserver_ahps_station_layer
        self.geoserver_drainage_line_uploaded = geoserver_drainage_line_uploaded
        self.geoserver_catchment_uploaded = geoserver_catchment_uploaded
        self.geoserver_gage_uploaded = geoserver_gage_uploaded
        self.geoserver_ahps_station_uploaded = geoserver_ahps_station_uploaded
        self.geoserver_search_for_flood_map = geoserver_search_for_flood_map
        self.kml_drainage_line_layer = kml_drainage_line_layer
        self.kml_catchment_layer = kml_catchment_layer
        self.kml_gage_layer = kml_gage_layer

class WatershedWatershedGroupLink(Base):
    '''
    SQLAlchemy many-to-many link between watershed and watershed_group
    '''
    __tablename__ = 'watershed_watershed_group_link'
    watershed_group_id = Column(Integer, ForeignKey('watershed_group.id'), primary_key=True)
    watershed_id = Column(Integer, ForeignKey('watershed.id'), primary_key=True)

class WatershedGroup(Base):
    '''
    WatershedGroup SQLAlchemy DB Model
    '''
    __tablename__ = 'watershed_group'

    # Columns
    id = Column(Integer, primary_key=True)
    name = Column(String)
    watersheds = relationship("Watershed", 
                              secondary='watershed_watershed_group_link')

    def __init__(self, name):
        self.name = name
        