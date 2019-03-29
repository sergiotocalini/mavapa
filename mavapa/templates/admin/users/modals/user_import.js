var USER_FOUND = [];
function user_search() {
    var table = '#table-users-search';
    var mail = document.forms["toolbar-user-search"]["mail"].value;
    var url = "{{ url_for('api_backends_search_users') }}?email=*" + mail + "*&only=noexist"
    $.ajax({
    	async: true,
    	url: url,
    	type: 'GET',
    	success: function(e) {
	    USER_FOUND = e['data'];
	    var table = '#table-users-search';
	    $(table).bootstrapTable('showLoading');
	    $(table).bootstrapTable('removeAll');
	    for(i in e['data']) {
		var user = e['data'][i];
		console.log(user);
		html = '<a class="user-import" data-id="' + i + '">';
                html+= '<i class="fa fa-fw fa-plus"></i>';
                html+= '</a>';
		$(table).bootstrapTable('append', {
		    'firstname': user[1]['givenName'],
		    'lastname': user[1]['sn'],
		    'name': user[1]['sn'] + ', ' + user[1]['givenName'],
		    'email': user[1]['mail'][0],
		    'backend': user[1]['backend']['name'],
		    'actions': html,
		});
	    };
	    $(table).bootstrapTable('hideLoading');
    	}
    });
    return false;
};
