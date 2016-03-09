/*****************************************************************************
 * FILE:    manage_geoservers.js
 * AUTHOR:  Alan D. Snow, Curtis Rae, and Shawn Crawley
 * COPYRIGHT: © 2015-2016 Alan D. Snow, Curtis Rae, and Shawn Crawley. All rights reserved.
 * LICENSE: BSD 3-Clause
 *****************************************************************************/


/*****************************************************************************
 *                      LIBRARY WRAPPER
 *****************************************************************************/

var ERFP_MANAGE_GEOSERVERS = (function() {
    // Wrap the library in a package function
    "use strict"; // And enable strict mode for this library

    /************************************************************************
    *                      MODULE LEVEL / GLOBAL VARIABLES
    *************************************************************************/
    var m_uploading_data, m_results_per_page;

    /************************************************************************
     *                    PRIVATE FUNCTION DECLARATIONS
     *************************************************************************/
    var initializeTableFunctions, getTablePage, displayResultsText;


    /************************************************************************
     *                    PRIVATE FUNCTION IMPLEMENTATIONS
     *************************************************************************/

    m_results_per_page = 5;

    initializeTableFunctions = function() {

        //handle the submit update event
        $('.submit-update-geoserver').off().click(function(){
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
            var safe_to_submit = {val: true, error:""};
            var parent_row = $(this).parent().parent().parent();
            var geoserver_id = parent_row.find('.geoserver-id').text();
            var geoserver_name = checkTableCellInputWithError(parent_row.find('.geoserver-name'),safe_to_submit);
            var geoserver_url = checkTableCellInputWithError(parent_row.find('.geoserver-url'),safe_to_submit);
            var geoserver_username = checkTableCellInputWithError(parent_row.find('.geoserver-username'),safe_to_submit);
            var geoserver_password = checkTableCellInputWithError(parent_row.find('.geoserver-password-input'),safe_to_submit);

            var data = {
                    geoserver_id: geoserver_id,
                    geoserver_name: geoserver_name,
                    geoserver_url: geoserver_url,
                    geoserver_username: geoserver_username,
                    geoserver_password: geoserver_password,
                    };

            //update database
            var xhr = submitRowData($(this), data, safe_to_submit);
            if (xhr != null) {
                xhr.done(function (data) {
                    if ('success' in data) {
                        addSuccessMessage("Geoserver Update Success!");
                    }
                });
            }
        });

        //handle the submit delete event
        $('.submit-delete-geoserver').click(function(){
        var data = {
            geoserver_id: $(this).parent().parent().parent()
                                .find('.geoserver-id').text()
                };
            //update database
            var xhr = deleteRowData($(this), data);
            if (xhr != null) {
                xhr.done(function (data) {
                    if ('success' in data) {
                        addSuccessMessage("Geoserver Successfully Deleted!");
                        var num_geoservers_data = $('#manage_geoservers_table').data('num_geoservers');
                        var page = parseInt($('#manage_geoservers_table').data('page'));
                        $('#manage_geoservers_table').data('num_geoservers', Math.max(0, parseInt(num_geoservers_data) - 1));
                        if (parseInt($('#manage_geoservers_table').data('num_geoservers')) <= m_results_per_page * page) {
                            $('#manage_geoservers_table').data('page', Math.max(0, page - 1));
                        }
                        getTablePage();
                    }
                });
            }
        });

        displayResultsText();
        if (m_results_per_page >= $('#manage_geoservers_table').data('num_geoservers')) {
            $('[name="prev_button"]').addClass('hidden');
            $('[name="next_button"]').addClass('hidden');
        }

        //pagination next and previous button update
        $('[name="prev_button"]').click(function(){
            var page = parseInt($('#manage_geoservers_table').data('page'));
            $('#manage_geoservers_table').data('page', Math.max(0, page-1));
            getTablePage();
        });
        $('[name="next_button"]').click(function(){
            var page = parseInt($('#manage_geoservers_table').data('page'));
            $('#manage_geoservers_table').data('page', Math.min(page+1,
                                                Math.floor(parseInt($('#manage_geoservers_table').data('num_geoservers')) / m_results_per_page - 0.1)));
            getTablePage();
        });
    };


    displayResultsText = function() {
        //dynamically show table results display info text on page
        var page = parseInt($('#manage_geoservers_table').data('page'));
        var num_geoservers_data = $('#manage_geoservers_table').data('num_geoservers');
        var display_min;
        if (num_geoservers_data == 0){
            display_min = 0
        }
        else{
            display_min = ((page + 1) * m_results_per_page) - (m_results_per_page - 1);
        }
        var display_max = Math.min(num_geoservers_data, ((page + 1) * m_results_per_page));
        $('[name="prev_button"]').removeClass('hidden');
        $('[name="next_button"]').removeClass('hidden');
        if (page == 0){
            $('[name="prev_button"]').addClass('hidden');
        } else if (page == Math.floor(num_geoservers_data / m_results_per_page - 0.1)) {
            $('[name="next_button"]').addClass('hidden');
        }
        if (num_geoservers_data != 0) {
            $('#display-info').append('Displaying geoservers ' + display_min + ' - ' +
                display_max + ' of ' + num_geoservers_data);
        }else {
            $('#display-info').append('No geoservers to display' + '<br>To add one, ' +
                'click <a href="../add-geoserver">here</a>.');
        }
    };

    getTablePage = function() {
        $.ajax({
            url: 'table',
            method: 'GET',
            data: {'page': $('#manage_geoservers_table').data('page')},
            success: function(data) {
                $("#manage_geoservers_table").html(data);
                initializeTableFunctions();
            }
        });
    };


    /************************************************************************
    *                  INITIALIZATION / CONSTRUCTOR
    *************************************************************************/

    $(function() {
        m_uploading_data = false;
        getTablePage();
    }); //document ready
}()); // End of package wrapper