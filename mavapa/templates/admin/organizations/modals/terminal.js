function jqlisteners_modal_terminal() {
    $("#terminal-save").unbind();
    $("#terminal-save").click(function(){
	var table = '#table-org-terminal';
	var modal = '#ModalTerminal';
	var params = {
	    dn: $(modal).find('#terminal-dn').val(),
	    backend: $(modal).find('#terminal-backend').val(),
	}
	var data = {
	    loginShell: $(modal).find('#terminal-loginShell').val(),
	    homeDirectory: $(modal).find('#terminal-homeDirectory').val(),
	    uid: $(modal).find('#terminal-uid').val(),
	    uidNumber: $(modal).find('#terminal-uidNumber').val(),
	    gidNumber: $(modal).find('#terminal-gidNumber').val(),
	    gecos: $(modal).find('#terminal-gecos').val(),
	}
	$.ajax({
	    url: "{{ url_for('api_backends_items') }}?" + $.param(params),
	    type: 'PUT',
	    contentType: "application/json",
	    dataType: "json",
	    data: JSON.stringify(data),
	    success: function(e) {
		$(modal).modal('hide');
		$(table).bootstrapTable('refresh');
	    }
	});
    });
};
