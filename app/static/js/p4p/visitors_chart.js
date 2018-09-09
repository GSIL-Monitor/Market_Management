function Visitors_Chart($container, visitors){
    this.$container = $container.empty()
    this.visitors = {}

    let that = this

    this.size = {'width': $container.parent().width(), 'height': $container.height()}
    this.margin = {'top': 20, 'bottom': 20, 'left': 37, 'right': 7}

    this.svg = d3.select($container[0]).append('svg')
        .attr('class', 'visitors')
        .attr('width', this.size.width)
        .attr('height', this.size.height)
        // .call(d3.zoom().on("zoom", this.zoom()));

    this.start_pos = undefined
    this.svg.on('click', function(){
        let coords = d3.mouse(this);
        if(!that.start_pos){
            that.start_pos = coords
        }else{
            that.load_visitors(that.start_pos, coords)
            that.start_pos = undefined
        }
    })

    this.svg.on('mousemove', function(){
        let coords = d3.mouse(this);
        that.update_xaxis_cursor(coords)
        that.update_yaxis_cursors(coords)
        if(that.start_pos){
            that.update_select_rect(that.start_pos, coords)
        }
    })

    this.min_date = undefined
    this.max_date = undefined
    // this.pvs = []
    let today = moment().format('YYYY-MM-DD')
    for(let visitor of visitors){
        let vid = visitor['id']
        this.visitors[vid] = visitor

        for(let pv of visitor['pv-detail']){
            let [d, t] = pv.time.split(' ')
            d = moment.tz(d, "America/Los_Angeles")
            t = moment.tz(today+'T'+t, "America/Los_Angeles")
            pv['d'] = d
            pv['t'] = t
            if(!this.min_date || d.isBefore(this.min_date)){
                this.min_date = d
            }
            if(!this.max_date || d.isAfter(this.max_date)){
                this.max_date = d
            }
        }
    }
    console.log(this.visitors)
    $('.visitors table.visitor_list').data('visitors', this.visitors)

    this.load_xAxis()
    this.load_xAxis_top()
    this.load_yAxis()

    this.select_rect = this.svg.append('g')
        .attr('class', 'select_rect')
        .attr('visibility', 'hidden')
    this.select_rect.append('rect')
        .attr('fill', 'lightgrey')
        // .attr('width', 70)
        // .attr('height', this.margin.bottom-1)
        // .attr('y', this.size.height - this.margin.bottom + 1)

    this.symbols_list = []
    this.load_pvs()

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

    this.xaxis_cursor_top = this.svg.append('g')
        .attr('class', 'xaxis_cursor_top')
        .attr('visibility', 'hidden')
    this.xaxis_cursor_top.append('path')
        .attr('stroke', 'gray')
        .attr('stroke-width', 0.5)
    this.xaxis_cursor_top.append('rect')
        .attr('width', 70)
        .attr('height', this.margin.top-1)
        .attr('fill', 'lightgreen')
        .attr('y', 1)
    this.xaxis_cursor_top.append('text')
        .attr('text-anchor', 'middle')
        .attr('y', 0)
        .attr('dy', 16)

    this.yaxis_cursor = this.svg.append('g')
        .attr('class', 'yaxis_cursor')
        .attr('visibility', 'hidden')
    this.yaxis_cursor.append('path')
        .attr('stroke', 'gray')
        .attr('stroke-width', 0.5)
    this.yaxis_cursor.append('rect')
        .attr('width', that.margin.left)
        .attr('height', 14)
        .attr('fill', 'lightgreen')
        .attr('x', 0)
    this.yaxis_cursor.append('text')
        .attr('font-size', '12px')
        .attr('text-anchor', 'end')
        .attr('text-baseline', 'middle')
        .attr('x', that.margin.left)
        .attr('dx', -5)
        .attr('dy', 5)

}

Visitors_Chart.prototype.load_xAxis = function(){
    let today = moment().format('YYYY-MM-DD')
    let dt_start = moment.tz(today+' 00:00:00', "America/Los_Angeles").toDate()

    let dt_end = moment.tz(today+' 00:00:00', "America/Los_Angeles").add(1, 'd').toDate()

    this.xDomain = [dt_start, dt_end]
    this.xRange = [this.margin.left, this.size.width-this.margin.right]
    this.xScale = d3.scaleTime().domain(this.xDomain).range(this.xRange)
    this.xAxis = d3.axisBottom(this.xScale).ticks(24).tickFormat(function(d){
        // if(d.getHours() == 0){
        //     return moment(d).tz('America/Los_Angeles').format('MM-DD')
        // }else{
        //     return moment(d).tz('America/Los_Angeles').format('HH:mm')
        // }
        return moment(d).tz('America/Los_Angeles').format('HH:mm')
    })
    this.x_axis = this.svg.append('g')
        .attr('class', 'xAxis')
        .attr('transform', `translate(0,${this.size.height-this.margin.bottom})`)
        .call(this.xAxis)
}

Visitors_Chart.prototype.load_xAxis_top = function(){
    let today = moment().format('YYYY-MM-DD')
    let dt_start = moment.tz(today+' 00:00:00', "America/Los_Angeles").toDate()

    let dt_end = moment.tz(today+' 00:00:00', "America/Los_Angeles").add(1, 'd').toDate()

    this.xDomain = [dt_start, dt_end]
    this.xRange = [this.margin.left, this.size.width-this.margin.right]
    this.xScale = d3.scaleTime().domain(this.xDomain).range(this.xRange)
    this.xAxis = d3.axisTop(this.xScale).ticks(24).tickFormat(function(d){
        return moment(d).tz('Asia/Shanghai').format('HH:mm')
    })
    this.x_axis = this.svg.append('g')
        .attr('class', 'xAxis')
        .attr('transform', `translate(0,${this.margin.top})`)
        .call(this.xAxis)
}

Visitors_Chart.prototype.load_yAxis = function(){
    let max = this.max_date.toDate()
    let min = this.min_date.toDate()
    let padding_top = 10
    let padding_bottom = 10

    this.yDomain = [min, max]
    this.yRange = [ this.size.height-this.margin.bottom-padding_bottom, this.margin.top+padding_top]
    // this.yRange = [ this.size.height-this.margin.bottom, this.margin.top]
    this.yScale = d3.scaleLinear().domain(this.yDomain).range(this.yRange)

    this.yRange = [ this.size.height-this.margin.bottom, this.margin.top]
    min = this.yScale.invert(this.yRange[0])
    max = this.yScale.invert(this.yRange[1])

    this.yDomain = [min, max]
    this.yScale = d3.scaleLinear().domain(this.yDomain).range(this.yRange)

    this.yAxis = d3.axisLeft(this.yScale).tickFormat(function(d){
        // if(d.getHours() == 0){
        //     return moment(d).format('MM-DD')
        // }else{
        //     return moment(d).format('HH:mm')
        // }
        return moment(d).format('MM-DD')
    })
    this.svg.append('g')
        .attr('class', 'yAxis')
        .attr('transform', `translate(${this.margin.left}, 0)`)
        .call(this.yAxis)
}

Visitors_Chart.prototype.load_pvs = function(){
    let that = this
    console.log(this.visitors)
    for(let id in this.visitors){
        let region = this.visitors[id]['region'].split(' ').join('_')
        // console.log(this.visitors[id]['pv-detail'].length)
        let g = this.svg.append('g').attr('class', `symbol_list visitor ${id} ${region}`)
        let gs = g.selectAll('g').data(this.visitors[id]['pv-detail'])
                  .enter().append('path')
                  .attr('class', function(d,j){
                    if(d.inquiried){
                        return 'symbol page_view inquiried'
                    }else if(d.tm_inquiried){
                        return 'symbol page_view tm_inquiried'
                    }else{
                        return 'symbol page_view'
                    }
                  })
                  .attr('d', function(d,j){
                    if(d.inquiried)
                        return d3.symbol().type(d3.symbols[4]).size(32)()
                    else if(d.tm_inquiried)
                        return d3.symbol().type(d3.symbols[5]).size(32)()
                    else
                        return d3.symbol().type(d3.symbols[0]).size(24)()
                  })
                  .attr('fill', function(d,j){
                        if(d.inquiried || d.tm_inquiried){
                            return "red";
                        }else{
                            return "gray";
                        }
                  })
                  .attr('fill-opacity', function(d,j){
                        if(d.inquiried || d.tm_inquiried){
                            return 1
                        }else{
                            return 0.5
                        }
                  })
                  // .attr('stroke', d3.schemeDark2[2])
                  // .attr('stroke-width', 1)
                  // .attr('stroke-opacity', 0.7)
                  .attr('transform', function(d,j){ 
                      return `translate(${that.xScale(d['t'])},${that.yScale(d['d'])})`; 
                  });

        this.symbols_list.push(gs)
    }
}

Visitors_Chart.prototype.update_xaxis_cursor = function(coords){

    // xAxis at bottom
    let x = coords[0]
    let cursor_time = moment(this.xScale.invert(x))
    this.xaxis_cursor.attr('visibility', 'visible')
    this.xaxis_cursor.select('path')
        .attr('d', `M${x},${this.yRange[0]}L${x},${this.yRange[1]}`)

    this.xaxis_cursor.select('text')
        .text(cursor_time.tz('America/Los_Angeles').format('HH:mm:ss'))
        .attr('x', x)
    this.xaxis_cursor.select('rect')
        .attr('x', x-35)

    // xAxis at top
    this.xaxis_cursor_top.attr('visibility', 'visible')
    this.xaxis_cursor_top.select('path')
        .attr('d', `M${x},${this.yRange[0]}L${x},${this.yRange[1]}`)

    this.xaxis_cursor_top.select('text')
        .text(cursor_time.tz('Asia/Shanghai').format('HH:mm:ss'))
        .attr('x', x)
    this.xaxis_cursor_top.select('rect')
        .attr('x', x-35)
}

Visitors_Chart.prototype.update_yaxis_cursors = function(coords){

    let x = coords[0]
    let cursor_time = moment(this.xScale.invert(x))
    let y = coords[1]
    let cursor_date = moment(this.yScale.invert(y))

    this.yaxis_cursor.attr('visibility', 'visible')
    this.yaxis_cursor.select('path')
            .attr('d', `M${this.xRange[0]},${y}L${x},${y}`)

    this.yaxis_cursor.select('text')
        .text(cursor_date.format('MM-DD'))
        .attr('y', y)
    this.yaxis_cursor.select('rect')
        .attr('y', y-6)
}

Visitors_Chart.prototype.update_select_rect = function(start_coords, end_coords){

    let x = start_coords[0]
    let y = start_coords[1]

    let w = end_coords[0] - start_coords[0]
    let h = end_coords[1] - start_coords[1]

    if(w<0){
        w = Math.abs(w)
        x = end_coords[0]
    }
    if(h<0){
        h = Math.abs(h)
        y = end_coords[1]
    }

    this.select_rect.attr('visibility', 'visible')
    this.select_rect.select('rect')
        .attr('width', w)
        .attr('height', h)
        .attr('x', x)
        .attr('y', y)
}

Visitors_Chart.prototype.load_visitors = function(start_coords, end_coords){
    
    let cursor_time_0 = moment(this.xScale.invert(start_coords[0]))
    let cursor_time_1 = moment(this.xScale.invert(end_coords[0]))
    let cursor_date_0 = moment(this.yScale.invert(start_coords[1]))
    let cursor_date_1 = moment(this.yScale.invert(end_coords[1]))

    let start_time = d3.min([cursor_time_0, cursor_time_1])
    let end_time = d3.max([cursor_time_0, cursor_time_1])
    let start_date = d3.min([cursor_date_0, cursor_date_1])
    let end_date = d3.max([cursor_date_0, cursor_date_1])

    // console.log(start_time.tz('America/Los_Angeles').format('HH:mm:ss'), end_time.tz('America/Los_Angeles').format('HH:mm:ss'))
    // console.log(start_date.format('MM-DD'), end_date.format('MM-DD'))
    // console.log(this.visitors)

    let trs = ''
    for(let id in this.visitors){
        let tds = ''
        let v = this.visitors[id]
        let region = v.region.split(' ').join('_')

        let selected = false
        for(let pv of v['pv-detail']){
            if(pv.d.isSameOrAfter(start_date) && pv.d.isSameOrBefore(end_date)){
                if(pv.t.isSameOrAfter(start_time) && pv.t.isSameOrBefore(end_time)){
                    selected = true
                    break
                }
            }
        }

        if(!selected){
            continue
        }

        if($('.visitors svg g.'+id).attr('visibility')=="hidden"){
            continue
        }

        tds = `${tds}<td class="vid">${id}</td>`
        tds = `${tds}<td class="region">${v.region}</td>`
        tds = `${tds}<td class="pv">${v.pv}</td>`
        tds = `${tds}<td class="stay">${v.stay}</td>`

        let kw_divs = ""
        for(let [idx, kw] of v.keywords.entries()){
            let cls = ""
            if('search_keyword_indices' in v && v.search_keyword_indices.includes(idx)){
                cls = ' class="is_searched"'
            }
            kw_divs = `${kw_divs}<div${cls}>${kw}</div>`
        }
        tds = `${tds}<td class="keywords">${kw_divs}</td>`

        let msa_divs = ""
        for(let acts of v['minisite-acts']){
            msa_divs = `${msa_divs}<div>${acts}</div>`
        }
        tds = `${tds}<td class="minisite_acts">${msa_divs}</td>`

        let wsa_divs = ""
        for(let acts of v['website-acts']){
            wsa_divs = `${wsa_divs}<div>${acts}</div>`
        }
        tds = `${tds}<td class="minisite_acts">${wsa_divs}</td>`
        trs = `${trs}<tr class="visitor ${id} ${region}" data-vid="${id}">${tds}</tr>`
    }

    $('.visitors table.visitor_list tbody').html(trs)
}
export{Visitors_Chart}