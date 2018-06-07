/*****************************************************************************
 * FILE:    map.js
 * AUTHOR:  Alan D. Snow
 * COPYRIGHT: © 2015-2016 Alan D. Snow. All rights reserved.
 * LICENSE: BSD 3-Clause
 *****************************************************************************/

/*****************************************************************************
 *                      LIBRARY WRAPPER
 *****************************************************************************/

var ERFP_MAP = (function() {
    // Wrap the library in a package function
    "use strict"; // And enable strict mode for this library

    /************************************************************************
     *                      MODULE LEVEL / GLOBAL VARIABLES
     *************************************************************************/
    var public_interface,                // Object returned by the module
        m_map,                    // the main map
        m_map_projection, //main map projection
        m_map_extent,           //the extent of all objects in map
        m_basemap_layer,
        m_drainage_line_layers,
        m_select_interaction,
        m_selected_feature,
        m_selected_ecmwf_watershed,
        m_selected_ecmwf_subbasin,
        m_selected_reach_id,
        m_selected_usgs_id,
        m_selected_nws_id,
        m_selected_hydroserver_url,
        m_downloading_ecmwf_hydrograph,
        m_downloading_long_term_select,
        m_downloading_usgs,
        m_downloading_nws,
        m_downloading_hydroserver,
        m_downloaded_historical_streamflow,
        m_downloaded_flow_duration,
        m_downloaded_daily_streamflow,
        m_downloaded_monthly_streamflow,
        m_searching_for_reach,
        m_long_term_chart_data_ajax_load_failed,
        m_long_term_select_data_ajax_handle,
        m_short_term_chart_data_ajax_load_failed,
        m_short_term_select_data_ajax_handle,
        m_ecmwf_forecast_folder,
        m_units,
        m_return_20_features_source,
        m_return_10_features_source,
        m_return_2_features_source,
        m_predicted_flood_maps;



    /************************************************************************
     *                    PRIVATE FUNCTION DECLARATIONS
     *************************************************************************/
    var stringToUTCmiliseconds, stringToUTCDate, resizeAppContent, bindInputs, 
        getCI, convertTimeSeriesEnglishToMetric, isNotLoadingPastRequest,
        zoomToAll, zoomToLayer, zoomToFeature, toTitleCase, datePadString,
        getBaseLayer, getTileLayer, clearAllMessages, clearInfoMessages,
        getDrainageLineLayer, getWarningPointsLayerGroup,
        dateToUTCString, clearChartSelect2, getChartData, displayHydrograph,
        loadHydrographFromFeature, resetChartSelectMessage,
        addECMWFSeriesToCharts, addSeriesToCharts, createEmptyForecastChart,
        isThereDataToLoad, checkCleanString, dateToUTCDateTimeString,
        getValidSeries, convertValueMetricToEnglish, unbindInputs,
        loadWarningPoints, updateWarningPoints, determineGeoServerLayerOrGroup,
        updateWarningSlider, isValidRiverSelected, loadFlowDurationChart,
        loadDailySeasonalStreamflowChart, loadMonthlySeasonalStreamflowChart,
        loadHistoricallStreamflowChart, updateDownloadForecastURL;


    /************************************************************************
     *                    PRIVATE FUNCTION IMPLEMENTATIONS
     *************************************************************************/
    stringToUTCmiliseconds = function(datetime_string) {
        var start_year = parseInt(datetime_string.substring(0,4));
        var start_month = parseInt(datetime_string.substring(4,6));
        var start_day = parseInt(datetime_string.substring(6,8));
        var start_hour = 0;
        var string_split = datetime_string.split(".");
        if (string_split.length > 1) {
            start_hour = parseInt(string_split[1].substring(0,2))
        }
        return Date.UTC(start_year, start_month-1,
                        start_day, start_hour, 0, 0, 0);

    }
    //FUNCTION: String to utc-date
    stringToUTCDate = function(datetime_string) {
        return new Date(stringToUTCmiliseconds(datetime_string));
    }
    //FUNCTION: reset chart and select options
    resetChartSelectMessage = function() {
        $('.long-term-select').addClass('hidden');
        //clear messages
        clearAllMessages();
    };

    //FUNCTION: binds dom elements to layer
    bindInputs = function(layerid, layer) {
        var visibilityInput = $(layerid + ' input.visible');
        visibilityInput.prop("checked", layer.getVisible());
        visibilityInput.on('change', function() {
            layer.setVisible(this.checked);
        });
        var opacityInput = $(layerid + ' input.opacity');
        opacityInput.val(layer.getOpacity());
        opacityInput.on('input change', function() {
          layer.setOpacity(parseFloat(this.value));
        });
    };
    
    //FUNCTION: unbind dom elements from layer
    unbindInputs = function(layerid) {
        $(layerid + ' input.visible').off();
        $(layerid + ' input.opacity').off();
    }

    //FUNCTION: check to see if a valid reach selected
    isValidRiverSelected = function(){
        return (m_selected_ecmwf_watershed != null
                && m_selected_ecmwf_subbasin != null
                && m_selected_reach_id != null);
    };

    //FUNCTION: check to see if there is data to redraw on chart
    isThereDataToLoad = function(){
        return (isValidRiverSelected()
               || (!isNaN(m_selected_usgs_id) && m_selected_usgs_id != null)
               || (!isNaN(m_selected_nws_id) && m_selected_nws_id != null)
               || m_selected_hydroserver_url != null);
    };

    //FUNCTION: convert units from metric to english
    convertValueMetricToEnglish = function(data_value) {
        var conversion_factor = 1;
        if(m_units=="english") {
            conversion_factor = 35.3146667;
        }
        return data_value * conversion_factor;
    };

    //FUNCTION: convert units from english to metric
    convertTimeSeriesEnglishToMetric = function(time_series, series_name) {
        var series_data = [];
        var series_dates = [];
        var date_time_value, data_value;
        var conversion_factor = 1;
        if (m_units == "metric") {
            conversion_factor = 35.3146667;
        }
        try {
            time_series.map(function(data) {
               if (series_name == "USGS") {
                   data_value = data.value;
                   date_time_value = data.dateTime;
               } else {
                   date_time_value = data[0];
                   data_value = data[1];
               }
               series_data.push(parseFloat(data_value)/conversion_factor);
               series_dates.push(new Date(date_time_value).toISOString().replace("T", " ").replace("Z", ""));
            });
        } catch (e) {
            console.log(e);
            if (e instanceof TypeError) {
                appendErrorMessage("Error loading " + series_name + " data.", "load_series_error", "message-error");
            }
        }

        return {dates: series_dates, data: series_data};
    };

    //FUNCTION: cleans sting and returns null if empty
    checkCleanString = function(string) {
        if(typeof string == 'undefined' || string == null) {
            return null;
        } else if (typeof string != 'string') {
            return string;
        } else {
            string = string.trim();
            //set to null if it is empty string
            if (string.length <= 0) {
                return null;
            }
            return string;
        }
    };

    //FUNCTION: ol case insensitive get feature property
    getCI = function(obj, prop){
        prop = prop.toLowerCase();
        for(var key in obj.getProperties()){
            if(prop == key.toLowerCase()){
                return checkCleanString(obj.get(key));
            }
        }
        return null;
    };

    //FUNCTION: get series with actual data
    getValidSeries = function(series_array){
        if (series_array != null) {
            var valid_series;
            for (var i=0; i<series_array.length; i++) {
                valid_series = true;
                for (var j=0; j<series_array[i].length; j++) {
                    if (series_array[i][j][1] < 0) {
                        valid_series = false;
                        break;
                    }
                }
                if (valid_series) {
                    return series_array[i];
                }
            }
        }
        return null;
    };

    //FUNCTION: check if loading past request
    isNotLoadingPastRequest = function() {
        return !m_downloading_ecmwf_hydrograph && !m_downloading_long_term_select &&
            !m_downloading_usgs && !m_downloading_nws && !m_downloading_hydroserver;
    };

    //FUNCTION: zooms to all layers
    zoomToAll = function() {
        m_map.getView().fit(m_map_extent, m_map.getSize());
    };

    //FUNCTION: zooms to layer with id layer_id
    zoomToLayer = function(layer_id) {
        var layer_extent = null;
        m_map.getLayers().forEach(function(layer, i) {
            if (layer instanceof ol.layer.Group) {
                if(layer.get('group_id') == layer_id) {
                    if (layer.get('layer_type') == "geoserver") {
                        layer_extent = layer.get('extent');
                    }
                }
            }
            else {
                if(layer.get('layer_id') == layer_id) {
                    if (layer.get('layer_type') == "geoserver") {
                        layer_extent = layer.get('extent');
                    } else {
                        layer_extent = layer.getSource().getExtent();
                    }
                } 
            }

            if (layer_extent != null && layer_extent !=ol.extent.createEmpty()) {
                m_map.getView().fit(layer_extent, m_map.getSize());
                return;
            }
        });    
    };

    //FUNCTION: zooms to feature in layer
    zoomToFeature = function(watershed_info, reach_id) {
        if(!m_searching_for_reach) {
            $("#reach-id-help-message").text('');
            $("#reach-id-help-message").parent().removeClass('alert-danger');
            var search_id_button = $("#submit-search-reach-id");
            var search_id_button_html = search_id_button.html();
            search_id_button.text('Searching ...');
            var watershed_split = watershed_info.split(":");        
            var watershed_name = watershed_split[0];
            var subbasin_name = watershed_split[1];
            
            m_drainage_line_layers.forEach(function(drainage_line_layer, j) {
                if(drainage_line_layer.get('watershed_name') == watershed_name &&
                    drainage_line_layer.get('subbasin_name') == subbasin_name) {
                    if (drainage_line_layer.get('layer_type') == "geoserver") {
                        m_searching_for_reach = true;
                        var reach_id_attr_name = getCI(drainage_line_layer, 'reach_id_attr_name');
                        if (reach_id_attr_name != null) {
                            //TODO: Make query more robust
                            var url = drainage_line_layer.get('geoserver_url') + 
                                  '&CQL_FILTER='+ drainage_line_layer.get('reach_id_attr_name') +' =' + reach_id +
                                  '&srsname=' + m_map_projection;
                            jQuery.ajax({
                                url: encodeURI(url),
                                dataType: 'json',
                            })
                            .done(function(response) {
                                if (response.totalFeatures > 0) {
                                    var geojsonFormat = new ol.format.GeoJSON();
                                    var features = geojsonFormat.readFeatures(response);
                                    m_map.getView().fit(features[0].getGeometry().getExtent(), m_map.getSize());
                                    m_select_interaction.getFeatures().clear();
                                    m_select_interaction.getFeatures().push(features[0]);
                                } else {
                                    $("#reach-id-help-message").text('Reach ID ' + reach_id + ' not found');
                                    $("#reach-id-help-message").parent().addClass('alert-danger');
                                }
                            })
                            .always(function() {
                                m_searching_for_reach = false;
                                search_id_button.html(search_id_button_html);
                            });
                        } else {
                            $("#reach-id-help-message").text('No valid reach ID attribute found.');
                            $("#reach-id-help-message").parent().addClass('alert-danger');
                        }
                        return;
                    }
                }
            });
        }   
    };

    //FUNCTION: converts string to title case  
    toTitleCase = function(str)
    {
        return str.replace(/\w\S*/g, function(txt){return txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase();});
    };

    //FUNCTION: to convert date to string
    datePadString = function(i) {
        return (i < 10) ? "0" + i : "" + i; 
    };

    //FUNCTION: adds appropriate base layer based on name
    getBaseLayer = function(base_layer_name) {
        if (base_layer_name.toLowerCase() == "esri") {
            return new ol.layer.Tile({
              source: new ol.source.XYZ({
                attributions: [new ol.Attribution({
                  html: 'Tiles &copy; <a href="https://services.arcgisonline.com/ArcGIS/' +
                      'rest/services/World_Topo_Map/MapServer">ArcGIS</a>'
                })],
                url: 'https://server.arcgisonline.com/ArcGIS/rest/services/' +
                    'World_Topo_Map/MapServer/tile/{z}/{y}/{x}'
              })
            });
        }
        //default to mapquest
        return new ol.layer.Group({
                        style: 'AerialWithLabels',
                        layers: [
                          new ol.layer.Tile({
                            source: new ol.source.MapQuest({layer: 'sat'})
                          }),
                          new ol.layer.Tile({
                            source: new ol.source.MapQuest({layer: 'hyb'})
                          })
                        ]
                });

    };

    //FUNCTION: gets tile layer for geoserver
    getTileLayer = function(layer_info, geoserver_url, layer_id, visible, input_opacity) {
        //validate extent
        var extent = layer_info['latlon_bbox'].map(Number)
        if (Math.abs(extent[0]-extent[1]) > 0.001 &&
            Math.abs(extent[2]-extent[3]) > 0.001) {

            var layer = new ol.layer.Tile({
                source: new ol.source.TileWMS({
                    url: geoserver_url,
                    params: {'LAYERS': layer_info['name'], 
                             'TILED': true},
                    serverType: 'geoserver',
                }),
                visible: visible,
                opacity: input_opacity,
            });
            layer.set('extent', ol.proj.transformExtent(extent, 
                                                        'EPSG:4326',
                                                        m_map_projection));
            layer.set('layer_id', layer_id);
            layer.set('layer_type', 'geoserver');
            return layer;
        }
        return null;
    };

    //FUNCTION: gets Drainage Line layer from attributes
    getDrainageLineLayer = function(watershed_layers_info) {
        var drainage_line_layer_id = 'layer-' + watershed_layers_info.id + '-drainage_line';
        if ("error" in watershed_layers_info.drainage_line) {
            appendErrorMessage("Drainage Line Layer: " + watershed_layers_info.title + 
                               ": " + watershed_layers_info.drainage_line.error, 
                               "error_" + drainage_line_layer_id, "message-error");
            return null;
        } else {
            //check if required parameters exist
            if(watershed_layers_info.drainage_line.missing_attributes.length > 2) {
                appendErrorMessage('The drainage line layer for ' +
                                  watershed_layers_info.watershed + '(' +
                                  watershed_layers_info.subbasin + ') ' +
                                  'is missing '+
                                  watershed_layers_info.drainage_line.missing_attributes.join(", ") +
                                  ' attributes and will not function properly.', 
                                  "layer_loading_error", "message-error");
                return null;
            } 
            var drainage_line;
            //check layer capabilites
            if(watershed_layers_info.drainage_line.geoserver_method == "natur_flow_query") {
                var load_features_xhr = null;
                var drainage_line_vector_source = new ol.source.Vector({
                    format: new ol.format.GeoJSON(),
                    url: function(extent, resolution, projection) {
                        var stream_flow_limit = 5000;
                        var map_zoom = m_map.getView().getZoom();
                        if (map_zoom >= 12) {
                            stream_flow_limit = 0;
                        } else if (map_zoom >= 11) {
                            stream_flow_limit = 20;
                        } else if (map_zoom >= 10) {
                            stream_flow_limit = 100;
                        } else if (map_zoom >= 9) {
                            stream_flow_limit = 1000;
                        } else if (map_zoom >= 8) {
                            stream_flow_limit = 3000;
                        } else if (map_zoom >= 7) {
                            stream_flow_limit = 4000;
                        }
                        //cancel load featues if still active
                        if(load_features_xhr != null) {
                            load_features_xhr.abort();
                        }
                        return watershed_layers_info.drainage_line.geojson + 
                              '&PROPERTYNAME=the_geom,' +
                               watershed_layers_info.drainage_line.contained_attributes.join(",") +
                              '&CQL_FILTER=' + watershed_layers_info.drainage_line.geoserver_query_attribute +
                              ' > ' + stream_flow_limit +
                              ' AND bbox(the_geom,' + extent.join(',') + 
                              ',\'' + m_map_projection + '\')' +
                              '&srsname=' + m_map_projection;
                      },
                      strategy: function(extent, resolution) {
                          var zoom_range = 1;
                          var map_zoom = m_map.getView().getZoom();
                          if (map_zoom >= 12) {
                              zoom_range = 2;
                          } else if (map_zoom >= 11) {
                              zoom_range = 3;
                          } else if (map_zoom >= 10) {
                              zoom_range = 4;
                          } else if (map_zoom >= 9) {
                              zoom_range = 5;
                          } else if (map_zoom >= 8) {
                              zoom_range = 6;
                          } else if (map_zoom >= 7) {
                              zoom_range = 7;
                          }
    
                          if(zoom_range != this.zoom_range && typeof this.zoom_range != 'undefined') {
                              this.clear();  
                          }
                          this.zoom_range = zoom_range;
                          return [extent];
                      },
                      projection: m_map_projection,
                });
                drainage_line = new ol.layer.Vector({
                    source: drainage_line_vector_source,
                    maxResolution: 1000,
                    style: [
                        new ol.style.Style({
                            stroke: new ol.style.Stroke({
                                color: 'rgba(255,255,255,0.01)',
                                width: 30
                            })
                        }),
                        new ol.style.Style({
                            stroke: new ol.style.Stroke({
                                color: '#50B0E9',
                                width: 2
                            })
                        })
                    ]
                });
            } 
            else if(watershed_layers_info.drainage_line.geoserver_method == "river_order_query") {
                var load_features_xhr = null;
                var drainage_line_vector_source = new ol.source.Vector({
                    format: new ol.format.GeoJSON(),
                    url: function(extent, resolution, projection) {
                        var river_order_limit = 1000;
                        var map_zoom = m_map.getView().getZoom();
                        if (map_zoom >= 12) {
                            river_order_limit = 0;
                        } else if (map_zoom >= 11) {
                            river_order_limit = 2;
                        } else if (map_zoom >= 10) {
                            river_order_limit = 8;
                        } else if (map_zoom >= 9) {
                            river_order_limit = 64;
                        } else if (map_zoom >= 8) {
                            river_order_limit = 128;
                        } else if (map_zoom >= 7) {
                            river_order_limit = 300;
                        }
                        //cancel load featues if still active
                        if(load_features_xhr != null) {
                            load_features_xhr.abort();
                        }
                        return watershed_layers_info.drainage_line.geojson + 
                              '&PROPERTYNAME=the_geom,' +
                               watershed_layers_info.drainage_line.contained_attributes.join(",") +
                              '&CQL_FILTER=' + watershed_layers_info.drainage_line.geoserver_query_attribute +
                              ' > ' + river_order_limit +
                              ' AND bbox(the_geom,' + extent.join(',') + 
                              ',\'' + m_map_projection + '\')' +
                              '&srsname=' + m_map_projection;
                      },
                      strategy: function(extent, resolution) {
                          var zoom_range = 1;
                          var map_zoom = m_map.getView().getZoom();
                          if (map_zoom >= 12) {
                              zoom_range = 2;
                          } else if (map_zoom >= 11) {
                              zoom_range = 3;
                          } else if (map_zoom >= 10) {
                              zoom_range = 4;
                          } else if (map_zoom >= 9) {
                              zoom_range = 5;
                          } else if (map_zoom >= 8) {
                              zoom_range = 6;
                          } else if (map_zoom >= 7) {
                              zoom_range = 7;
                          }
    
                          if(zoom_range != this.zoom_range && typeof this.zoom_range != 'undefined') {
                              this.clear();  
                          }
                          this.zoom_range = zoom_range;
                          return [extent];
                      },
                      projection: m_map_projection,
                });
                drainage_line = new ol.layer.Vector({
                    source: drainage_line_vector_source,
                    maxResolution: 1000,
                    style: [
                        new ol.style.Style({
                            stroke: new ol.style.Stroke({
                                color: 'rgba(255,255,255,0.01)',
                                width: 30
                            })
                        }),
                        new ol.style.Style({
                            stroke: new ol.style.Stroke({
                                color: '#50B0E9',
                                width: 2
                            })
                        })
                    ]
                });
            } 
            else { //watershed_layers_info.drainage_line.geoserver_method == "simple"
                var drainage_line_vector_source = new ol.source.Vector({
                    format: new ol.format.GeoJSON(),
                    url: function(extent, resolution, projection) {
                        return watershed_layers_info.drainage_line.geojson + 
                              '&PROPERTYNAME=the_geom,' +
                               watershed_layers_info.drainage_line.contained_attributes.join(",") +
                              '&bbox=' + extent.join(',') + 
                              ','+ m_map_projection +
                              '&srsname=' + m_map_projection;
                    },
                    strategy: ol.loadingstrategy.tile(ol.tilegrid.createXYZ({
                        maxZoom: 19
                    })),
                    projection: m_map_projection
                });
                drainage_line = new ol.layer.Vector({
                    source: drainage_line_vector_source,
                    maxResolution: 300,
                    style: [
                        new ol.style.Style({
                            stroke: new ol.style.Stroke({
                                color: 'rgba(255,255,255,0.01)',
                                width: 30
                            })
                        }),
                        new ol.style.Style({
                            stroke: new ol.style.Stroke({
                                color: '#50B0E9',
                                width: 2
                            })
                        })
                    ]
                });
                
            }
    
            watershed_layers_info.drainage_line.contained_attributes.some(function(attribute) {
                if (attribute.toLowerCase() == "comid" || attribute.toLowerCase() == "hydroid") {
                    drainage_line.set('reach_id_attr_name', attribute);
                    return true;
                }
            });
    
            drainage_line.set('geoserver_url', watershed_layers_info.drainage_line.geojson)
            drainage_line.set('watershed_name', watershed_layers_info.watershed);
            drainage_line.set('subbasin_name', watershed_layers_info.subbasin);
            drainage_line.set('extent', ol.proj.transformExtent(watershed_layers_info.drainage_line.latlon_bbox.map(Number), 
                                                                'EPSG:4326',
                                                                m_map_projection));
            drainage_line.set('layer_id', drainage_line_layer_id);
            drainage_line.set('layer_type', 'geoserver');

            return drainage_line;
        }
    };

    //FUNCTION: Gets warning points layer
    getWarningPointsLayerGroup = function(fill_color, symbols, return_period, 
                                          group_id, ecmwf_watershed, ecmwf_subbasin) 
    {
        var layer_array = [];
        for(var i=0; i<16; i++) {
            layer_array.push(new ol.layer.Vector({
                source: new ol.source.Cluster({
                                                source: new ol.source.Vector({ source: []}),
                                                distance: 20
                                             }),
                style: function(feature, resolution) {
                    var features = feature.get("features");
                    var size = -1
                    if (typeof features != 'undefined') {
                        var size = features.length;
                    } 
                    var style;
                    if (size > 3) {
                        style = [new ol.style.Style({
                            image: new ol.style.RegularShape({
                              points: 3,
                              radius: 12,
                              stroke: new ol.style.Stroke({
                                color: '#fff'
                              }),
                              fill: new ol.style.Fill({
                                color: fill_color
                              })
                            }),
                            text: new ol.style.Text({
                              text: size.toString(),
                              fill: new ol.style.Fill({
                                color: '#fff'
                              })
                            })
                        })];
                    } else if (size < 0) {
                        style = [];
                    } else {
                        style = [];
                        for (var i=0; i<size; i++) {
                            style.push(new ol.style.Style({
                                image: symbols[features[i].getProperties().size]
                              }));
                        }
                    }
                    return style;
                },
            }));
        }
        return new ol.layer.Group({ 
                        layers: layer_array,
                        group_id: group_id,
                        layer_type: 'warning_points',
                        ecmwf_watershed_name: ecmwf_watershed,
                        ecmwf_subbasin_name: ecmwf_subbasin,
                        return_period: return_period,
                        daily_warnings: false,
                    });
    };

    //FUNCTION: removes message and hides the div
    clearInfoMessages = function() {
        $('#message').addClass('hidden');
        $('#message').empty();
    };

    clearAllMessages = function() {
        clearInfoMessages();
        $('#message-error').addClass('hidden');
        $('#message-error').empty();
    };

    //FUNCTION: removes chart select2
    clearChartSelect2 = function(model_name) {
        if($('#' + model_name + '-select').data('select2')) {
            $('#' + model_name + '-select').off('change.select2') //remove event handler
                             .select2('val', '') //remove selection
                             .select2('destroy'); //destroy
        }

    };

    //FUNCTION: converts date to UTC string in the format yyyy-mm-dd
    dateToUTCString = function(date) {
        return datePadString(date.getUTCFullYear()) + "-" +
              datePadString(1 + date.getUTCMonth()) + "-" +
              datePadString(date.getUTCDate());
    };

    //FUNCTION: converts date to UTC string in the format yyyy-mm-dd
    dateToUTCDateTimeString = function(date) {
        return dateToUTCString(date) + "T00:00:00";
    };

    //FUNCTION: updates forecast download URL
    updateDownloadForecastURL = function() {
        var params = {
            watershed_name: m_selected_ecmwf_watershed,
            subbasin_name: m_selected_ecmwf_subbasin,
            reach_id: m_selected_reach_id,
            units: m_units,
        };
        var sel_data = $('#download-select').select2('data');
        if (sel_data != null)
        {
            params.forecast_folder = sel_data.id;
        }

        //change download button urls
        $('#submit-download-forecast').attr({
            target: '_blank',
            href: 'get-forecast-streamflow-csv?' + jQuery.param( params )
        });
    }

    //FUNCTION: adds data to the chart
    addSeriesToCharts = function(series_data){
        $("#long-term-chart").removeClass('hidden');
        var existing_chart = $("#long-term-chart .js-plotly-plot");
        Plotly.addTraces(existing_chart[0], series_data);
        $(window).resize();
    };

    //FUNCTION: creates empty forecast chart
    createEmptyForecastChart = function(){
        $("#long-term-chart").html('<div><div id="plot_containter"></div></div>');
        var y_axis_title = "Streamflow (m<sup>3</sup>/s)";
        if (m_units == "english") {
            y_axis_title = "Streamflow (ft<sup>3</sup>/s)";
        }

        var layout = {
          title: 'Forecast',
          xaxis: {
            title: 'Date',
          },
          yaxis: {
            title: y_axis_title,
          },
          showlegend: true
        };

        Plotly.newPlot($("#long-term-chart #plot_containter")[0], [], layout);
    };

    //FUNCTION: gets all data for chart
    getChartData = function(from_units_toggle) {
        $('#long-term-chart').html('');
        from_units_toggle = (typeof from_units_toggle === 'undefined') ? false : from_units_toggle;

        if(!isNotLoadingPastRequest()) {
            //updateInfoAlert
            addWarningMessage("Please wait for datasets to download before making another selection.");

        } else if (!isThereDataToLoad()) {
            resetChartSelectMessage();
            //updateInfoAlert
            addWarningMessage("No data found to load. Please toggle on a dataset.");
        } else {
            resetChartSelectMessage();
            m_long_term_chart_data_ajax_load_failed = false;
            $('#donwnload_message').addClass('hidden');
            $('#download_interim').removeClass('hidden');

            if (!from_units_toggle)
            {
                m_downloaded_historical_streamflow = false;
                $("#historical_streamflow_data").removeClass('alert alert-info alert-danger')
                                                .text("");

                m_downloaded_flow_duration = false;
                $("#flow_duration_data").removeClass('alert alert-info alert-danger')
                                        .text("");

                m_downloaded_daily_streamflow = false;
                $("#daily_streamflow_data").removeClass('alert alert-info alert-danger')
                                           .text("");

                m_downloaded_monthly_streamflow = false;
                $("#monthly_streamflow_data").removeClass('alert alert-info alert-danger')
                                             .text("");

            }

            //UPDATE DOWNLOAD BUTTONS
            var params = {
                watershed_name: m_selected_ecmwf_watershed,
                subbasin_name: m_selected_ecmwf_subbasin,
                reach_id: m_selected_reach_id,
                units: m_units,
                daily: false
            };

            //change download button urls
            updateDownloadForecastURL();

            $('#submit-download-interim-csv').attr({
                target: '_blank',
                href: 'get-historic-data-csv?' + jQuery.param( params )
            });

            params.daily = true;
            $('#submit-download-interim-csv-daily').attr({
                target: '_blank',
                href: 'get-historic-data-csv?' + jQuery.param( params )
            });

            //turn off select interaction
            m_map.removeInteraction(m_select_interaction);

            addInfoMessage("Retrieving Data ...");
            if (!from_units_toggle) {
                $('#forecast_tab_link').tab('show'); //switch to plot tab
            }
            var ecmwf_deferred = null;
            //get ecmwf data
            if (isValidRiverSelected()) {
                ecmwf_deferred = $.Deferred();
                $('#long-term-chart').addClass('hidden');
                m_downloading_ecmwf_hydrograph = true;
                jQuery.ajax({
                    type: "GET",
                    url: "get-ecmwf-hydrograph-plot",
                    data: {
                        watershed_name: m_selected_ecmwf_watershed,
                        subbasin_name: m_selected_ecmwf_subbasin,
                        reach_id: m_selected_reach_id,
                        forecast_folder: m_ecmwf_forecast_folder,
                        units: m_units,
                    },
                })
                .done(function (data) {
                    $('.long-term-select').removeClass('hidden');
                    $('#long-term-chart').removeClass('hidden');
                    $('#long-term-chart').html(data);
                    Plotly.Plots.resize($("#long-term-chart .js-plotly-plot")[0]);
                    ecmwf_deferred.resolve();
                })
                .fail(function (request, status, error) {
                    $(document).trigger('forecast_chart_ready');
                    m_long_term_chart_data_ajax_load_failed = true;
                    appendErrorMessage(request.responseText, "ecmwf_error", "message-error");
                    clearChartSelect2('long-term');
                    clearChartSelect2('download');

                    createEmptyForecastChart();
                    ecmwf_deferred.resolve();
                })
                .always(function () {
                    m_downloading_ecmwf_hydrograph = false;
                    m_map.addInteraction(m_select_interaction);
                    if(isNotLoadingPastRequest()){
                        clearInfoMessages();
                    }
                });
            }
            else
            {
                createEmptyForecastChart()
            }

            if (isValidRiverSelected()) {
                $('#mytable').addClass('hidden');
                jQuery.ajax({
                    url: "get-ecmwf-forecast-probabilities",
                    type: "GET",
                    dataType: "json",
                    data: {
                        reach_id: m_selected_reach_id,
                        watershed_name: m_selected_ecmwf_watershed,
                        subbasin_name: m_selected_ecmwf_subbasin,
                        forecast_folder: m_ecmwf_forecast_folder,
                        units: m_units
                    },
                })
                .fail(function() {
                        $('#info').html('<p class="alert alert-danger" style="text-align: center"><strong>An unknown error occurred while retrieving the forecast table</strong></p>');
                        $('#info').removeClass('hidden');

                        setTimeout(function() {
                            $('#info').addClass('hidden')
                        }, 5000);
                })
                .done(function(response) {

                        var data  = response['percentages']
                        console.log(data)

                        $("#tbody").empty();
                        var tbody = document.getElementById('tbody');

                        var columNames = {
                            'two': 'Percent Exceedance (2-yr)',
                            'ten': 'Percent Exceedance (10-yr)',
                            'twenty': 'Percent Exceedance (20-yr)'
                        };

                        for (var object1 in data) {
                            if (object1 == "dates") {
                                var cellcolor = ""
                            } else if (object1 == "two") {
                                var cellcolor = "yellow"
                            } else if (object1 == "ten") {
                                var cellcolor = "red"
                            } else if (object1 == "twenty") {
                                var cellcolor = "purple"
                            }
                            if (object1 == "dates") {
                                var tr = "<tr id=" + object1.toString() + "><th>Dates</th>";
                                for (var value1 in data[object1]) {
                                    tr += "<th>" + data[object1][value1].toString() + "</th>"
                                }
                                tr += "</tr>";
                                tbody.innerHTML += tr;
                            } else {
                                var tr = "<tr id=" + object1.toString() + "><td>" + columNames[object1.toString()] + "</td>";
                                for (var value1 in data[object1]) {
                                    if (parseInt(data[object1][value1][1]) == 0) {
                                        tr += "<td class=" + cellcolor + "zero>" + data[object1][value1][1].toString() + "</td>"
                                    } else if (parseInt(data[object1][value1][1]) <= 20) {
                                        tr += "<td class=" + cellcolor + "twenty>" + data[object1][value1][1].toString() + "</td>"
                                    } else if (parseInt(data[object1][value1][1]) <= 40) {
                                        tr += "<td class=" + cellcolor + "fourty>" + data[object1][value1][1].toString() + "</td>"
                                    } else if (parseInt(data[object1][value1][1]) <= 60) {
                                        tr += "<td class=" + cellcolor + "sixty>" + data[object1][value1][1].toString() + "</td>"
                                    } else if (parseInt(data[object1][value1][1]) <= 80) {
                                        tr += "<td class=" + cellcolor + "eighty>" + data[object1][value1][1].toString() + "</td>"
                                    } else {
                                        tr += "<td class=" + cellcolor + "hundred>" + data[object1][value1][1].toString() + "</td>"
                                    }
                                }
                                tr += "</tr>";
                                tbody.innerHTML += tr;
                            }
                        }

                        $("#twenty").prependTo("#mytable");
                        $("#ten").prependTo("#mytable");
                        $("#two").prependTo("#mytable");
                        $("#percdates").prependTo("#mytable");
                        $('#mytable').removeClass('hidden');
                })
            }

            //get current dates
            var date_now = new Date();
            var date_past = new Date();
            date_past.setUTCDate(date_now.getUTCDate()-3);
            var date_future = new Date();
            date_future.setUTCDate(date_now.getUTCDate()+15);

            var date_observed_end =  date_now;
            var date_nws_end = date_future;

            //ECMWF Dates
            var ecmwf_date_forecast_begin = new Date(8640000000000000);
            var ecmwf_date_forecast_end = new Date(-8640000000000000);
            var get_ecmwf = m_ecmwf_forecast_folder != null && typeof m_ecmwf_forecast_folder != "undefined" &&
                m_ecmwf_forecast_folder != "most_recent";
            //get ECMWF forcast dates if available
            if(get_ecmwf) {
                var ecmwf_forecast_start_year = parseInt(m_ecmwf_forecast_folder.substring(0,4));
                var ecmwf_forecast_start_month = parseInt(m_ecmwf_forecast_folder.substring(4,6));
                var ecmwf_forecast_start_day = parseInt(m_ecmwf_forecast_folder.substring(6,8));
                var ecmwf_forecast_start_hour = parseInt(m_ecmwf_forecast_folder.split(".")[1].substring(0,2));
                ecmwf_date_forecast_begin = new Date(Date.UTC(ecmwf_forecast_start_year, ecmwf_forecast_start_month-1,
                                                     ecmwf_forecast_start_day, ecmwf_forecast_start_hour));
                ecmwf_date_forecast_end = new Date();
                ecmwf_date_forecast_end.setUTCDate(ecmwf_date_forecast_begin.getUTCDate()+15);

                //reset dates if applicable
                date_observed_end = ecmwf_date_forecast_end;
                date_nws_end = ecmwf_date_forecast_end;
            }

            var date_observed_start = new Date(Math.min.apply(null,[date_past, ecmwf_date_forecast_begin]));
            var date_nws_start = new Date(Math.min.apply(null,[date_now, ecmwf_date_forecast_begin]));

            //Get USGS data if USGS ID attribute exists
            if(!isNaN(m_selected_usgs_id) && m_selected_usgs_id != null) {
                if(m_selected_usgs_id.length >= 8) {
                    m_downloading_usgs = true;
                    //get USGS data
                    jQuery.ajax({
                        type: "GET",
                        url: "https://waterservices.usgs.gov/nwis/iv/",
                        dataType: "json",
                        data: {
                            format: 'json',
                            sites: m_selected_usgs_id,
                            startDT: dateToUTCString(date_observed_start),
                            endDT: dateToUTCString(date_observed_end),
                            parameterCd: '00060',
                        },
                    })
                    .done(function (data) {
                        if (typeof data != 'undefined') {
                            try {
                                var time_series_data = convertTimeSeriesEnglishToMetric(data.value.timeSeries[0].values[0].value, "USGS");
                                var usgs_series = [{
                                    name: "USGS (" + m_selected_usgs_id + ")",
                                    x: time_series_data.dates,
                                    y: time_series_data.data,
                                    line: {
                                            color: 'brown',
                                            dash: 'dash'
                                    },
                                    type: 'scatter'
                                }];

                                $.when(ecmwf_deferred).done(function() {
                                    addSeriesToCharts(usgs_series);
                                });

                            } catch (e) {
                                if (e instanceof TypeError) {
                                    appendErrorMessage("Recent USGS data not found.", "usgs_error", "message-error");
                                }
                            }
                        }
                    })
                    .fail(function (request, status, error) {
                        appendErrorMessage("USGS Error: " + error, "usgs_error", "message-error");
                    })
                    .always(function () {
                        m_downloading_usgs = false;
                        if(isNotLoadingPastRequest()){
                           clearInfoMessages();
                        }
                    });
                }
            }
            //Get AHPS data if NWD ID attribute exists
            if(m_selected_nws_id != null) {

                m_downloading_nws = true;
                //get NWS data
                //Example URL: http://ua-fews.ua.edu/WaterMlService/waterml?
                //             request=GetObservation&featureId=ACRT2&observedProperty=QINE 
                //             &beginPosition=2015-01-01T00:00:00&endPosition=2015-06-22T00:00:00
                jQuery.ajax({
                    type: "GET",
                    url: "http://ua-fews.ua.edu/WaterMlService/waterml",
                    data: {
                        request: 'GetObservation',
                        observedProperty: 'QINE',
                        featureId: m_selected_nws_id,
                        beginPosition: dateToUTCDateTimeString(date_nws_start),
                        endPosition:  dateToUTCDateTimeString(date_nws_end), 
                    },
                })
                .done(function(data) {
                    //var series_data = getValidSeries(WATERML.get_json_from_streamflow_waterml(data, m_units));
                    var series_data = WATERML.get_json_from_streamflow_waterml(data, m_units, "T0 (Time of analysis)");
                    if(series_data == null) {
                        appendErrorMessage("No valid recent data found for AHPS (" + 
                                            m_selected_nws_id + ")", "ahps_error", "message-error");
                    } else {
                        var ahps_series = [{
                            name: "AHPS (" + m_selected_nws_id + ")",
                            x: series_data[0].dates,
                            y: series_data[0].data,
                            line: {
                                color: '#80cdc1', //light-turquiose
                                dash: 'dash'
                            },
                            type: 'scatter'
                        }];
                        $.when(ecmwf_deferred).done(function() {
                            addSeriesToCharts(ahps_series);
                        });
                    }
                })
                .fail(function(request, status, error) {
                    appendErrorMessage("AHPS Error: " + error, "ahps_error", "message-error");
                })
                .always(function() {
                    m_downloading_nws = false;
                    if(isNotLoadingPastRequest()){
                       clearInfoMessages();
                    }
                });
            }
            //Get HydroServer Data if Available
            if(m_selected_hydroserver_url != null) {
                m_downloading_hydroserver = true;
                //get WorldWater data
                jQuery.ajax({
                    type: "GET",
                    url: m_selected_hydroserver_url,
                    data: {
                        startDate: dateToUTCString(date_observed_start),
                        endDate:  dateToUTCString(date_observed_end), 
                    },
                })
                .done(function(data) {
                    var series_data = WATERML.get_json_from_streamflow_waterml(data, m_units);
                    if(series_data == null) {
                        appendErrorMessage("No data found for WorldWater", "hydro_server_error", "message-error");
                    } else {
                        var hydro_server_series = [{
                            name: "HydroServer",
                            x: series_data[0].dates,
                            y: series_data[0].data,
                            line: {
                                color: 'purple',
                                dash: 'dash'
                            },
                            type: 'scatter'
                        }];
                        $.when(ecmwf_deferred).done(function() {
                            addSeriesToCharts(hydro_server_series);
                        });
                    }
                })
                .fail(function(request, status, error) {
                    appendErrorMessage(request.responseText, "hydro_server_error", "message-error");
                })
                .always(function() {
                    m_downloading_hydroserver = false;
                    if(isNotLoadingPastRequest()){
                       clearInfoMessages();
                    }
                });
            }


        }
    };

    //FUNCTION: displays hydrograph at stream segment
    displayHydrograph = function(from_units_toggle) {
        if ($("#long-term-chart .js-plotly-plot").length)
        {
            Plotly.purge($("#long-term-chart .js-plotly-plot")[0]);
        }

        $('#chart_modal').modal('show');
        //check if old ajax call still running
        if(!isNotLoadingPastRequest()) {
            //updateInfoAlert
            appendWarningMessage("Please wait for datasets to download before making another selection.", "wait_warning");

        } else if (!isThereDataToLoad()) {
            resetChartSelectMessage();
            //updateInfoAlert
            addWarningMessage("No data found to load. Please toggle on a dataset.");
        }
        else {
            resetChartSelectMessage();

            //Get chart data
            m_ecmwf_forecast_folder = "most_recent";
            getChartData(from_units_toggle);
            //Get available ECMWF Dates
            if (m_selected_ecmwf_watershed != null
                && m_selected_ecmwf_subbasin != null)
            {
                m_downloading_long_term_select = true;
                m_long_term_select_data_ajax_handle = jQuery.ajax({
                    type: "GET",
                    url: "ecmwf-get-avaialable-dates",
                    dataType: "json",
                    data: {
                        watershed_name: m_selected_ecmwf_watershed,
                        subbasin_name: m_selected_ecmwf_subbasin,
                        reach_id: m_selected_reach_id,
                    },
                })
                .done(function (data) {
                    if (!m_long_term_chart_data_ajax_load_failed) {
                        //remove select2 if exists
                        clearChartSelect2('long-term');
                        clearChartSelect2('download');

                        $('.long-term-select').removeClass('hidden');
                        //create new select2
                        $('#long-term-select').select2({
                            data: data.output_directories,
                            placeholder: "Select a Date"
                        });

                        $('#download-select').select2({
                            data: data.output_directories,
                            placeholder: "Select a Date"
                        });

                        if (m_downloading_ecmwf_hydrograph) {
                            $('.long-term-select').addClass('hidden');
                        }
                        //add on change event handler
                        $('#long-term-select').on('change.select2', function () {
                            m_ecmwf_forecast_folder = $(this).select2('data').id;
                            getChartData();
                        });
                                                //add on change event handler
                        $('#download-select').on('change.select2', function () {
                            updateDownloadForecastURL();
                        });
                    }
                })
                .fail(function (request, status, error) {
                    appendErrorMessage(request.responseText, "ecmwf_error", "message-error");
                    clearChartSelect2('long-term');
                    clearChartSelect2('download');
                })
                .always(function () {
                    m_downloading_long_term_select = false;
                    if(isNotLoadingPastRequest()){
                       clearInfoMessages();
                    }
                });
            }

        }
    };

    //FUNCTION: Loads Hydrograph from Selected feature
    loadHydrographFromFeature = function(selected_feature, from_units_toggle) {
        $('.intro_message').addClass('hidden');
        $('#app-content-wrapper #app-content').css('padding-bottom', 0);
        //check if old ajax call still running
        if(!isNotLoadingPastRequest()) {
            //updateInfoAlert
            appendWarningMessage("Please wait for datasets to download before making another selection.", "wait_warning");

        } else {
            //get attributes
            var reach_id = getCI(selected_feature, 'COMID'); 
            var ecmwf_watershed_name = getCI(selected_feature, "watershed");
            var ecmwf_subbasin_name = getCI(selected_feature, "subbasin");
            var usgs_id = getCI(selected_feature, "usgs_id");
            var nws_id = getCI(selected_feature, "nws_id");
            var hydroserver_url = getCI(selected_feature, "hydroserve");
            
            //check if the variables are under a different name
            if(reach_id == null || isNaN(reach_id)) {
                var reach_id = getCI(selected_feature, 'hydroid');
            }
    
            if(ecmwf_watershed_name == null) {
                var ecmwf_watershed_name = getCI(selected_feature, 'watershed_name');
            }
            if(ecmwf_subbasin_name == null) {
                var ecmwf_subbasin_name = getCI(selected_feature, 'subbasin_name');
            }
    
            //clean up usgs_id
            if(!isNaN(usgs_id) && usgs_id != null) {
                //add zero in case it was removed when converted to a number
                while(usgs_id.length < 8 && usgs_id.length > 0) {
                    usgs_id = '0' + usgs_id;
                }
            }

            if(reach_id != null &&  
               (ecmwf_watershed_name != null && 
                ecmwf_subbasin_name != null))
            {
                m_selected_feature = selected_feature;
                m_selected_reach_id = reach_id;
                m_selected_ecmwf_watershed = ecmwf_watershed_name;
                m_selected_ecmwf_subbasin = ecmwf_subbasin_name;
                m_selected_usgs_id = usgs_id;
                m_selected_nws_id = nws_id;
                m_selected_hydroserver_url = hydroserver_url;

                displayHydrograph(from_units_toggle);
            } else {
                appendErrorMessage('The attributes in the file are faulty. Please fix and upload again.',
                                    "file_attr_error",
                                    "message-error");
            }
        }
    };

    //FUNCTION: LOAD WARNING POINTS
    loadWarningPoints = function(watershed_layer_group, group_id, datetime_string) {
        $(group_id).parent().addClass('hidden');

        //get warning points for map
        var xhr = jQuery.ajax({
            type: "GET",
            url: 'get-warning-points',
            dataType: "json",
            data: {
                watershed_name: watershed_layer_group.get('ecmwf_watershed_name'),
                subbasin_name: watershed_layer_group.get('ecmwf_subbasin_name'),
                return_period: watershed_layer_group.get('return_period'),
                forecast_folder: datetime_string || "",
            },
        })
        var xhr2 = xhr.done(function (data) {
            var feature_array = (new ol.format.GeoJSON()).readFeatures(data, {featureProjection: 'EPSG:3857'});
            if (feature_array.length > 0) {
                $(group_id).parent().removeClass('hidden');
                var first_layer = null;
                var feature_dict = {};
                watershed_layer_group.getLayers().forEach(function(sublayer, j) {
                    var peak_date = stringToUTCDate(datetime_string);
                    peak_date.setUTCDate(peak_date.getUTCDate()+j);
                    sublayer.set('peak_date', peak_date);
                    sublayer.set('peak_date_str', dateToUTCString(peak_date));
                    feature_dict[dateToUTCString(peak_date)] = [];
                    if (first_layer == null) {
                        first_layer = sublayer;
                    }
                });

                for (var i = 0; i < feature_array.length; ++i) {
                    feature_dict[feature_array[i].getProperties().peak_date].push(feature_array[i]);
                }

                watershed_layer_group.getLayers().forEach(function(sublayer, j) {
                    sublayer.getSource().getSource().addFeatures(feature_dict[sublayer.get('peak_date_str')]);
                    sublayer.setVisible(true);
                });
                watershed_layer_group.set("daily_warnings", true);
                m_map.render();
            }
        })
        xhr.always(function() {
            m_map.render();
        });
        return xhr2;
    };

    //FUNCTION: updates the warning points for all layers
    updateWarningPoints = function(datetime_string) {
        $('#message_warning_points').removeClass('hidden');
        $('#warning_input_area').addClass('hidden');
        //STEP 1: REMOVE ALL OLD WARNINGS
        m_map.getLayers().forEach(function(watershed_layer, i){
            if (watershed_layer.get('layer_type') == "warning_points") {
                if (watershed_layer instanceof ol.layer.Group) {
                    var removed_old = false;
                    watershed_layer.getLayers().forEach(function(sublayer, j) {
                        if (sublayer instanceof ol.layer.Group) {
                            sublayer.getLayers().forEach(function(subsublayer, j) {
                                subsublayer.getSource().getSource().clear(); //remove previous elements
                            });
                        }
                        else if (!removed_old) {
                            watershed_layer.getLayers().forEach(function(sublayer, j) {
                                sublayer.getSource().getSource().clear(); //remove previous elements
                            });
                            removed_old = true;
                        }
                    });
                }
            }
        });

        //STEP 2: LOAD NEW WARNINGS
        var warning_xhr_list = [];
        m_map.getLayers().forEach(function(watershed_layer, i){
            if (watershed_layer.get('layer_type') == "warning_points") {
                if (watershed_layer instanceof ol.layer.Group) {
                    var group_id = '#'+watershed_layer.get('group_id');
                    var loaded = false;
                    watershed_layer.getLayers().forEach(function(sublayer, j) {
                        if (sublayer instanceof ol.layer.Group) {
                            warning_xhr_list.push(loadWarningPoints(sublayer, group_id, datetime_string));
                        }
                        else if (!loaded) {
                            warning_xhr_list.push(loadWarningPoints(watershed_layer, group_id, datetime_string));
                            loaded = true;
                        }
                    });
                }
            }
        });
        jQuery.when.apply(jQuery, warning_xhr_list).always(function() {
            updateWarningSlider(datetime_string);
            $('#message_warning_points').addClass('hidden');
            $('#warning_input_area').removeClass('hidden');
        });

    };

    //FUNCTION: updates the warning slider
    updateWarningSlider = function(datetime_string) {
        var date_array = [];
        for(var i=0; i<15; i++) {
            var peak_date = stringToUTCDate(datetime_string);
            peak_date.setUTCDate(peak_date.getUTCDate()+i);
            peak_date.setUTCHours(0,0,0,0);
            date_array.push(peak_date);
        }
        //set max to 15 days later (because it could have +12 hrs)
        var peak_date = stringToUTCDate(datetime_string);
        peak_date.setUTCDate(peak_date.getUTCDate()+15);
        date_array.push(peak_date);

        //update associated slider
        var dateSlider = document.getElementById('warning-date-slider-range');
        if (dateSlider != null) {
            var noui_data = dateSlider.noUiSlider;
            if(typeof noui_data != 'undefined') {
                noui_data.destroy();
            }
            noUiSlider.create(dateSlider, {
                range: {
                    'min': date_array[0].getTime(),
                    '7%':  date_array[1].getTime(),
                    '13%': date_array[2].getTime(),
                    '20%': date_array[3].getTime(),
                    '27%': date_array[4].getTime(),
                    '33%': date_array[5].getTime(),
                    '40%': date_array[6].getTime(),
                    '47%': date_array[7].getTime(),
                    '53%': date_array[8].getTime(),
                    '60%': date_array[9].getTime(),
                    '67%': date_array[10].getTime(),
                    '73%': date_array[11].getTime(),
                    '80%': date_array[12].getTime(),
                    '87%': date_array[13].getTime(),
                    '93%': date_array[14].getTime(),
                    'max': date_array[15].getTime()
                },
                step: 16,
                connect: true,
                snap: true,
                start: [date_array[0].getTime(), date_array[5].getTime()],
                format: wNumb({
                    decimals: 0
                })
            });
    
            var dateValues = [
            	document.getElementById('warning-start'),
            	document.getElementById('warning-end')
            ];
            
            dateSlider.noUiSlider.on('update', function( values, handle ) {
                dateValues[handle].innerHTML = dateToUTCString(new Date(+values[handle]));
                var warning_date_start = new Date();
                warning_date_start.setTime(+values[0]);
                var warning_date_end = new Date();
                warning_date_end.setTime(+values[1]);
                //parse through warning points
                m_map.getLayers().forEach(function(layer, i){
                    if (layer instanceof ol.layer.Group) {
                        if (layer.get('layer_type') == "warning_points") {
                            //filter out layers by date
                            layer.getLayers().forEach(function(sublayer, j) {
                                if (sublayer instanceof ol.layer.Group) {
                                    if (sublayer.get("daily_warnings")) {
                                        sublayer.getLayers().forEach(function(subsublayer, j) {
                                            var layer_date = subsublayer.get('peak_date');
                                            if(typeof layer_date != 'undefined') {
                                                subsublayer.setVisible(true);
                                                if (layer_date < warning_date_start || layer_date > warning_date_end) 
                                                {
                                                    subsublayer.setVisible(false);
                                                } 
                                            }
                                        });
                                    }
                                }
                                else if (layer.get("daily_warnings")) {
                                    var layer_date = sublayer.get('peak_date');
                                    if(typeof layer_date != 'undefined') {
                                        sublayer.setVisible(true);
                                        if (layer_date < warning_date_start || layer_date > warning_date_end) 
                                        {
                                            sublayer.setVisible(false);
                                        } 
                                    }
                                }
                            });
                        }
                    }
                });
                m_map.render();
            });
        }
    };

    //FUNCTION: Determines whether it is a layer or a group
    determineGeoServerLayerOrGroup = function(layer_array, divide_into_groups, 
                                              custom_group_id, custom_layer_type,
                                              visible) {
        if (layer_array.length > 1 && divide_into_groups) {
            return new ol.layer.Group({ 
                            layers: layer_array,
                            group_id: custom_group_id,
                            layer_type: custom_layer_type,
                            visible: visible,
                        });
        } else if (layer_array.length > 0 && divide_into_groups){
            layer_array[0].set("layer_id", custom_group_id);
            layer_array[0].setVisible(visible);
            return layer_array[0];
        } else if (layer_array.length > 0) {
            return layer_array[0];
        }
        return null;
    };

    //FUNCTION: Loads historical streamflow chart
    loadHistoricallStreamflowChart = function() {
        m_downloaded_historical_streamflow = true;
        $.ajax({
            url: 'get-historical-hydrograph',
            method: 'GET',
            data: {
                watershed_name: m_selected_ecmwf_watershed,
                subbasin_name: m_selected_ecmwf_subbasin,
                reach_id: m_selected_reach_id,
                units: m_units,
            },
        })
        .done(function(data) {
                $("#historical_streamflow_data").removeClass('alert alert-info');
                $("#historical_streamflow_data").html(data);
        })
        .fail(function (request, status, error) {
            addErrorMessage(request.responseText, "historical_streamflow_data");
        });
    };

    //FUNCTION: Loads flow duration curve chart
    loadFlowDurationChart = function() {
        m_downloaded_flow_duration = true;
        $.ajax({
            url: 'get-flow-duration-curve',
            method: 'GET',
            data: {
                watershed_name: m_selected_ecmwf_watershed,
                subbasin_name: m_selected_ecmwf_subbasin,
                reach_id: m_selected_reach_id,
                units: m_units,
            },
        })
        .done(function(data) {
                $("#flow_duration_data").removeClass('alert alert-info');
                $("#flow_duration_data").html(data);
        })
        .fail(function (request, status, error) {
            m_downloaded_flow_duration = false;
            addErrorMessage(request.responseText, "flow_duration_data");
        });
    };

    //FUNCTION: Loads daily seasonal streamflow chart
    loadDailySeasonalStreamflowChart = function() {
        m_downloaded_daily_streamflow = true;
        $.ajax({
            url: 'get-daily-seasonal-streamflow-chart',
            method: 'GET',
            data: {
                watershed_name: m_selected_ecmwf_watershed,
                subbasin_name: m_selected_ecmwf_subbasin,
                reach_id: m_selected_reach_id,
                units: m_units,
            },
        })
        .done(function(data) {
                $("#daily_streamflow_data").removeClass('alert alert-info');
                $("#daily_streamflow_data").html(data);
        })
        .fail(function (request, status, error) {
            m_downloaded_daily_streamflow = false;
            addErrorMessage(request.responseText, "daily_streamflow_data");
        });
    };

    //FUNCTION: Loads monthly seasonal streamflow chart
    loadMonthlySeasonalStreamflowChart = function() {
        m_downloaded_monthly_streamflow = true;
        $.ajax({
            url: 'get-monthly-seasonal-streamflow-chart',
            method: 'GET',
            data: {
                watershed_name: m_selected_ecmwf_watershed,
                subbasin_name: m_selected_ecmwf_subbasin,
                reach_id: m_selected_reach_id,
                units: m_units,
            },
        })
        .done(function(data) {
                $("#monthly_streamflow_data").removeClass('alert alert-info');
                $("#monthly_streamflow_data").html(data);
        })
        .fail(function (request, status, error) {
            m_downloaded_monthly_streamflow = false;
            addErrorMessage(request.responseText, "monthly_streamflow_data");
        });
    };

    /************************************************************************
    *                        DEFINE PUBLIC INTERFACE
    *************************************************************************/
    /*
     * Library object that contains public facing functions of the package.
     * This is the object that is returned by the library wrapper function.
     * See below.
     * NOTE: The functions in the public interface have access to the private
     * functions of the library because of JavaScript function scope.
     */
    public_interface = {
        zoomToAll: function() {
            zoomToAll();
        },
    };
    
    /************************************************************************
    *                  INITIALIZATION / CONSTRUCTOR
    *************************************************************************/
    
    // Initialization: jQuery function that gets called when 
    // the DOM tree finishes loading
    $(function() {
        //initialize map global variables
        m_map_projection = 'EPSG:3857';
        m_map_extent = ol.extent.createEmpty();
        m_selected_feature = null;
        m_selected_ecmwf_watershed = null;
        m_selected_ecmwf_subbasin = null;
        m_selected_reach_id = null;
        m_selected_usgs_id = null;
        m_selected_nws_id = null;
        m_selected_hydroserver_url = null;
        m_downloading_ecmwf_hydrograph = false;
        m_downloading_long_term_select = false;
        m_downloading_usgs = false;
        m_downloading_nws = false;
        m_downloading_hydroserver = false;
        m_downloaded_daily_streamflow = false;
        m_downloaded_monthly_streamflow = false;
        m_downloaded_flow_duration = false;
        m_downloaded_historical_streamflow = false;
        m_searching_for_reach = false;
        m_long_term_chart_data_ajax_load_failed = false;
        m_short_term_chart_data_ajax_load_failed = false;
        m_long_term_select_data_ajax_handle = null;
        m_ecmwf_forecast_folder = "most_recent";
        //Init from toggle
        m_units = "metric";
        if(!$('#units-toggle').bootstrapSwitch('state')) {
            m_units = "english";
        }

        //create symbols for warnings
        var twenty_symbols = [new ol.style.RegularShape({
                                              points: 3,
                                              radius: 9,
                                              fill: new ol.style.Fill({
                                                color: 'rgba(128,0,128,0.8)'
                                              }),
                                              stroke: new ol.style.Stroke({
                                                color: 'rgba(128,0,128,1)',
                                                width: 1
                                              }),
                                    }),new ol.style.RegularShape({
                                                              points: 3,
                                                              radius: 12,
                                                              fill: new ol.style.Fill({
                                                                color: 'rgba(128,0,128,0.3)'
                                                              }),
                                                              stroke: new ol.style.Stroke({
                                                                color: 'rgba(128,0,128,1)',
                                                                width: 1
                                                              }),
                                    })];

        //symbols
        var ten_symbols = [new ol.style.RegularShape({
                                              points: 3,
                                              radius: 9,
                                              fill: new ol.style.Fill({
                                                color: 'rgba(255,0,0,0.7)'
                                              }),
                                              stroke: new ol.style.Stroke({
                                                color: 'rgba(255,0,0,1)',
                                                width: 1
                                              }),
                        }),new ol.style.RegularShape({
                                                  points: 3,
                                                  radius: 12,
                                                  fill: new ol.style.Fill({
                                                    color: 'rgba(255,0,0,0.3)'
                                                  }),
                                                  stroke: new ol.style.Stroke({
                                                    color: 'rgba(255,0,0,1)',
                                                    width: 1
                                                  }),
                        })];

        //symbols
        var two_symbols = [new ol.style.RegularShape({
                                              points: 3,
                                              radius: 9,
                                              fill: new ol.style.Fill({
                                                color: 'rgba(255,255,0,0.7)'
                                              }),
                                              stroke: new ol.style.Stroke({
                                                color: 'rgba(255,255,0,1)',
                                                width: 1
                                              }),
                        }),new ol.style.RegularShape({
                                                  points: 3,
                                                  radius: 12,
                                                  fill: new ol.style.Fill({
                                                    color: 'rgba(255,255,0,0.3)'
                                                  }),
                                                  stroke: new ol.style.Stroke({
                                                    color: 'rgba(255,255,0,1)',
                                                    width: 1
                                                  }),
                        })];

        //load base layer
        var base_layer_info = JSON.parse($("#map").attr('base-layer-info'));
        var warning_point_forecast_folder = $("#map").attr('warning-point-start-folder');
        m_basemap_layer = getBaseLayer(base_layer_info.name);
        
        //load drainage line layers
        var watershed_layers_info_array = JSON.parse($("#map").attr('watershed-layers-info-array'));
        var watershed_group_info_array = JSON.parse($("#map").attr('watershed-group-info-array'));

        var all_watershed_layers = [];
        m_drainage_line_layers = [];
        m_predicted_flood_maps = [];

        var watershed_group_iteration_array = [];
        var divide_into_groups = false;
        if (watershed_group_info_array.length > 0) {
            watershed_group_iteration_array = watershed_group_info_array;
            divide_into_groups = true;
        } else {
            watershed_group_iteration_array = [{
                                                'group_id' : -1,
                                                'group_name' : "ALL",
                                                'watershed_layers_info' : watershed_layers_info_array,
                                               }]
        }

        watershed_group_iteration_array.forEach(function(watershed_group_info, group_iteration_index) {

            var group_drainage_line_layers = [];
            var group_boundary_layers = [];
            var group_gage_layers = [];
            var group_historical_flood_map_layers = [];
            var group_ahps_station_layers = [];
            var group_return_20_layers = [];
            var group_return_10_layers = [];
            var group_return_2_layers = [];
            
            //add watershed layers
            watershed_group_info.watershed_layers_info.forEach(function(watershed_layers_info) {
                //add boundary if exists
                if('boundary' in watershed_layers_info) {
                    var boundary_layer_id = 'layer-' + watershed_layers_info.id + '-boundary';
                    if ("error" in watershed_layers_info.boundary) {
                        appendErrorMessage("Boundary Layer: " + watershed_layers_info.title + 
                                            ": " + watershed_layers_info.boundary.error, 
                                           "error_" + boundary_layer_id, "message-error");
                    } else {
                        var boundary_layer = getTileLayer(watershed_layers_info.boundary, 
                                                          watershed_layers_info.geoserver_url, 
                                                          boundary_layer_id,
                                                          true, 
                                                          0.5);
                        boundary_layer.setMinResolution(300);
                        if (boundary_layer != null) {
                            if (divide_into_groups) {
                                group_boundary_layers.push(boundary_layer);
                            } else {
                                all_watershed_layers.push(boundary_layer);
                            }
                            
                        } else {
                            appendErrorMessage("Boundary Layer Invalid ... ", 
                                               "error_" + boundary_layer_id, "message-error");
                        }
                    }
                }
                //add gage if exists
                if('gage' in watershed_layers_info) {
                    var gage_layer_id = 'layer-' + watershed_layers_info.id + '-gage';
                    if ("error" in watershed_layers_info.gage) {
                        appendErrorMessage("Gage Layer: " + watershed_layers_info.title + 
                                           ": " + watershed_layers_info.gage.error, 
                                           'error_' + gage_layer_id, "message-error");
                    } else {
                        var gage_layer = getTileLayer(watershed_layers_info.gage, 
                                                      watershed_layers_info.geoserver_url, 
                                                      gage_layer_id, 
                                                      divide_into_groups, 
                                                      0.5);
                        if (gage_layer != null) {
                            if (divide_into_groups) {
                                group_gage_layers.push(gage_layer);
                            } else {
                                all_watershed_layers.push(gage_layer);
                            }
                        } else {
                            appendErrorMessage("Gage Layer Invalid ... ", 
                                               "error_" + gage_layer_id, "message-error");
                        }
                    }
                }
                //add historical flood map if exists
                if('historical_flood_map' in watershed_layers_info) {
                    var historical_flood_map_layer_id = 'layer-' + watershed_layers_info.id + '-historical_flood_map';
                    if ("error" in watershed_layers_info.historical_flood_map) {
                        appendErrorMessage("Historical Flood Map Layer: " + watershed_layers_info.title + 
                                           ": " + watershed_layers_info.historical_flood_map.error, 
                                           'error_' + historical_flood_map_layer_id, "message-error");
                    } else {
                        var historical_flood_map_layer = getTileLayer(watershed_layers_info.historical_flood_map, 
                                                                      watershed_layers_info.geoserver_url, 
                                                                      historical_flood_map_layer_id, 
                                                                      divide_into_groups, 
                                                                      0.5);

                        historical_flood_map_layer.setMaxResolution(300);
                        if (historical_flood_map_layer != null) {
                            if (divide_into_groups) {
                                group_historical_flood_map_layers.push(historical_flood_map_layer);
                            } else {
                                all_watershed_layers.push(historical_flood_map_layer);
                            }
                        } else {
                            appendErrorMessage("Historical Flood Map Layer Invalid ... ", 
                                               "error_" + historical_flood_map_layer_id, "message-error");
                        }
                    }
                }
                //add flood maps if they exist
                if('predicted_flood_maps' in watershed_layers_info) {
                    var predicted_flood_maps = [];
                    if ('geoserver_info_list' in watershed_layers_info.predicted_flood_maps) {
                        var flood_map_dataset_id = 'layer-' + watershed_layers_info.id + '-predicted_flood_maps';
                        watershed_layers_info.predicted_flood_maps.geoserver_info_list.forEach(function(flood_map_info, flood_map_index){
                            var flood_map_sublayer_id = flood_map_dataset_id + "f" + flood_map_index;
                            if ("error" in flood_map_info) {
                                
                                appendErrorMessage("Predicted Flood Map Layer: " + watershed_layers_info.title + 
                                                    " " + flood_map_info.forecast_directory +
                                                   ": " + flood_map_info.error, 
                                                   'error_' +flood_map_sublayer_id , "message-error");
                                
                            } else {
                                var layer = getTileLayer(flood_map_info, 
                                                         watershed_layers_info.geoserver_url, 
                                                         flood_map_dataset_id,
                                                         divide_into_groups, 
                                                         0.5);
                                if (layer != null) {
                                    layer.set('watershed_name', watershed_layers_info.watershed);
                                    layer.set('subbasin_name', watershed_layers_info.subbasin);
                                    layer.set('date_timestep', flood_map_info.forecast_directory);
                                    layer.set("flood_map_sublayer_id", flood_map_sublayer_id);
                                    layer.setMaxResolution(300);
                                    predicted_flood_maps.push(layer);
                                }
                                else {
                                    console.log("Invalid Predicted Floodmap Layer: ");
                                    //console.log(flood_map_info);
                                }
                                
                            }
                        });
                        if (predicted_flood_maps.length > 0) {
                            m_predicted_flood_maps.push(new ol.layer.Group({ 
                                layers: predicted_flood_maps,
                            }));
                        }
                    }
                }
                //add ahps station if exists
                if('ahps_station' in watershed_layers_info) {
                    var ahps_station_layer_id = 'layer-' + watershed_layers_info.id + '-ahps_station';
                    if ("error" in watershed_layers_info.ahps_station) {
                        appendErrorMessage("AHPS Station Layer: " + watershed_layers_info.title + 
                                           ": " + watershed_layers_info.ahps_station.error, 
                                           'error_' + ahps_station_layer_id, "message-error")
                    } else {
    
                        var ahps_station_vector_source = new ol.source.Vector({
                            format: new ol.format.GeoJSON(),
                            url: function(extent, resolution, projection) {
                            return watershed_layers_info.ahps_station.geojson + 
                                   '&PROPERTYNAME=the_geom' +
                                   '&srsname=' + m_map_projection;
                            },
                            strategy: ol.loadingstrategy.tile(ol.tilegrid.createXYZ({
                                maxZoom: 19
                            }))
                        });
                            
                        var ahps_station = new ol.layer.Vector({
                            source: ahps_station_vector_source,
                            style: new ol.style.Style({
                                    image: new ol.style.RegularShape({
                                      points: 5,
                                      radius: 7,
                                      stroke: new ol.style.Stroke({
                                        color: 'rgba(0,255,0,0.3)'
                                      }),
                                      fill: new ol.style.Fill({
                                        color: 'rgba(0,128,0,0.5)'
                                      })
                                    }),
                            }),
                            visible: divide_into_groups, 
                        });
                        ahps_station.set('geoserver_url', watershed_layers_info.ahps_station.geojson)
                        ahps_station.set('watershed_name', watershed_layers_info.watershed);
                        ahps_station.set('subbasin_name', watershed_layers_info.subbasin);
                        ahps_station.set('extent', ol.proj.transformExtent(watershed_layers_info.ahps_station.latlon_bbox.map(Number), 
                                                                'EPSG:4326',
                                                                m_map_projection));
                        ahps_station.set('layer_id', ahps_station_layer_id);
                        ahps_station.set('layer_type', 'geoserver');
                        if (divide_into_groups) {
                            group_ahps_station_layers.push(ahps_station);
                        } else {
                            all_watershed_layers.push(ahps_station);
                        }
    
                    }
                }
                //add drainage line if exists
                if('drainage_line' in watershed_layers_info) {
                    var drainage_line = getDrainageLineLayer(watershed_layers_info);
                    if (drainage_line != null) {
                        m_drainage_line_layers.push(drainage_line);
                        if (divide_into_groups) {
                            group_drainage_line_layers.push(drainage_line);
                        } else {
                            all_watershed_layers.push(drainage_line);
                        }
                    }
                } 
                //create empty layers to add data to later
                var return_20_layer = getWarningPointsLayerGroup('rgba(128,0,128,0.7)', 
                                                                 twenty_symbols, 
                                                                 20, 
                                                                 'layer-' + watershed_layers_info.id + '-20_year_warnings', 
                                                                  watershed_layers_info.ecmwf_watershed,
                                                                  watershed_layers_info.ecmwf_subbasin);

        
                var return_10_layer = getWarningPointsLayerGroup('rgba(255,0,0,0.6)', 
                                                                ten_symbols, 
                                                                10, 
                                                                'layer-' + watershed_layers_info.id + '-10_year_warnings', 
                                                                 watershed_layers_info.ecmwf_watershed,
                                                                 watershed_layers_info.ecmwf_subbasin);
        
                var return_2_layer = getWarningPointsLayerGroup('rgba(255,255,0,0.3)', 
                                                               two_symbols, 
                                                               2, 
                                                               'layer-' + watershed_layers_info.id + '-2_year_warnings', 
                                                               watershed_layers_info.ecmwf_watershed,
                                                               watershed_layers_info.ecmwf_subbasin);
    
                if (divide_into_groups) {
                    group_return_2_layers.push(return_2_layer);
                    group_return_10_layers.push(return_10_layer);
                    group_return_20_layers.push(return_20_layer);
                } else {
                    all_watershed_layers.push(return_2_layer);
                    all_watershed_layers.push(return_10_layer);
                    all_watershed_layers.push(return_20_layer);
                }
    
            });

            if(divide_into_groups) {
                var drainage_line_layer = determineGeoServerLayerOrGroup(group_drainage_line_layers, divide_into_groups, 
                                                                         "watershed_group-" + watershed_group_info.group_id + "-drainage_line_layer", 
                                                                         "geoserver",
                                                                         true);
                if (drainage_line_layer != null) {
                    all_watershed_layers.push(drainage_line_layer);
                }
    
                var boundary_layer = determineGeoServerLayerOrGroup(group_boundary_layers, 
                                                                    divide_into_groups, 
                                                                    "watershed_group-" + watershed_group_info.group_id + "-boundary_layer", 
                                                                    "geoserver",
                                                                    true);
                if (boundary_layer != null) {
                    all_watershed_layers.push(boundary_layer);
                }
    
                var gage_layer = determineGeoServerLayerOrGroup(group_gage_layers, 
                                                                divide_into_groups, 
                                                                "watershed_group-" + watershed_group_info.group_id + "-gage_layer", 
                                                                "geoserver",
                                                                false);
                if (gage_layer != null) {
                    all_watershed_layers.push(gage_layer);
                }

                var historical_flood_map_layer = determineGeoServerLayerOrGroup(group_historical_flood_map_layers, 
                                                                                divide_into_groups, 
                                                                                "watershed_group-" + watershed_group_info.group_id + "-historical_flood_map_layer", 
                                                                                "geoserver",
                                                                                false);
                if (historical_flood_map_layer != null) {
                    all_watershed_layers.push(historical_flood_map_layer);
                }
    
                var ahps_station_layer = determineGeoServerLayerOrGroup(group_ahps_station_layers, 
                                                                        divide_into_groups, 
                                                                        "watershed_group-" + watershed_group_info.group_id + "-ahps_station_layer", 
                                                                        "geoserver",
                                                                        false);
                if (ahps_station_layer != null) {
                    all_watershed_layers.push(ahps_station_layer);
                }
    
                var warnings_2_year = determineGeoServerLayerOrGroup(group_return_2_layers,
                                                                     divide_into_groups,
                                                                     "watershed_group-" + watershed_group_info.group_id + "-2_year_warnings",
                                                                     "warning_points",
                                                                     true);
                if (warnings_2_year != null) {
                    all_watershed_layers.push(warnings_2_year);
                }

                var warnings_10_year = determineGeoServerLayerOrGroup(group_return_10_layers, 
                                                                      divide_into_groups, 
                                                                      "watershed_group-" + watershed_group_info.group_id + "-10_year_warnings", 
                                                                      "warning_points",
                                                                      true);
                if (warnings_10_year != null) {
                    all_watershed_layers.push(warnings_10_year);
                }
    
                var warnings_20_year = determineGeoServerLayerOrGroup(group_return_20_layers,
                                                                      divide_into_groups,
                                                                      "watershed_group-" + watershed_group_info.group_id + "-20_year_warnings",
                                                                      "warning_points",
                                                                      true);
                if (warnings_20_year != null) {
                    all_watershed_layers.push(warnings_20_year);
                }
            }

        });


        //send message to user if Drainage Line file not found
        if (m_drainage_line_layers.length <= 0) {
            appendErrorMessage('No valid drainage line layers found. Please upload to begin.', "drainage_line_error", "message-error");
        }

        //make drainage line layers selectable
        m_select_interaction = new ol.interaction.Select({
                                    layers: m_drainage_line_layers,
                                    hitTolerance: 50,
                                });

        var all_map_layers = [m_basemap_layer].concat(all_watershed_layers);

        if(m_predicted_flood_maps.length > 0) {
            all_map_layers = all_map_layers.concat(m_predicted_flood_maps);
        }

        //create map
        m_map = new ol.Map({
            target: 'map',
            controls: ol.control.defaults().extend([
                new ol.control.FullScreen(),
                new ol.control.ZoomToExtent(),
                new ol.control.ScaleLine(),
                new ol.control.Control({element: document.getElementById('map-view-legend')}),
            ]),
            interactions: ol.interaction.defaults().extend([
                new ol.interaction.DragRotateAndZoom(),
                m_select_interaction,

            ]),
            layers : all_map_layers,
            view: new ol.View({
                center: [-33519607, 5616436],
                zoom: 8
            }),
        });

        var warning_xhr_list = []
        //wait for layers to load and then zoom to them
        all_watershed_layers.forEach(function(watershed_layer){
            var group_id = '#'+watershed_layer.get('group_id');
            var layer_id = '#'+watershed_layer.get('layer_id');
            if (watershed_layer instanceof ol.layer.Group) {
                if (watershed_layer.get('layer_type') == "warning_points") {
                    var loaded = false;
                    watershed_layer.getLayers().forEach(function(sublayer, j) {
                        if (sublayer instanceof ol.layer.Group) {
                            if (!loaded) {
                                bindInputs(group_id, watershed_layer);
                            }
                            warning_xhr_list.push(loadWarningPoints(sublayer, group_id, warning_point_forecast_folder));
                        }
                        else if (!loaded) {
                            loaded = true;
                            bindInputs(group_id, watershed_layer);
                            warning_xhr_list.push(loadWarningPoints(watershed_layer, group_id, warning_point_forecast_folder));
                        }
                    });
                } else {
                    bindInputs(group_id, watershed_layer);
                    var group_extent = ol.extent.createEmpty();
                    watershed_layer.getLayers().forEach(function(sublayer, j) {
                        if (sublayer.get('layer_type') == "geoserver") {
                            ol.extent.extend(group_extent, sublayer.get('extent'));
                        }
                    });
                    if (watershed_layer.get('layer_type') == "geoserver" &&
                        group_extent != ol.extent.createEmpty()) {
                        watershed_layer.set("extent", group_extent);
                        ol.extent.extend(m_map_extent, group_extent);
                        m_map.getView().fit(m_map_extent, m_map.getSize());
                    } 
                }
            
            } else if (watershed_layer.get('layer_type') == "geoserver") {
                bindInputs('#'+watershed_layer.get('layer_id'), watershed_layer);
                ol.extent.extend(m_map_extent, watershed_layer.get('extent'));
                m_map.getView().fit(m_map_extent, m_map.getSize());
            } 
        });

        //update slider
        jQuery.when.apply(jQuery, warning_xhr_list).always(function() {
            updateWarningSlider(warning_point_forecast_folder);
        });

        //bind flood maps
        m_predicted_flood_maps.forEach(function(layer_group, j) {
            layer_group.getLayers().forEach(function(layer, j) {
                if (j==0){
                    bindInputs('#'+layer.get('layer_id'), layer);
                }
            });
        });

        //when selected, call function to make hydrograph
        m_select_interaction.getFeatures().on('change:length', function(e) {
          if (e.target.getArray().length === 0) {
            // this means it's changed to no features selected
          } else {
            // this means there is at least 1 feature selected
            var selected_feature = e.target.item(0); // 1st feature in Collection
            loadHydrographFromFeature(selected_feature);

          }
        });

        //change displayed flood map on click
        $('.flood_map_select').off().change(function() {
            var watershed_name = $(this).parent().parent().parent().parent().attr('watershed');
            var subbasin_name = $(this).parent().parent().parent().parent().attr('subbasin');
            var date_timestep = $(this).val();

            m_predicted_flood_maps.forEach(function(layer_group, j) {
                layer_group.getLayers().forEach(function(layer, j) {
                    if (layer.get('watershed_name') == watershed_name && 
                        layer.get('subbasin_name') == subbasin_name) 
                    {
                        layer.setVisible(false);
                        unbindInputs('#'+layer.get('layer_id'));
                    }
                });
            });
            m_predicted_flood_maps.forEach(function(layer_group, j) {
                layer_group.getLayers().forEach(function(layer, j) {
                    if (layer.get('watershed_name') == watershed_name && 
                        layer.get('subbasin_name') == subbasin_name) 
                    {
                        if (layer.get('date_timestep') == date_timestep){
                            layer.setVisible(true);
                            bindInputs('#'+layer.get('layer_id'), layer);
                        }
                    }
                });
            });
        });
        
        //create function to zoom to layer
        $('.zoom-to-layer').off().click(function() {
            var layer_id = $(this).parent().parent().attr('id');
            zoomToLayer(layer_id);
        });

        //function to zoom to feature by id
        $('#submit-search-reach-id').off().click(function() {
            var watershed_info = $('#watershed_select').select2('val');
            var reach_id = $('#reach-id-input').val();
            zoomToFeature(watershed_info, reach_id);
        });

        //function to change warning points forecast date
        $('#warning_point_date_select').on('change.select2', function () {
            var forecast_folder = $(this).select2('data').id;
            updateWarningPoints(forecast_folder);
        });

        //zoom to all
        $('.ol-zoom-extent').off().click(function() {
            zoomToAll();
        });

        //show hide elements based on shape upload toggle selection
        $('#units-toggle').on('switchChange.bootstrapSwitch', function(event, state) {
            if(state) {
                //units metric
                m_units = "metric";
            } else {
                //units english
                m_units = "english";
            }
            if (m_selected_feature != null) {
                loadHydrographFromFeature(m_selected_feature, true);

                if (m_downloaded_historical_streamflow)
                {
                    loadHistoricallStreamflowChart();
                }
                if (m_downloaded_flow_duration)
                {
                    loadFlowDurationChart();
                }
                if (m_downloaded_daily_streamflow)
                {
                    loadDailySeasonalStreamflowChart();
                }
                if (m_downloaded_monthly_streamflow)
                {
                    loadMonthlySeasonalStreamflowChart();
                }
           }
            
        });

        $("#forecast_tab_link").click(function(){
            Plotly.Plots.resize($("#long-term-chart .js-plotly-plot")[0]);
        });

        $("#historical_tab_link").click(function(){
            if (!m_downloaded_historical_streamflow && isValidRiverSelected()) {
                addInfoMessage("Loading data ...", "historical_streamflow_data");
                loadHistoricallStreamflowChart();
            }
            else if (m_downloaded_historical_streamflow)
            {
                Plotly.Plots.resize($("#historical_streamflow_data .js-plotly-plot")[0]);
            }
        });

        $("#flow_duration_tab_link").click(function(){
            if (!m_downloaded_flow_duration && isValidRiverSelected()) {
                addInfoMessage("Loading data ...", "flow_duration_data");
                loadFlowDurationChart();
            }
            else if (m_downloaded_flow_duration)
            {
                Plotly.Plots.resize($("#flow_duration_data .js-plotly-plot")[0]);
            }
        });

        $("#daily_tab_link").click(function(){
            if (!m_downloaded_daily_streamflow && isValidRiverSelected()) {
                addInfoMessage("Loading data ...", "daily_streamflow_data");
                loadDailySeasonalStreamflowChart();
            }
            else if (m_downloaded_daily_streamflow)
            {
                Plotly.Plots.resize($("#daily_streamflow_data .js-plotly-plot")[0]);
            }
        });

        $("#monthly_tab_link").click(function(){
            if (!m_downloaded_monthly_streamflow && isValidRiverSelected()) {
                addInfoMessage("Loading data ...", "monthly_streamflow_data");
                loadMonthlySeasonalStreamflowChart();
            }
            else if (m_downloaded_monthly_streamflow)
            {
                Plotly.Plots.resize($("#monthly_streamflow_data .js-plotly-plot")[0]);
            }
        });

        //make sure active Plotly plots resize on window resize
        window.onresize = function() {
            $('#chart_modal .modal-body .tab-pane.active .js-plotly-plot').each(function(){
                Plotly.Plots.resize($(this)[0]);
            });
        };

        //make sure active Plotly plots resize on modal show
        $('#chart_modal').on('shown.bs.modal', function() {
            $('#chart_modal .modal-body .tab-pane.active .js-plotly-plot').each(function(){
                Plotly.Plots.resize($(this)[0]);
            });
        });

        //remove space at bottom when message dismissed
        $("#close_map_intro_message").click(function() {
            $('#app-content-wrapper #app-content').css('padding-bottom', 0);
        });

        //init tooltip
        $('.boot_tooltip').tooltip();


    });

    return public_interface;

}()); // End of package wrapper 
// NOTE: that the call operator (open-closed parenthesis) is used to invoke the library wrapper 
// function immediately after being parsed.
