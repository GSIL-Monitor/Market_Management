$('ul').on('click', 'li a', function(){
    $(this).parent().siblings().find('a').removeClass('active')
    $(this).addClass('active')
})

let name = window.location.pathname.split('/').pop()

$('#top span.market').text(' - ' + name)
if(window.location.pathname.startsWith("/p4p")){
    $('#top li a.p4p').addClass('active').parent().siblings().find('a').removeClass('active')
}else if(window.location.pathname.startsWith("/markets")){
    $('#top li a.markets').addClass('active').parent().siblings().find('a').removeClass('active')
}