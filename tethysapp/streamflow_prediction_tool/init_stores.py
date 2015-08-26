# Put your persistent store initializer functions in here
from .model import (Base, BaseLayer, DataStore, DataStoreType, Geoserver, MainSettings,
                    mainEngine, mainSessionMaker)

def init_main_db(first_time):
    # Create tables
    Base.metadata.create_all(mainEngine)
    
    # Initial data
    if first_time:
        #make session
        session = mainSessionMaker()
        
        #add all possible base layers
        session.add(BaseLayer("MapQuest","none",))
        session.add(BaseLayer("Esri","none",))
        session.add(BaseLayer("BingMaps","",))
        
        #add all possible data story types
        session.add(DataStoreType("local", "Local (KML)"))
        session.add(DataStoreType("ckan", "CKAN"))
        session.add(DataStoreType("hydroshare", "HydroShare"))
        
        #add all possible data stores
        session.add(DataStore("Local Server", 1, "local", ""))

        #add all possible geoservers
        session.add(Geoserver("Local Server", "media", "", ""))

        #add main settings
        session.add(MainSettings(1, "", "", ""))
        
        session.commit()
        session.close()
