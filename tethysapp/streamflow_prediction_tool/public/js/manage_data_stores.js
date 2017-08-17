/*****************************************************************************
 * FILE:    manage_data_stores.js
 * AUTHOR:  Alan D. Snow, Curtis Rae, and Shawn Crawley
 * COPYRIGHT: © 2015-2016 Alan D. Snow, Curtis Rae, and Shawn Crawley. All rights reserved.
 * LICENSE: BSD 3-Clause
 *****************************************************************************/


/*****************************************************************************
 *                      LIBRARY WRAPPER
 *****************************************************************************/

var ERFP_MANAGE_DATA_STORES = (function() {
    // Wrap the library in a package function
    "use strict"; // And enable strict mode for this library

    /************************************************************************
    *                      MODULE LEVEL / GLOBAL VARIABLES
    *************************************************************************/
    var m_uploading_data;

    /************************************************************************
     *                    PRIVATE FUNCTION DECLARATIONS
     *************************************************************************/
    var initializeTableFunctions, getTablePage;


    /************************************************************************
     *                    PRIVATE FUNCTION IMPLEMENTATIONS
     *************************************************************************/
    initializeTableFunctions = function() {
        $("#data_store_table").off();

        $("#data_store_table").DataTable({
            destroy: true,
            columnDefs: [{
                orderable: false,
                targets: [0, 1]
            }],
            order: [[ 3, "asc" ]]
        });

        //handle the submit update event
        $('#data_store_table').on("click", ".submit-update-data-store", function(){
            //clear messages
            $('#message').addClass('hidden');
            $('#message').empty()
                .addClass('hidden')
                .removeClass('alert-success')
                .removeClass('alert-info')
                .removeClass('alert-warning')
                .removeClass('alert-danger');
            var parent_row = $(this).parent().parent().parent();
            //check data store input
            var safe_to_submit = {val: true, error:""};
            var data_store_id = parent_row.find('.data-store-id').text();
            var data_store_name = checkTableCellInputWithError(parent_row.find('.data-store-name'),safe_to_submit);
            var data_store_owner_org = checkTableCellInputWithError(parent_row.find('.data-store-owner_org'),safe_to_submit);
            var data_store_api_endpoint = checkTableCellInputWithError(parent_row.find('.data-store-api-endpoint'),safe_to_submit);
            var data_store_api_key = checkTableCellInputWithError(parent_row.find('.data-store-api-key-input'),safe_to_submit);
        
            var data = {
                    data_store_id: data_store_id,
                    data_store_name: data_store_name,
                    data_store_api_endpoint: data_store_api_endpoint,
                    data_store_api_key: data_store_api_key,
                    data_store_owner_org: data_store_owner_org,
                    };
            //update database
            var xhr = submitRowData($(this), data, safe_to_submit); 
            xhr.done(function(data) {
                addSuccessMessage("Data Store Successfully Updated!");
            });
        });
        
        //handle the submit delete event
        $('#data_store_table').on("click", '.submit-delete-data-store', function(){
            var data = {
                    data_store_id: $(this).parent().parent().parent()
                                    .find('.data-store-id').text(),
                    };
            //update database
            var xhr = deleteRowData($(this), data);
            if (xhr != null) {
                xhr.done(function (data) {
                    getTablePage();
                    addSuccessMessage("Data Store Successfully Deleted!");
                });
            }
        });

    };


    getTablePage = function() {
        $.ajax({
            url: 'table',
            method: 'GET',
            success: function(data) {
                $("#manage_data_stores_table").html(data);
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
    }); //document ready
}()); // End of package wrapper