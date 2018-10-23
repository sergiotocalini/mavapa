function jqlisteners_modal_backend() {
    $("#backend-update").unbind();
    $("#backend-update").click(function(){
	var modal = '#ModalBackend';
	var id = $(modal).find('#backend_id').val();
	console.log(id);
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
		{'name': $(modal).find('#name').val(),
		 'host': $(modal).find('#host').val(),
		 'type': $(modal).find('#type').val(),
		 'timeout':$(modal).find('#timeout').val(),
		 'binddn':$(modal).find('#account').val(),
		 'bindpw':$(modal).find('#password').val(),
		 'basedn':$(modal).find('#search').val(),
		 'filter':$(modal).find('#filter').val(),
		}
	    ),
	    contentType: "application/json",
	    success: function(e) {
		$(modal).modal('hide');
	    }
	});
    });
};
