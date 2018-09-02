import {Utils} from '../../libs/utils/utils.js'
import {Tab} from '../framework/tab.js'
import {Keyword_Chart} from './keyword_chart.js'
import {Sponsor_Chart} from './sponsor_chart.js'

function Tab_Chart(socket, market=undefined, categories=undefined, directory=undefined, filename=undefined){
    Tab.call(this, socket, market, categories, directory, filename)

    this.name = 'chart'
    this.title = '图 表'

    this.keywords = undefined
    this.sponsors = undefined
    this.balance = []

    let buttons = `<select class="custom-select" id="crawling_results"></select>`
    buttons = `${buttons}<button type="button" class="btn btn-sm btn-primary ok" style="margin-left:0px;">OK</button>`
    this.$button_group = $(`<div class="btn-group mr-2 chart" role="group">${buttons}</div>`)

    this.$content = fw.load_from_template('#template_chart')
    this.$svg_container = this.$content.find('.svg_container')
    this.$keywords_table = this.$content.find('table.keywords')
    this.$sponsors_table = this.$content.find('table.sponsors')
    this.chart = undefined

    let that = this

    socket.emit('get_p4p_keywords_crawl_result_file_list', market, function(files){
        // console.log(files)
        let options = ''
        for(let file of files.reverse()){
            let dt = file.split('.')[0].split('_').pop()
            options = `${options}<option value="${dt}">${dt}</option>`
        }
        $('#crawling_results').html(options)
    })

    this.$button_group.on('click', 'button.ok', function(){
        let dt = $('#crawling_results').val()
        let fn = 'p4p_keywords_crawl_result_'+dt+'.json.gz'

        socket.emit('get_p4p_records', market, [], dt, function(data){
            console.log(data[0])
            console.log(data[1])

            let keywords = {}
            let sponsors = {}
            that.balance = []

            if(data[1]) {
                for (let arr of data[1]) {
                    that.balance.push([moment(arr[0]), arr[1]])
                }
            }

            for(let turn of data[0]){
                for(let item of turn){
                    let id = item[1]
                    // if(id == '77942874814'){
                    //     console.log(item)
                    // }
                    let keyword = undefined
                    if(id in keywords){
                        keyword = keywords[id]
                    }else{
                        keyword = {'id':id, 'lines': [[],[],[],[],[],[]], 'sponsors':[[],[],[],[],[],[]]}
                        keyword['name'] = item[2]
                        keyword['group'] = item[3]
                        keywords[id] = keyword
                    }
                    let lines = keyword.lines
                    lines[0].push(moment(item[0]))
                    for(let [idx, price] of item[4].entries()){
                        if(idx>4){
                            console.log('prices array is longer than expected', item)
                            break
                        }
                        lines[idx+1].push(+price)
                    }

                    let sponsor_list = item[5].sponsor_list
                    sponsor_list.unshift(item[5].top_sponsor)
                    for(let [idx, sps] of keyword.sponsors.entries()){
                        let sp = undefined
                        if(idx<sponsor_list.length){
                            sp = sponsor_list[idx]
                        }
                        if(!sp){
                            sps.push(undefined)
                            continue
                        }
                        let sp_id = sp.url.match('.*//([^/]+\.alibaba\.com)/.*')[1]
                        sps.push(sp_id)

                        let sponsor = undefined
                        if(sp_id in sponsors){
                            sponsor = sponsors[sp_id]
                        }else{
                            sponsor = sp
                            sponsor['id'] = sp_id
                            sponsor['keywords'] = {}
                            sponsor['dt'] = moment(item[0])
                            sponsors[sp_id] = sponsor
                        }

                        if(!(item[1] in sponsor['keywords'])){
                            sponsor['keywords'][item[1]] = []
                        }
                        if(idx==0){
                            sponsor['keywords'][item[1]].push([moment(item[0]), 0])
                        }else{
                            let price = +item[4][idx-1]
                            if(!isNaN(price))
                                sponsor['keywords'][item[1]].push([moment(item[0]), price])
                        }
                    }
                }
            }

            that.keywords = keywords
            that.sponsors = sponsors

            console.log(that.keywords, that.sponsors, that.balance)
            that.load_keywords()
            that.load_sponsors()
            that.$content.on('click', 'tr a', function(e){
                e.preventDefault()
            })
        })
    })

    this.$keywords_table.on('click', 'tbody tr td.name', function(){
        that.$sponsors_table.find('tr.selected').removeClass('selected')
        that.$sponsors_table.find('tr.related').removeClass('related')
        that.$keywords_table.find('tbody path.symbol').attr('d', '').removeClass('symbol').parents('td').next().empty()
        let $tr = $(this).parent()

        let id = $tr.data('id')
        $tr.toggleClass('selected').siblings('.selected').removeClass('selected')
        if($tr.hasClass('selected')){
            let kw = that.keywords[id]
            that.load_keyword_chart(kw)
        }
    })

    this.$sponsors_table.on('click', 'tbody tr td.name', function(){
        that.$keywords_table.find('tr.selected').removeClass('selected')
        that.$keywords_table.find('tr.related').removeClass('related')
        that.$sponsors_table.find('tbody path.symbol').attr('d', '').removeClass('symbol').parents('td').next().empty()

        let $tr = $(this).parent()

        let id = $tr.data('id')
        $tr.toggleClass('selected').siblings('.selected').removeClass('selected')
        if($tr.hasClass('selected')){
            let sponsor = that.sponsors[id]
            console.log(sponsor)
            that.load_sponsor_chart(sponsor)
        }
    })

    $('body').on('keypress', function(e){
        
        if(e.which>47 && e.which<54){
            let n = e.which - 48
            if($('.svg_container svg .position_'+n).attr('visibility') == 'hidden'){
                $('.svg_container svg .position_'+n).attr('visibility', 'visible')
            }else{
                $('.svg_container svg .position_'+n).attr('visibility', 'hidden')
            }
        }else if(e.which == 96){
            
            let $hidden_g = $('.svg_container svg .symbol[visibility="hidden"]')
            let $hidden_path = $('.svg_container svg .symbol path[visibility="hidden"]')
            if($hidden_g.length || $hidden_path.length){
                $hidden_g.attr('visibility', 'visible')
                $hidden_path.attr('visibility', 'visible')
            }else{
                $('.svg_container svg .symbol').attr('visibility', 'hidden')
            }
        }else if(e.which == 27){
            that.chart.hide_cursor()
        }
    })

    $('body').on('keydown', function(e){
        console.log('keydown: ', e.which)

        if(e.which == 27){
            if(that.chart){
                that.chart.hide_cursor()
                $('.chart tr.related').removeClass('related')
            }
        }

        if(e.which == 109 && that.chart && that.chart.max_prices){
            let max = that.chart.yDomain[1]
            let maxs = that.chart.max_prices
            let idx = maxs.indexOf(max)
            idx--
            if(idx<0){
                return
            }
            max = maxs[idx]
            that.chart.set_yDomain_max(max)
        }

        if(e.which == 107 && that.chart && that.chart.max_prices){
            let max = that.chart.yDomain[1]
            let maxs = that.chart.max_prices
            let idx = maxs.indexOf(max)
            idx++
            if(idx>=maxs.length){
                return
            }
            max = maxs[idx]
            that.chart.set_yDomain_max(max)
        }
    })

    this.$sponsors_table.on('click', 'th:first-child', function(){
        
        let $hidden_g = $('.svg_container svg .symbol[visibility="hidden"]')
        let $hidden_path = $('.svg_container svg .symbol path[visibility="hidden"]')
        if($hidden_g.length || $hidden_path.length){
            $hidden_g.attr('visibility', 'visible')
            $hidden_path.attr('visibility', 'visible')
        }else{
            $('.svg_container svg .sponsor_history path').attr('visibility', 'hidden')
        }
    })
    this.$sponsors_table.on('click', 'td:first-child', function(){
        let cls = $(this).parent().data('id').split('.').join('_')
        let path =  $('.svg_container svg .sponsor_history path.'+cls)
        if(path.attr('visibility') == 'hidden'){
            path.attr('visibility', 'visible')
        }else{
            path.attr('visibility', 'hidden')
        }
    })

    this.$content.find('table').on('click', 'th', function(){
        let $th = $(this)
        if($th.index() == 0){
            return
        }
        console.log(Utils)
        let $table = $th.parents('table')

        Utils.table_sort($table, $th)
    })
}

Tab_Chart.prototype.load_keyword_chart = function(kw){
    this.chart = new Keyword_Chart(this.$svg_container, kw)
}

Tab_Chart.prototype.load_sponsor_chart = function(sponsor){
    if(sponsor.name.includes('Qingdao Glitter')){
        if (!('balance' in sponsor) && this.balance.length != 0){
            sponsor['balance'] = this.balance
        }
    }
    this.chart = new Sponsor_Chart(this.$svg_container, sponsor)
}

Tab_Chart.prototype.load_keywords = function(){
    let trs = ''
    let count = 0
    let url = 'https://www.alibaba.com/trade/search?fsb=y&IndexArea=product_en&CatId=&SearchText='
    let f = d3.format('.2f')
    for(let key in this.keywords){
        count++
        let kw = this.keywords[key]
        let sponsors_set = new Set()
        for(let [idx, sponsors] of kw.sponsors.entries()){
            if(idx != 0)
                sponsors_set = new Set([...sponsors_set, ...sponsors])
        }
        let tds = `<td><svg width="18" height="18"><g><path fill="#1f77b4" fill-opacity="1" stroke="white" stroke-width="0" stroke-opacity="1" transform="translate(10, 10)"></path></g></svg></td>`
        tds = `${tds}<td class="count" style="text-align: right;"></td>`
        tds = `${tds}<td class="sponsors_count" style="text-align: right;">${sponsors_set.size}</td>`
        tds = `${tds}<td class="name"><a href="${url}${kw.name.split(' ').join('+')}">${kw.name}</a></td>`
        tds = `${tds}<td class="mean_price" style="text-align: right;">${f(d3.mean(kw.lines[4]))}</td>`
        tds = `${tds}<td class="mean_price" style="text-align: right;">${f(d3.mean(kw.lines[5]))}</td>`
        trs = `${trs}<tr class="${key}" data-id="${key}">${tds}</tr>`
    }
    this.$keywords_table.find('tbody').html(trs)
    this.$keywords_table.find('th.name span').text(count)
}

Tab_Chart.prototype.load_sponsors = function(){
    let trs = ''
    let count = 0
    for(let key in this.sponsors){
        count++
        let sponsor = this.sponsors[key]
        let tds = `<td><svg width="18" height="18"><g><path fill="#1f77b4" fill-opacity="1" stroke="white" stroke-width="0" stroke-opacity="1" transform="translate(10, 10)"></path></g></svg></td>`
        tds = `${tds}<td class="count" style="text-align: right;"></td>`
        tds = `${tds}<td style="text-align: right;">${Object.keys(sponsor.keywords).length}</td>`
        tds = `${tds}<td class="name"><a href="${sponsor.url}">${sponsor.name}</a></td>`
        tds = `${tds}<td style="text-align: right;">${sponsor.years}</td>`
        let idx = sponsor.record.indexOf('Transactions(6 months)')
        if( idx != -1){
            tds = `${tds}<td style="text-align: right;">${sponsor.record[idx-1]}</td>`
            tds = `${tds}<td style="text-align: right;">${sponsor.record[idx+1]}</td>`
        }else{
            tds = `${tds}<td style="text-align: right;">------</td>`
            tds = `${tds}<td style="text-align: right;">------</td>`
        }

        idx = sponsor.record.indexOf("Response Rate")
        if(idx != -1){
            tds = `${tds}<td style="text-align: right;">${sponsor.record[idx+1]}</td>`
        }else{
            tds = `${tds}<td style="text-align: right;">--%</td>`
        }
        trs = `${trs}<tr class="${key.split('.').join('_')}" data-id="${key}">${tds}</tr>`
    }
    this.$sponsors_table.find('tbody').html(trs)
    this.$sponsors_table.find('th.name span').text(count)
}


export {Tab_Chart}