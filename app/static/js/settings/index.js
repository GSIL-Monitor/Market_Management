import {Tabs} from '../framework/tabs.js'
import {Tab_Markets} from './tab_markets.js'

$('#left,#right').hide()

let socket = io.connect('http://' + document.domain + ':' + location.port + '/markets');

let $main_content = $('#main .main_content').empty()
let tabs = new Tabs()
tabs.init($main_content)
tabs.append_tab(new Tab_Markets(socket))