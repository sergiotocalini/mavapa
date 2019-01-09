function jqlisteners_modal_backend() {
    $("#backend-save").unbind();
    $("#backend-save").click(function(){
	var modal = '#ModalBackend';
	var id = $(modal).find('#backend-id').val();
	if ( typeof id === 'undefined' || id === null) {
	    var url = "{{ url_for('api_backends') }}";
	} else {
	    var url = "{{ url_for('api_backends') }}?id=" + id;
	}
	$.ajax({
	    async: false,
	    url: url,
	    type: 'POST',
	    data: JSON.stringify(
		{'name': $(modal).find('#backend-name').val(),
		 'host': $(modal).find('#backend-url').val(),
		 'type': $(modal).find('#backend-type').val(),
		 'timeout':$(modal).find('#backend-timeout').val(),
		 'binddn':$(modal).find('#backend-username').val(),
		 'bindpw':$(modal).find('#backend-password').val(),
		 'basedn':$(modal).find('#backend-search').val(),
		 'filter':$(modal).find('#backend-filter').val(),
		 'login': $(modal).find('#backend-attribute').val(),
		 'onfly': $(modal).find('#backend-onfly').prop('checked')
		}
	    ),
	    contentType: "application/json",
	    success: function(e) {
		$(modal).modal('hide');
	    }
	});
    });
};
