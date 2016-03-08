/*****************************************************************************
 * FILE:    main.js
 * AUTHOR:  Alan D. Snow
 * COPYRIGHT: © 2015-2016 Alan D Snow. All rights reserved.
 * LICENSE: BSD 2-Clause
 *****************************************************************************/

//get cookie
function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie != '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

//find if method is csrf safe
function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}

//add csrf token to appropriate ajax requests
$(function() {
    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", getCookie("csrftoken"));
            }
        }
    });
}); //document ready

//FUNCTION: Check shapefile inputs to make sure required files are attached
function checkShapefile(shapefile, safe_to_submit) {
    var required_extensions = ['shp', 'shx', 'prj','dbf'];
    var accepted_extensions = [];
    for (var i = 0; i < shapefile.length; ++i) {
        var file_extension = shapefile[i].name.split('.').pop();
        required_extensions.forEach(function(required_extension){
            if (file_extension == required_extension) {
                accepted_extensions.push(required_extension);
                required_extensions.splice(required_extensions.indexOf(required_extension),1);
            }
        });
    }
    if(accepted_extensions.length < 4) {
        safe_to_submit.val = false;
        safe_to_submit.error = "Problem with shapefile.";
        return false;
    }
    return true;
}

//FUNCTION: Check KML file inputs to make sure required file is there
function checkKMLfile(kml_file, safe_to_submit) {
    if(typeof kml_file == 'undefined') {
        safe_to_submit.val = false;
        safe_to_submit.error = "No KML file selected.";
        return false;
    }
    if("kml" != kml_file.name.split('.').pop()) {
        safe_to_submit.val = false;
        safe_to_submit.error = "Problem with KML file.";
        return false;
    }
    return true;
}

//form submission check function
function checkInputWithError(input, safe_to_submit, one_parent, select_two) {
    one_parent = typeof one_parent !== 'undefined' ? one_parent : false;
    select_two = typeof select_two !== 'undefined' ? select_two : false;

    if(select_two) {
        var data_value = input.select2("val");
    } else {
        var data_value = input.val();
    }

    if(one_parent){
        var parent = input.parent();
    } else {
        var parent = input.parent().parent();    
    }

    if(data_value) {
        parent.removeClass('has-error');
        parent.find('.help-block').addClass('hidden');
        if (typeof data_value == "string") {
            return data_value.trim();
        } else {
            return data_value;
        }
    } else {
        safe_to_submit.val = false;
        parent.addClass('has-error');
        parent.find('.help-block').removeClass('hidden');
        return null;
    }
}

//form submission check function
function checkTableCellInputWithError(input, safe_to_submit, error_msg) {
    var data_value = input.text();
    if(data_value == "") {
        data_value = input.val();
    }
    var parent = input.parent();

    if(data_value) {
        if (safe_to_submit.val) {
            parent.removeClass('danger');
        }
        return data_value.trim();
    } else {
        safe_to_submit.val = false;
        safe_to_submit.error = "Data missing in input";
        if (typeof error_msg != 'undefined' && error_msg != null) {
            safe_to_submit.error = error_msg;
        }
        parent.addClass('danger');
        return null;
    }
}

//add error message to #message div
function addErrorMessage(error, div_id) {
    var div_id_string = '#message';
    if (typeof div_id != 'undefined') {
        div_id_string = '#'+div_id;
    }
    $(div_id_string).html(
      '<span class="glyphicon glyphicon-exclamation-sign" aria-hidden="true"></span>' +
      '<span class="sr-only">Error:</span> ' + error
    )
    .removeClass('hidden')
    .removeClass('alert-success')
    .removeClass('alert-info')
    .removeClass('alert-warning')
    .addClass('alert')
    .addClass('alert-danger');
 
}

//add warning message to #message div
function addWarningMessage(error, div_id) {
    var div_id_string = '#message';
    if (typeof div_id != 'undefined') {
        div_id_string = '#'+div_id;
    }
    $(div_id_string).html(
      '<span class="glyphicon glyphicon-exclamation-sign" aria-hidden="true"></span>' +
      '<span class="sr-only">Warning:</span> ' + error
    )
    .removeClass('hidden')
    .removeClass('alert-success')
    .removeClass('alert-info')
    .removeClass('alert-danger')
    .addClass('alert')
    .addClass('alert-warning');
 
}

//add information message to #message div
function addInfoMessage(message, div_id) {
    var div_id_string = '#message';
    if (typeof div_id != 'undefined') {
        div_id_string = '#'+div_id;
    }
    $(div_id_string).html(
      '<span class="glyphicon glyphicon-info-sign" aria-hidden="true"></span>' +
      '<span class="sr-only">Info:</span> ' + message
    )
    .removeClass('hidden')
    .removeClass('alert-success')
    .removeClass('alert-danger')
    .removeClass('alert-warning')
    .addClass('alert')
    .addClass('alert-info');
 
}

//add success message to #message div
function addSuccessMessage(message, div_id) {
    var div_id_string = '#message';
    if (typeof div_id != 'undefined') {
        div_id_string = '#'+div_id;
    }
    $(div_id_string).html(
      '<span class="glyphicon glyphicon-ok-circle" aria-hidden="true"></span>' +
      '<span class="sr-only">Sucess:</span> ' + message
    ).removeClass('hidden')
    .removeClass('alert-danger')
    .removeClass('alert-info')
    .removeClass('alert-warning')
    .addClass('alert')
    .addClass('alert-success');
}

//add error message to #message div
function appendErrorMessage(message, div_id, message_div_id) {
    var div_id_string = '';
    if (typeof div_id != 'undefined') {
        div_id_string = 'id = "'+div_id+'"';
    }
    var message_div_id_string = '#message';
    if (typeof message_div_id != 'undefined') {
        message_div_id_string = '#'+message_div_id;
    }
    $('#'+div_id).remove();
    $(message_div_id_string).append(
      '<div '+ div_id_string +' class="alert alert-danger alert-dissmissible" role="alert">' +
      '<button type="button" class="close" data-dismiss="alert" aria-label="Close">' +
      '<span aria-hidden="true">&times;</span></button>' +
      '<span class="glyphicon glyphicon-fire" aria-hidden="true"></span>' +
      '<span class="sr-only">Error:</span> ' + message + '</div>'
    )
    .removeClass('hidden');
}

//add error message to #message div
function appendWarningMessage(message, div_id, message_div_id) {
    var div_id_string = '';
    if (typeof div_id != 'undefined') {
        div_id_string = 'id = "'+div_id+'"';
    }
    var message_div_id_string = '#message';
    if (typeof message_div_id != 'undefined') {
        message_div_id_string = '#'+message_div_id;
    }
    $('#'+div_id).remove();
    $(message_div_id_string).append(
      '<div '+ div_id_string +' class="alert alert-warning alert-dissmissible" role="alert">' +
      '<button type="button" class="close" data-dismiss="alert" aria-label="Close">' +
      '<span aria-hidden="true">&times;</span></button>' +
      '<span class="glyphicon glyphicon-exclamation-sign" aria-hidden="true"></span>' +
      '<span class="sr-only">Error:</span> ' + message + '</div>'
    )
    .removeClass('hidden');
}

//add info message to #message div
function appendInfoMessage(message, div_id) {
    var div_id_string = '';
    if (typeof div_id != 'undefined') {
        div_id_string = 'id = "'+div_id+'"';
    }
    $('#message').append(
      '<div '+ div_id_string +' class="alert alert-info alert-dissmissible" role="alert">' +
      '<button type="button" class="close" data-dismiss="alert" aria-label="Close">' +
      '<span aria-hidden="true">&times;</span></button>' +
      '<span class="glyphicon glyphicon-info-sign" aria-hidden="true"></span>' +
      '<span class="sr-only">Info:</span> ' + message + '</div>'
    )
    .removeClass('hidden');
}

//add success message to #message div
function appendSuccessMessage(message, div_id) {
    var div_id_string = '';
    if (typeof div_id != 'undefined') {
        div_id_string = 'id = "'+div_id+'"';
    }
    $('#message').append(
      '<div '+ div_id_string +' class="alert alert-success" role="alert">' +
      '<br><span class="glyphicon glyphicon-ok-circle" aria-hidden="true"></span>' +
      '<span class="sr-only">Sucess:</span> ' + message + '</div>'
    )
    .removeClass('hidden');
}

//send data to database with error messages
function ajax_update_database(ajax_url, ajax_data, div_id) {
    //backslash at end of url is requred
    if (ajax_url.substr(-1) !== "/") {
        ajax_url = ajax_url.concat("/");
    }
    //update database
    var xhr = jQuery.ajax({
        type: "POST",
        url: ajax_url,
        dataType: "json",
        data: ajax_data
    });
    xhr.done(function(data) {
        if("success" in data) {
            appendSuccessMessage(data['success'], div_id);
        } else {
            addWarningMessage("Submission failed");
            appendErrorMessage(data['error'], div_id);
        }
    }) 
    .fail(function(xhr, status, error) {
        addWarningMessage("Submission failed");
        appendErrorMessage(error, div_id);
        console.log(xhr.responseText);
    });

    return xhr;
}

//ajax file submit
//send data to database with error messages
function ajax_update_database_with_file(ajax_url, ajax_data, div_id) {
    //backslash at end of url is required
    if (ajax_url.substr(-1) !== "/") {
        ajax_url = ajax_url.concat("/");
    }
    //update database
    var xhr = jQuery.ajax({
        url: ajax_url,
        type: "POST",
        data: ajax_data,
        dataType: "json",
        processData: false, // Don't process the files
        contentType: false // Set content type to false as jQuery will tell the server its a query string request
    });
    xhr.done(function(data) {
        if("success" in data) {
            addSuccessMessage(data['success'], div_id);
        } else {
            addWarningMessage("Submission failed");
            appendErrorMessage(data['error'], div_id);
        }
    })
    .fail(function(xhr, status, error) {
            addWarningMessage("Submission failed");
            appendErrorMessage(error, div_id);
            console.log(xhr.responseText);
    });
    return xhr;
}

//send data to database with error messages
function ajax_update_database_multiple_files(ajax_url, ajax_data, custom_message, div_id) {
    //backslash at end of url is required
    if (ajax_url.substr(-1) !== "/") {
        ajax_url = ajax_url.concat("/");
    }
    //update database
    var xhr = jQuery.ajax({
        url: ajax_url,
        type: "POST",
        data: ajax_data,
        dataType: "json",
        processData: false, // Don't process the files
        contentType: false, // Set content type to false as jQuery will tell the server it's a query string request
    });
    xhr.done(function(data){
        if("success" in data) {
            addSuccessMessage(custom_message, div_id);
        } else {
            addWarningMessage("Submission failed");
            appendErrorMessage(data['error'], div_id);
        }
    })
    .fail(function(xhr, status, error) {
        addWarningMessage("Submission failed");
        appendErrorMessage(error, div_id);
        console.log(xhr.responseText);
    });
    return xhr;
}

//FUNCTION: AJAX upload of ECMWF RAPID Input
function upload_AJAX_ECMWF_RAPID_input(watershed_id, data_store_id) {
    var xhr_ecmwf_rapid = null;
    var ecmwf_rapid_input_file = null;
    if(data_store_id>1) {
        ecmwf_rapid_input_file = $('#ecmwf-rapid-files-upload-input')[0].files[0];
        if(ecmwf_rapid_input_file != null) {
            appendInfoMessage("Uploading ECMWF RAPID Input Data ...",
                              "message_ecmwf_rapid_input");
            var data = new FormData();
            data.append("watershed_id", watershed_id);
            data.append("ecmwf_rapid_input_file",ecmwf_rapid_input_file);
            xhr_ecmwf_rapid = ajax_update_database_multiple_files("upload_ecmwf_rapid",
                                                                  data,
                                                                  "ECMWF RAPID Input Upload Success!",
                                                                  "message_ecmwf_rapid_input");
            //clear input
            xhr_ecmwf_rapid.done(function() {
                $('#ecmwf-rapid-files-upload-input').val('');
            });
        }
    }
    return xhr_ecmwf_rapid
}

//submit row data
function submitRowData(submit_button, data, safe_to_submit) {
    if(safe_to_submit.val) {
        //give user information
        addInfoMessage("Submitting Data. Please Wait.");
        var submit_button_html = submit_button.html();
        submit_button.text('Submitting ...');
        var xhr = ajax_update_database("submit",data);
        xhr.always(function(){
            submit_button.html(submit_button_html);
        });
        return xhr;
    } else {
        addWarningMessage("Submission failed");
        appendErrorMessage(safe_to_submit.error);
        return null;
    }
}

//delete row data
function deleteRowData(submit_button, data, div_id) {
    if (window.confirm("Are you sure?")) {
        var parent_row = submit_button.parent().parent().parent();
        if (typeof div_id == 'undefined') {
            div_id = 'message';
        }
        //give user information
        addInfoMessage("Deleting Data. Please Wait.", div_id);
        var submit_button_html = submit_button.html();
        submit_button.text('Deleting ...');
    
        var xhr = ajax_update_database("delete",data);
        xhr.done(function(data) {
            if ('success' in data) {
                parent_row.remove();
                addSuccessMessage(data['success'], div_id);
            }
        })
        .fail(function(xhr, status, error) {
            addErrorMessage(error, div_id);
        })
        .always(function(){
            submit_button.html(submit_button_html);
        });
        return xhr;
    }
    return null;
}