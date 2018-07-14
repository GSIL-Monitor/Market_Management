import {Tab} from '../framework/tab.js'
import {Utils} from '../../libs/utils/utils.js'

function Tab_Keywords(socket, market=undefined, categories=undefined, directory=undefined, filename=undefined){
    Tab.call(this, socket, market, categories, directory, 'p4p_keywords_list.json')

    this.name = 'keywords'
    this.title = '关 键 字'

    let buttons = `<button type="button" class="btn btn-sm btn-primary refresh">刷 新</button>`
    buttons = `${buttons}<button type="button" class="btn btn-sm btn-primary save">保 存</button>`
    this.$button_group = $(`<div class="btn-group mr-2 keywords" role="group">${buttons}</div>`)

    this.$content = fw.load_from_template('#template_keywords')
    let that = this

    this.$button_group.on('click', 'button.save', function(){
        let ids_recording = {}
        for(let input of that.$content.find('input.recording:checked')){
            ids_recording[$(input).val()] = $(input).parents('tr').find('td.keywords').text().trim()
        }

        let ids_monitor = {}
        for(let input of that.$content.find('input.monitor:checked')){
            ids_monitor[$(input).val()] = $(input).parents('tr').find('td.keywords').text().trim()
        }

        that.socket.emit('serialize', ids_recording, that.market, [], 'p4p_keywords_list_recording.json')
        that.socket.emit('serialize', ids_monitor, that.market, [], 'p4p_keywords_list_monitor.json')
    })

    this.$button_group.on('click', 'button.refresh', function(){
        that.socket.emit('refresh_p4p_keywords', that.market, function(){
        })
        that.socket.once('refresh_p4p_keywords_result', function(data){
            that.load_keywords(data)
        })
    })

    this.fetch_values_from_server()
        .then(function(results){
            if(!results[0]){
                return
            }

            that.load_keywords(results[0])
        }).catch(error => console.log(error))

    this.$content.find('thead').on('click', 'th', function(){
        let $th = $(this)
        if($th.index() == 1 || $th.index() == 2){
            let cls = $th.attr('class')
            if($th.data('checked')){
                that.$content.find(`tbody input.${cls}`).prop('checked', false)
                $th.data('checked', false)
            }else{
                that.$content.find(`tbody input.${cls}`).prop('checked', true)
                $th.data('checked', true)
            }
        }else{
            Utils.table_sort($th.parents('table'), $th)
        }
    })

    this.$content.find('tbody').on('click', 'input[type="checkbox"]', function(){
        let id = $(this).val()
        let cls = $(this).attr('class')
        console.log(id, cls, $(this).prop('checked'))
        if($(this).prop('checked')){
            that.$content.find(`tbody tr.${id} input.${cls}`).prop('checked', true)
        }else{
            that.$content.find(`tbody tr.${id} input.${cls}`).prop('checked', false)
        }
    })
}

Tab_Keywords.prototype = Tab.prototype

Tab_Keywords.prototype.load_recording_keywords = function(){
    let that = this
    this.socket.emit('deserialize', this.market, [], 'p4p_keywords_list_recording.json', true, function(data){
        if(!data){
            return
        }
        for(let id in data){
            that.$content.find('tr.'+id+' td:nth-child(2) input').prop('checked', true)
        }
    })
}

Tab_Keywords.prototype.load_monitor_keywords = function(){
    let that = this
    this.socket.emit('deserialize', this.market, [], 'p4p_keywords_list_monitor.json', true, function(data){
        if(!data){
            return
        }
        for(let id in data){
            that.$content.find('tr.'+id+' td:nth-child(3) input').prop('checked', true)
        }
    })
}

Tab_Keywords.prototype.load_keywords = function(data){

        let trs = ""
        let count = 0
        for(let kw of data){
            count ++
            let tds = ""
            tds = `${tds}<td>${count}</td>`
            tds = `${tds}<td><input class="recording" type="checkbox" value="${kw.id}"></td>`
            tds = `${tds}<td><input class="monitor" type="checkbox" value="${kw.id}"></td>`
            tds = `${tds}<td class="keywords">${kw.kws}</td>`
            tds = `${tds}<td>${kw.status}</td>`
            tds = `${tds}<td>${kw.group}</td>`
            tds = `${tds}<td>${kw.my_price}</td>`
            tds = `${tds}<td>${kw.average_price}</td>`
            tds = `${tds}<td>${kw.match_level}</td>`
            tds = `${tds}<td>${kw.search_count}</td>`
            tds = `${tds}<td>${kw.buy_count}</td>`
            trs = `${trs}<tr class="${kw.id}" data-id="${kw.id}">${tds}</tr>`
        }

        this.$content.find('tbody').html(trs)

        this.load_recording_keywords()
        this.load_monitor_keywords()

        console.log('keywords was reloaded')
}


export {Tab_Keywords}