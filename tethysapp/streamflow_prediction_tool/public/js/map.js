/*****************************************************************************
 * FILE:    map.js
 * AUTHOR:  Alan Snow
 * COPYRIGHT: © 2015 Alan D Snow. All rights reserved.
 * LICENSE: BSD 2-Clause
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
        m_selected_wrf_hydro_watershed,
        m_selected_wrf_hydro_subbasin,
        m_selected_reach_id,
        m_selected_usgs_id,
        m_selected_nws_id,
        m_selected_hydroserver_url,
        m_downloading_ecmwf_hydrograph,
        m_downloading_era_interim_hydrograph,
        m_downloading_long_term_select,
        m_downloading_short_term_select,
        m_downloading_wrf_hydro_hydrograph,
        m_downloading_usgs,
        m_downloading_nws,
        m_downloading_hydroserver,
        m_searching_for_reach,
        m_long_term_chart_data_ajax_load_failed,
        m_long_term_select_data_ajax_handle,
        m_short_term_chart_data_ajax_load_failed,
        m_short_term_select_data_ajax_handle,
        m_ecmwf_start_folder,
        m_wrf_hydro_date_string,
        m_units,
        m_ecmwf_show,
        m_wrf_show,
        m_return_20_features_source,
        m_return_10_features_source,
        m_return_2_features_source,
        m_flood_maps;



    /************************************************************************
     *                    PRIVATE FUNCTION DECLARATIONS
     *************************************************************************/
    var resizeAppContent, bindInputs, convertTimeSeriesMetricToEnglish, getCI,
        convertTimeSeriesEnglishToMetric, isNotLoadingPastRequest, zoomToAll,
        zoomToLayer, zoomToFeature, toTitleCase, datePadString, getBaseLayer,
        getTileLayer, clearAllMessages, clearInfoMessages,
        clearOldChart, dateToUTCString, clearChartSelect2, getChartData,
        displayHydrograph, loadHydrographFromFeature,resetChartSelectMessage,
        addECMWFSeriesToCharts, addSeriesToCharts, isThereDataToLoad, 
        checkCleanString, dateToUTCDateTimeString, getValidSeries, 
        convertValueMetricToEnglish, unbindInputs;


    /************************************************************************
     *                    PRIVATE FUNCTION IMPLEMENTATIONS
     *************************************************************************/
     //FUNCTION: reset chart and select options
    resetChartSelectMessage = function() {
        //remove old chart reguardless
        clearOldChart('long-term');
        $('.short-term-select').addClass('hidden');
        $('.long-term-select').addClass('hidden');
        //clear messages
        clearAllMessages();
    };

    //FUNCTION: resize content based
    resizeAppContent = function() {
        var map_div = $('#inner-app-content').children().first();
        map_div.attr("style","height:" + parseInt($(document).height()*0.8) + "px");
        if (typeof m_map != 'undefined') {
            m_map.updateSize();
        }
        var document_width = $(document).width();

        if (document_width > 900) {
            $('#app-content-wrapper').addClass('show-nav');
        }

        var container = $('.container');
        container.removeClass('no-padding');

        var height_ratio = 0.97;
        if (document_width > 1500) {
            height_ratio = 0.57;
        }
        $('#wrf_toogle_col').removeClass('col-sm-2')
                            .removeClass('col-sm-3')
                            .removeClass('col-sm-4');

        if (document_width > 1900) {
            $('#wrf_toogle_col').addClass('col-sm-2');
        } else if (document_width > 1400){
            $('#wrf_toogle_col').addClass('col-sm-3');
        } else if (document_width > 900) {
            $('#wrf_toogle_col').addClass('col-sm-4');
        } else if (document_width > 700) {
            $('#wrf_toogle_col').addClass('col-sm-2');
        } else {
            $('#wrf_toogle_col').addClass('col-sm-3');
        }
        //resize highchart
        var long_term_chart = $("#long-term-chart").highcharts();
        if (typeof long_term_chart != 'undefined') {
            var width = $("#long-term-chart-row").width();
            long_term_chart.setSize(0.97*width,height_ratio*width);
        }
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

    //FUNCTION: check to see if there is data to redraw on chart
    isThereDataToLoad = function(){
        return ((m_ecmwf_show && m_selected_ecmwf_watershed != null && m_selected_ecmwf_subbasin != null)
               || (m_wrf_show && m_selected_wrf_hydro_watershed != null && m_selected_wrf_hydro_subbasin != null)
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


    //FUNCTION: convert units from metric to english
    convertTimeSeriesMetricToEnglish = function(time_series) {
        var new_time_series = [];
        var conversion_factor = 1;
        if(m_units=="english") {
            conversion_factor = 35.3146667;
        }
        time_series.map(function(data_row) {
            var new_data_array = [data_row[0]];
            for (var i = 1; i<data_row.length; i++) {
                new_data_array.push(parseFloat((data_row[i]*conversion_factor).toFixed(5)));
            }
            new_time_series.push(new_data_array);
        });
        return new_time_series;
    };

    //FUNCTION: convert units from english to metric
    convertTimeSeriesEnglishToMetric = function(time_series, series_name) {
        var new_time_series = [];
        var date_time_value, data_value;
        var conversion_factor = 1;
        try {
            if (m_units == "metric") {
                conversion_factor = 35.3146667;
            }
            time_series.map(function(data) {
               if (series_name=="USGS") {
                   data_value = data.value;
                   date_time_value = data.dateTime;
               } else {
                   date_time_value = data[0];
                   data_value = data[1];
               }
               new_time_series.push([Date.parse(date_time_value), 
                                        parseFloat(data_value)/conversion_factor]);
            });
        } catch (e) {
            if (e instanceof TypeError) {
                appendErrorMessage("Error loading " + series_name + " data.", "load_series_error", "message-error");
            }
        }
        return new_time_series;
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
    getCI = function(obj,prop){
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
            !m_downloading_usgs && !m_downloading_nws && !m_downloading_hydroserver &&
            !m_downloading_short_term_select && !m_downloading_wrf_hydro_hydrograph &&
            !m_downloading_era_interim_hydrograph;
    };

    //FUNCTION: zooms to all layers
    zoomToAll = function() {
        m_map.getView().fit(m_map_extent, m_map.getSize());
    };

    //FUNCTION: zooms to layer with id layer_id
    zoomToLayer = function(layer_id) {
        m_map.getLayers().forEach(function(layer, i) {
            if (layer instanceof ol.layer.Group) {
                layer.getLayers().forEach(function(sublayer, j) {
                    if(sublayer.get('layer_id') == layer_id) {
                        if (sublayer.get('layer_type') == "geoserver") {
                            m_map.getView().fit(sublayer.get('extent'), m_map.getSize());
                            return;
                        }
                    }
                });
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
                                  '&format_options=callback:searchFeatures' +
                                  '&CQL_FILTER='+ drainage_line_layer.get('reach_id_attr_name') +' =' + reach_id +
                                  '&srsname=' + m_map_projection;
                            jQuery.ajax({
                                url: encodeURI(url),
                                dataType: 'jsonp',
                                jsonpCallback: 'searchFeatures',
                            })
                            .done(function(response) {
                                if (response.totalFeatures > 0) {
                                    var features = drainage_line_layer.getSource().readFeatures(response);
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
    getBaseLayer = function(base_layer_name, api_key) {
        if(base_layer_name == "BingMaps") {
            return new ol.layer.Tile({
                        source: new ol.source.BingMaps({key: api_key, imagerySet: "AerialWithLabels"}),
                    });
        } 
        else if (base_layer_name == "Esri") {
            return new ol.layer.Tile({
              source: new ol.source.XYZ({
                attributions: [new ol.Attribution({
                  html: 'Tiles &copy; <a href="http://services.arcgisonline.com/ArcGIS/' +
                      'rest/services/World_Topo_Map/MapServer">ArcGIS</a>'
                })],
                url: 'http://server.arcgisonline.com/ArcGIS/rest/services/' +
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
    getTileLayer = function(layer_info, geoserver_url, layer_id, input_opacity) {
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
                visible: false,
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

    //FUNCTION: removes message and hides the div
    clearInfoMessages = function() {
        $('#message').addClass('hidden');
        $('#message').empty();
    };

    clearAllMessages = function() {
        clearInfoMessages();
        $('#message-error').addClass('hidden');
        $('#message-error').empty();
    }

    //FUNCTION: removes highchart
    clearOldChart = function(model_name) {
       //clear old chart
        var highcharts_attr = $('#' + model_name + '-chart').attr('data-highcharts-chart');
        // For some browsers, `attr` is undefined; for others,
        // `attr` is false.  Check for both.
        if (typeof highcharts_attr !== typeof undefined && highcharts_attr !== false) {
            $("#" + model_name +"-chart").highcharts().destroy();
            $('#' + model_name + '-chart').empty();
        }
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

    //FUNCTION: adds a series to both the chart
    addECMWFSeriesToCharts = function(series_name, series_data, series_color, series_type){
        var long_term_chart = $("#long-term-chart").highcharts();
        var new_series = {
                            name: series_name,
                            data: convertTimeSeriesMetricToEnglish(series_data),
                            color: series_color,
                            selected: true
                         };
        if(typeof series_type != 'undefined' && new_series != null) {
            new_series.type = series_type;
            new_series.lineWidth = 0;
            new_series.linkedTo = ":previous";
            new_series.fillOpacity = 0.3;
        }
        long_term_chart.addSeries(new_series);
    };

    //FUNCTION: adds data to the chart
    addSeriesToCharts = function(series){
        var long_term_chart = $("#long-term-chart").highcharts();
        long_term_chart.addSeries(series);
        $("#long-term-chart").removeClass("hidden");
    };


    //FUNCTION: gets all data for chart
    getChartData = function() {
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
            //turn off select interaction
            m_map.removeInteraction(m_select_interaction);
            addInfoMessage("Retrieving Data ...");
            var y_axis_title = "Flow (cms)";
            if (m_units == "english") {
                y_axis_title = "Flow (cfs)";
            }
            var default_chart_settings = {

                title: { text: "Forecast"},
                chart: {
                    zoomType: 'x',
                },
                rangeSelector: {
                    selected: 0
                },
                plotOptions: {
                    series: {
                        marker: {
                            enabled: false
                        }
                    }
                },
                xAxis: {
                    type: 'datetime',
                    ordinal: false,
                    title: {
                        text: 'Date (UTC)'
                    },
                    minRange: 1 * 24 * 3600000 // one day
                },
                yAxis: {
                    title: {
                        text: y_axis_title
                    },
                    min: 0,
                    opposite: false
                },
            };
            //handle subtitles - ECMWF first priority
            var subtitle = null;
            if(m_selected_ecmwf_watershed != null && m_selected_ecmwf_subbasin != null) {
                subtitle = {text: toTitleCase(m_selected_ecmwf_watershed) + " (" +
                             toTitleCase(m_selected_ecmwf_subbasin) + "): " + m_selected_reach_id}
            } else if (m_selected_wrf_hydro_watershed != null && m_selected_wrf_hydro_subbasin != null) {
                subtitle = {text: toTitleCase(m_selected_wrf_hydro_watershed) + " (" +
                             toTitleCase(m_selected_wrf_hydro_subbasin) + "): " + m_selected_reach_id}
            }

            if (subtitle != null) {
                default_chart_settings.subtitle = subtitle;
            }

            $("#long-term-chart").highcharts('StockChart', default_chart_settings);

            //get ecmwf data
            if (m_ecmwf_show && m_selected_ecmwf_watershed != null &&
                m_selected_ecmwf_subbasin != null) {

                m_downloading_ecmwf_hydrograph = true;
                var xhr_ecmwf_hydrograph = jQuery.ajax({
                    type: "GET",
                    url: "ecmwf-get-hydrograph",
                    dataType: "json",
                    data: {
                        watershed_name: m_selected_ecmwf_watershed,
                        subbasin_name: m_selected_ecmwf_subbasin,
                        reach_id: m_selected_reach_id,
                        start_folder: m_ecmwf_start_folder,
                    },
                });
                xhr_ecmwf_hydrograph.done(function (data) {
                    if ("success" in data) {
                        if ("mean" in data) {
                            addECMWFSeriesToCharts("ECMWF", data.mean, 
                                                    Highcharts.getOptions().colors[2]);
                        }
                        if ("outer_range" in data) {
                            addECMWFSeriesToCharts("ECMWF - Outer Range",
                                                    data.outer_range, 
                                                    Highcharts.getOptions().colors[2], 
                                                    'arearange');
                        }
                        if ("std_dev_range" in data) {
                            addECMWFSeriesToCharts("ECMWF - Std. Dev.", 
                                                   data.std_dev_range, 
                                                   Highcharts.getOptions().colors[2], 
                                                   'arearange');
                        }
                        if ("high_res" in data) {
                            addECMWFSeriesToCharts("ECMWF - High Res.",
                                                   data.high_res,
                                                   Highcharts.getOptions().colors[1]);
                        }
                        $('.long-term-select').removeClass('hidden');
                        var long_term_chart = $("#long-term-chart").highcharts();
                        long_term_chart.rangeSelector.clickButton(0,0,true);
                        $('#long-term-chart').removeClass('hidden');
                    } else {
                        m_long_term_chart_data_ajax_load_failed = true;
                        appendErrorMessage(data["error"], "ecmwf_error", "message-error");
                        clearChartSelect2('long-term');
                    }
                })
                .fail(function (request, status, error) {
                        m_long_term_chart_data_ajax_load_failed = true;
                        appendErrorMessage("Error: " + error, "ecmwf_error", "message-error");
                        clearChartSelect2('long-term');
                })
                .always(function () {
                    m_downloading_ecmwf_hydrograph = false;
                    m_map.addInteraction(m_select_interaction);
                    if(isNotLoadingPastRequest()){
                        clearInfoMessages();
                    }
                });

                m_downloading_era_interim_hydrograph = true;
                jQuery.ajax({
                    type: "GET",
                    url: "era-interim-get-hydrograph",
                    dataType: "json",
                    data: {
                        watershed_name: m_selected_ecmwf_watershed,
                        subbasin_name: m_selected_ecmwf_subbasin,
                        reach_id: m_selected_reach_id,
                    },
                })
                .done(function (data) {
                        if ("success" in data) {
                            var long_term_chart = $("#long-term-chart").highcharts();
                            //load interim data to chart
                            xhr_ecmwf_hydrograph.always(function(){
                                if ("era_interim" in data) {
                                    if (!("error" in data.era_interim)) {
                                        var era_interim_series = {
                                            name: "ERA Interim",
                                            data: convertTimeSeriesMetricToEnglish(data.era_interim.series),
                                            dashStyle: 'longdash',
                                            color: Highcharts.getOptions().colors[10],
                                        };
                                        long_term_chart.addSeries(era_interim_series);
                                    } else {
                                        appendErrorMessage("Error: " + data.era_interim.error, "era_interim_error", "message-error");
                                    }
                                }
                                //load return peeriod data to chart
                                if ("return_period" in data) {
                                    if (!("error" in data.return_period)) {
        
                                        var extremes = long_term_chart.yAxis[0].getExtremes();
                                        var maxY = Math.max(extremes.max, convertValueMetricToEnglish(parseFloat(data.return_period.max)));
                                        long_term_chart.yAxis[0].addPlotBand({
                                            from: convertValueMetricToEnglish(parseFloat(data.return_period.twenty)),
                                            to: convertValueMetricToEnglish(maxY),
                                            color: 'rgba(128,0,128,0.4)',
                                            id: '20-yr',
                                            label: {
                                                text: '20-yr',
                                                align: 'right',
                                            }
                                        });
                                        long_term_chart.yAxis[0].addPlotBand({
                                            from: convertValueMetricToEnglish(parseFloat(data.return_period.ten)),
                                            to: convertValueMetricToEnglish(parseFloat(data.return_period.twenty)),
                                            color: 'rgba(255,0,0,0.3)',
                                            id: '10-yr',
                                            label: {
                                                text: '10-yr',
                                                align: 'right',
                                            }
                                        });
                                        long_term_chart.yAxis[0].addPlotBand({
                                            from: convertValueMetricToEnglish(parseFloat(data.return_period.two)),
                                            to: convertValueMetricToEnglish(parseFloat(data.return_period.ten)),
                                            color: 'rgba(255,255,0,0.3)',
                                            id: '2-yr',
                                            label: {
                                                text: '2-yr',
                                                align: 'right',
                                            }
                                        });
                                    } else {
                                        appendErrorMessage("Error: " + data.return_period.error, "era_interim_error", "message-error");
                                    }  
                                }
                                //if ERA Interim series present, show chart
                                if ("era_interim" in data) {
                                    if (!("error" in data.era_interim)) {
                                        $('#long-term-chart').removeClass('hidden');
                                    }
                                }
                            });
                        } else {
                            appendErrorMessage("Error: " + data.error, "era_interim_error", "message-error");
                        }
                })
                .fail(function (request, status, error) {
                    appendErrorMessage("Error: " + error, "era_interim_error", "message-error");
                })
                .always(function () {
                    m_downloading_era_interim_hydrograph = false;
                    m_map.addInteraction(m_select_interaction);
                    if(isNotLoadingPastRequest()){
                        clearInfoMessages();
                    }
                });

            }
            //if there is a wrf watershed & subbasin attribute
            if (m_wrf_show && m_selected_wrf_hydro_watershed != null 
                && m_selected_wrf_hydro_subbasin != null) {

                m_downloading_wrf_hydro_hydrograph = true;
                jQuery.ajax({
                    type: "GET",
                    url: "wrf-hydro-get-hydrograph",
                    dataType: "json",
                    data: {
                        watershed_name: m_selected_wrf_hydro_watershed,
                        subbasin_name: m_selected_wrf_hydro_subbasin,
                        reach_id: m_selected_reach_id,
                        date_string: m_wrf_hydro_date_string,
                    },
                })
                .done(function (data) {
                        if ("success" in data) {
                            //wrf_hydro
                            if ("wrf_hydro" in data) {
                                var wrf_series = {
                                    name: "WRF-Hydro (HRRR)",
                                    data: convertTimeSeriesMetricToEnglish(data.wrf_hydro),
                                    dashStyle: 'longdash',
                                    color: Highcharts.getOptions().colors[3]
                                };
                                var long_term_chart = $("#long-term-chart").highcharts();
                                long_term_chart.addSeries(wrf_series);
                                $('.short-term-select').removeClass('hidden');
                                $('#long-term-chart').removeClass('hidden');
                            }
                        } else {
                            m_short_term_chart_data_ajax_load_failed = true;
                            appendErrorMessage("Error: " + data["error"], "wrf_hydro_error", "message-error");
                            clearChartSelect2('short-term');
                        }
                })
                .fail(function (request, status, error) {
                        m_short_term_chart_data_ajax_load_failed = true;
                        appendErrorMessage("Error: " + error, "wrf_hydro_error", "message-error");
                        clearChartSelect2('short-term');
                })
                .always(function () {
                    m_downloading_wrf_hydro_hydrograph = false;
                    m_map.addInteraction(m_select_interaction);
                    if(isNotLoadingPastRequest()){
                        clearInfoMessages();
                    }
                });
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
            var get_ecmwf = m_ecmwf_start_folder != null && typeof m_ecmwf_start_folder != "undefined" &&
                m_ecmwf_start_folder != "most_recent" && m_ecmwf_show;
            //get ECMWF forcast dates if available
            if(get_ecmwf) {
                var ecmwf_forecast_start_year = parseInt(m_ecmwf_start_folder.substring(0,4));
                var ecmwf_forecast_start_month = parseInt(m_ecmwf_start_folder.substring(4,6));
                var ecmwf_forecast_start_day = parseInt(m_ecmwf_start_folder.substring(6,8));
                var ecmwf_forecast_start_hour = parseInt(m_ecmwf_start_folder.split(".")[1].substring(0,2));
                ecmwf_date_forecast_begin = new Date(Date.UTC(ecmwf_forecast_start_year, ecmwf_forecast_start_month-1,
                                                     ecmwf_forecast_start_day, ecmwf_forecast_start_hour));
                ecmwf_date_forecast_end = new Date();
                ecmwf_date_forecast_end.setUTCDate(ecmwf_date_forecast_begin.getUTCDate()+15);

                //reset dates if applicable
                date_observed_end = ecmwf_date_forecast_end;
                date_nws_end = ecmwf_date_forecast_end;
            }
            //WRF-Hydro Dates
            var wrf_hydro_date_forecast_begin = new Date(8640000000000000);
            var wrf_hydro_date_forecast_end = new Date(-8640000000000000);
            //get WRF-Hydro forcast dates if available
            if(m_wrf_hydro_date_string != null && typeof m_wrf_hydro_date_string != "undefined" &&
                m_wrf_hydro_date_string != "most_recent" && m_wrf_show) {
                var wrf_hydro_forecast_start_year = parseInt(m_wrf_hydro_date_string.substring(0,4));
                var wrf_hydro_forecast_start_month = parseInt(m_wrf_hydro_date_string.substring(4,6));
                var wrf_hydro_forecast_start_day = parseInt(m_wrf_hydro_date_string.substring(6,8));
                var wrf_hydro_forecast_start_hour = parseInt(m_wrf_hydro_date_string.split("T")[1].substring(0,2));
                wrf_hydro_date_forecast_begin = new Date(Date.UTC(wrf_hydro_forecast_start_year, wrf_hydro_forecast_start_month-1,
                                                         wrf_hydro_forecast_start_day, wrf_hydro_forecast_start_hour));
                wrf_hydro_date_forecast_end = new Date(wrf_hydro_date_forecast_begin.getTime()+15*60*60000);

                //reset dates if applicable
                if(get_ecmwf) {
                    date_observed_end = new Date(Math.max.apply(null,[date_observed_end, wrf_hydro_date_forecast_end]));
                    date_nws_end = new Date(Math.max.apply(null,[date_nws_end, wrf_hydro_date_forecast_end]));
                } else {
                    date_observed_end = wrf_hydro_date_forecast_end;
                    date_nws_end = wrf_hydro_date_forecast_end;
                }

            }

            var date_observed_start = new Date(Math.min.apply(null,[date_past, ecmwf_date_forecast_begin, wrf_hydro_date_forecast_begin]));
            var date_nws_start = new Date(Math.min.apply(null,[date_now, ecmwf_date_forecast_begin, wrf_hydro_date_forecast_begin]));

            

            //Get USGS data if USGS ID attribute exists
            if(!isNaN(m_selected_usgs_id) && m_selected_usgs_id != null) {
                if(m_selected_usgs_id.length >= 8) {
                    m_downloading_usgs = true;
                    //get USGS data
                    var chart_usgs_data_ajax_handle = jQuery.ajax({
                        type: "GET",
                        url: "http://waterservices.usgs.gov/nwis/iv/",
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
                                var usgs_series = {
                                    name: "USGS (" + m_selected_usgs_id + ")",
                                    data: convertTimeSeriesEnglishToMetric(data.value.timeSeries[0].values[0].value, "USGS"),
                                    dashStyle: 'longdash',
                                    color: Highcharts.getOptions().colors[0]
                                };
                                addSeriesToCharts(usgs_series);
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
                var chart_nws_data_ajax_handle = jQuery.ajax({
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
                        var ahps_series = {
                                        name: "AHPS (" + m_selected_nws_id + ")",
                                        data: series_data[0],
                                        dashStyle: 'longdash',
                                        color: Highcharts.getOptions().colors[4],
                        };
                    
                        addSeriesToCharts(ahps_series);
                        $('#long-term-chart').removeClass('hidden');
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
                var chart_ww_data_ajax_handle = jQuery.ajax({
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
                        var hydro_server_series = {
                                        name: "HydroServer",
                                        data: series_data[0],
                                        dashStyle: 'longdash',
                                        color: Highcharts.getOptions().colors[5],
                                    };
                        addSeriesToCharts(hydro_server_series);
                    }
                })
                .fail(function(request, status, error) {
                    appendErrorMessage("Error: " + error, "hydro_server_error", "message-error");
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
    displayHydrograph = function() {
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
            m_ecmwf_start_folder = "most_recent";
            m_wrf_hydro_date_string = "most_recent";
            getChartData();

            //Get available ECMWF Dates
            if (m_ecmwf_show && m_selected_ecmwf_watershed != null 
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
                    if ("success" in data && !m_long_term_chart_data_ajax_load_failed) {
                        //remove select2 if exists
                        clearChartSelect2('long-term');
                        $('.long-term-select').removeClass('hidden');
                        //create new select2
                        $('#long-term-select').select2({
                            data: data.output_directories,
                            placeholder: "Select a Date"
                        });
                        if (m_downloading_ecmwf_hydrograph && m_downloading_era_interim_hydrograph) {
                            $('.long-term-select').addClass('hidden');
                        }
                        //add on change event handler
                        $('#long-term-select').on('change.select2', function () {
                            m_ecmwf_start_folder = $(this).select2('data').id;
                            getChartData();
                        });
                    } else if ("error" in data) {
                        appendErrorMessage("Error: " + data.error, "ecmwf_error", "message-error");
                        clearChartSelect2('long-term');
                    }
                })
                .fail(function (request, status, error) {
                    appendErrorMessage("Error: " + error, "ecmwf_error", "message-error");
                    clearChartSelect2('long-term');
                })
                .always(function () {
                    m_downloading_long_term_select = false;
                    if(isNotLoadingPastRequest()){
                       clearInfoMessages();
                    }
                });
            }
            //Get available WRF-Hydro Dates
            if (m_wrf_show && m_selected_wrf_hydro_watershed != null 
                && m_selected_wrf_hydro_subbasin != null) {
                m_downloading_short_term_select = true;
                m_short_term_select_data_ajax_handle = jQuery.ajax({
                    type: "GET",
                    url: "wrf-hydro-get-avaialable-dates",
                    dataType: "json",
                    data: {
                        watershed_name: m_selected_wrf_hydro_watershed,
                        subbasin_name: m_selected_wrf_hydro_subbasin,
                    },
                })
                .done(function (data) {
                    if ("success" in data && !m_short_term_chart_data_ajax_load_failed) {
                        //remove select2 if exists
                        clearChartSelect2('short-term');
                        $('.short-term-select').removeClass('hidden');
                        //create new select2
                        $('#short-term-select').select2({
                            data: data.output_files,
                            placeholder: "Select a Date"
                        });
                        if (m_downloading_wrf_hydro_hydrograph) {
                            $('.short-term-select').addClass('hidden');
                        }
                        //add on change event handler
                        $('#short-term-select').on('change.select2', function () {
                            m_wrf_hydro_date_string = $(this).select2('data').id;
                            getChartData();
                        });
                    } else if ("error" in data) {
                        appendErrorMessage("Error: " + data.error, "wrf_hydro_error", "message-error");
                        clearChartSelect2('short-term');
                    }
                })
                .fail(function (request, status, error) {
                    appendErrorMessage("Error: " + error, "wrf_hydro_error", "message-error");
                    clearChartSelect2('short-term');
                })
                .always(function () {
                    m_downloading_short_term_select = false;
                    if(isNotLoadingPastRequest()){
                       clearInfoMessages();
                    }
                });
            }

        }
    };
    //FUNCTION: Loads Hydrograph from Selected feature
    loadHydrographFromFeature = function(selected_feature) {
        //check if old ajax call still running
        if(!isNotLoadingPastRequest()) {
            //updateInfoAlert
            appendWarningMessage("Please wait for datasets to download before making another selection.", "wait_warning");

        } else {
            //get attributes
            var reach_id = getCI(selected_feature, 'COMID'); 
            var ecmwf_watershed_name = getCI(selected_feature, "watershed");
            var ecmwf_subbasin_name = getCI(selected_feature, "subbasin");
            var wrf_hydro_watershed_name = getCI(selected_feature, "wwatershed");
            var wrf_hydro_subbasin_name = getCI(selected_feature, "wsubbasin");
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
                ecmwf_subbasin_name != null) ||
               (wrf_hydro_watershed_name != null &&
                wrf_hydro_subbasin_name != null))
            {
                m_selected_feature = selected_feature;
                m_selected_reach_id = reach_id;
                m_selected_ecmwf_watershed = ecmwf_watershed_name;
                m_selected_ecmwf_subbasin = ecmwf_subbasin_name;
                m_selected_wrf_hydro_watershed = wrf_hydro_watershed_name;
                m_selected_wrf_hydro_subbasin = wrf_hydro_subbasin_name;
                m_selected_usgs_id = usgs_id;
                m_selected_nws_id = nws_id;
                m_selected_hydroserver_url = hydroserver_url;

                displayHydrograph(); 
            } else {
                appendErrorMessage('The attributes in the file are faulty. Please fix and upload again.',
                                    "file_attr_error",
                                    "message-error");
            }
        }
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
        resizeAppContent();
        $('#map_top_navigation').find('.form-group').addClass('inline-block');
        //initialize map global variables
        m_map_projection = 'EPSG:3857';
        m_map_extent = ol.extent.createEmpty();
        m_selected_feature = null;
        m_selected_ecmwf_watershed = null;
        m_selected_ecmwf_subbasin = null;
        m_selected_wrf_hydro_watershed = null;
        m_selected_wrf_hydro_subbasin = null;
        m_selected_reach_id = null;
        m_selected_usgs_id = null;
        m_selected_nws_id = null;
        m_selected_hydroserver_url = null;
        m_downloading_ecmwf_hydrograph = false;
        m_downloading_era_interim_hydrograph = false;
        m_downloading_long_term_select = false;
        m_downloading_wrf_hydro_hydrograph = false;
        m_downloading_short_term_select = false;
        m_downloading_usgs = false;
        m_downloading_nws = false;
        m_downloading_hydroserver = false;
        m_searching_for_reach = false;
        m_long_term_chart_data_ajax_load_failed = false;
        m_short_term_chart_data_ajax_load_failed = false;
        m_long_term_select_data_ajax_handle = null;
        m_ecmwf_start_folder = "most_recent";
        m_wrf_hydro_date_string = "most_recent";
        //Init from toggle
        m_units = "metric";
        if(!$('#units-toggle').bootstrapSwitch('state')) {
            m_units = "english";
        }
        m_wrf_show = $('#wrf-toggle').bootstrapSwitch('state');
        m_ecmwf_show = $('#ecmwf-toggle').bootstrapSwitch('state');

        //create symbols for warnings
        var twenty_symbols = [new ol.style.RegularShape({
                                              points: 3,
                                              radius: 5,
                                              fill: new ol.style.Fill({
                                                color: 'rgba(128,0,128,0.8)'
                                              }),
                                              stroke: new ol.style.Stroke({
                                                color: 'rgba(128,0,128,1)',
                                                width: 1
                                              }),
                                    }),new ol.style.RegularShape({
                                                              points: 3,
                                                              radius: 9,
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
                                              radius: 5,
                                              fill: new ol.style.Fill({
                                                color: 'rgba(255,0,0,0.7)'
                                              }),
                                              stroke: new ol.style.Stroke({
                                                color: 'rgba(255,0,0,1)',
                                                width: 1
                                              }),
                        }),new ol.style.RegularShape({
                                                  points: 3,
                                                  radius: 9,
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
                                              radius: 5,
                                              fill: new ol.style.Fill({
                                                color: 'rgba(255,255,0,0.7)'
                                              }),
                                              stroke: new ol.style.Stroke({
                                                color: 'rgba(255,255,0,1)',
                                                width: 1
                                              }),
                        }),new ol.style.RegularShape({
                                                  points: 3,
                                                  radius: 9,
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
        
        m_basemap_layer = getBaseLayer(base_layer_info.name,base_layer_info.api_key);
        
        //load drainage line layers
        var layers_info = JSON.parse($("#map").attr('layers-info'));
        var all_group_layers = [];
        m_drainage_line_layers = [];
        m_flood_maps = [];
        //add each watershed group
        layers_info.forEach(function(layer_info, group_index) {
            var layers = [];
            //add catchment if exists
            if('catchment' in layer_info) {
                var catchment_layer_id = 'layer' + group_index + 'g' + 1
                if ("error" in layer_info.catchment) {
                    appendErrorMessage("Catchment Layer: " + layer_info.title + 
                                        ": " + layer_info.catchment.error, 
                                       "error_" + catchment_layer_id, "message-error");
                } else {
                    var layer = getTileLayer(layer_info['catchment'], layer_info['geoserver_url'], catchment_layer_id, 0.5);
                    if (layer != null) {
                        layers.push(layer);
                    } else {
                        appendErrorMessage("Catchment Layer Invalid ... ", 
                                           "error_" + catchment_layer_id, "message-error");
                    }
                }
            }
            //add gage if exists
            if('gage' in layer_info) {
                var gage_layer_id = 'layer' + group_index + 'g' + 2;
                if ("error" in layer_info.gage) {
                    appendErrorMessage("Gage Layer: " + layer_info.title + 
                                       ": " + layer_info.gage.error, 
                                       'error_' + gage_layer_id, "message-error");
                } else {
                    var layer = getTileLayer(layer_info['gage'], layer_info['geoserver_url'], gage_layer_id, 0.5);
                    if (layer != null) {
                        layers.push(layer);
                    } else {
                        appendErrorMessage("Gage Layer Invalid ... ", 
                                           "error_" + gage_layer_id, "message-error");
                    }
                }
            }
            //add flood maps if they exist
            if('flood_maps' in layer_info) {
                var flood_maps = [];
                if ('geoserver_info_list' in layer_info.flood_maps) {
                    var flood_map_dataset_id = 'layer' + group_index + 'g' + 7;
                    layer_info.flood_maps.geoserver_info_list.forEach(function(flood_map_info, flood_map_index){
                        var flood_map_sublayer_id = flood_map_dataset_id + "f" + flood_map_index;
                        if ("error" in flood_map_info) {
                            
                            appendErrorMessage("Flood Map Layer: " + layer_info.title + 
                                                " " + flood_map_info.forecast_directory +
                                               ": " + flood_map_info.error, 
                                               'error_' +flood_map_sublayer_id , "message-error");
                            
                        } else {
                            var layer = getTileLayer(flood_map_info, 
                                                     layer_info.geoserver_url, 
                                                     flood_map_dataset_id,
                                                     0.5);
                            if (layer != null) {
                                layer.set('watershed_name', layer_info.watershed);
                                layer.set('subbasin_name', layer_info.subbasin);
                                layer.set('date_timestep', flood_map_info.forecast_directory);
                                layer.set("flood_map_sublayer_id", flood_map_sublayer_id);
                                layer.setMaxResolution(1000);
                                flood_maps.push(layer);
                            }
                            else {
                                console.log("Invalid Floodmap Layer: ");
                                console.log(flood_map_info);
                            }
                            
                        }
                    });
                    if (flood_maps.length > 0) {
                        m_flood_maps.push(new ol.layer.Group({ 
                            layers: flood_maps,
                        }));
                    }
                }
            }
            //add ahps station if exists
            if('ahps_station' in layer_info) {
                var ahps_station_layer_id = 'layer' + group_index + 'g' + 3;
                if ("error" in layer_info.ahps_station) {
                    appendErrorMessage("AHPS Station Layer: " + layer_info.title + 
                                       ": " + layer_info.ahps_station.error, 
                                       'error_' + ahps_station_layer_id, "message-error")
                } else {

                    var ahps_station_vector_source = new ol.source.Vector({
                        format: new ol.format.GeoJSON(),
                        url: function(extent, resolution, projection) {
                        return layer_info.ahps_station.geojsonp + 
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
                        })
                    });
                    ahps_station.setVisibility(false);
                    ahps_station.set('geoserver_url', layer_info.ahps_station.geojsonp)
                    ahps_station.set('watershed_name', layer_info.watershed);
                    ahps_station.set('subbasin_name', layer_info.subbasin);
                    ahps_station.set('extent', ol.proj.transformExtent(layer_info.ahps_station.latlon_bbox.map(Number), 
                                                            'EPSG:4326',
                                                            m_map_projection));
                    ahps_station.set('layer_id', ahps_station_layer_id);
                    ahps_station.set('layer_type', 'geoserver');
                    layers.push(ahps_station);
                }
            }
            //add drainage line if exists
            if('drainage_line' in layer_info) {
                var drainage_line_layer_id = 'layer' + group_index + 'g' + 0;
                if ("error" in layer_info.drainage_line) {
                    appendErrorMessage("Drainage Line Layer: " + layer_info.title + 
                                       ": " + layer_info.drainage_line.error, 
                                       "error_" + drainage_line_layer_id, "message-error");
                } else {
                    //check if required parameters exist
                    if(layer_info['drainage_line']['missing_attributes'].length > 2) {
                        appendErrorMessage('The drainage line layer for ' +
                                          layer_info['watershed'] + '(' +
                                          layer_info['subbasin'] + ') ' +
                                          'is missing '+
                                          layer_info['drainage_line']['missing_attributes'].join(", ") +
                                          ' attributes and will not function properly.', "layer_loading_error", "message-error");
                    } 
                    var drainage_line;
                    //check layer capabilites
                    if(layer_info['drainage_line']['geoserver_method'] == "natur_flow_query") {
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
                                return layer_info.drainage_line.geojsonp + 
                                      '&PROPERTYNAME=the_geom,' +
                                       layer_info.drainage_line.contained_attributes.join(",") +
                                      '&CQL_FILTER=' + layer_info.drainage_line.geoserver_query_attribute +
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
                            maxResolution: 10000
                        });
                    } 
                    else if(layer_info['drainage_line']['geoserver_method'] == "river_order_query") {
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
                                return layer_info.drainage_line.geojsonp + 
                                      '&PROPERTYNAME=the_geom,' +
                                       layer_info.drainage_line.contained_attributes.join(",") +
                                      '&CQL_FILTER=' + layer_info.drainage_line.geoserver_query_attribute +
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
                            maxResolution: 10000
                        });
                    } 
                    else { //layer_info['drainage_line']['geoserver_method'] == "simple"
                        var drainage_line_vector_source = new ol.source.Vector({
                            format: new ol.format.GeoJSON(),
                            loader: function(extent, resolution, projection) {
                                this.geojsonp_url = layer_info['drainage_line']['geojsonp'];
                                this.callback = 'loadFeatures' + drainage_line_layer_id;
                                this.attributes = layer_info['drainage_line']['contained_attributes'].join(",");
                                return this.geojsonp_url + 
                                      '&PROPERTYNAME=the_geom,' +
                                       this.attributes +
                                      '&BBOX=' + extent.join(',') + 
                                      ','+ m_map_projection +
                                      '&srsname=' + m_map_projection;
                            },
                            strategy: ol.loadingstrategy.bbox,
                            projection: m_map_projection
                        });
                        drainage_line = new ol.layer.Vector({
                            source: drainage_line_vector_source,
                            maxResolution: 1000
                        });
                        
                    }

                    layer_info['drainage_line']['contained_attributes'].some(function(attribute) {
                        if (attribute.toLowerCase() == "comid" || attribute.toLowerCase() == "hydroid") {
                            drainage_line.set('reach_id_attr_name', attribute);
                            return true;
                        }
                    });

                    drainage_line.set('geoserver_url', layer_info['drainage_line']['geojsonp'])
                    drainage_line.set('watershed_name', layer_info['watershed']);
                    drainage_line.set('subbasin_name', layer_info['subbasin']);
                    drainage_line.set('extent', ol.proj.transformExtent(layer_info['drainage_line']['latlon_bbox'].map(Number), 
                                                            'EPSG:4326',
                                                            m_map_projection));
                    drainage_line.set('layer_id', drainage_line_layer_id);
                    drainage_line.set('layer_type', 'geoserver');
                    m_drainage_line_layers.push(drainage_line);
                    layers.push(drainage_line);
                }
            } 
            //create empty layers to add data to later
            var return_20_layer = new ol.layer.Vector({
                source: new ol.source.Cluster({
                                                source: new ol.source.Vector({ source: []}),
                                                distance: 20
                                             }),
                style: function(feature, resolution) {
                    var features = feature.get("features");
                    var size = -1
                    if (typeof features != 'undefined') {
                        size = features.length;
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
                                color: 'rgba(128,0,128,0.7)'
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
                                image: twenty_symbols[features[i].get('point_size')],
                              }));
                        }
                    }
                    return style;
                }
            });
            return_20_layer.set('layer_id', 'layer' + group_index + 'g' + 4);
            return_20_layer.set('layer_type', 'warning_points');
            return_20_layer.set('return_period', 20);
            return_20_layer.set('ecmwf_watershed_name', layer_info['ecmwf_watershed']);
            return_20_layer.set('ecmwf_subbasin_name', layer_info['ecmwf_subbasin']);
    
            var return_10_layer = new ol.layer.Vector({
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
                                color: 'rgba(255,0,0,0.6)'
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
                                image: ten_symbols[features[i].get('point_size')]
                              }));
                        }
                    }
                    return style;
                }
            });
           return_10_layer.set('layer_id', 'layer' + group_index + 'g' + 5);
           return_10_layer.set('layer_type', 'warning_points');
           return_10_layer.set('return_period', 10);
           return_10_layer.set('ecmwf_watershed_name', layer_info['ecmwf_watershed']);
           return_10_layer.set('ecmwf_subbasin_name', layer_info['ecmwf_subbasin']);
    
            var return_2_layer = new ol.layer.Vector({
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
                                color: 'rgba(255,255,0,0.6)'
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
                                image: two_symbols[features[i].get('point_size')]
                              }));
                        }
                    }
                    return style;
    
                }
            });
            return_2_layer.set('layer_id', 'layer' + group_index + 'g' + 6);
            return_2_layer.set('layer_type', 'warning_points');
            return_2_layer.set('return_period', 2);
            return_2_layer.set('ecmwf_watershed_name', layer_info['ecmwf_watershed']);
            return_2_layer.set('ecmwf_subbasin_name', layer_info['ecmwf_subbasin']);

            layers.push(return_2_layer);
            layers.push(return_10_layer);
            layers.push(return_20_layer);
            //make sure there are layers to add
            if (layers.length > 0) {
                var group_layer = new ol.layer.Group({ 
                        layers: layers,
                });
                all_group_layers.push(group_layer);
            }
        });


        //send message to user if Drainage Line file not found
        if (m_drainage_line_layers.length <= 0) {
            appendErrorMessage('No valid drainage line layers found. Please upload to begin.', "drainage_line_error", "message-error");
        }
        //make drainage line layers selectable
        m_select_interaction = new ol.interaction.Select({
                                    layers: m_drainage_line_layers,
                                });

        if(m_flood_maps.length > 0) {
            all_group_layers = all_group_layers.concat(m_flood_maps);
        }
        var all_map_layers = [m_basemap_layer].concat(all_group_layers);
        //var all_map_layers = all_group_layers;
        //create map
        m_map = new ol.Map({
            target: 'map',
            controls: ol.control.defaults().extend([
                new ol.control.FullScreen(),
                new ol.control.ZoomToExtent(),
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
        //wait for layers to load and then zoom to them
        all_group_layers.forEach(function(group_layer){
            if (group_layer instanceof ol.layer.Group) {
                group_layer.getLayers().forEach(function(vector_layer, j) {
                    if (vector_layer.get('layer_type') == "geoserver") {
                        bindInputs('#'+vector_layer.get('layer_id'), vector_layer);
                        ol.extent.extend(m_map_extent, vector_layer.get('extent'));
                        m_map.getView().fit(m_map_extent, m_map.getSize());
                    } else if (vector_layer.get('layer_type') == "warning_points") {
                        var layer_id = '#'+vector_layer.get('layer_id');
                        bindInputs(layer_id, vector_layer);
                        //get warning points for map
                        jQuery.ajax({
                            type: "GET",
                            url: 'get-warning-points',
                            dataType: "json",
                            data: {
                                watershed_name: vector_layer.get('ecmwf_watershed_name'),
                                subbasin_name: vector_layer.get('ecmwf_subbasin_name'),
                                return_period: vector_layer.get('return_period'),
                            },
                        })
                        .done(function (data) {
                            if ("success" in data) {
                                $(layer_id).parent().removeClass('hidden');
                                //symbols
                                var feature_count = data.warning_points.length
                                var features = [];
                                var feature, geometry, symbol;
                                for (var i = 0; i < feature_count; ++i) {
                                  geometry = new ol.geom.Point(ol.proj.transform([data.warning_points[i].lon, 
                                                                                 data.warning_points[i].lat], 
                                                                                'EPSG:4326', m_map_projection));
                                  feature = new ol.Feature({
                                                            geometry: geometry,
                                                            point_size: data.warning_points[i].size,
                                                            comid: data.warning_points[i].comid
                                                            });
                                  features.push(feature);
                                }
                                var vector_source = vector_layer.getSource().getSource();
                                vector_source.addFeatures(features);
                                m_map.render();
            
                            } else {
                                console.log(data.error);
                                //appendErrorMessage("Error: " + data["error"], "warning_points_error", "message-error");
                            }
                        })
                        .fail(function (request, status, error) {
                            console.log(error);
                            //appendErrorMessage("Error: " + error, "warning_points_error", "message-error");
                        });
                    }
                });
            }
        });

        //bind flood maps
        m_flood_maps.forEach(function(layer_group, j) {
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

            m_flood_maps.forEach(function(layer_group, j) {
                layer_group.getLayers().forEach(function(layer, j) {
                    if (layer.get('watershed_name') == watershed_name && 
                        layer.get('subbasin_name') == subbasin_name) 
                    {
                        layer.setVisible(false);
                        unbindInputs('#'+layer.get('layer_id'));
                    }
                });
            });
            m_flood_maps.forEach(function(layer_group, j) {
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
            var watershed_info = $(this).parent().parent().find('#watershed_select').select2('val');
            var reach_id = $(this).parent().parent().find('#reach-id-input').val();
            zoomToFeature(watershed_info, reach_id);
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
                loadHydrographFromFeature(m_selected_feature);
            }
            
        });

        //show/hide forecasts based on toggle
         $('#ecmwf-toggle').on('switchChange.bootstrapSwitch', function(event, state) {
             m_ecmwf_show = state;
             if (m_selected_feature != null && m_selected_ecmwf_watershed != null 
                 && m_selected_ecmwf_subbasin != null) {
                 loadHydrographFromFeature(m_selected_feature);
             }
        });

        $('#wrf-toggle').on('switchChange.bootstrapSwitch', function(event, state) {
            m_wrf_show = state;
            if (m_selected_feature != null && m_selected_wrf_hydro_watershed != null 
                && m_selected_wrf_hydro_subbasin != null) {
                loadHydrographFromFeature(m_selected_feature);
            }
        });

        //resize app content based on window size and nav bar
        $('.toggle-nav').off();

        $(window).resize(function() {
            resizeAppContent();
        });

    });

    return public_interface;

}()); // End of package wrapper 
// NOTE: that the call operator (open-closed parenthesis) is used to invoke the library wrapper 
// function immediately after being parsed.
