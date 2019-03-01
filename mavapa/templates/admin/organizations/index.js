var BACKEND_ID = null;
$(document).ready(function () {
    $(".section-toolbar a[data-click=section-switch]").on("click", function(a) {
	a.preventDefault();
	if (BACKEND_ID != null) {
	    $(".section-switch").toggleClass("hidden");
	    $(".section-content").toggleClass("hidden");	
	    autosize_tables();
	}
    });
    
    $(".section-switch .button-connection").on("dblclick", function(a) {
	a.preventDefault();
	BACKEND_ID = $(this).data('id');
	getTree();
	$('#table-org-terminal').bootstrapTable("refreshOptions", {
	    url: "{{ url_for('api_backends_search') }}?backend=" + BACKEND_ID,
	});
	$(".section-switch").addClass("hidden");
	$(".section-content").removeClass("hidden");
	autosize_tables();
    });
    
    $(".section-switch a[data-click=connect]").on("click", function(a) {
	a.preventDefault();
	BACKEND_ID = $(this).parent().parent().parent().parent().parent().data('id');
	getTree();
	$('#table-org-terminal').bootstrapTable("refreshOptions", {
	    url: "{{ url_for('api_backends_search') }}?backend=" + BACKEND_ID,
	});
	$(".section-switch").addClass("hidden");
	$(".section-content").removeClass("hidden");
	autosize_tables();
    });

    $(".section-switch a[data-click=delete]").on("click", function(a) {
	a.preventDefault();
	var backend = $(this).parent().parent().parent().parent().parent().data('id');
	$.ajax({
	    url: "{{ url_for('api_backends') }}?id=" + backend,
	    type: 'DELETE',
	    contentType: "application/json",
	    success: function(e) {
		console.log(e);
	    }
	});
    });
    
    $(".section-switch a[data-click=edit]").on("click", function(a) {
	a.preventDefault();
	var backend = $(this).parent().parent().parent().parent().parent().data('id');
	var modal = "#ModalBackend";
	$.ajax({
	    url: "{{ url_for('api_backends') }}?id=" + backend,
	    type: 'GET',
	    contentType: "application/json",
	    success: function(e) {
		$(modal).find('.modal-title').html(e['backends'][0]['name']);
		$(modal).find('#backend-id').val(e['backends'][0]['id']);
		$(modal).find('#backend-name').val(e['backends'][0]['name']);
		$(modal).find('#backend-type').selectpicker('val', e['backends'][0]['type']);
		$(modal).find('#backend-url').val(e['backends'][0]['host']);
		$(modal).find('#backend-timeout').val(e['backends'][0]['timeout']);
		$(modal).find('#backend-username').val(e['backends'][0]['binddn']);
		$(modal).find('#backend-password').val(e['backends'][0]['bindpw']);
		$(modal).find('#backend-search').val(e['backends'][0]['basedn']);
		$(modal).find('#backend-filter').val(e['backends'][0]['filter']);
		$(modal).find('#backend-attribute').val(e['backends'][0]['login']);
		$(modal).find('#backend-onfly').prop('checked', e['backends'][0]['onfly']).change();
		$(modal).modal('show');
	    }
	});
    });
    
    $(".switch-toolbar a[data-click=new]").on("click", function(a) {
	a.preventDefault();
	$("#ModalBackend").modal("show");
    });
    
    $(".nav-tabs a[data-toggle=tab]").on("click", function(e) {
	if ($(this).parent().hasClass("disabled")) {
	    e.preventDefault();
	    return false;
	}
    });
});


function jqlisteners() {
    console.log("Loading");
    jqlisteners_modal_backend();
    jqlisteners_modal_terminal();
    
    $("#table-org-terminal a[data-click=user-term-open]").unbind()
    $("#table-org-terminal a[data-click=user-term-open]").on("click", function(a) {
	a.preventDefault();
	var backend = $(this).data('backend');
	var dn = $(this).data('dn');
	var modal = '#ModalTerminal';

	$.ajax({
	    url: "{{ url_for('api_backends_items') }}",
	    type: 'GET',
	    contentType: "application/json",
	    data: { dn: dn, backend: backend },
	    success: function(e) {
		var user = e['data'] ? e['data'][0] : ['', {}];
		$(modal).find('.modal-title').html('<i class="fa fa-fw fa-user"></i> ' + user[1]['uid']);
		$(modal).find('#terminal-dn').val(user[0]);
		$(modal).find('#terminal-backend').val(backend);
		$(modal).find('#terminal-uidNumber').val(user[1]['uidNumber'][0]);
		$(modal).find('#terminal-gidNumber').val(user[1]['gidNumber'][0]);
		$(modal).find('#terminal-homeDirectory').val(user[1]['homeDirectory'][0]);
		$(modal).find('#terminal-gecos').val(user[1]['gecos'] ? user[1]['gecos'][0] : '');
		$(modal).find('#terminal-loginShell').selectpicker('val', user[1]['loginShell'] ? user[1]['loginShell'][0] : '/bin/bash');
		$(modal).find('#terminal-uid').val(user[1]['uid'][0]);
		$(modal).modal('show');
	    }	
	});
    });    
};


function OrgItemFormatterValue(value, row) {
    var html = ""
    html += '<div class="text-ellipsis">'
    html +=  '<span>' + value + '</span>';
    html += '</div>'
    return html;
};


function TerminalParams(params) {
    return {
	filter: '(ObjectClass=posixAccount)',
	exclude: 'jpegPhoto,photo'
    }
};


function TerminalResponseHandler(res) {
    var data = [];
    for (r in res.data) {
	var row = res.data[r];
	var doc = {
	    'backend': row[1]['backend'] ? row[1]['backend']['id'] : null,
	    'dn': row[0],
	    'uidNumber': row[1]['uidNumber'] ? row[1]['uidNumber'][0] : null,
	    'uid': row[1]['uid'] ? row[1]['uid'][0] : null,
	    'gecos': row[1]['gecos'] ? row[1]['gecos'][0] : null,
	    'gidNumber': row[1]['gidNumber'] ? row[1]['gidNumber'][0] : null,
	    'homeDirectory': row[1]['homeDirectory'] ? row[1]['homeDirectory'][0] : null,
	    'loginShell': row[1]['loginShell'] ? row[1]['loginShell'][0] : null,
	    'mail': row[1]['mail'] ? row[1]['mail'][0] : null
	};
	data.push(doc);
    };
    return data
};


function getTree() {
    $.ajax({
	url: "{{ url_for('api_backends_tree') }}",
	type: 'GET',
	contentType: "application/json",
	data: { backend: BACKEND_ID, type: 'items' },
	success: function(e) {
	    var get_tree = function(item) {
		var data = []
		if (item.children) {
		    for (child in item.children) {
			data.push(get_tree(item.children[child]));
		    }
		} else {
		    info = {text: item.name, dn: item.dn, backend: BACKEND_ID}
		    if (item.name.startsWith("dc=")) {
			info['icon'] = 'fa fa-fw fa-book'
		    } else if (item.name.startsWith("ou=")) {
			info['icon'] = 'fa fa-fw fa-cubes'
		    } else {
			info['icon'] = 'fa fa-fw fa-cube'
		    }
		    return info
		}
		info = {
		    text: item.name, dn: item.dn, backend: BACKEND_ID,
		    nodes: data, tags: [ data.length ]
		}
		if (item.name.startsWith("dc=")) {
		    info['icon'] = 'fa fa-fw fa-book'
		} else if (item.name.startsWith("ou=")) {
		    info['icon'] = 'fa fa-fw fa-cubes'
		} else {
		    info['icon'] = 'fa fa-fw fa-cube'
		}
		return info
	    };
	    $('#treeview-org').treeview({
		data: [get_tree(e['data'])],
		showTags: true,
	    });
	    $('#treeview-org').on('searchComplete', function(event, data) {
		// Your logic goes here
		$(this).treeview('checkAll', { silent: true });
		var nodes = $(this).treeview('getChecked');
		var find_node_dep = function(nodeid) {
		    var data = []
		    var node = $('#treeview-org').treeview('getNode', nodeid);
		    if (typeof node.parentId !== "undefined") {
			data.push(find_node_dep(node['parentId']))
		    } else {
			return node['nodeId'];
		    }
		    data.push(node['nodeId']);
		    return data;
		}
		var nodes_enable = []
		for (e in data) {
		    var enables = find_node_dep(data[e]['nodeId']);
		    console.log(data[e]);
		    nodes_enable.concat(enables);
		}
		console.log(nodes_enable);
		for (c in nodes) {
		    if ( ! nodes_enable.includes(nodes[c]['nodeId']) ) {
			// var node = $(this).treeview('getNode', c);
			$('li[data-nodeid=' + nodes[c]['nodeId'] + ']').addClass('hidden');
		    }
		}
	    });
	    $('#treeview-org').on('nodeSelected', function(event, data) {
		var get_path = function(nodeid) {
		    var data = []
		    var node = $('#treeview-org').treeview('getNode', nodeid);
		    if (typeof node.parentId !== "undefined") {
			data.push(get_path(node['parentId']));
		    } else {
			return node['text'];
		    }
		    data.push(node['text']);
		    data.reverse();
		    return data.join(',');
		};
		// var dn = get_path(data['nodeId']);
		var table = '#table-org-explore';
		$(table).bootstrapTable('removeAll');
		$(table).bootstrapTable('showLoading');
		$(table).parent().addClass('table-loading');
		$.ajax({
		    url: "{{ url_for('api_backends_items') }}",
		    type: 'GET',
		    contentType: "application/json",
		    data: { dn: data['dn'], backend: data['backend'] },
		    success: function(e) {
			var data = e['data'];
			for (user in data) {
			    $(table).bootstrapTable('append', {
				'key': 'dn',
				'value': data[user][0],
				'input': data[user][0],				
			    });
			    for (key in data[user][1]) {
				for (value in data[user][1][key]) {
				    $(table).bootstrapTable('append', {
					'key': key,
					'value': data[user][1][key][value],
					'input': data[user][1][key][value],
				    });
				};
			    };
			};
			$(table).parent().removeClass('table-loading');
			$(table).bootstrapTable('hideLoading');
		    },
		    error: function(e) {
			$(table).parent().removeClass('table-loading');
			$(table).bootstrapTable('hideLoading');
		    }
		});
	    });
	    $('#treeview-org').treeview('selectNode', [ 0 ]);	    
	}
    });
};

function TerminalFormatterActions(value, row) {
    html ='<a class="user-term-open" data-toggle="confirmation" data-click="user-term-open"';
    html+='   data-dn="' + row.dn + '" data-backend="' + row.backend + '" data-container="body" href="#user-term-open">';
    html+=' <i class="fa fa-fw fa-search"></i>';
    html+='</a>';
    return html;
}
