import * as left from './left.js'

let socket = io.connect('http://' + document.domain + ':' + location.port + '/markets');
let markets = {}

let data = {}
data['$container'] = $('#left')
data['socket'] = socket
data['markets'] = markets

left.init(data)

socket.on('notify', function(msg){
    fw.notify(msg)
})

socket.on('title_reserved', function(data){
    let title = data.title.toLowerCase()
    for(let span of $('#right span.title')){
        let $span = $(span)
        if($span.hasClass('used') || $span.hasClass('reserved')){
            continue
        }
        let text = $span.text().toLowerCase()
        if(title == text){
            $span.addClass('reserved')
        }
    }

    let market = left.current_market()
    market.reserved_titles[title] = data.product
})

socket.on('product_posting_finished', function(){
    socket.off('product_posting')
})