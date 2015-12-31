/*****************************************************************************
 * FILE:    manage_watershed_groups.js
 * AUTHOR:  Alan Snow
 * COPYRIGHT: © 2015 Alan D Snow. All rights reserved.
 * LICENSE: BSD 2-Clause
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

        $(".watershed-select").each(function() {
            $(this).select2({placeholder: "Add Watershed to Group", width: '100%'});
        });

        //handle the submit update event
        $('.submit-update-watershed-group').off().click(function(){
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
            var watershed_group_watershed_ids = checkInputWithError(parent_row.find('.watershed-select'),safe_to_submit, true, true);

            var data = {
                    watershed_group_id: watershed_group_id,
                    watershed_group_name: watershed_group_name,
                    watershed_group_watershed_ids: watershed_group_watershed_ids
                    };
            //update database
            var xhr = submitRowData($(this), data, safe_to_submit);
            xhr.done(function(data){
                if ('success' in data) {
                    addSuccessMessage("Watershed Group Update Complete!");
                }
            });
        });

        //handle the submit delete event
        $('.submit-delete-watershed-group').off().click(function(){
            var data = {
                watershed_group_id: $(this).parent().parent().parent().find('.watershed-group-id').text()
            };
            //update database
            var xhr = deleteRowData($(this), data);
            if (xhr != null) {
                xhr.done(function (data) {
                    if ('success' in data) {
                        var num_watershed_groups_data = $('#manage_watershed_groups_table').data('num_watershed_groups');
                        var page = parseInt($('#manage_watershed_groups_table').data('page'));
                        $('#manage_watershed_groups_table').data('num_watershed_groups', Math.max(0, parseInt(num_watershed_groups_data) - 1));
                        if (parseInt($('#manage_watershed_groups_table').data('num_watershed_groups')) <= m_results_per_page * page) {
                            $('#manage_watershed_groups_table').data('page', Math.max(0, page - 1));
                        }
                        addSuccessMessage("Watershed Group Successfully Deleted!");
                        getTablePage();
                    }
                });
            }
        });

        displayResultsText();
        if (m_results_per_page >= $('#manage_watershed_groups_table').data('num_watershed_groups')) {
            $('[name="prev_button"]').addClass('hidden');
            $('[name="next_button"]').addClass('hidden');
        }

        //pagination next and previous button update
        $('[name="prev_button"]').click(function(){
            var page = parseInt($('#manage_watershed_groups_table').data('page'));
            $('#manage_watershed_groups_table').data('page', Math.max(0, page-1));
            getTablePage();
        });
        $('[name="next_button"]').click(function(){
            var page = parseInt($('#manage_watershed_groups_table').data('page'));
            $('#manage_watershed_groups_table').data('page', Math.min(page+1,
                                                Math.floor(parseInt($('#manage_watershed_groups_table').data('num_watershed_groups')) / m_results_per_page - 0.1)));
            getTablePage();
        });
    };


    displayResultsText = function() {
        //dynamically show table results display info text on page
        var page = parseInt($('#manage_watershed_groups_table').data('page'));
        var num_watershed_groups_data = $('#manage_watershed_groups_table').data('num_watershed_groups');
        var display_min;
        if (num_watershed_groups_data == 0){
            display_min = 0
        }
        else{
            display_min = ((page + 1) * m_results_per_page) - (m_results_per_page - 1);
        }
        var display_max = Math.min(num_watershed_groups_data, ((page + 1) * m_results_per_page));
        $('[name="prev_button"]').removeClass('hidden');
        $('[name="next_button"]').removeClass('hidden');
        if (page == 0){
            $('[name="prev_button"]').addClass('hidden');
        } else if (page == Math.floor(num_watershed_groups_data / m_results_per_page - 0.1)) {
            $('[name="next_button"]').addClass('hidden');
        }
        if (num_watershed_groups_data != 0) {
            $('#display-info').append('Displaying watershed groups ' + display_min + ' - ' +
                display_max + ' of ' + num_watershed_groups_data);
        }else {
            $('#display-info').append('No watershed groups to display' + '<br>To add one, ' +
                'click <a href="../add-watershed-group">here</a>.');
        }
    };

    getTablePage = function() {
        $.ajax({
            url: 'table',
            method: 'GET',
            data: {'page': $('#manage_watershed_groups_table').data('page')},
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
        getTablePage();
    }); //document ready
}()); // End of package wrapper