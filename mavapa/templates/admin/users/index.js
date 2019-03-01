function jqlisteners_users() {
    $(".user-import").unbind();
    $(".user-import").click(function(e) {
	e.preventDefault();
	var user = USER_FOUND[$(this).data('id')];
	var url = "{{ url_for('api_users') }}?email=" + user['mail'][0];
	$.ajax({
	    async: true,
	    url: url,
	    type: 'POST',
	    data: JSON.stringify({
		'email': user['mail'][0],
		'firstname': user['firstname'],
		'lastname': user['lastname'],
		'mobile': user['mobile'],
		'mailrecovery': user['mailrecovery'],
		'backend': user['backend']['id'],
		'admin': false,
	    }),
	    contentType: "application/json",
	    success: function(e) {
		var listdel = {'field': 'email', 'values': [user['mail'][0]] };
		$('#table-users-search').bootstrapTable('remove', listdel);
		$('#table-users').bootstrapTable('refresh');
	    }
	});
    });
    $("#user-add").unbind();
    $("#user-add").click(function(e){
	e.preventDefault();
	var modal = '#ModalUser';
	$(modal).modal('show');
    });
    $(".user-edit").unbind();
    $(".user-edit").click(function(e){
	e.preventDefault();
	var modal = '#ModalUser';
	var userid = $(this).data('id');
	$.ajax({
	    async: true,
	    url: "{{ url_for('api_users') }}?id=" + userid,
	    type: 'GET',
	    success: function(e) {
		var data = e['users'][0];
		var profile = '{{ url_for("profile") }}/' + data['id'];
		var display = data['lastname'] + ', ' + data['firstname'];
		$(modal).find('.modal-title').html(display);
		$(modal).find('#avatar').attr('src', data['avatar']);
		$(modal).find('#user-profile').attr('href', profile);
		$(modal).find('#user-form-basic-id').val(data['id']);
		$(modal).find('#user-form-basic-email').val(data['email']);
		$(modal).find('#user-form-basic-emailrecovery').val(data['mailrecovery']);
		$(modal).find('#user-form-basic-mobile').val(data['mobile']);
		$(modal).find('#user-form-basic-genre').selectpicker('val', data['genre']);
		$(modal).find('#user-form-basic-lang').selectpicker('val', data['lang']);
		$(modal).find('#user-form-basic-timezone').selectpicker('val', data['timezone']);
		$(modal).find('#user-form-settings-status').prop('checked', data['status']).change();
		$(modal).find('#user-form-settings-admin').prop('checked', data['admin']).change();
		$.ajax({
		    async: true,
		    url: "{{ url_for('api_backends') }}",
		    type: 'GET',
		    success: function(e2) {
			var backends = e2['backends']
			if (data['backend']) {
			    html = '<option value="0">Local</option>'
			} else {
			    html = '<option value="0" selected="selected">Local</option>'
			}
			for(i in backends) {
			    if (data['backend']['id'] == backends[i]['id']) {
				html += '<option selected="selected" '
				html += 'value="' + backends[i]['id'] + '">';
				html += backends[i]['name'] +'</option>';
			    } else {
				html += '<option value="' + backends[i]['id'];
				html += '">' + backends[i]['name'] + '</option>';
			    }
			}
			$(modal).find('#user-form-basic-backends').html(html);
			$(modal).find('#user-form-basic-backends').selectpicker('refresh');
		    }
		});
		$('#user-menu-context li[href="#user-form-basic"]').tab('show');
		$(modal).modal('show');
	    }
	});
    });
};

function UsersParams(params) {
    return params
};

function UsersResponseHandler(res) {
    var data = [];
    for(r in res.data) {
	var row = res.data[r];
	var doc = {
	    id: row.id,
	    displayname: row.displayname,
	    avatar: row.avatar,
	    backend: row.backend,
	    email: row.email,
	    created_at: row.created_at,
	    last_seen: row.last_seen,
	    admin: row.admin,
	    status: row.status,
	};
	data.push(doc);
    };
    console.log(data);
    return data;
    return {
	total: res.total,
	rows: data,
    }
};

function UsersFormatterName(value, row) {
    var html = ""
    html += '<img class="fa fa-fw img-circle" src="';
    html += row.avatar + '"/> ';
    html += row.displayname;
    if (! row.status) {
	html += '<i style="margin:0.5%" class="fa fa-fw fa-user-slash pull-right"></i>';
    }
    if (row.admin) {
	html += '<i style="margin:0.5%" class="fa fa-fw fa-user-shield pull-right"></i>';
    }
    return html;
};

function UsersFormatterBackend(value, row) {
    var html = ""
    html += '<i class="fa fa-fw fa-database"></i> ';
    if (row.backend) {
	html += row.backend.name;
    } else {
	html += 'Local';
    }
    return html;
};

function UsersFormatterActions(value, row) {
    var html = ""
    html += '<a class="user-edit" data-toggle="confirmation" ';
    html += 'data-id="' + row.id + '" href="#">';
    html += '<i class="fa fa-fw fa-pencil-alt"></i>';
    html += '</a>';
    return html;
};

function UsersFormatterDate(value, row) {
    return moment(Date.parse(value)).format("YYYY-MM-DD hh:mm");
};

function UsersFormatterDateAgo(value, row) {
    return moment(Date.parse(value)).fromNow();
};
