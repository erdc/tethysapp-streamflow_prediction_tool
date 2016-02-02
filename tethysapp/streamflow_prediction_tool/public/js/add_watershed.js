/*****************************************************************************
 * FILE:    add_watershed.js
 * AUTHOR:  Alan Snow
 * COPYRIGHT: © 2015 Alan D Snow. All rights reserved.
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
    
        $('#geoserver-drainage-line-input').parent().parent().addClass('geo_input');
        $('#geoserver-catchment-input').parent().parent().addClass('geo_input');
        $('#geoserver-gage-input').parent().parent().addClass('geo_input');
        $('#geoserver-ahps-station-input').parent().parent().addClass('geo_input');
        $('.geo_input').addClass('hidden');

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
            var geoserver_search_for_flood_map = false;

            //Initialize Data Store Data
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

            //Initialize Geoserver Data
            if (!$('#shp-upload-toggle').bootstrapSwitch('state')) {
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
                if($('#shp-upload-toggle').bootstrapSwitch('state')){
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
                    for(var i = 0; i < drainage_line_shp_files.length; i++) {
                        data.append("drainage_line_shp_file", drainage_line_shp_files[i]);
                    }
                    
                    if (geoserver_drainage_line_layer != null) {
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
                                //upload catchment when  drainage line finishes if exists
                                if(catchment_shp_files.length >= 4) {
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
                                    }
                                    if(gage_shp_files.length >= 4) {
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
                                        data.append("geoserver_catchment_layer", geoserver_catchment_layer);
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
                                            data.append("geoserver_gage_layer", geoserver_gage_layer);
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

        //show hide elements based on shape upload toggle selection
        $('#shp-upload-toggle').on('switchChange.bootstrapSwitch', function(event, state) {
            if(state) {
                //show file upload
                $('.geo_upload').removeClass('hidden');
                $('.geo_input').addClass('hidden');
            } else {
                $('.geo_upload').addClass('hidden');
                $('.geo_input').removeClass('hidden');
                $('#drainage-line-shp-upload-input').val('');
                $('#catchment-shp-upload-input').val('');
                $('#gage-shp-upload-input').val('');
                $('#ahps-station-shp-upload-input').val('');
            }
            
        });
    }); //page load
}()); // End of package wrapper 