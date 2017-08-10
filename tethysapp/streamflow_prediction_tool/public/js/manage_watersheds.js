/*****************************************************************************
 * FILE:    manage_watersheds.js
 * AUTHOR:  Alan D. Snow, Curtis Rae, and Shawn Crawley
 * COPYRIGHT: © 2015-2016 Alan D. Snow, Curtis Rae, and Shawn Crawley. All rights reserved.
 * LICENSE: BSD 3-Clause
 *****************************************************************************/

/*****************************************************************************
 *                      LIBRARY WRAPPER
 *****************************************************************************/

var ERFP_MANAGE_WATERSHEDS = (function() {
    // Wrap the library in a package function
    "use strict"; // And enable strict mode for this library
    
    /************************************************************************
    *                      MODULE LEVEL / GLOBAL VARIABLES
    *************************************************************************/
    var m_uploading_data;

    /************************************************************************
     *                    PRIVATE FUNCTION DECLARATIONS
     *************************************************************************/
    var getModalHTML, initializeModal, initializeTableFunctions, getTablePage;


    /************************************************************************
     *                    PRIVATE FUNCTION IMPLEMENTATIONS
     *************************************************************************/
    getModalHTML = function(watershed_id, reload) {
        reload = typeof reload !== 'undefined' ? reload : false;
        $.ajax({
            url: 'edit',
            method: 'GET',
            data: {
                'watershed_id': watershed_id
            },
            success: function(data) {
                $("#edit_watershed_modal").find('.modal-body').html(data);
                initializeModal();
                if (reload) {
                    addSuccessMessage("Watershed Update Complete!");
                }
            }
        });
    };

    initializeModal = function() {
        //turn the select options into select2
        $("#data-store-select").select2();
        $("#geoserver-select").select2();

        // Initialize any switch elements
        $('.bootstrap-switch').each(function () {
            $(this).bootstrapSwitch();
        });

        //initialize gizmo classes
        $('#geoserver-drainage-line-input').parent().parent().addClass('geo_input');
        $('#geoserver-boundary-input').parent().parent().addClass('geo_input');
        $('#geoserver-gage-input').parent().parent().addClass('geo_input');
        $('#geoserver-historical-flood-map-input').parent().parent().addClass('geo_input');
        $('#geoserver-ahps-station-input').parent().parent().addClass('geo_input');
        $('.geo_upload').addClass('hidden');

        //show/hide elements based on data store selection
        $('#data-store-select').change(function() {
            var select_val = $(this).val();
            if(select_val == 1) {
                //local upload
                $('.data_store').addClass('hidden');
            } else {
                $('.data_store').removeClass('hidden');
            }

        });

        $("#data-store-select").change();

        //show hide elements based on shape upload toggle selection
        $('#shp-upload-toggle').on('switchChange.bootstrapSwitch', function(event, state) {
            if(state) {
                //show file upload
                $('.geo_upload').removeClass('hidden');
                $('.geo_input').addClass('hidden');
            } else {
                $('.geo_upload').addClass('hidden');
                $('.geo_input').removeClass('hidden');
            }
        });

        //handle the submit event
        $('#edit_modal_submit').off().click(function () {
             //scroll back to top
            window.scrollTo(0,0);
            //clear messages
            $('#message').addClass('hidden');
           //clear message div
            $('#message').empty()
                .addClass('hidden')
                .removeClass('alert-success')
                .removeClass('alert-info')
                .removeClass('alert-warning')
                .removeClass('alert-danger');

            //check data store input
            var safe_to_submit = {val: true};
            var watershed_id = $("#watershed_id").val();
            var watershed_name = checkInputWithError($('#watershed-name-input'),safe_to_submit);
            var subbasin_name = checkInputWithError($('#subbasin-name-input'),safe_to_submit);
            var data_store_id = checkInputWithError($('#data-store-select'),safe_to_submit, true);
            var geoserver_id = checkInputWithError($('#geoserver-select'),safe_to_submit, true);

            //initialize values
            var ecmwf_data_store_watershed_name = "";
            var ecmwf_data_store_subbasin_name = "";
            var geoserver_drainage_line_layer = "";
            var geoserver_boundary_layer = "";
            var geoserver_gage_layer = "";
            var geoserver_historical_flood_map_layer = "";
            var geoserver_ahps_station_layer = "";
            var drainage_line_shp_files = [];
            var boundary_shp_files = [];
            var gage_shp_files = [];
            var ahps_station_shp_files = [];

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

            if(!ecmwf_ready) {
                safe_to_submit.val = false;
                safe_to_submit.error = "Need ECMWF watershed and subbasin names to proceed";
         
            }

            //geoserver update
            geoserver_drainage_line_layer = $('#geoserver-drainage-line-input').val();
            geoserver_boundary_layer = $('#geoserver-boundary-input').val(); //optional
            geoserver_gage_layer = $('#geoserver-gage-input').val(); //optional
            geoserver_historical_flood_map_layer = $('#geoserver-historical-flood-map-input').val(); //optional
            geoserver_ahps_station_layer = $('#geoserver-ahps-station-input').val(); //optional
            //geoserver upload
            drainage_line_shp_files = $('#drainage-line-shp-upload-input')[0].files;
            if (drainage_line_shp_files.length > 0) {
                if (!checkShapefile(drainage_line_shp_files, safe_to_submit)) {
                    $('#drainage-line-shp-upload-input').parent().addClass('has-error');
                } else {
                    $('#drainage-line-shp-upload-input').parent().removeClass('has-error');
                }
            }
            boundary_shp_files = $('#boundary-shp-upload-input')[0].files;
            if (boundary_shp_files.length > 0) {
                if(!checkShapefile(boundary_shp_files, safe_to_submit)) {
                    $('#boundary-shp-upload-input').parent().addClass('has-error');
                } else {
                    $('#boundary-shp-upload-input').parent().removeClass('has-error');
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

            //submit if the form is ok
            if (safe_to_submit.val && !m_uploading_data) {
                if (window.confirm("Are you sure? You will delete prediction files " +
                    "if either of the watershed or subbasin data store names are changed.")) {

                    m_uploading_data = true;
                    var submit_button = $(this);
                    var submit_button_html = submit_button.html();
                    var xhr = null;
                    var xhr_no_files = null;
                    var xhr_boundary = null;
                    var xhr_gage = null;
                    var xhr_ahps_station = null;
                    var xhr_ecmwf_rapid = null;
                    //give user information
                    addInfoMessage("Submiting data. Please be patient! " +
                    "This may take a few minutes ...");
                    submit_button.text('Submitting ...');
                    //update database
                    if ($('#shp-upload-toggle').bootstrapSwitch('state')) {
                        //file upload
                        if (drainage_line_shp_files.length >= 4 ||
                            geoserver_drainage_line_layer.length > 0) {
                            var data = new FormData();
                            data.append("watershed_id", watershed_id);
                            data.append("watershed_name", watershed_name);
                            data.append("subbasin_name", subbasin_name);
                            data.append("data_store_id", data_store_id);
                            data.append("ecmwf_data_store_watershed_name",ecmwf_data_store_watershed_name);
                            data.append("ecmwf_data_store_subbasin_name",ecmwf_data_store_subbasin_name);
                            data.append("geoserver_id", geoserver_id);
                            data.append("geoserver_drainage_line_layer", geoserver_drainage_line_layer);
                            data.append("geoserver_boundary_layer", geoserver_boundary_layer);
                            data.append("geoserver_gage_layer", geoserver_gage_layer);
                            data.append("geoserver_historical_flood_map_layer", geoserver_historical_flood_map_layer);
                            data.append("geoserver_ahps_station_layer", geoserver_ahps_station_layer);
                            for (var i = 0; i < drainage_line_shp_files.length; i++) {
                                data.append("drainage_line_shp_file", drainage_line_shp_files[i]);
                            }
                            var drainage_success_message = "Drainage Line Upload Success!";
                            if (drainage_line_shp_files.length >= 4) {
                                appendInfoMessage("Uploading Drainage Line ...", "message_drainage_line");
                            } else {
                                appendInfoMessage("Uploading Watershed Data ...", "message_drainage_line");
                                drainage_success_message = "Watershed Data Upload Success!"
                            }
                            //needs to be outside
                            xhr = ajax_update_database_multiple_files("submit",
                                                                      data,
                                                                      drainage_success_message,
                                                                      "message_drainage_line");

                            //upload boundary when drainage line finishes if boundary exist
                            jQuery.when(xhr).done(function (return_data) {
                                if (return_data != null && typeof return_data != 'undefined') {
                                    if ('geoserver_drainage_line_layer' in return_data) {
                                        geoserver_drainage_line_layer = return_data['geoserver_drainage_line_layer'];
                                    }
                                }
                                //upload boundary when  drainage line finishes if exists
                                if (boundary_shp_files.length >= 4) {
                                    appendInfoMessage("Uploading Boundary ...", "message_boundary");
                                    var data = new FormData();
                                    data.append("watershed_id", watershed_id);
                                    data.append("watershed_name", watershed_name);
                                    data.append("subbasin_name", subbasin_name);
                                    data.append("data_store_id", data_store_id);
                                    data.append("ecmwf_data_store_watershed_name",ecmwf_data_store_watershed_name);
                                    data.append("ecmwf_data_store_subbasin_name",ecmwf_data_store_subbasin_name);
                                    data.append("geoserver_id", geoserver_id);
                                    data.append("geoserver_drainage_line_layer", geoserver_drainage_line_layer);
                                    data.append("geoserver_boundary_layer", geoserver_boundary_layer);
                                    data.append("geoserver_gage_layer", geoserver_gage_layer);
                                    data.append("geoserver_historical_flood_map_layer", geoserver_historical_flood_map_layer);
                                    data.append("geoserver_ahps_station_layer", geoserver_ahps_station_layer);
                                    for (var i = 0; i < boundary_shp_files.length; i++) {
                                        data.append("boundary_shp_file", boundary_shp_files[i]);
                                    }
                                    xhr_boundary = ajax_update_database_multiple_files("submit", 
                                                                                        data,
                                                                                        "Boundary Upload Success!",
                                                                                        "message_boundary");
                                }
                                //upload gage when boundary and drainage line finishes if gage exists
                                jQuery.when(xhr_boundary).done(function (boundary_data) {
                                    if (boundary_data != null && typeof boundary_data != 'undefined') {
                                        if ('geoserver_boundary_layer' in boundary_data) {
                                            geoserver_boundary_layer = boundary_data['geoserver_boundary_layer'];
                                        }
                                    }
                                    if (gage_shp_files.length >= 4) {
                                        appendInfoMessage("Uploading Gages ...", "message_gages");
                                        var data = new FormData();
                                        data.append("watershed_id", watershed_id)
                                        data.append("watershed_name", watershed_name);
                                        data.append("subbasin_name", subbasin_name);
                                        data.append("data_store_id", data_store_id);
                                        data.append("ecmwf_data_store_watershed_name",ecmwf_data_store_watershed_name);
                                        data.append("ecmwf_data_store_subbasin_name",ecmwf_data_store_subbasin_name);
                                        data.append("geoserver_id", geoserver_id);
                                        data.append("geoserver_drainage_line_layer", geoserver_drainage_line_layer);
                                        data.append("geoserver_boundary_layer", geoserver_boundary_layer);
                                        data.append("geoserver_gage_layer", geoserver_gage_layer);
                                        data.append("geoserver_historical_flood_map_layer", geoserver_historical_flood_map_layer);
                                        data.append("geoserver_ahps_station_layer", geoserver_ahps_station_layer);
                                        for (var i = 0; i < gage_shp_files.length; i++) {
                                            data.append("gage_shp_file", gage_shp_files[i]);
                                        }
                                        xhr_gage = ajax_update_database_multiple_files("submit",
                                                                                        data,
                                                                                        "Gages Upload Success!",
                                                                                        "message_gages");
                                    }
                                    jQuery.when(xhr_gage).done(function(gage_data){
                                        if (gage_data != null && typeof gage_data != 'undefined') {
                                            if ('geoserver_gage_layer' in gage_data) {
                                                geoserver_gage_layer = gage_data['geoserver_gage_layer'];
                                            }
                                        }
                                        if (ahps_station_shp_files.length >= 4) {
                                            appendInfoMessage("Uploading AHPS Stations ...", "message_ahps_stations");
                                            var data = new FormData();
                                            data.append("watershed_id", watershed_id)
                                            data.append("watershed_name", watershed_name);
                                            data.append("subbasin_name", subbasin_name);
                                            data.append("data_store_id", data_store_id);
                                            data.append("ecmwf_data_store_watershed_name",ecmwf_data_store_watershed_name);
                                            data.append("ecmwf_data_store_subbasin_name",ecmwf_data_store_subbasin_name);
                                            data.append("geoserver_id", geoserver_id);
                                            data.append("geoserver_drainage_line_layer", geoserver_drainage_line_layer);
                                            data.append("geoserver_boundary_layer", geoserver_boundary_layer);
                                            data.append("geoserver_gage_layer", geoserver_gage_layer);
                                            data.append("geoserver_historical_flood_map_layer", geoserver_historical_flood_map_layer);
                                            data.append("geoserver_ahps_station_layer", geoserver_ahps_station_layer);
                                            for (var i = 0; i < ahps_station_shp_files.length; i++) {
                                                data.append("ahps_station_shp_file", ahps_station_shp_files[i]);
                                            }
                                            xhr_ahps_station = ajax_update_database_multiple_files("submit",
                                                                                                    data,
                                                                                                    "AHPS Stations Upload Success!",
                                                                                                    "message_ahps_stations");
                                        }
                                        jQuery.when(xhr_ahps_station).done(function(){
                                            //upload RAPID file if exists
                                            xhr_ecmwf_rapid = upload_AJAX_ECMWF_RAPID_input(watershed_id,
                                                                                            data_store_id);
                                            //when everything is finished
                                            jQuery.when(xhr, xhr_boundary, xhr_gage,
                                                        xhr_ahps_station, xhr_ecmwf_rapid)
                                                .done(function(xhr_data, xhr_boundary_data, xhr_gage_data,
                                                               xhr_ahps_station_data, xhr_ecmwf_rapid_data){
                                                //update the input boxes to reflect change
                                                getModalHTML(watershed_id, true);
                                            })
                                            .always(function () {
                                                submit_button.html(submit_button_html);
                                                m_uploading_data = false;
                                            });
                                        });
                                    });
                                });

                            });
                        } else {
                            appendErrorMessage("Need a drainage line to continue.", "error_form");
                        }
                    } else {
                        var data = {
                            watershed_id: watershed_id,
                            watershed_name: watershed_name,
                            subbasin_name: subbasin_name,
                            data_store_id: data_store_id,
                            ecmwf_data_store_watershed_name: ecmwf_data_store_watershed_name,
                            ecmwf_data_store_subbasin_name: ecmwf_data_store_subbasin_name,
                            geoserver_id: geoserver_id,
                            geoserver_drainage_line_layer: geoserver_drainage_line_layer,
                            geoserver_boundary_layer: geoserver_boundary_layer,
                            geoserver_gage_layer: geoserver_gage_layer,
                            geoserver_historical_flood_map_layer: geoserver_historical_flood_map_layer,
                            geoserver_ahps_station_layer: geoserver_ahps_station_layer,
                        };

                        var xhr_no_files = ajax_update_database("submit", data);

                        jQuery.when(xhr_no_files).done(function (data) {
                            if ('success' in data) {
                                //upload RAPID file if exists
                                xhr_ecmwf_rapid = upload_AJAX_ECMWF_RAPID_input(watershed_id,
                                    data_store_id);
    
                                jQuery.when(xhr, xhr_ecmwf_rapid).done(function () {
                                    //update the input boxes to reflect change
                                    getModalHTML(watershed_id, true);
                                });
                            } 
                        })
                        .always(function () {
                            submit_button.html(submit_button_html);
                            m_uploading_data = false;
                        });
                    }
                } //window confirm
            } else if (m_uploading_data) {
                appendWarningMessage("Submitting Data. Please Wait.", "please_wait");
            } else {
                appendErrorMessage(safe_to_submit.error, "error_form");
            }

        });
    };

    initializeTableFunctions = function() {
        $("#watershed_table").DataTable({
            destroy: true,
            columnDefs: [{
                orderable: false,
                targets: [0, 1]
            }],
            order: [[ 2, "asc" ]]
        });

        //handle the submit edit event
        $('.submit-edit-watershed').off().click(function () {
            getModalHTML($(this).parent().parent().parent().find('.watershed-name').data('watershed_id'));
        });


        //handle the submit update event
        $('.submit-delete-watershed').off().click(function () {
            var data = {
                watershed_id: $(this).parent().parent().parent().find('.watershed-name').data('watershed_id')
            };
            //update database
            var xhr = deleteRowData($(this), data, "main_message");
            if (xhr != null) {
                xhr.done(function (data) { 
                    getTablePage();
                });
            }
        });

    };

    getTablePage = function() {
        $.ajax({
            url: 'table',
            method: 'GET',
            success: function(data) {
                $("#manage_watersheds_table").html(data);
                initializeTableFunctions();
            }
        });
    };
    /************************************************************************
    *                  INITIALIZATION / CONSTRUCTOR
    *************************************************************************/
    
    $(function() {
        m_uploading_data = false;
        initializeTableFunctions();
        $('#edit_modal_submit').removeAttr('data-dismiss');
        $('#edit_watershed_modal').on('hidden.bs.modal', function () {
            $("#edit_watershed_modal").find('.modal-body').html('<p class="lead">Loading ...</p>');
            getTablePage();
        });
    }); //document ready
}()); // End of package wrapper 
