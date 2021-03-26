var BACKEND_ID = null;
$(document).ready(function () {
    $('.nav a').on('shown.bs.tab', function() {
	autosize_tables();
    });
    $(".section-toolbar a[data-click=section-switch]").on("click", function(a) {
	a.preventDefault();
	if (BACKEND_ID != null) {
	    $(".section-switch").toggleClass("hidden");
	    $(".section-content").toggleClass("hidden");	
	    autosize_tables();
	}
    });
        
    $(".switch-toolbar a[data-click=new]").on("click", function(a) {
	a.preventDefault();
	$("#ModalBackend").modal("show");
    });

    $(".switch-toolbar a[data-click=refresh]").on("click", function(e){
	e.preventDefault();
	getOrgs();
    });
    
    $(".nav-tabs a[data-toggle=tab]").on("click", function(e) {
	if ($(this).parent().hasClass("disabled")) {
	    e.preventDefault();
	    return false;
	}
    });
    getOrgs();
});


function jqlisteners() {
    console.log("Loading");
    jqlisteners_modal_backend();
    jqlisteners_modal_person();
};

function jqlisteners_orgs() {
    $(".section-switch .button-connection").on("dblclick", function(a) {
	a.preventDefault();
	BACKEND_ID = $(this).data('id');
	getTree();
	$('#table-org-people').bootstrapTable("refreshOptions", {
	    url: "{{ url_for('api_backends_search_users') }}?backend=" + BACKEND_ID,
	});
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
	$('#table-org-people').bootstrapTable("refreshOptions", {
	    url: "{{ url_for('api_backends_search_users') }}?backend=" + BACKEND_ID,
	});
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
}

function getOrgs() {
    console.log("entro");
    
    $.ajax({
	url: "{{ url_for('api_backends') }}",
	type: 'GET',
	contentType: "application/json",
	success: function(e) {
	    var html = ""
	    for (var idx in e.backends) {
		var org = e.backends[idx];
		org["last_seen_ago"] = moment(Date.parse(org["last_seen"])).fromNow();
		html += `
<button type="button" data-id="${org.id}" style="outline:none;" class="list-group-item list-group-item-action button-connection">
  <div class="d-flex w-100 justify-content-between">
    <h4 class="mb-1">
      <em class="fa fa-database"></em>
      ${org.name}
    </h4>
    <div class="bt-group" style="position: absolute;
				 right: 0px;
				 top: 0px;
				 margin: 1%;
				 padding: 1.5% 3%;
				 border-radius: 50%;">
      <a href="#" class="dropdown-toggle" data-toggle="dropdown" style="color: gray;">
	<em class="fa fa-ellipsis-v"></em>
      </a>
      <ul class="dropdown-menu dropdown-menu-right">
	<li>
	  <a href="#connect" data-click="connect">
	    <em class="fa fa-fw fa-plug"></em>
	    Connect
	  </a>
	</li>
	<li>
	  <a href="#edit" data-click="edit">
	    <em class="fa fa-fw fa-pencil-alt"></em>
	    Edit
	  </a>
	</li>
	<li>
	  <a href="#copy" data-click="copy">
	    <em class="fa fa-fw fa-copy"></em>
	    Copy
	  </a>
	</li>
	<li role="separator" class="divider"></li>
	<li>
	  <a href="#delete" data-click="delete">
	    <em class="fa fa-fw fa-trash"></em>
	    Delete
	  </a>
	</li>
      </ul>
    </div>
  </div>
  
  <div class="d-flex w-100 justify-content-between">
    <p class="mb-1">${org.type}</p>
  </div>
      
  <div class="d-flex w-100 justify-content-between">
    <small class="mb-1">
      <i class="fa fa-fw fa-plug"></i>
      ${org.host}
    </small>
    <small class="pull-right">
      ${org.last_seen_ago}
    </small>
  </div>
</button>
`
	    }
	    $("#orgs-list").html(html);
	    jqlisteners_orgs();
	}
    });

};

function OrgItemFormatterValue(value, row) {
    var html = ""
    html += '<div class="text-ellipsis">'
    html +=  '<span>' + value + '</span>';
    html += '</div>'
    return html;
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
		    for (var child in item.children) {
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
		for (var e in data) {
		    var enables = find_node_dep(data[e]['nodeId']);
		    console.log(data[e]);
		    nodes_enable.concat(enables);
		}
		console.log(nodes_enable);
		for (var c in nodes) {
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
			console.log(data);
			for (user in data) {
			    $(table).bootstrapTable('append', {
				'key': 'dn',
				'value': data[user][0],
				'input': data[user][0],				
			    });
			    for (var key in data[user][1]) {
				for (var value in data[user][1][key]) {
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


function PeopleParams(params) {
    return {
	filter: '(&(objectClass=person)(objectClass=top))',
    }
};


function PeopleResponseHandler(res) {
    var data = [];
    for (var r in res.data) {
	var row = res.data[r];
	var avatar = "{{ config['CDN_LOCAL'] }}/img/avatar.jpg";
	if (row[1]['jpegPhoto']) {
	    avatar = "data:image/jpg;base64," + row[1]['jpegPhoto'][0];
	} else if (row[1]['photo']) {
	    avatar = "data:image/jpg;base64," + row[1]['Photo'][0];
	}
	var doc = {
	    'backend': row[1]['backend'] ? row[1]['backend']['id'] : null,
	    'dn': row[0], 'display': row[1]['displayName'] ? row[1]['displayName'][0] : null,
	    'firstname': row[1]['givenName'] ? row[1]['givenName'][0] : null,
	    'lastname': row[1]['sn'] ? row[1]['sn'][0] : null,
	    'email': row[1]['mail'] ? row[1]['mail'][0] : null,
	    'exist': row[1]['exist'], 'avatar': avatar,
	    'uidNumber': row[1]['uidNumber'] ? row[1]['uidNumber'][0] : null,
	    'uid': row[1]['uid'] ? row[1]['uid'][0] : null,
	    'gecos': row[1]['gecos'] ? row[1]['gecos'][0] : null,
	    'gidNumber': row[1]['gidNumber'] ? row[1]['gidNumber'][0] : null,
	    'homeDirectory': row[1]['homeDirectory'] ? row[1]['homeDirectory'][0] : null,
	    'loginShell': row[1]['loginShell'] ? row[1]['loginShell'][0] : null,
	};
	data.push(doc);
    };
    return data
};


function PeopleFormatterName(value, row) {
    var html = ""
    html += '<img class="fa fa-fw img-circle img-zoom-2x" src="' + row.avatar + '"/> ';
    html += row.lastname + ', ' + row.firstname;
    return html;
};


function PeopleFormatterEmail(value, row) {
    var html = ""
    html +='<span class="pull-left">'
    html +=' <a href="mailto:' + value + '" style="padding-right:4px;text-decoration:none;outline:none;color:inherit;">';
    html +='  <i class="fa fa-fw fa-envelope-open-text" style="vertical-align: middle;"></i>';
    html +=' </a>';
    html +='</span>';
    html += value;
    return html;
};


function PeopleFormatterUsername(value, row) {
    var html = ""
    html += value
    html+='<span class="pull-right">';
    if (row.uidNumber) {
	html+='<span class="fa-stack" style="font-size: 0.60em;">'
	html+=' <i class="fas fa-square fa-stack-2x" style="vertical-align: middle;"></i>'
	html+=' <i class="fas fa-terminal fa-stack-1x fa-inverse" style="vertical-align: middle;"></i>'
	html+='</span>'
    }
    html+='</span>';
    return html;
};


function PeopleFormatterActions(value, row) {
    var html ='';    
    if (! row.exist) {
	html+='<a class="person-add" data-toggle="confirmation" data-click="person-add" style="color: Orange;"';
	html+='   data-dn="' + row.dn + '" data-backend="' + row.backend + '" data-container="body" href="#person-add">';
	html+=' <i class="fa fa-fw fa-plus-circle"></i>';
	html+='</a>';
	html+='<span style="color: Marron;">';
	html+=' <i class="fa fa-fw fa-recycle"></i>';
	html+='</span>';
    } else {
	html+='<span style="color: Green;">';
	html+=' <i class="fa fa-fw fa-check-circle"></i>';
	html+='</span>';
	html+='<a class="person-sync" data-toggle="confirmation" data-click="person-sync"';
	html+='   data-dn="' + row.dn + '" data-backend="' + row.backend + '" data-container="body" href="#person-sync">';
	html+=' <i class="fa fa-fw fa-recycle"></i>';
	html+='</a>';
    }
    html+='<a class="person-open" data-toggle="confirmation" data-click="person-open"';
    html+='   data-dn="' + row.dn + '" data-backend="' + row.backend + '" data-container="body" href="#person-open">';
    html+=' <i class="fa fa-fw fa-search"></i>';
    html+='</a>';
    return html;
};

