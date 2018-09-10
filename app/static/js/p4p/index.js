import {Tabs} from '../framework/tabs.js'
import {Tab_Keywords} from './tab_keywords.js'
import {Tab_Task} from './tab_task.js'
import {Tab_Visitors} from './tab_visitors.js'
import {Tab_Chart} from './tab_chart.js'

$('#left,#right').hide()
let $main_content = $('#main .main_content').empty()

let market_name = window.location.pathname.split('/').pop()
let socket = io.connect('http://' + document.domain + ':' + location.port + '/markets');

let tab_task = undefined
let tab_visitors = undefined
let tab_chart = undefined

let market = {}
socket.emit('get_market', market_name, function(mkt){
    market = mkt
    let tabs = new Tabs()
    tabs.init($main_content)
    tabs.append_tab(new Tab_Keywords(socket, market))

    tab_task = new Tab_Task(socket, market)
    tabs.append_tab(tab_task)

    tab_visitors = new Tab_Visitors(socket, market)
    tabs.append_tab(tab_visitors)

    tab_chart = new Tab_Chart(socket, market)
    tabs.append_tab(tab_chart)
})

