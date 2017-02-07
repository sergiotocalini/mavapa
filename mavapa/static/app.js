$('.sidebar-nav > li').on('click', function (e) {
    e.preventDefault();
    $('.sidebar-nav > li').removeClass('active');
    $(this).addClass('active');
});
