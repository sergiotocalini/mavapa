function jqlisteners_modal_person() {
    $("#table-org-people a[data-click=person-open]").unbind()
    $("#table-org-people a[data-click=person-open]").on("click", function(a) {
	a.preventDefault();
	var backend = $(this).data('backend');
	var dn = $(this).data('dn');
	var modal = '#ModalPerson';
	$.ajax({
	    url: "{{ url_for('api_backends_items') }}",
	    type: 'GET',
	    contentType: "application/json",
	    data: { dn: dn, backend: backend },
	    success: function(e) {
		var user = e['data'] ? e['data'][0] : ['', {}];
		var display = user[1]['displayName'] ? user[1]['displayName'][0] : user[0];
		var avatar = "{{ config['CDN_LOCAL'] }}/img/avatar.jpg";
		if (user[1]['jpegPhoto']) {
		    avatar = "data:image/jpg;base64," + user[1]['jpegPhoto'][0];
		} else if (user[1]['photo']) {
		    avatar = "data:image/jpg;base64," + user[1]['Photo'][0];
		}
		$(modal).find('.modal-title').html('<i class="fa fa-fw fa-address-card"></i> ' + display);
		$(modal).find('#person-form-basic-avatar').attr('src', avatar);
		$(modal).find('#person-form-basic-dn').val(user[0]);
		$(modal).find('#person-form-basic-backend').val(backend);
		$(modal).find('#person-form-basic-uid').val(user[1]['uid'][0]);
		$(modal).find('#person-form-basic-lastname').val(user[1]['sn'] ? user[1]['sn'][0] : null);
		$(modal).find('#person-form-basic-firstname').val(user[1]['givenName'] ? user[1]['givenName'][0] : null);
		$(modal).find('#person-form-basic-email').val(user[1]['mail'][0]);
		$(modal).find('#person-form-basic-displayname').val(user[1]['displayName'] ? user[1]['displayName'][0] : null);
		$(modal).find('#person-form-basic-mobile').val(user[1]['mobile'] ? user[1]['mobile'][0] : null);
		$(modal).find('#person-form-basic-title').val(user[1]['title'] ? user[1]['title'][0] : null);
		$(modal).find('#person-form-terminal-homeDirectory').val(user[1]['homeDirectory'] ? user[1]['homeDirectory'][0] : null);
		$(modal).find('#person-form-terminal-uidNumber').val(user[1]['uidNumber'] ? user[1]['uidNumber'][0] : null);
		$(modal).find('#person-form-terminal-gidNumber').val(user[1]['gidNumber'] ? user[1]['gidNumber'][0] : null);
		$(modal).find('#person-form-terminal-homeDirectory').val(user[1]['homeDirectory'] ? user[1]['homeDirectory'][0] : null);
		$(modal).find('#person-form-terminal-gecos').val(user[1]['gecos'] ? user[1]['gecos'][0] : null);
		$(modal).find('#person-form-terminal-loginShell').selectpicker(
		    'val', user[1]['loginShell'] ? user[1]['loginShell'][0] : '/bin/bash'
		);
		$('#person-menu-context li[href="#person-form-basic"]').tab('show');
		$(modal).modal('show');
	    }	
	});
    });
    $("#person-save").unbind();
    $("#person-save").click(function(){
	var table = '#table-org-people';
	var modal = '#ModalPerson';
	var params = {
	    dn: $(modal).find('#person-form-basic-dn').val(),
	    backend: $(modal).find('#person-form-basic-backend').val(),
	}
	console.log(params);
	$.ajax({
	    url: "{{ url_for('api_backends_items') }}?" + $.param(params),
	    type: 'PUT',
	    contentType: "application/json",
	    dataType: "json",
	    data: JSON.stringify({
		loginShell: $(modal).find('#person-form-terminal-loginShell').val(),
		homeDirectory: $(modal).find('#person-form-terminal-homeDirectory').val(),
		uid: $(modal).find('#person-form-basic-uid').val(),
		uidNumber: $(modal).find('#person-form-terminal-uidNumber').val(),
		gidNumber: $(modal).find('#person-form-terminal-gidNumber').val(),
		gecos: $(modal).find('#person-form-terminal-gecos').val(),
		mail: $(modal).find('#person-form-basic-email').val(),
		title: $(modal).find('#person-form-basic-title').val(),
		displayName: $(modal).find('#person-form-basic-displayname').val(),
		mobile: $(modal).find('#person-form-basic-mobile').val(),
		sn: $(modal).find('#person-form-basic-lastname').val(),
		givenName: $(modal).find('#person-form-basic-firstname').val(),
	    }),
	    success: function(e) {
		$(modal).modal('hide');
		$(table).bootstrapTable('refresh');
	    }
	});
    });
};

