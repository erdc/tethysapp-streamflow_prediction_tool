/*****************************************************************************
 * FILE:    Add Watershed
 * DATE:    2/26/2015
 * AUTHOR:  Alan Snow
 * COPYRIGHT: (c) 2015 Brigham Young University
 * LICENSE: BSD 2-Clause
 *****************************************************************************/

/*****************************************************************************
 *                      LIBRARY WRAPPER
 *****************************************************************************/

var ERFP_ADD_WATERSHED = (function() {
    // Wrap the library in a package function
    "use strict"; // And enable strict mode for this library
    
    /************************************************************************
    *                      MODULE LEVEL / GLOBAL VARIABLES
    *************************************************************************/
    var m_uploading_data;

     /************************************************************************
    *                    PRIVATE FUNCTION DECLARATIONS
    *************************************************************************/
    var checkErrors, finishReset;


    /************************************************************************
    *                    PRIVATE FUNCTION IMPLEMENTATIONS
    *************************************************************************/
    //FUNCTION: Check output from array of xhr
    checkErrors = function(output_array) {
        output_array.forEach(function(output){
            if(output != null && typeof output != 'undefined') {
                if ("error" in output) {
                    return {"error" : output["error"]};
                }
            }
        });
        return {"success" : "Watershed Upload Success!"};
    };

    //FUNCTION: RESET EVERYTHING WHEN DONE
    finishReset = function(result, watershed_id) {
        if ("success" in result) {
            //reset inputs
            $('#watershed-name-input').val('');
            $('#subbasin-name-input').val('');
            $('#data-store-select').select2('val','1');
            $('#ecmwf-data-store-watershed-name-input').val('');
            $('#ecmwf-data-store-subbasin-name-input').val('');
            $('#wrf-hydro-data-store-watershed-name-input').val('');
            $('#wrf-hydro-data-store-subbasin-name-input').val('');
            $('#geoserver-select').select2('val','1');
            $('#drainage-line-kml-upload-input').val('');
            $('#catchment-kml-upload-input').val('');
            $('#gage-kml-upload-input').val('');
            $('#geoserver-drainage-line-input').val('');
            $('#geoserver-catchment-input').val('');
            $('#geoserver-gage-input').val('');
            $('#geoserver-ahps-station-input').val('');
            $('#drainage-line-shp-upload-input').val('');
            $('#catchment-shp-upload-input').val('');
            $('#gage-shp-upload-input').val('');
            $('#ahps-station-shp-upload-input').val('');
            $('#ecmwf-rapid-files-upload-input').val('');
            $('.data_store').addClass('hidden');
            $('.kml').removeClass('hidden');
            $('.shapefile').addClass('hidden');
            addSuccessMessage("Watershed Upload Complete!");
        } else {
            //delete watershed and show error
            var xhr = ajax_update_database("delete",{watershed_id: watershed_id});
            appendErrorMessage(result["error"], "error_reset");
        }
     };


    /************************************************************************
    *                  INITIALIZATION / CONSTRUCTOR
    *************************************************************************/
    
    $(function() {
        //initialize modlule variables
        m_uploading_data = false;

        //initialize gizmo help blockss
        var help_html = '<p class="help-block hidden">No watershed name specified.</p>';
        $('#watershed-name-input').parent().parent().append(help_html);
        help_html = '<p class="help-block hidden">No subbasin name specified.</p>';
        $('#subbasin-name-input').parent().parent().append(help_html);

        help_html = '<p class="help-block hidden">No data store selected.</p>';
        $('#data-store-select').parent().append(help_html);
        help_html = '<p class="help-block hidden">No ECMWF watershed name specified.</p>';
        $('#ecmwf-data-store-watershed-name-input').parent().append(help_html);
        help_html = '<p class="help-block hidden">No ECMWF subbasin name specified.</p>';
        $('#ecmwf-data-store-subbasin-name-input').parent().append(help_html);
        help_html = '<p class="help-block hidden">No WRF-Hydro watershed name specified.</p>';
        $('#wrf-hydro-data-store-watershed-name-input').parent().append(help_html);
        help_html = '<p class="help-block hidden">No WRF-Hydro subbasin name specified.</p>';
        $('#wrf-hydro-data-store-subbasin-name-input').parent().append(help_html);

        help_html = '<p class="help-block hidden">No Geoserver selected.</p>';
        $('#geoserver-select').parent().append(help_html);
        help_html = '<p class="help-block hidden">No Geoserver drainage line layer name specified.</p>';
        $('#geoserver-drainage-line-input').parent().parent().append(help_html);
    
        //initialize gizmo classes
        $('#ecmwf-data-store-watershed-name-input').parent().parent().addClass('data_store');
        $('#ecmwf-data-store-subbasin-name-input').parent().parent().addClass('data_store');
        $('#wrf-hydro-data-store-watershed-name-input').parent().parent().addClass('data_store');
        $('#wrf-hydro-data-store-subbasin-name-input').parent().parent().addClass('data_store');
        $('.data_store').addClass('hidden');

        $('#geoserver-drainage-line-input').parent().parent().addClass('shapefile');
        $('#geoserver-catchment-input').parent().parent().addClass('shapefile');
        $('#geoserver-gage-input').parent().parent().addClass('shapefile');
        $('#geoserver-ahps-station-input').parent().parent().addClass('shapefile');
        $('#search-floodmap-toggle').parent().parent().parent().addClass('shapefile');
        $('#shp-upload-toggle').parent().parent().parent().addClass('shapefile');
        $('.shapefile').addClass('hidden');
        
        //handle the submit event
        $('#submit-add-watershed').click(function(){
            //scroll back to top
            window.scrollTo(0,0);
            //clear messages
            $('#message').addClass('hidden');
            $('#message').empty()
                .addClass('hidden')
                .removeClass('alert-success')
                .removeClass('alert-info')
                .removeClass('alert-warning')
                .removeClass('alert-danger');

            //check data store input
            var safe_to_submit = {val: true, error: ""};
            var watershed_name = checkInputWithError($('#watershed-name-input'),safe_to_submit);
            var subbasin_name = checkInputWithError($('#subbasin-name-input'),safe_to_submit);
            var data_store_id = checkInputWithError($('#data-store-select'),safe_to_submit, true);
            var geoserver_id = checkInputWithError($('#geoserver-select'),safe_to_submit, true);
    
            //initialize values
            var ecmwf_data_store_watershed_name = "";
            var ecmwf_data_store_subbasin_name = "";
            var wrf_hydro_data_store_watershed_name = "";
            var wrf_hydro_data_store_subbasin_name = "";
            var geoserver_drainage_line_layer = "";
            var geoserver_catchment_layer = "";
            var geoserver_gage_layer = "";
            var geoserver_ahps_station_layer = "";
            var drainage_line_shp_files = [];
            var catchment_shp_files = [];
            var gage_shp_files = [];
            var ahps_station_shp_files = [];
            var drainage_line_kml_file = null;
            var catchment_kml_file = null;
            var gage_kml_file = null;
            var kml_drainage_line_layer = "";
            var kml_catchment_layer = "";
            var kml_gage_layer = "";
            var geoserver_search_for_flood_map = false;

            //Initialize Data Store Data
            if(data_store_id>1) {
                //check ecmwf inputs
                var ecmwf_ready = false
                ecmwf_data_store_watershed_name = $('#ecmwf-data-store-watershed-name-input').val();
                ecmwf_data_store_subbasin_name = $('#ecmwf-data-store-subbasin-name-input').val();
                if (typeof ecmwf_data_store_watershed_name == 'undefined' || 
                    typeof ecmwf_data_store_subbasin_name == 'undefined') {
                    ecmwf_data_store_watershed_name = "";
                    ecmwf_data_store_subbasin_name = "";
                } else {
                    ecmwf_data_store_watershed_name = ecmwf_data_store_watershed_name.trim();
                    ecmwf_data_store_subbasin_name = ecmwf_data_store_subbasin_name.trim();
                    ecmwf_ready = (ecmwf_data_store_watershed_name.length > 0 &&
                                   ecmwf_data_store_subbasin_name.length > 0);
                }

                //check wrf-hydro inputs
                var wrf_hydro_ready = false;
                wrf_hydro_data_store_watershed_name = $('#wrf-hydro-data-store-watershed-name-input').val();
                wrf_hydro_data_store_subbasin_name = $('#wrf-hydro-data-store-subbasin-name-input').val();
                if (typeof wrf_hydro_data_store_watershed_name == 'undefined' || 
                    typeof wrf_hydro_data_store_subbasin_name == 'undefined') {
                    wrf_hydro_data_store_watershed_name = "";
                    wrf_hydro_data_store_subbasin_name = "";
                } else {
                    wrf_hydro_data_store_watershed_name = wrf_hydro_data_store_watershed_name.trim();
                    wrf_hydro_data_store_subbasin_name = wrf_hydro_data_store_subbasin_name.trim();
                    wrf_hydro_ready = (wrf_hydro_data_store_watershed_name.length > 0 && 
                                       wrf_hydro_data_store_subbasin_name.length > 0);
                }
                //need at least one to be OK to proceed
                if(!ecmwf_ready && !wrf_hydro_ready) {
                    safe_to_submit.val = false;
                    safe_to_submit.error = "Need ECMWF or WRF-Hydro watershed and subbasin names to proceed";
             
                }
            }

            //Initialize Geoserver Data
            if(geoserver_id==1){
                //kml upload
                drainage_line_kml_file = $('#drainage-line-kml-upload-input')[0].files[0];
                if(!checkKMLfile(drainage_line_kml_file, safe_to_submit)) {
                    $('#drainage-line-kml-upload-input').parent().addClass('has-error');
                }
                catchment_kml_file = $('#catchment-kml-upload-input')[0].files[0];
                if(typeof catchment_kml_file != 'undefined') {
                    if(!checkKMLfile(catchment_kml_file, safe_to_submit)) {
                        $('#catchment-kml-upload-input').parent().addClass('has-error');
                    }
                } else {
                    catchment_kml_file = null;;
                }
                gage_kml_file = $('#gage-kml-upload-input')[0].files[0];
                if(typeof gage_kml_file != 'undefined') {
                    if(!checkKMLfile(gage_kml_file, safe_to_submit)) {
                        $('#gage-kml-upload-input').parent().addClass('has-error');
                    }
                } else {
                    gage_kml_file = null;;
                }               
            } else if (!$('#shp-upload-toggle').bootstrapSwitch('state')) {
                //geoserver update
                geoserver_drainage_line_layer = checkInputWithError($('#geoserver-drainage-line-input'),safe_to_submit);
                geoserver_catchment_layer = $('#geoserver-catchment-input').val(); //optional
                geoserver_gage_layer = $('#geoserver-gage-input').val(); //optional
                geoserver_ahps_station_layer = $('#geoserver-ahps-station-input').val(); //optional
                geoserver_search_for_flood_map = $('#search-floodmap-toggle').bootstrapSwitch('state');
            } else {
                //geoserver upload
                drainage_line_shp_files = $('#drainage-line-shp-upload-input')[0].files;
                if(!checkShapefile(drainage_line_shp_files, safe_to_submit)) {
                    $('#drainage-line-shp-upload-input').parent().addClass('has-error');
                } else {
                    $('#drainage-line-shp-upload-input').parent().removeClass('has-error');
                }
                catchment_shp_files = $('#catchment-shp-upload-input')[0].files;
                if (catchment_shp_files.length > 0) {
                    if(!checkShapefile(catchment_shp_files, safe_to_submit)) {
                        $('#catchment-shp-upload-input').parent().addClass('has-error');
                    } else {
                        $('#catchment-shp-upload-input').parent().removeClass('has-error');
                    }
                }
                gage_shp_files = $('#gage-shp-upload-input')[0].files;
                if (gage_shp_files.length > 0) {
                    if(!checkShapefile(gage_shp_files, safe_to_submit)) {
                        $('#gage-shp-upload-input').parent().addClass('has-error');
                    } else {
                        $('#gage-shp-upload-input').parent().removeClass('has-error');
                    }
                }
                ahps_station_shp_files = $('#ahps-station-shp-upload-input')[0].files;
                if (ahps_station_shp_files.length > 0) {
                    if(!checkShapefile(ahps_station_shp_files, safe_to_submit)) {
                        $('#ahps-station-shp-upload-input').parent().addClass('has-error');
                    } else {
                        $('#ahps-station-shp-upload-input').parent().removeClass('has-error');
                    }
                }
                geoserver_search_for_flood_map = $('#search-floodmap-toggle').bootstrapSwitch('state');
            }
            
            //submit if the form is ready
            if(safe_to_submit.val && !m_uploading_data) {
                var submit_button = $(this);
                var submit_button_html = submit_button.html();
                var xhr = null;
                var xhr_catchment = null;
                var xhr_gage = null;
                var xhr_ahps_station = null;
                var xhr_ecmwf_rapid = null;
                //give user information
                addInfoMessage("Submiting data. Please be patient! " +
                               "This may take a few minutes ...");
                submit_button.text('Submitting ...');
                //update database
                if(geoserver_id==1 || $('#shp-upload-toggle').bootstrapSwitch('state')){
                    //upload files
                    var data = new FormData();
                    data.append("watershed_name",watershed_name);
                    data.append("subbasin_name",subbasin_name);
                    data.append("data_store_id",data_store_id);
                    data.append("ecmwf_data_store_watershed_name",ecmwf_data_store_watershed_name);
                    data.append("ecmwf_data_store_subbasin_name",ecmwf_data_store_subbasin_name);
                    data.append("wrf_hydro_data_store_watershed_name",wrf_hydro_data_store_watershed_name);
                    data.append("wrf_hydro_data_store_subbasin_name",wrf_hydro_data_store_subbasin_name);
                    data.append("geoserver_id",geoserver_id);
                    data.append("geoserver_search_for_flood_map",geoserver_search_for_flood_map);
                    data.append("geoserver_drainage_line_layer",geoserver_drainage_line_layer);
                    data.append("geoserver_catchment_layer",geoserver_catchment_layer);
                    data.append("geoserver_gage_layer",geoserver_gage_layer);
                    data.append("drainage_line_kml_file",drainage_line_kml_file);
                    for(var i = 0; i < drainage_line_shp_files.length; i++) {
                        data.append("drainage_line_shp_file", drainage_line_shp_files[i]);
                    }
                    
                    if (drainage_line_kml_file != null || geoserver_drainage_line_layer != null) {
                        appendInfoMessage("Uploading Drainage Line ...", "message_drainage_line");
                    }
                    xhr = ajax_update_database_multiple_files("submit",data, 
                            "Drainage Line Upload Success!", "message_drainage_line");
                    
                    //upload catchment when drainage line finishes if catchment exists
                    xhr.done(function(return_data){
                        if ('success' in return_data) {
                            if('watershed_id' in return_data) {
                                var watershed_id  = return_data['watershed_id'];
                                if ('geoserver_drainage_line_layer' in return_data) {
                                    geoserver_drainage_line_layer = return_data['geoserver_drainage_line_layer'];
                                }
                                if ('kml_drainage_line_layer' in return_data) {
                                    kml_drainage_line_layer = return_data['kml_drainage_line_layer'];
                                }
                                //upload catchment when  drainage line finishes if exists
                                if(catchment_kml_file != null || catchment_shp_files.length >= 4) {
                                    appendInfoMessage("Uploading Catchment ...", "message_catchment");
                                    var data = new FormData();
                                    data.append("watershed_id", watershed_id)
                                    data.append("watershed_name", watershed_name);
                                    data.append("subbasin_name", subbasin_name);
                                    data.append("data_store_id", data_store_id);
                                    data.append("ecmwf_data_store_watershed_name", ecmwf_data_store_watershed_name);
                                    data.append("ecmwf_data_store_subbasin_name", ecmwf_data_store_subbasin_name);
                                    data.append("wrf_hydro_data_store_watershed_name", wrf_hydro_data_store_watershed_name);
                                    data.append("wrf_hydro_data_store_subbasin_name", wrf_hydro_data_store_subbasin_name);
                                    data.append("geoserver_id",geoserver_id);
                                    data.append("geoserver_search_for_flood_map",geoserver_search_for_flood_map);
                                    data.append("geoserver_drainage_line_layer", geoserver_drainage_line_layer);
                                    for(var i = 0; i < catchment_shp_files.length; i++) {
                                        data.append("catchment_shp_file",catchment_shp_files[i]);
                                    }
                                    data.append("kml_drainage_line_layer", kml_drainage_line_layer);
                                    xhr_catchment = ajax_update_database_multiple_files("update",
                                                                                        data, 
                                                                                        "Catchment Upload Success!",
                                                                                        "message_catchment");
                                }
    
                                //upload gage when catchment and drainage line finishes if gage exists
                                jQuery.when(xhr_catchment).done(function(catchment_data){
                                    if(catchment_data != null && typeof catchment_data != 'undefined') {
                                        if('geoserver_catchment_layer' in catchment_data) {
                                            geoserver_catchment_layer = catchment_data['geoserver_catchment_layer'];
                                        }
                                        if('kml_catchment_layer' in catchment_data) {
                                            kml_catchment_layer = catchment_data['kml_catchment_layer'];
                                        }
                                    }
                                    if(gage_kml_file != null || gage_shp_files.length >= 4) {
                                        appendInfoMessage("Uploading Gages ...", "message_gages");
                                        var data = new FormData();
                                        data.append("watershed_id", watershed_id)
                                        data.append("watershed_name",watershed_name);
                                        data.append("subbasin_name",subbasin_name);
                                        data.append("data_store_id",data_store_id);
                                        data.append("ecmwf_data_store_watershed_name",ecmwf_data_store_watershed_name);
                                        data.append("ecmwf_data_store_subbasin_name",ecmwf_data_store_subbasin_name);
                                        data.append("wrf_hydro_data_store_watershed_name",wrf_hydro_data_store_watershed_name);
                                        data.append("wrf_hydro_data_store_subbasin_name",wrf_hydro_data_store_subbasin_name);
                                        data.append("geoserver_id",geoserver_id);
                                        data.append("geoserver_search_for_flood_map",geoserver_search_for_flood_map);
                                        data.append("geoserver_drainage_line_layer", geoserver_drainage_line_layer);
                                        data.append("kml_drainage_line_layer", kml_drainage_line_layer);
                                        data.append("geoserver_catchment_layer", geoserver_catchment_layer);
                                        data.append("kml_catchment_layer", kml_catchment_layer);
                                        data.append("gage_kml_file", gage_kml_file);
                                        for(var i = 0; i < gage_shp_files.length; i++) {
                                            data.append("gage_shp_file", gage_shp_files[i]);
                                        }

                                        xhr_gage = ajax_update_database_multiple_files("update",data,
                                                                                       "Gages Upload Success!",
                                                                                        "message_gages");
                                    }
                                    //upload gage when catchment and drainage line finishes if gage exists
                                    jQuery.when(xhr_gage).done(function(gage_data){
                                        if(gage_data != null && typeof gage_data != 'undefined') {
                                            if('geoserver_gage_layer' in gage_data) {
                                                geoserver_gage_layer = gage_data['geoserver_gage_layer'];
                                            }
                                            if('kml_gage_layer' in gage_data) {
                                                kml_gage_layer = gage_data['kml_gage_layer'];
                                            }
                                        }
                                        if(ahps_station_shp_files.length >= 4) {
                                            appendInfoMessage("Uploading AHPS Stations ...", "message_ahps_stations");
                                            var data = new FormData();
                                            data.append("watershed_id", watershed_id)
                                            data.append("watershed_name",watershed_name);
                                            data.append("subbasin_name",subbasin_name);
                                            data.append("data_store_id",data_store_id);
                                            data.append("ecmwf_data_store_watershed_name",ecmwf_data_store_watershed_name);
                                            data.append("ecmwf_data_store_subbasin_name",ecmwf_data_store_subbasin_name);
                                            data.append("wrf_hydro_data_store_watershed_name",wrf_hydro_data_store_watershed_name);
                                            data.append("wrf_hydro_data_store_subbasin_name",wrf_hydro_data_store_subbasin_name);
                                            data.append("geoserver_id",geoserver_id);
                                            data.append("geoserver_search_for_flood_map",geoserver_search_for_flood_map);
                                            data.append("geoserver_drainage_line_layer", geoserver_drainage_line_layer);
                                            data.append("geoserver_catchment_layer", geoserver_catchment_layer);
                                            data.append("kml_drainage_line_layer", kml_drainage_line_layer);
                                            data.append("kml_catchment_layer", kml_catchment_layer);
                                            data.append("geoserver_gage_layer", geoserver_gage_layer);
                                            data.append("kml_gage_layer", kml_gage_layer);
                                            for(var i = 0; i < ahps_station_shp_files.length; i++) {
                                                data.append("ahps_station_shp_file", ahps_station_shp_files[i]);
                                            }
    
                                            xhr_ahps_station = ajax_update_database_multiple_files("update",data,
                                                                                                   "AHPS Stations Upload Success!",
                                                                                                   "message_ahps_stations");
                                        }
                                        jQuery.when(xhr_ahps_station).done(function(){
                                            if(data_store_id>1) {
                                                //upload RAPID file if exists
                                                xhr_ecmwf_rapid = upload_AJAX_ECMWF_RAPID_input(watershed_id,
                                                                                                data_store_id);
                                            }
                                            //when everything is finished
                                            jQuery.when(xhr, xhr_catchment, xhr_gage, 
                                                        xhr_ahps_station, xhr_ecmwf_rapid)
                                                  .done(function(xhr_data, xhr_catchment_data, xhr_gage_data,
                                                                 xhr_ahps_station_data, xhr_ecmwf_rapid_data){
                                                        //Reset The Output
                                                        finishReset(checkErrors([xhr_data, xhr_catchment_data, xhr_gage_data,
                                                                                 xhr_ahps_station_data, xhr_ecmwf_rapid_data]),
                                                                    watershed_id);
                                            });
                                        });
                                    });
                                });
                            }
                        } else {
                            appendErrorMessage(return_data['error'], "error_submit");
                        }
                    });
                } else {
                    var data = {
                            watershed_name: watershed_name,
                            subbasin_name: subbasin_name,
                            data_store_id: data_store_id,
                            ecmwf_data_store_watershed_name: ecmwf_data_store_watershed_name,
                            ecmwf_data_store_subbasin_name: ecmwf_data_store_subbasin_name,
                            wrf_hydro_data_store_watershed_name: wrf_hydro_data_store_watershed_name,
                            wrf_hydro_data_store_subbasin_name: wrf_hydro_data_store_subbasin_name,
                            geoserver_id: geoserver_id,
                            geoserver_search_for_flood_map: geoserver_search_for_flood_map,
                            geoserver_drainage_line_layer: geoserver_drainage_line_layer,
                            geoserver_catchment_layer: geoserver_catchment_layer,
                            geoserver_gage_layer: geoserver_gage_layer,
                            geoserver_ahps_station_layer: geoserver_ahps_station_layer,
                            };
            
                    var xhr = ajax_update_database("submit",data);

                    //when everything finishes uploading
                    xhr.done(function(return_data){
                        if ('success' in return_data) {
                            var watershed_id = return_data['watershed_id'];
                            if (data_store_id>1) {
                                xhr_ecmwf_rapid = upload_AJAX_ECMWF_RAPID_input(watershed_id,
                                                                                data_store_id);
                            }
                            //when everything is finished
                            jQuery.when(xhr_ecmwf_rapid).done(function(){
                                finishReset(return_data);
                            });
                        } else {
                            appendErrorMessage(return_data['error'], "error_submit");
                        }
                    })
                }
                m_uploading_data = true;

                jQuery.when(xhr, xhr_catchment, xhr_gage, xhr_ahps_station, xhr_ecmwf_rapid)
                      .always(function(){
                          submit_button.html(submit_button_html);
                          m_uploading_data = false;
                });

            } else if (m_uploading_data) {
                //give user information
                addWarningMessage("Submitting Data. Please Wait.");
            } else {
                appendErrorMessage("Not submitted. Please fix form errors to proceed.", "error_form");
                appendErrorMessage(safe_to_submit.error, "error_form_info");
            }
        });
        
        //show/hide elements based on data store selection
        $('#data-store-select').change(function() {
            var select_val = $(this).val();
            if(select_val == 1) {
                //local upload
                $('.data_store').addClass('hidden');
            } else {
                //files on data store
                $('.data_store').removeClass('hidden');
            }        
        });

        //show/hide elements based on geoserver selection
        $('#geoserver-select').change(function() {
            var select_val = $(this).val();
            if(select_val == 1) {
                //local upload
                $('#geoserver-drainage-line-input').val('');
                $('#geoserver-catchment-input').val('');
                $('#drainage-line-shp-upload-input').val('');
                $('#catchment-shp-upload-input').val('');
                $('#gage-shp-upload-input').val('');
                $('#ahps-station-shp-upload-input').val('');
                $('.kml').removeClass('hidden');
                $('.shapefile').addClass('hidden');
            } else {
                //file located on geoserver
                $('.kml').addClass('hidden');
                $('.shapefile').removeClass('hidden');
                $('#drainage-line-kml-upload-input').val('');
                $('#catchment-kml-upload-input').val('');
                $('#gage-kml-upload-input').val('');
                $('#shp-upload-toggle').bootstrapSwitch('state',true);
                $('.upload').removeClass('hidden');
                $('#geoserver-drainage-line-input').parent().parent().addClass('hidden');
                $('#geoserver-catchment-input').parent().parent().addClass('hidden');
                $('#geoserver-gage-input').parent().parent().addClass('hidden');
                $('#geoserver-ahps-station-input').parent().parent().addClass('hidden');
            }
        
        });
    
        //show hide elements based on shape upload toggle selection
        $('#shp-upload-toggle').on('switchChange.bootstrapSwitch', function(event, state) {
            if(state) {
                //show file upload
                $('.upload').removeClass('hidden');
                $('#geoserver-drainage-line-input').parent().parent().addClass('hidden');
                $('#geoserver-catchment-input').parent().parent().addClass('hidden');
                $('#geoserver-gage-input').parent().parent().addClass('hidden');
                $('#geoserver-ahps-station-input').parent().parent().addClass('hidden');
            } else {
                $('.upload').addClass('hidden');
                $('#drainage-line-shp-upload-input').val('');
                $('#catchment-shp-upload-input').val('');
                $('#gage-shp-upload-input').val('');
                $('#geoserver-drainage-line-input').parent().parent().removeClass('hidden');
                $('#geoserver-catchment-input').parent().parent().removeClass('hidden');
                $('#geoserver-gage-input').parent().parent().removeClass('hidden');
                $('#geoserver-ahps-station-input').parent().parent().removeClass('hidden');
            }
            
        });
    }); //page load
}()); // End of package wrapper 