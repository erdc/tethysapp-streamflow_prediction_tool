//initialize help blockss
var help_html = '<p class="help-block hidden">No watershed group name specified.</p>';
$('#watershed-group-name-input').parent().parent().append(help_html);
help_html = '<p class="help-block hidden">No watersheds selected.</p>';
$('#watershed_select').parent().append(help_html);

//handle the submit event
$('#submit-add-watershed-group').click(function(){
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
    var watershed_group_name = checkInputWithError($('#watershed-group-name-input'),safe_to_submit);
    var watershed_group_watershed_ids = checkInputWithError($('#watershed_select'),safe_to_submit, true);
    if(safe_to_submit.val) {
        var submit_button = $(this);
        var submit_button_html = submit_button.html();
        //give user information
        addInfoMessage("Submitting Data. Please Wait.");
        submit_button.text('Submitting ...');
        //update database
        data = {
                'watershed_group_name': watershed_group_name,
                'watershed_group_watershed_ids': watershed_group_watershed_ids,
                };

        var xhr = ajax_update_database("submit",data);
        xhr.done(function(data) {
            if ('success' in data) {
                //reset inputs
                $('#watershed-group-name-input').val('');
                $('[name="watershed_select"]').select2('val','');
                addSuccessMessage("Watershed Group Update Complete!");
            }
        })
        .always(function() {
            submit_button.html(submit_button_html);
        });

    }

});