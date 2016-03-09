/*****************************************************************************
 * FILE:    add_data_store.js
 * AUTHOR:  Alan D. Snow
 * COPYRIGHT: © 2015-2016 Alan D Snow. All rights reserved.
 * LICENSE: BSD 3-Clause
 *****************************************************************************/

//initialize help blockss
var help_html = '<p class="help-block hidden">No data store name specified.</p>';
$('#data-store-name-input').parent().parent().append(help_html);
help_html = '<p class="help-block hidden">No data store type specified.</p>';
$('#data-store-type-select').parent().append(help_html);
help_html = '<p class="help-block hidden">No datastore API endpoint specified.</p>';
$('#data-store-endpoint-input').parent().parent().append(help_html);
help_html = '<p id="endpoint-error" class="help-block hidden">Endpoint must end in "api/3/action"</p>';
$('#data-store-endpoint-input').parent().parent().append(help_html);
help_html = '<p class="help-block hidden">No API key specified.</p>';
$('#data-store-api-key-input').parent().parent().append(help_html);

//handle the submit event
$('#submit-add-data-store').click(function(){
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
    var safe_to_submit = {val: true};
    var data_store_name = checkInputWithError($('#data-store-name-input'),safe_to_submit);
    var data_store_type_id = checkInputWithError($('#data-store-type-select'),safe_to_submit, true);
    var data_store_endpoint = checkInputWithError($('#data-store-endpoint-input'),safe_to_submit);
    var data_store_api_key = checkInputWithError($('#data-store-api-key-input'),safe_to_submit);

    if(safe_to_submit.val) {
        var submit_button = $(this);
        var submit_button_html = submit_button.html();
        //give user information
        addInfoMessage("Submitting Data. Please Wait.");
        submit_button.text('Submitting ...');
        //update database
        data = {
                data_store_name: data_store_name,
                data_store_type_id: data_store_type_id,
                data_store_endpoint: data_store_endpoint,
                data_store_api_key: data_store_api_key
                };

        var xhr = ajax_update_database("submit",data);
        xhr.done(function(data) {
            if ('success' in data) {
                //reset inputs
                $('#data-store-name-input').val('');
                $('#data-store-type-select').select2('val','2');
                $('#data-store-endpoint-input').val('');
                $('#data-store-api-key-input').val('');
                addSuccessMessage("Data Store Successfully Added!");
            }
        })
        .always(function() {
            submit_button.html(submit_button_html);
        });
    }
});

$('#data-store-endpoint-input').change(function() {
    if ($(this).val() == "") {
        $("#endpoint-error").addClass('hidden');
    }
    else if ($(this).val().slice(-12) != "api/3/action") {
        $("#endpoint-error").removeClass('hidden');
    }
    else {
        $("#endpoint-error").addClass('hidden');
    }
});