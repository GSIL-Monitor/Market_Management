import {Utils} from '../../libs/utils/utils.js'
import {Tab} from '../framework/tab.js'
import {Visitors_Chart} from './visitors_chart.js'

function Tab_Visitors(socket, market=undefined, categories=undefined, directory=undefined, filename=undefined){
    Tab.call(this, socket, market, categories, directory, filename)

    this.name = 'visitors'
    this.title = '访 客'
    this.visitors = []
    let buttons = `<button type="button" class="btn btn-sm btn-primary refresh">刷 新</button>`
    this.$button_group = $(`<div class="btn-group mr-2 visitors" role="group">${buttons}</div>`)

    this.$content = fw.load_from_template('#template_visitors')
    this.$svg_container = this.$content.find('.svg_container')

    let that = this

    this.socket.emit('get_visitors', that.market, function(data){
        that.visitors = data
        console.log(that.visitors)

        that.chart = new Visitors_Chart(that.$svg_container, that.visitors)
    })

    this.$content.on('click', '.region_selection label', function(){
        let region = $(this).find('input').data('region')
        let is_current_active = $(this).hasClass('active')
        let cls = "visitor"
        if(region!='All'){
            cls = region.split(' ').join('_')
        }else{
            if(is_current_active){
                $(this).siblings('label').removeClass('active')
            }else{
                $(this).siblings('label').addClass('active')
            }
        }

        if(is_current_active){
            $(`svg g.${cls}`).attr("visibility", "hidden")
            $(`table.visitor_list tr.${cls}`).hide()
        }else{
            $(`svg g.${cls}`).attr("visibility", "visible")
            $(`table.visitor_list tr.${cls}`).show()
        }
    })


    $('body').on('keydown', function(e){
        console.log('keydown: ', e.which)
        if(e.which==27){
            $('.visitors svg g.select_rect').attr('visibility', 'hidden')
            $('.visitors svg g.xaxis_cursor').attr('visibility', 'hidden')
            $('.visitors svg g.xaxis_cursor_top').attr('visibility', 'hidden')
            $('.visitors svg g.yaxis_cursor').attr('visibility', 'hidden')
            $('.visitors table.visitor_list tbody').empty()
        }
    })

    this.$content.find('table.visitor_list').on('click', 'th', function(){
        let $th = $(this)
        if($th.index() >= 4){
            return
        }

        let $table = $th.parents('table')

        Utils.table_sort($table, $th)
    })

    this.$content.find('table.visitor_list tbody').on('mouseenter', 'tr', function(){
        let id = $(this).data('vid')
        $('.visitors svg g.'+id+' path').attr('fill', 'blue')
    })
    this.$content.find('table.visitor_list tbody').on('mouseleave', 'tr', function(){
        let id = $(this).data('vid')
        for(let path of $('.visitors svg g.'+id+' path')){
            let $path = $(path)
            if($path.hasClass('inquiried') || $path.hasClass('tm_inquiried')){
                $path.attr('fill', 'red')
            }else{
                $path.attr('fill', 'gray')
            }
        }
    })

    this.$content.find('table.visitor_list').on('click', 'tr', function(){
        let id = $(this).data('vid')
        let visitors = $(this).parents('table').data('visitors')
        console.log(visitors[id])
    })
}

export {Tab_Visitors}