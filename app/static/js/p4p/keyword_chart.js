function Keyword_Chart($container, kws){
    this.$container = $container.empty()
    this.kws = kws

    let that = this

    this.size = {'width': $container.width(), 'height': $container.height()}
    this.margin = {'top': 20, 'bottom': 20, 'left': 30, 'right': 20}

    this.svg = d3.select($container[0]).append('svg')
        .attr('class', 'keyword')
        .attr('width', this.size.width)
        .attr('height', this.size.height)
        .call(d3.zoom().on("zoom", this.zoom()));

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
            if(that.svg.classed('keyword')){
                let $tbody = $('.chart table.sponsors tbody')
                let css_selectors = []
                for(let sponsors of that.kws.sponsors){
                    let key = sponsors[that.cursor_idx]
                    if(key){
                        css_selectors.push(`tr.${key.split('.').join('_')}`)
                    }
                }
                $tbody.find('tr.related').removeClass('related')
                css_selectors.reverse()
                for(let cs of css_selectors){
                    $tbody.find(cs).addClass('related').prependTo($tbody)
                }

                for(let [idx, prices] of that.kws.lines.entries()){
                    if(idx == 0){
                        // data.push(that.yRange[1])
                    }else{
                        data.push(that.yScale(prices[that.cursor_idx]))
                    }
                }
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

Keyword_Chart.prototype.load_xAxis = function(){
    let dt = this.kws.lines[0][0]
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

Keyword_Chart.prototype.load_yAxis = function(){
    let max = d3.max(this.kws.lines[1])
    let min = d3.min(this.kws.lines[5])
    let padding_top = 10
    let padding_bottom = 10

    this.yDomain = [min, max]
    this.yRange = [ this.size.height-this.margin.bottom-padding_bottom, this.margin.top+padding_top]
    this.yScale = d3.scaleLinear().domain(this.yDomain).range(this.yRange)

    this.yRange = [ this.size.height-this.margin.bottom, this.margin.top]
    min = this.yScale.invert(this.yRange[0])
    max = this.yScale.invert(this.yRange[1])

    this.yDomain = [min, max]
    this.yScale = d3.scaleLinear().domain(this.yDomain).range(this.yRange)

    this.yAxis = d3.axisLeft(this.yScale)
    // .tickFormat(function(d){
    //     if(d.getHours() == 0){
    //         return moment(d).format('MM-DD')
    //     }else{
    //         return moment(d).format('HH:mm')
    //     }
    // })
    this.svg.append('g')
        .attr('class', 'yAxis')
        .attr('transform', `translate(${this.margin.left}, 0)`)
        .call(this.yAxis)
}

Keyword_Chart.prototype.load_prices = function(){
    let that = this

    let line = d3.line()
                .x(function(d, j) { return that.xScale(that.kws.lines[0][j]); }) // set the x values for the line generator
                .y(function(d) { return that.yScale(d); }) // set the y values for the line generator 
                .defined(function(d) { return !isNaN(d); })
                .curve(d3.curveMonotoneX) // apply smoothing to the line


    for(let i=1; i<=5; i++){

        let g = this.svg.append('g').attr('class', `line price_line position_${i}`)
        let gs = g.append('path')
                .datum(this.kws.lines[i])
                .attr('class', 'price line')
                .attr('fill', 'None')
                .attr('stroke',d3.schemeDark2[i])
                .attr('stroke-width', 1)
                .attr('d', line)

        g = this.svg.append('g').attr('class', `symbol price_history position_${i}`)
        gs = g.selectAll('g').data(this.kws.lines[i])
                  .enter().append('path')
                  .attr('class', 'price symbol')
                  .attr('d', d3.symbol().type(d3.symbols[i]).size(32))
                  .attr('fill', 'white')
                  .attr('stroke',d3.schemeDark2[i])
                  .attr('stroke-width',1)
                  .attr('stroke-opacity', 0.7)
                  .attr('transform', function(d,j){ 
                      return `translate(${that.xScale(that.kws.lines[0][j])},${that.yScale(that.kws.lines[i][j])})`; 
                  });

        this.symbols_list.push(gs)
    }
}

Keyword_Chart.prototype.load_sponsors = function(){
    let that = this
    console.log(this.kws.sponsors)

    let $tbody = $('table.sponsors tbody')
    $tbody.find('path.symbol').attr('d', '').removeClass('symbol').parents('td').next().empty()

    let symbols = {}
    let sponsors = {}
    for(let i=0; i<=5; i++){

        for(let j=0; j<this.kws.sponsors[i].length; j++){
            let key = this.kws.sponsors[i][j]

            if(!(key in symbols)){
                if(key){
                    let symbol_count = Object.keys(symbols).length
                    let symbol_idx = Math.floor(symbol_count/10)%7
                    let color_idx = symbol_count%10
                    let symbol = d3.symbol().type(d3.symbols[symbol_idx]).size(50)()
                    let color = d3.schemeCategory10[color_idx]
                    symbols[key] = {'symbol':symbol, 'fill': color, 'fill-opacity': 1, 'stroke':'white', 'stroke-width': 0, 'stroke-opacity': 1}

                    d3.select('table.sponsors tbody tr.'+key.split('.').join('_')+' svg path')
                        .attr('class', 'symbol')
                        .attr('d', d => d3.symbol().type(d3.symbols[symbol_idx]).size(100)())
                        .attr('fill', d => color)
                }else{
                    symbols[key] = {'symbol': '', 'fill': 'white', 'fill-opacity': 0, 'stroke':'white', 'stroke-width': 0, 'stroke-opacity': 1}
                }
            }

            if(key){
                if(key in sponsors){
                    sponsors[key] ++
                }else{
                    sponsors[key] = 1
                }
            }
        }

        let g = this.svg.append('g').attr('class', `symbol sponsor_history position_${i}`)
        let gs = g.selectAll('g').data(this.kws.sponsors[i])
                  .enter().append('path')
                  .attr('class', d => d ? d.split('.').join('_') : 'undefined')
                  .attr('d', d=> symbols[d]['symbol'])
                  .attr('fill', d => symbols[d]['fill'])
                  .attr('fill-opacity', d => symbols[d]['fill-opacity'])
                  .attr('stroke', d => symbols[d]['stroke'])
                  .attr('stroke-width', d => symbols[d]['stroke-width'])
                  .attr('stroke-opacity', d => symbols[d]['stroke-opacity'])
                  .attr('transform', function(d,j){ 
                        if(i==0){
                            return `translate(${that.xScale(that.kws.lines[0][j])},${that.yRange[1]})`; 
                        }else{
                            return `translate(${that.xScale(that.kws.lines[0][j])},${that.yScale(that.kws.lines[i][j])})`; 
                        }
                    });

        this.symbols_list.push(gs)
    }

    for(let key in sponsors){
        let $tr = $tbody.find('tr.'+key.split('.').join('_')+' td.count').text(sponsors[key])
    }

    let $trs = $tbody.find('path.symbol').parents('tr')
    $trs.remove().sort(function(a,b){
        let a_count = +$(a).find('td.count').text()
        let b_count = +$(b).find('td.count').text()
        return b_count - a_count;
    }).prependTo($tbody)
}

Keyword_Chart.prototype.zoom = function(){
    let chart = this
        // re-scale y axis during zoom; ref [2]
    return function(){
        chart.x_axis.transition()
            .duration(50)
            .call(chart.xAxis.scale(d3.event.transform.rescaleX(chart.xScale)));

        // re-draw circles using new y-axis scale; ref [3]
        chart.new_xScale = d3.event.transform.rescaleX(chart.xScale);

        let line = d3.line()
                    .x(function(d, j) { return chart.new_xScale(chart.kws.lines[0][j]); }) // set the x values for the line generator
                    .y(function(d) { return chart.yScale(d); }) // set the y values for the line generator 
                    .defined(function(d) { return !isNaN(d); })
                    .curve(d3.curveMonotoneX) // apply smoothing to the line

        let count = 0
        for(let symbols of chart.symbols_list){
            symbols.attr('transform', function(d, j){
                if(count == 5){
                    return `translate(${chart.new_xScale(chart.kws.lines[0][j])},${chart.yRange[1]})`; 
                }else{
                    let idx = count
                    if(idx>5){
                        idx = idx-5
                    }else if(idx<5){
                        idx = idx+1
                    }
                    return `translate(${chart.new_xScale(chart.kws.lines[0][j])},${chart.yScale(chart.kws.lines[idx][j])})`; 
                }   
            })
            count++
        }

        for(let i=1; i<=5; i++){
            // let g = this.svg.append('g').attr('class', `symbol price_history position_${i}`)
            // let gs = g.selectAll('g').data(this.kws.lines[i])
            //           .enter().append('path')
            //           .attr('class', 'price symbol')
            //           .attr('d', d3.symbol().type(d3.symbols[i]).size(16))
            //           .attr('fill', 'white')
            //           .attr('stroke',d3.schemeDark2[i])
            //           .attr('stroke-width',1)
            //           .attr('stroke-opacity', 0.7)
            //           .attr('transform', function(d,j){ 
            //               return `translate(${that.xScale(that.kws.lines[0][j])},${that.yScale(that.kws.lines[i][j])})`; 
            //           });

            // this.symbols_list.push(gs)

            // console.log(chart.svg.selectAll(`g.price_line.position_${i} path`).size())
            chart.svg.select(`g.price_line.position_${i} path`)
                     .attr('d', line)
                    // .datum(this.kws.lines[i])
                    // .attr('class', 'price line')
                    // .attr('fill', 'None')
                    // .attr('stroke',d3.schemeDark2[i])
                    // .attr('stroke-width', 1)
        }

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

Keyword_Chart.prototype.update_xaxis_cursor = function(coords, forced=false){
    let pre_cursor_idx = this.cursor_idx
    this.cursor_idx = undefined
    let xScale = this.xScale
    if(this.new_xScale){
        xScale = this.new_xScale
    }

    let x = coords[0]
    let mdt = moment(xScale.invert(x))

    let th = 180000

    let dts = this.kws.lines[0]
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
Keyword_Chart.prototype.update_yaxis_cursors = function(data){
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
            .attr('d', `M${that.xRange[0]},${d}L${x},${d}`)
        cursor.select('text')
            .text(f(that.yScale.invert(d)))
            .attr('y', d)
        cursor.select('rect')
            .attr('y', d-6)
    })

    cursors.enter().append('g').each(function(d, j){
        let cursor = d3.select(this)
        cursor.append('path')
            .attr('stroke', 'gray')
            .attr('stroke-width', 0.5)
            .attr('d', `M${that.xRange[0]},${d}L${x},${d}`)
        cursor.append('rect')
            .attr('width', that.margin.left)
            .attr('height', 12)
            .attr('fill', 'lightgreen')
            .attr('x', 0)
            .attr('y', d-6)
        cursor.append('text')
            .text(f(that.yScale.invert(d)))
            .attr('font-size', '12px')
            .attr('text-anchor', 'end')
            .attr('text-baseline', 'middle')
            .attr('x', that.margin.left)
            .attr('y', d)
            .attr('dx', -3)
            .attr('dy', 5)
    })

    cursors.exit().remove()

    this.yaxis_cursors.attr('visibility', 'visible')
}

Keyword_Chart.prototype.hide_cursor = function(){
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
export{Keyword_Chart}