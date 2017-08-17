/*****************************************************************************
 * FILE:    manage_watershed_groups.js
 * AUTHOR:  Alan D. Snow
 * COPYRIGHT: © 2015-2016 Alan D Snow. All rights reserved.
 * LICENSE: BSD 3-Clause
 *****************************************************************************/

/*****************************************************************************
 *                      LIBRARY WRAPPER
 *****************************************************************************/

var ERFP_MANAGE_WATERSHED_GROUPS = (function() {
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
        $("#watershed_groups_table").off();

        $("#watershed_groups_table").DataTable({
            destroy: true,
            columnDefs: [{
                orderable: false,
                targets: [0, 1]
            }],
            order: [[ 3, "asc" ]]
        });

        $(".watershed-select").each(function() {
            $(this).select2({placeholder: "Add Watershed to Group", width: '100%'});
        });

        //handle the submit update event
        $('#watershed_groups_table').on("click", '.submit-update-watershed-group', function(){
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
            var safe_to_submit = {val: true, error:""};
            var parent_row = $(this).parent().parent().parent();
            //check data store input
            var watershed_group_id = parent_row.find('.watershed-group-id').text();
            var watershed_group_name = checkTableCellInputWithError(parent_row.find('.watershed-group-name'),safe_to_submit);
            var watershed_group_watershed_ids = checkInputWithError(parent_row.find('select.watershed-select'),safe_to_submit, true, true);

            var data = {
                watershed_group_id: watershed_group_id,
                watershed_group_name: watershed_group_name,
                watershed_group_watershed_ids: watershed_group_watershed_ids
            };
            //update database
            var xhr = submitRowData($(this), data, safe_to_submit);
            if (xhr != null) {
                xhr.done(function(data){
                    addSuccessMessage("Watershed Group Update Complete!");
                });
            }
        });

        //handle the submit delete event
        $('#watershed_groups_table').on("click", '.submit-delete-watershed-group', function(){
            var data = {
                watershed_group_id: $(this).parent().parent().parent().find('.watershed-group-id').text()
            };
            //update database
            var xhr = deleteRowData($(this), data);
            if (xhr != null) {
                xhr.done(function (data) {
                    addSuccessMessage("Watershed Group Successfully Deleted!");
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
                $("#manage_watershed_groups_table").html(data);
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