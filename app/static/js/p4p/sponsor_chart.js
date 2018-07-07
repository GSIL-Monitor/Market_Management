import {Utils} from '../../libs/utils/utils.js'

function Sponsor_Chart($container, sponsor){
    this.$container = $container.empty()
    this.sponsor = sponsor

    let that = this

    this.size = {'width': $container.width(), 'height': $container.height()}
    this.margin = {'top': 20, 'bottom': 20, 'left': 30, 'right': 20}

    this.do_zoom = this.zoom()
    this.svg = d3.select($container[0]).append('svg')
        .attr('class', 'sponsor')
        .attr('width', this.size.width)
        .attr('height', this.size.height)
        .call(d3.zoom().on("zoom", this.do_zoom));

    this.hold_cursor = true

    this.svg.on('click', function(){
        let coords = d3.mouse(this);
        that.update_xaxis_cursor(coords)
        if(that.hold_cursor){
            that.hold_cursor = false
            $('.chart tr.related').removeClass('related')

            that.xaxis_cursor.select('path')
                .attr('stroke', 'gray')
                .attr('stroke-width', 0.5)
            that.update_xaxis_cursor(coords)
            that.yaxis_cursors.attr('visibility', 'hidden')
        }else{
            that.hold_cursor = true

            that.xaxis_cursor.select('path')
                .attr('stroke', 'black')
                .attr('stroke-width', 0.7)
        }
        if(that.hold_cursor && that.cursor_idx != undefined){
            let data = []
            if(that.svg.classed('sponsor')){
                let $tbody = $('.chart table.keywords tbody')

                let dt = that.dt_list[that.cursor_idx]
                let items = that.dts[dt.format()]
                items.sort(function(a,b){
                    return a[1] - b[1]
                })
                for(let [key, price] of items){
                    data.push(price)
                    $tbody.find(`tr.${key}`).addClass('related').prependTo($tbody)
                }
                data.reverse()
            }
            that.update_yaxis_cursors(data)
        }
    })

    this.svg.on('mousemove', function(){
        let coords = d3.mouse(this);
        if(that.xaxis_cursor.attr('visibility') != 'hidden' && !that.hold_cursor){
            that.update_xaxis_cursor(coords)
        }
    })

    this.load_xAxis()
    this.load_yAxis()

    this.symbols_list = []

    this.load_prices()
    this.load_sponsors()

    this.xaxis_cursor = this.svg.append('g')
        .attr('class', 'xaxis_cursor')
        .attr('visibility', 'hidden')
    this.xaxis_cursor.append('path')
        .attr('stroke', 'gray')
        .attr('stroke-width', 0.5)
    this.xaxis_cursor.append('rect')
        .attr('width', 70)
        .attr('height', this.margin.bottom-1)
        .attr('fill', 'lightgreen')
        .attr('y', this.size.height - this.margin.bottom + 1)
    this.xaxis_cursor.append('text')
        .attr('text-anchor', 'middle')
        .attr('y', this.size.height - this.margin.bottom)
        .attr('dy', 16)

    this.yaxis_cursors = this.svg.append('g')
        .attr('class', 'yaxis_cursor')
        .attr('visibility', 'hidden')
}

Sponsor_Chart.prototype.load_xAxis = function(){
    let dt = this.sponsor.dt
    if(moment(dt.format('YYYY-MM-DD')+' 23:00:00').isBefore(dt)){
        dt = moment(dt.format('YYYY-MM-DD')).add(1, 'd')
    }
    let dt_start = moment(dt.format('YYYY-MM-DD')).toDate()
    let dt_end = moment(dt.format('YYYY-MM-DD')).add(1, 'd').toDate()
    
    this.xDomain = [dt_start, dt_end]
    this.xRange = [this.margin.left, this.size.width-this.margin.right]
    this.xScale = d3.scaleTime().domain(this.xDomain).range(this.xRange)
    
    this.xAxis = d3.axisBottom(this.xScale).ticks(24).tickFormat(function(d){
        if(d.getHours() == 0){
            return moment(d).format('MM-DD')
        }else{
            return moment(d).format('HH:mm')
        }
    })

    this.x_axis = this.svg.append('g')
        .attr('class', 'xAxis')
        .attr('transform', `translate(0,${this.size.height-this.margin.bottom})`)
        .call(this.xAxis)
}

Sponsor_Chart.prototype.load_yAxis = function(){
    let max = 0
    let min = 99999

    let maxs = []
    let symbols = {}

    let $table = $('.chart table.keywords')
    let $tbody = $table.find('tbody')
    $tbody.find('path.symbol').attr('d', '').removeClass('symbol').parents('td').next().empty()

    let dts = {}
    let dt_list = []
    for(let [key, kws] of Object.entries(this.sponsor.keywords)){
        if(!(key in symbols)){
            let symbol_count = Object.keys(symbols).length
            let symbol_idx = Math.floor(symbol_count/10)%7
            let color_idx = symbol_count%10

            symbols[key] = {}
            symbols[key]['symbol'] = d3.symbol().type(d3.symbols[symbol_idx]).size(32)()
            symbols[key]['color'] = d3.schemeCategory10[color_idx]

            d3.select('.chart table.keywords tbody tr[data-id="'+key+'"] svg path')
                .attr('class', 'symbol')
                .attr('d', d3.symbol().type(d3.symbols[symbol_idx]).size(100)())
                .attr('fill', d3.schemeCategory10[color_idx] )
            $tbody.find('tr[data-id="'+key+'"] td.count').text(kws.length)
        }

        for(let item of kws){
            let [dt, price] = item

            if(max<price) {
                maxs.push(price)
                if(maxs.length > 5){
                    maxs.shift()
                }
                max = price
            }
            if(min>price && price != 0){
                min = price
            }

            let dt_key = dt.format()
            if(dt_key in dts){
                dts[dt_key].push([key, price])
            }else{
                dts[dt_key] = []
                dts[dt_key].push([key, price])
                dt_list.push(dt)
            }
        }
    }
    if('balance' in this.sponsor){
        for(let item of this.sponsor.balance){
            let [dt, price] = item

            price = Math.abs(price)
            if(max<price) {
                maxs.push(price)
                if(maxs.length > 5){
                    maxs.shift()
                }
                max = price
            }
            if(min>price && price != 0){
                min = price
            }
        }
    }
    dt_list.sort(function(a,b){
        return a.isBefore(b) ? -1 : (a.isAfter(b) ? 1 : 0)
    })
    maxs.reverse()
    this.max_prices = maxs
    this.dt_list = dt_list
    this.dts = dts
    this.symbols = symbols
    let $th = $table.find('th:nth-child(2)')
    $th[0].setAttribute('descending', '')
    Utils.table_sort($table, $th)

    if(min == max){
        min = min - 1
        max = max + 1
    }

    this.y_domain_min = min

    let padding_top = 10
    let padding_bottom = 10

    this.yDomain = [min, max]
    this.yRange = [this.size.height-this.margin.bottom-padding_bottom, this.margin.top+padding_top]
    this.yScale = d3.scaleLinear().domain(this.yDomain).range(this.yRange)

    this.yRange = [this.size.height-this.margin.bottom, this.margin.top]
    min = this.yScale.invert(this.yRange[0])
    max = this.yScale.invert(this.yRange[1])

    this.yDomain = [min, max]
    this.yScale = d3.scaleLinear().domain(this.yDomain).range(this.yRange)

    this.yAxis = d3.axisLeft(this.yScale)

    this.y_axis = this.svg.append('g')
        .attr('class', 'yAxis')
        .attr('transform', `translate(${this.margin.left}, 0)`)
        .call(this.yAxis)
}

Sponsor_Chart.prototype.load_prices = function(){
    let that = this

    let line = d3.line()
                .x(function(d, j) { return that.xScale(d[0]); }) // set the x values for the line generator
                .y(function(d, j) { return d[1] == 0 ? that.yRange[1] : that.yScale(d[1]); }) // set the y values for the line generator 
                .defined(function(d) { return !isNaN(d[1]); })
                .curve(d3.curveMonotoneX) // apply smoothing to the line

    for(let [key, kws]of Object.entries(this.sponsor.keywords)){
        let g = this.svg.append('g').attr('class', `line price_line`)
        let gs = g.append('path')
                .datum(kws)
                .attr('class', 'price line')
                .attr('data-id', key)
                .attr('fill', 'None')
                .attr('stroke', this.symbols[key]['color'])
                .attr('stroke-width', 1)
                .attr('d', line)

        g = this.svg.append('g').attr('class', `symbol price_history`)
        gs = g.selectAll('g').data(kws)
                  .enter().append('path')
                  .attr('class', 'price symbol')
                  .attr('d', this.symbols[key]['symbol'])
                  .attr('fill', this.symbols[key]['color'])
                  .attr('stroke', this.symbols[key]['color'])
                  .attr('stroke-width',1)
                  .attr('stroke-opacity', 0.7)
                  .attr('transform', function(d,j){
                    if(d[1] == 0){
                        return `translate(${that.xScale(d[0])},${that.yRange[1]})`; 
                    }else{
                        return `translate(${that.xScale(d[0])},${that.yScale(d[1])})`; 
                    }
                  });

        this.symbols_list.push(gs)
    }

    if('balance' in this.sponsor){
        let g = this.svg.append('g').attr('class', `symbol balance_changes`)
        let gs = g.selectAll('g').data(this.sponsor.balance)
                  .enter().append('path')
                  .attr('class', 'balance symbol')
                  .attr('d', d3.symbol().type(d3.symbols[1]).size(64)())
                  .attr('fill', (d,j) => parseFloat(d[1]) < 0 ? '#00ff00' : '#ff0000')
                  .attr('stroke', (d,j) => parseFloat(d[1]) < 0 ? '#00ff00' : '#ff0000')
                  .attr('stroke-width',0)
                  .attr('transform', function(d,j){
                        return `translate(${that.xScale(d[0])},${that.yScale(Math.abs(parseFloat([1])))}) rotate(-45)`;
                  });
        this.symbols_list.push(gs)
    }
}

Sponsor_Chart.prototype.load_sponsors = function(){
}

Sponsor_Chart.prototype.set_yDomain_max = function(max){

    let padding_top = 10
    let padding_bottom = 10

    this.yDomain = [this.y_domain_min, max]
    let yRange = [this.size.height-this.margin.bottom-padding_bottom, this.margin.top]
    let yScale = d3.scaleLinear().domain(this.yDomain).range(yRange)

    this.yRange = [this.size.height-this.margin.bottom, this.margin.top]
    let min = yScale.invert(this.yRange[0])

    this.yDomain[0] = min
    this.yScale = d3.scaleLinear().domain(this.yDomain).range(this.yRange)

    this.y_axis.transition()
            .duration(50)
            .call(this.yAxis.scale(this.yScale))

    let that = this
    let xScale = this.xScale
    if(this.new_xScale){
        xScale = this.new_xScale
    }
    let line = d3.line()
            .x(function(d, j) { return xScale(d[0]); }) // set the x values for the line generator
            .y(function(d, j) { return d[1] == 0 ? that.yRange[1] : that.yScale(d[1]); }) // set the y values for the line generator 
            .defined(function(d) { return !isNaN(d[1]); })
            .curve(d3.curveMonotoneX) // apply smoothing to the line

    for(let symbols of this.symbols_list){
        symbols.attr('transform', function(d){
            if(d[1] == 0){
                return `translate(${xScale(d[0])},${that.yRange[1]})`; 
            }else{
                return `translate(${xScale(d[0])},${that.yScale(d[1])})`; 
            }
        });
    }

    this.svg.selectAll('.price_line path').each(function(){
        let path = d3.select(this)
        path.attr('d', line)
    })

    if(this.xaxis_cursor.attr('visibility') != 'hidden'){
        if(this.cursor_datetime){
            let x = xScale(this.cursor_datetime)
            this.update_xaxis_cursor([x, 0], true)

            if(this.yaxis_cursors.attr('visibility') != 'hidden'){
                this.yaxis_cursors.selectAll('path').each(function(){
                    let d = this.getAttribute('d').replace(/L[-.\d]*/, `L${x}`)
                    this.setAttribute('d', d)
                })
            }
        }
    }
}

Sponsor_Chart.prototype.zoom = function(){
    let chart = this
        // re-scale y axis during zoom; ref [2]
    return function(){
        chart.x_axis.transition()
            .duration(50)
            .call(chart.xAxis.scale(d3.event.transform.rescaleX(chart.xScale)));

        // re-draw circles using new y-axis scale; ref [3]
        chart.new_xScale = d3.event.transform.rescaleX(chart.xScale);

        let line = d3.line()
                .x(function(d, j) { return chart.new_xScale(d[0]); }) // set the x values for the line generator
                .y(function(d, j) { return d[1] == 0 ? chart.yRange[1] : chart.yScale(d[1]); }) // set the y values for the line generator 
                // .defined(function(d) { return !isNaN(d); })
                .curve(d3.curveMonotoneX) // apply smoothing to the line

        for(let symbols of chart.symbols_list){
            if(symbols.classed('balance')){
                symbols.attr('transform', function(d){
                    return `translate(${chart.new_xScale(d[0])},${chart.yScale(Math.abs(parseFolat(d[1])))}) rotate(-45)`;
                });
            }else{
                symbols.attr('transform', function(d){
                    if(d[1] == 0){
                        return `translate(${chart.new_xScale(d[0])},${chart.yRange[1]})`; 
                    }else{
                        return `translate(${chart.new_xScale(d[0])},${chart.yScale(d[1])})`; 
                    }
                });
            }
        }

        chart.svg.selectAll('.price_line path').each(function(){
            let path = d3.select(this)
            path.attr('d', line)
        })

        if(chart.xaxis_cursor.attr('visibility') != 'hidden'){
            if(chart.cursor_datetime){
                let x = chart.new_xScale(chart.cursor_datetime)
                chart.update_xaxis_cursor([x, 0], true)

                if(chart.yaxis_cursors.attr('visibility') != 'hidden'){
                    chart.yaxis_cursors.selectAll('path').each(function(){
                        let d = this.getAttribute('d').replace(/L[-.\d]*/, `L${x}`)
                        this.setAttribute('d', d)
                    })
                }
            }
        }
    }
}

Sponsor_Chart.prototype.update_xaxis_cursor = function(coords, forced=false){
    let pre_cursor_idx = this.cursor_idx
    this.cursor_idx = undefined
    let xScale = this.xScale
    if(this.new_xScale){
        xScale = this.new_xScale
    }

    let x = coords[0]
    let mdt = moment(xScale.invert(x))

    let th = 180000

    let dts = this.dt_list
    let idx = locationOf(mdt, dts)
    idx++

    let pdiff = 86400000
    let adiff = 86400000

    if(idx < dts.length){
        adiff = dts[idx].diff(mdt)
    }

    if(idx != 0){
        pdiff = mdt.diff(dts[idx-1])
    }

    if(pdiff < adiff && pdiff < th){
        mdt = dts[idx-1]
        this.cursor_idx = idx-1
    }

    if(pdiff > adiff && adiff < th){
        mdt = dts[idx]
        this.cursor_idx = idx
    }

    // console.log(idx, this.cursor_idx, pre_cursor_idx)
    if(forced || pre_cursor_idx == undefined || (this.cursor_idx != undefined && this.cursor_idx != pre_cursor_idx)){
        this.cursor_datetime = mdt
        x = xScale(mdt)

        this.xaxis_cursor.attr('visibility', 'visible')
        this.xaxis_cursor.select('path')
            .attr('d', `M${x},${this.yRange[0]}L${x},${this.yRange[1]}`)

        this.xaxis_cursor.select('text')
            .text(this.cursor_datetime.format('HH:mm:ss'))
            .attr('x', x)
        this.xaxis_cursor.select('rect')
            .attr('x', x-35)
    }
}
Sponsor_Chart.prototype.update_yaxis_cursors = function(data){
    let that = this
    let xScale = this.xScale
    if(this.new_xScale){
        xScale = this.new_xScale
    }
    let x = xScale(this.cursor_datetime)

    let cursors = this.yaxis_cursors.selectAll('g').data(data)

    let f = d3.format(".1f")
    cursors.each(function(d, j){
        let cursor = d3.select(this)
        cursor.select('path')
            .attr('d', `M${that.xRange[0]},${that.yScale(d)}L${x},${that.yScale(d)}`)
        cursor.select('text')
            .text(f(d))
            .attr('y', that.yScale(d))
        cursor.select('rect')
            .attr('y', that.yScale(d)-6)
    })

    cursors.enter().append('g').each(function(d, j){
        let cursor = d3.select(this)
        cursor.append('path')
            .attr('stroke', 'gray')
            .attr('stroke-width', 0.5)
            .attr('d', `M${that.xRange[0]},${that.yScale(d)}L${x},${that.yScale(d)}`)
        cursor.append('rect')
            .attr('width', that.margin.left)
            .attr('height', 12)
            .attr('fill', 'lightgreen')
            .attr('x', 0)
            .attr('y', that.yScale(d)-6)
        cursor.append('text')
            .text(f(d))
            .attr('font-size', '12px')
            .attr('text-anchor', 'end')
            .attr('text-baseline', 'middle')
            .attr('x', that.margin.left)
            .attr('y', that.yScale(d))
            .attr('dx', -3)
            .attr('dy', 5)
    })

    cursors.exit().remove()

    this.yaxis_cursors.attr('visibility', 'visible')
}

Sponsor_Chart.prototype.hide_cursor = function(){
    this.xaxis_cursor.attr('visibility', 'hidden')
    this.yaxis_cursors.attr('visibility', 'hidden')
}

function locationOf(element, array, start, end) {
    start = start || 0;
    end = end || array.length;
    let pivot = parseInt(start + (end - start) / 2, 10);
    if (array[pivot].isSame(element)) 
        return pivot;
    if (end - start <= 1)
        return array[pivot].isAfter(element) ? pivot - 1 : pivot;
    if (array[pivot].isBefore(element)) {
        return locationOf(element, array, pivot, end);
    } else {
        return locationOf(element, array, start, pivot);
    }
}
export{Sponsor_Chart}