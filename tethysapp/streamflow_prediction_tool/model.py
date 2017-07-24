# -*- coding: utf-8 -*-
##
##  model.py
##  streamflow_prediction_tool
##
##  Created by Alan D. Snow.
##  Copyright © 2015-2016 Alan D Snow. All rights reserved.
##  License: BSD 3-Clause

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Boolean, Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from uuid import uuid5, NAMESPACE_DNS
from datetime import datetime

Base = declarative_base()


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
        

class DataStore(Base):
    '''
    DataStore SQLAlchemy DB Model
    '''
    __tablename__ = 'data_store'

    # Columns
    id = Column(Integer, primary_key=True)
    name = Column(String)
    owner_org = Column(String)
    data_store_type_id = Column(Integer,ForeignKey('data_store_type.id'))
    data_store_type = relationship("DataStoreType")
    api_endpoint = Column(String)
    api_key = Column(String)

    def __init__(self, server_name, owner_org, data_store_type_id, 
                       api_endpoint, api_key):
        self.name = server_name
        self.owner_org = owner_org
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


class GeoServerLayer(Base):
    '''
    Geoserver Layer SQLAlchemy DB Model
    '''
    __tablename__ = 'geoserver_layer'

    # Columns
    id = Column(Integer, primary_key=True)
    name = Column(String)
    uploaded = Column(Boolean)
    latlon_bbox = Column(String)
    projection = Column(String)
    attribute_list = Column(String)
    wfs_url = Column(String)
    
    def __init__(self, name, uploaded=False, latlon_bbox="", projection="",
                 attribute_list="", wfs_url=""):
        self.name = name
        self.uploaded = uploaded
        self.latlon_bbox = latlon_bbox
        self.projection = projection
        self.attribute_list = attribute_list
        self.wfs_url = wfs_url
    
class Watershed(Base):
    '''
    Watershed SQLAlchemy DB Model
    '''
    __tablename__ = 'watershed'

    # Columns
    id = Column(Integer, primary_key=True)
    data_store_id = Column(Integer, ForeignKey('data_store.id'))
    geoserver_id = Column(Integer, ForeignKey('geoserver.id'))
    geoserver_drainage_line_layer_id = Column(Integer, ForeignKey('geoserver_layer.id'))
    geoserver_boundary_layer_id = Column(Integer, ForeignKey('geoserver_layer.id'))
    geoserver_gage_layer_id = Column(Integer, ForeignKey('geoserver_layer.id'))
    geoserver_historical_flood_map_layer_id = Column(Integer, ForeignKey('geoserver_layer.id'))
    geoserver_ahps_station_layer_id = Column(Integer, ForeignKey('geoserver_layer.id'))
    watershed_name = Column(String)
    subbasin_name = Column(String)
    watershed_clean_name = Column(String)
    subbasin_clean_name = Column(String)
    data_store = relationship("DataStore")
    ecmwf_rapid_input_resource_id = Column(String)
    ecmwf_data_store_watershed_name = Column(String)
    ecmwf_data_store_subbasin_name = Column(String)
    wrf_hydro_data_store_watershed_name = Column(String)
    wrf_hydro_data_store_subbasin_name = Column(String)
    geoserver = relationship("Geoserver")
    geoserver_drainage_line_layer = relationship("GeoServerLayer", 
                                                 foreign_keys=[geoserver_drainage_line_layer_id],
                                                 single_parent=True,
                                                 cascade="save-update,merge,delete,delete-orphan")
    geoserver_boundary_layer = relationship("GeoServerLayer", 
                                            foreign_keys=[geoserver_boundary_layer_id],
                                            single_parent=True,
                                            cascade="save-update,merge,delete,delete-orphan")
    geoserver_gage_layer = relationship("GeoServerLayer", 
                                        foreign_keys=[geoserver_gage_layer_id],
                                        single_parent=True,
                                        cascade="save-update,merge,delete,delete-orphan")
    geoserver_historical_flood_map_layer = relationship("GeoServerLayer", 
                                                        foreign_keys=[geoserver_historical_flood_map_layer_id],
                                                        single_parent=True,
                                                        cascade="save-update,merge,delete,delete-orphan")
    geoserver_ahps_station_layer = relationship("GeoServerLayer", 
                                                foreign_keys=[geoserver_ahps_station_layer_id],
                                                single_parent=True,
                                                cascade="save-update,merge,delete,delete-orphan")
    watershed_groups = relationship("WatershedGroup",
                                    secondary='watershed_watershed_group_link')


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
        