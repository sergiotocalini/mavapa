function makeMenu(apps) {
    var url =$('script[src$="/mavapa.js"]').attr('src') + '/../../../../apps';
    var html = "";
    for (var x in apps){
	var app = apps[x];
	var li = '<li><a href="{url}"><img class="app-icon" src="{image}"></i><p>{name}</p></a></li>';
	li = li.replace(/{url}/g, app['url']);
	li = li.replace(/{image}/g, app['icon']);
	li = li.replace(/{name}/g, app['name']);
	html += li;
    }
    html += '<a class="more" arial-label="More Mavapa apps" href="' + url + '" target="_blank" aria-expanded="false" aria-hidden="false">More</a>';
    return html;
}

$(document).ready(function(){
    var url = $('script[src$="/mavapa.js"]').attr('src') + '/../../../../api/apps?favorites=true';
    $.ajax({
	url: url,
	type: 'GET',
	crossDomain: true,
	xhrFields: {
	    withCredentials: true
	},
	success: function(data) {
	    var html = makeMenu(data['apps']);
	    $("#mavapa-apps-menu").html(html);
	},
    });
});

