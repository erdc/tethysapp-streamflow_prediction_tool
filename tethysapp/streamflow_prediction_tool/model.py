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


Base = declarative_base()


class DataStore(Base):
    """
    DataStore SQLAlchemy DB Model
    """
    __tablename__ = 'data_store'

    # Columns
    id = Column(Integer, primary_key=True)
    name = Column(String)
    owner_org = Column(String)
    data_store_type_id = Column(Integer,ForeignKey('data_store_type.id'))
    data_store_type = relationship("DataStoreType")
    api_endpoint = Column(String)
    api_key = Column(String)


class DataStoreType(Base):
    """
    DataStoreType SQLAlchemy DB Model
    """
    __tablename__ = 'data_store_type'

    # Columns
    id = Column(Integer, primary_key=True)
    code_name = Column(String)
    human_readable_name = Column(String)


class Geoserver(Base):
    """
    Geoserver SQLAlchemy DB Model
    """
    __tablename__ = 'geoserver'

    # Columns
    id = Column(Integer, primary_key=True)
    name = Column(String)
    url = Column(String)
    username = Column(String)
    password = Column(String)


class GeoServerLayer(Base):
    """
    Geoserver Layer SQLAlchemy DB Model
    """
    __tablename__ = 'geoserver_layer'

    # Columns
    id = Column(Integer, primary_key=True)
    name = Column(String)
    uploaded = Column(Boolean, default=False)
    latlon_bbox = Column(String, default="")
    projection = Column(String, default="")
    attribute_list = Column(String, default="")
    wfs_url = Column(String, default="")
    

class Watershed(Base):
    """
    Watershed SQLAlchemy DB Model
    """
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
    """
    SQLAlchemy many-to-many link between watershed and watershed_group
    """
    __tablename__ = 'watershed_watershed_group_link'
    watershed_group_id = Column(Integer, ForeignKey('watershed_group.id'), primary_key=True)
    watershed_id = Column(Integer, ForeignKey('watershed.id'), primary_key=True)


class WatershedGroup(Base):
    """
    WatershedGroup SQLAlchemy DB Model
    """
    __tablename__ = 'watershed_group'

    # Columns
    id = Column(Integer, primary_key=True)
    name = Column(String)
    watersheds = relationship("Watershed", 
                              secondary='watershed_watershed_group_link')
