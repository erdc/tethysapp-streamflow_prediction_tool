# -*- coding: utf-8 -*-
##
##  init_stores.py
##  streamflow_prediction_tool
##
##  Created by Alan D. Snow.
##  Copyright © 2015-2016 Alan D. Snow. All rights reserved.
##  License: BSD 3-Clause

from .app import StreamflowPredictionTool as app
from .model import Base, BaseLayer, DataStore, DataStoreType, MainSettings


def init_main_db(engine, first_time):
    # Create tables
    Base.metadata.create_all(engine)
    
    # Initial data
    if first_time:
        #make session
        session_maker = app.get_persistent_store_database('main_db', as_sessionmaker=True)
        session = session_maker()

        #add all possible base layers
        session.add(BaseLayer("MapQuest","none",))
        session.add(BaseLayer("Esri","none",))
        session.add(BaseLayer("BingMaps","",))
        
        #add all possible data story types
        session.add(DataStoreType("local", "Computations Local (None)"))
        session.add(DataStoreType("ckan", "CKAN"))
        session.add(DataStoreType("hydroshare", "HydroShare"))
        
        #add all possible data stores
        session.add(DataStore("Local Server", "", 1, "local", ""))

        #add main settings
        session.add(MainSettings(1, "", "", ""))
        
        session.commit()
        session.close()
