# -*- coding: utf-8 -*-
"""model.py

    Created by Alan D. Snow, 2015-2017.
    License: BSD 3-Clause
"""
import os
from shutil import rmtree

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Boolean, Column, Integer, String, ForeignKey, and_
from sqlalchemy.event import listens_for
from sqlalchemy.orm import relationship

from spt_dataset_manager.dataset_manager import (CKANDatasetManager,
                                                 GeoServerDatasetManager)

from .app import StreamflowPredictionTool as app

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
    data_store_type_id = Column(Integer, ForeignKey('data_store_type.id'))
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


class GeoServer(Base):
    """
    GeoServer SQLAlchemy DB Model
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
    geoserver_drainage_line_layer_id = \
        Column(Integer, ForeignKey('geoserver_layer.id'))
    geoserver_boundary_layer_id = \
        Column(Integer, ForeignKey('geoserver_layer.id'))
    geoserver_gage_layer_id = \
        Column(Integer, ForeignKey('geoserver_layer.id'))
    geoserver_historical_flood_map_layer_id = \
        Column(Integer, ForeignKey('geoserver_layer.id'))
    geoserver_ahps_station_layer_id = \
        Column(Integer, ForeignKey('geoserver_layer.id'))
    watershed_name = Column(String)
    subbasin_name = Column(String)
    watershed_clean_name = Column(String)
    subbasin_clean_name = Column(String)
    data_store = relationship("DataStore")
    ecmwf_rapid_input_resource_id = Column(String)
    ecmwf_data_store_watershed_name = Column(String)
    ecmwf_data_store_subbasin_name = Column(String)
    geoserver = relationship("GeoServer")
    geoserver_drainage_line_layer = \
        relationship("GeoServerLayer",
                     foreign_keys=[geoserver_drainage_line_layer_id],
                     single_parent=True,
                     cascade="save-update,merge,delete,delete-orphan")
    geoserver_boundary_layer = \
        relationship("GeoServerLayer",
                     foreign_keys=[geoserver_boundary_layer_id],
                     single_parent=True,
                     cascade="save-update,merge,delete,delete-orphan")
    geoserver_gage_layer = \
        relationship("GeoServerLayer",
                     foreign_keys=[geoserver_gage_layer_id],
                     single_parent=True,
                     cascade="save-update,merge,delete,delete-orphan")
    geoserver_historical_flood_map_layer = \
        relationship("GeoServerLayer",
                     foreign_keys=[geoserver_historical_flood_map_layer_id],
                     single_parent=True,
                     cascade="save-update,merge,delete,delete-orphan")
    geoserver_ahps_station_layer = \
        relationship("GeoServerLayer",
                     foreign_keys=[geoserver_ahps_station_layer_id],
                     single_parent=True,
                     cascade="save-update,merge,delete,delete-orphan")
    watershed_groups = relationship("WatershedGroup",
                                    secondary='watershed_watershed_group_link')

    def delete_geoserver_files(self):
        """
        Removes old watershed geoserver files from system
        """
        # initialize geoserver manager
        app_instance_id = app.get_custom_setting('app_instance_id')
        geoserver_manager = \
            GeoServerDatasetManager(engine_url=self.geoserver.url,
                                    username=self.geoserver.username,
                                    password=self.geoserver.password,
                                    app_instance_id=app_instance_id)

        # delete layers which need to be deleted
        if self.geoserver_drainage_line_layer:
            if self.geoserver_drainage_line_layer.uploaded:
                geoserver_manager.purge_remove_geoserver_layer(
                    self.geoserver_drainage_line_layer.name)

        if self.geoserver_boundary_layer:
            if self.geoserver_boundary_layer.uploaded:
                geoserver_manager.purge_remove_geoserver_layer(
                    self.geoserver_boundary_layer.name)

        if self.geoserver_gage_layer:
            if self.geoserver_gage_layer.uploaded:
                geoserver_manager.purge_remove_geoserver_layer(
                    self.geoserver_gage_layer.name)

        if self.geoserver_ahps_station_layer:
            if self.geoserver_ahps_station_layer.uploaded:
                geoserver_manager.purge_remove_geoserver_layer(
                    self.geoserver_ahps_station_layer.name)

    def delete_prediction_files(self):
        """
        Removes prediction files from system
        if no other watershed has them
        """
        def delete_prediciton_files(watershed_folder_name,
                                    local_prediction_files_location):
            """
            Removes predicitons from folder and folder if not empty
            """
            prediciton_folder = os.path.join(local_prediction_files_location,
                                             watershed_folder_name)
            # remove watersheds subbsasins folders/files
            if watershed_folder_name and \
                    local_prediction_files_location and os.path.exists(
                prediciton_folder):

                # remove all prediction files from watershed/subbasin
                try:
                    rmtree(prediciton_folder)
                except OSError:
                    pass

                # remove watershed folder if no other subbasins exist
                try:
                    os.rmdir(os.path.join(local_prediction_files_location,
                                          watershed_folder_name))
                except OSError:
                    pass

        # initialize session
        session_maker = app.get_persistent_store_database('main_db',
                                                          as_sessionmaker=True)
        session = session_maker()

        # Remove ECMWF Forecasta
        # Make sure that you don't delete if another watershed is using the
        # same predictions
        num_ecmwf_watersheds_with_forecast = session.query(Watershed) \
            .filter(
            and_(
                Watershed.ecmwf_data_store_watershed_name ==
                self.ecmwf_data_store_watershed_name,
                Watershed.ecmwf_data_store_subbasin_name ==
                self.ecmwf_data_store_subbasin_name
            )
        ) \
            .filter(Watershed.id != self.id) \
            .count()
        if num_ecmwf_watersheds_with_forecast <= 0:
            ecmwf_rapid_prediction_directory = \
                app.get_custom_setting('ecmwf_forecast_folder')
            delete_prediciton_files(
                "{0}-{1}".format(self.ecmwf_data_store_watershed_name,
                                 self.ecmwf_data_store_subbasin_name),
                ecmwf_rapid_prediction_directory
            )

        session.close()

    def delete_rapid_input_ckan(self):
        """
        This function deletes RAPID input on CKAN
        """
        if 'ckan' == self.data_store.data_store_type.code_name \
                and self.ecmwf_rapid_input_resource_id.strip():
            # get dataset managers
            data_manager = CKANDatasetManager(self.data_store.api_endpoint,
                                              self.data_store.api_key,
                                              "ecmwf")
            data_manager.dataset_engine.delete_resource(
                self.ecmwf_rapid_input_resource_id)
            self.ecmwf_rapid_input_resource_id = ""

    def delete_all_files(self):
        """
        Removes old files from system
        """
        # remove old geoserver files
        self.delete_geoserver_files()
        # remove old ECMWF prediction files
        self.delete_prediction_files()
        # remove RAPID input files on CKAN
        self.delete_rapid_input_ckan()


@listens_for(Watershed, 'after_delete')
def delete_watershed_files(mapper, connect, target):
    """
    Removes old watershed geoserver files from system
    """
    target.delete_all_files()


class WatershedWatershedGroupLink(Base):
    """
    SQLAlchemy many-to-many link between watershed and watershed_group
    """
    __tablename__ = 'watershed_watershed_group_link'
    watershed_group_id = \
        Column(Integer, ForeignKey('watershed_group.id'), primary_key=True)
    watershed_id = \
        Column(Integer, ForeignKey('watershed.id'), primary_key=True)


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
