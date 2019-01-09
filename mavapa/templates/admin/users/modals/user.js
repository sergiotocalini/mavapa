
function jqlisteners_modal_user() {
    $("#user-update").unbind();
    $("#user-update").click(function() {
	var table = '#table-users';
	var modal = '#ModalUser';
	var userid   = $(modal).find('#user-form-basic-id').val();
	var mrecover = $(modal).find('#user-form-basic-mailrecovery').val();
	var mobile   = $(modal).find('#user-form-basic-mobile').val();
	var genre    = $(modal).find('#user-form-basic-genre').val();
	var backend  = $(modal).find('#user-form-basic-backends').val();
	var locale   = $(modal).find('#user-form-basic-lang').val();
	var timezone = $(modal).find('#user-form-basic-timezone').val();
	var admin    = $(modal).find('#user-form-settings-admin').prop('checked');
	var status   = $(modal).find('#user-form-settings-status').prop('checked');
	$.ajax({
	    url: "{{ url_for('api_users') }}?id=" + userid,
	    type: 'POST',
	    data: JSON.stringify({
		'mailrecovery': mrecover,
		'mobile': mobile,
		'genre': genre,
		'backend': backend,
		'admin': admin,
		'lang': locale,
		'timezone': timezone,
		'status': status,
	    }),
	    contentType: "application/json",
	    success: function(e) {
		$(table).bootstrapTable('refresh');
		$(modal).modal('hide');
	    }
	});	    
    });
};

function UserBackendFormatterValue(value, row) {
    var html = ""
    html += '<div class="text-ellipsis">'
    html +=  '<span>' + value + '</span>';
    html += '</div>'
    return html;
};
