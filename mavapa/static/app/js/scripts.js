$(document).ready(function () {
    autosize_tables();
    $(window).resize(function () {
	autosize_tables();
    });
    $('.modal').on('hidden.bs.modal', function(){
	$('.modal').find('.modal-title').html('New');
	var forms = $(this).find('form');
	forms.each(function(row){
	    forms[row].reset();
	});
	var selectpickers = $(this).find('.selectpicker');
	selectpickers.each(function(row){
	    $(selectpickers[row]).selectpicker('refresh');
	});
    });
    $(".nav-tabs a[data-toggle=tab]").on("click", function(e) {
	if ($(this).parent().hasClass("disabled")) {
	    e.preventDefault();
	    return false;
	}
    });
    jqlisteners();
});

// $('.sidebar-nav > li').on('click', function (e) {
//     e.preventDefault();
//     $('.sidebar-nav > li').removeClass('active');
//     $(this).addClass('active');
// });

function autosize_tables() {
    var tables = $('body').find(".table-autosize");
    tables.each(function(row){
	var selector = $(tables[row]).attr('id');
	selector = '#' + selector;
	$(selector).on('post-body.bs.table', function () {
	    jqlisteners();
	});
	$(selector).bootstrapTable({
	    height: table_height(selector),
	});
	$(selector).bootstrapTable('resetView', {
	    height: table_height(selector),
	});	    
    });
}

function table_height(table) {
    var parent = $(table).parent().parent().parent().parent();
    return parent.height();
};

