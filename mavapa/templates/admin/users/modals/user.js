$(document).ready(function () {
    $('#user-menu-context li[href="#user-form-backend"]').on('shown.bs.tab', function (e) {
	console.log("y ahora??");
    });
});

function jqlisteners_modal_user() {
    $("#user-update").unbind();
    $("#user-update").click(function() {
	var table = '#table-users';
	var modal = '#ModalUser';
	var userid = $(modal).find('#userid').val();
	var mailrecovery = $(modal).find('#recovery').val();
	var mobile = $(modal).find('#mobile').val();
	var genre = $(modal).find('#genre').val();
	var admin = $(modal).find('#user-form-basic-admin').prop('checked');
	var backend = $(modal).find('#backends').val();
	var lang = $(modal).find('#lang').val();
	var timezone = $(modal).find('#timezone').val();
	var url = "{{ url_for('api_users') }}?id=" + userid;
	$.ajax({
	    url: url,
	    type: 'POST',
	    data: JSON.stringify(
		{
		    'mailrecovery': mailrecovery,
		    'mobile': mobile,
		    'genre': genre,
		    'backend': backend,
		    'admin': admin,
		    'lang': lang,
		    'timezone': timezone,
		}
	    ),
	    contentType: "application/json",
	    success: function(e) {
		$(table).bootstrapTable('refresh');
		$(modal).modal('hide');
	    }
	});	    
    });
};
