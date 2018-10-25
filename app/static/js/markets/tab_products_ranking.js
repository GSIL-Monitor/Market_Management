import {Tab} from '../framework/tab.js'

function Tab_products_ranking(socket, market, categories=undefined, directory=undefined, filename='hot_searched_keywords.json', compact=false){
    Tab.call(this, socket, market, categories, directory, filename)
    
    this.name = 'products_ranking'
    this.title = '产品排名'
    this.hot_searched_keywords = []
    this.binding = {}
    this.products_rankings = {}

    this.colors = ['#e6194b', '#3cb44b', '#ffe119', '#4363d8', '#f58231', '#911eb4', '#46f0f0', '#f032e6', '#bcf60c', '#fabebe', '#008080', '#e6beff', '#9a6324', '#fffac8', '#800000', '#aaffc3', '#808000', '#ffd8b1', '#000075', '#808080']
    this.color_idx = 0

    this.load_keyword_groups()
    let buttons = `<button type="button" class="btn btn-sm btn-primary update_rankings">更新</button>`
    // let buttons = ``
    this.$button_group = $(`<div class="btn-group mr-2 products_ranking" role="group">${buttons}</div>`)

    this.$content = fw.load_from_template('#template_products_ranking')

    this.shift_pressed = false
    this.shift_idx = undefined
    this.shift_selection = []
    let that = this

    this.$content.find('#load_supplier').on('click', function(){
        let sid = $('select.suppliers').val()
        let supplier = that.products_rankings[sid]
        let color = that.colors[that.color_idx]
        that.color_idx++
        that.load_supplier(supplier, color)
    })

    $('body').on("keyup", function(e){
        console.log('keyup: ', e.key);
        if(e.key == 'Shift'){
            that.shift_pressed = false
        }
        if(e.key == 'Escape'){
            that.shift_idx = undefined
            that.shift_pressed = false
            that.$content.find('td.place_holder').attr('style', '')
            that.$content.find('td.glittereyelash').attr('style', 'background-color: #000000;border:1px solid #000000;')
            that.$content.find('table tr.selected').removeClass('selected')
        }
    })

    $('body').on("keydown", function(e){
        console.log('keyup: ', e.key);
        if(e.key == 'Shift'){
            that.shift_pressed = true
        }
    })

    this.$button_group.find('.update_rankings').click(function(){
    	let kws = []
    	for(let tr of that.$content.find('table.products_ranking tr.selected')){
    		kws.push($(tr).data('word'))
    	}
    	that.socket.emit('crawl_products_rankings', this.market, kws)
    })

	this.$content.find('table.products_ranking tbody').on('click', 'tr', function(){
		console.log(that.shift_pressed, $(this).index())
		let $tbody = that.$content.find('table.products_ranking tbody')
		let $tr = $(this)
		let idx = $tr.index()
		if(that.shift_pressed){
			if(that.shift_idx==undefined){
				that.shift_idx = idx
				$tr.addClass('selected')
			}else{
				for(let $e of that.shift_selection){
					$e.removeClass('selected')
				}
				that.shift_selection = []

				let step = 1
				if(idx>that.shift_idx){
					step = -1
				}

				do{
					if(idx==that.shift_idx){
						break
					}

					$tr.addClass('selected')
					that.shift_selection.push($tr)
					idx = idx + step
					console.log(`tr:nth-child(${idx+1})`)
					$tr = $tbody.find(`tr:nth-child(${idx+1})`)
					
				}while(true)
			}
		}else{
			$tr.toggleClass('selected')
			if($tr.hasClass('selected')){
				that.shift_idx = idx
			}
		}
	})    

    this.$content.find('table.products_ranking tbody').on('click', 'td.place_holder', function(){
    	if(that.shift_pressed){
    		return
    	}
        let key = $(this).data('supplier')
        console.log(key)
        that.$content.find('select.suppliers').val(key).selectpicker('refresh')

        let record = $(this).data('record')
        console.log(record)
    })

    this.$content.find('#load_keywords').on('click', function(){
        that.load_keywords($('select.kws_grp').val())
    })

    this.socket.on('crawl_products_rankings_finished_kws', function(kws){
    	let $tbody = that.$content.find('table.products_ranking tbody')
    	for(let kw of kws){
    		// let cls = kw.split(' ').join('_')
            let cls = kw.replace(/ /g, '-space-')
            cls = cls.replace(/%/g, '-percent-')
            cls = cls.replace(/\./g, '-point-')
    		console.log(cls)
    		let $tr = $tbody.find(`tr.${cls}`)
    		$tr.removeClass('selected')
    	}
    })

    this.socket.on('crawl_products_rankings_results', function(records){
    	that.load_products_rankings(records)
    })

    this.fetch_values_from_server()
        .then(function(results){
            that.hot_searched_keywords = results[0]
            console.log(that.hot_searched_keywords.length)
        }).catch(error => console.log(error))
}

Tab_products_ranking.prototype = Tab.prototype

Tab_products_ranking.prototype.load_keywords = function(grp){
    let kws = []
    let tbody = this.$content.find('table.products_ranking tbody')
    let trs = ''
    let idx = 1
    for(let item of this.hot_searched_keywords){

        if(!(item.keyword in this.binding) || this.binding[item.keyword] != grp){
            continue
        }
        
        let key = item.keyword

        if(!(key in this.products_rankings)){
            kws.push(key)
        }
        let tds =''
        tds = `${tds}<td class="number">${idx}</td>`
        tds = `${tds}<td class="number">${item.supplier_competition}</td>`
        tds = `${tds}<td class="number">${item.showroom_count}</td>`
        tds = `${tds}<td class="number">${item.search_frequency}</td>`
        tds = `${tds}<td class="keyword">${key}</td>`

        let pages = 5
        let page_counts = 36
        for(let i = 0; i<pages; i++){
            for(let j=0; j<page_counts;j++){
                if((i==0 && j<6) || i==1 || i==3){
                    tds = `${tds}<td class="place_holder page_even"></td>`
                }else{
                    tds = `${tds}<td class="place_holder"></td>`
                }
            }
        }


        let cls = key.replace(/ /g, '-space-')
        cls = cls.replace(/%/g, '-percent-')
        cls = cls.replace(/\./g, '-point-')

        trs = `${trs}<tr class="${cls}" data-word="${key}">${tds}</tr>`
        idx ++
    }
    tbody.empty().append(trs)
    this.load_suppliers(kws)
}

Tab_products_ranking.prototype.load_supplier = function(supplier, color){

    let style = `background-color: ${color};border:1px solid ${color};`
    let $tbody = this.$content.find('table.products_ranking tbody')
    for(let kw in supplier){
        if(kw=='company' || kw=='id' || kw=='occurrences'){
            continue
        }
        // let cls = kw.split(' ').join('_')

        let cls = kw.replace(/ /g, '-space-')
        cls = cls.replace(/%/g, '-percent-')
        cls = cls.replace(/\./g, '-point-')

        let $tr = $tbody.find(`tr.${cls}`)
        if($tr.length==0){
            continue
        }

        for(let record of supplier[kw]){
            let loc = record.location
            let idx_td = (loc.page-1)*36+loc.position+5
            $tr.find(`td:nth-child(${idx_td})`)
                .addClass(supplier.id)
                .attr('style', style)
                .attr('data-supplier', supplier.id)
                .data('record', record)
        }
        
    }
    console.log(supplier)
}

Tab_products_ranking.prototype.load_suppliers = function(kws){
    let that = this
    this.socket.emit('get_products_rankings', this.market, kws, function(data){
        that.load_products_rankings(data)
    })
}

Tab_products_ranking.prototype.crawl_products_rankings = function(kws){
    let that = this
    this.socket.emit('crawl_products_rankings', this.market, kws, function(data){
        that.crawl_products_rankings(data)
    })
}

Tab_products_ranking.prototype.load_products_rankings = function(data){
        // this.products_rankings = data
    let $tbody = this.$content.find('table.products_ranking tbody')
    for(let item of data){
        let keyword = item['keyword']
        let datetime = new Date(item['datetime'])
        let records = item['records']

        let cls = keyword.replace(/ /g, '-space-')
        cls = cls.replace(/%/g, '-percent-')
        cls = cls.replace(/\./g, '-point-')
    
        let $tr = $tbody.find(`tr.${cls}`)
        $tr.addClass('has_ranking')

        for(let record of records){
        	if(!record['company']['href']){
                console.log(keyword, record)
        		continue
        	}
            // console.log(keyword, record)
            let key = record['company']['href'].match(/\/\/([^\.]*)\./)[1]
            let company = undefined
            if(key in this.products_rankings){
                company = this.products_rankings[key]
            }else{
                company = {}
                company['id'] = key
                company['occurrences'] = 0
                company['company'] = record.company
                this.products_rankings[key] = company
            }

            if(!(keyword in company)){
                company[keyword] = []
            }

            company[keyword].push(record)
            company['occurrences'] ++
        }
    }

    let rankings = []
    for(let [key, value] of Object.entries(this.products_rankings)){
        rankings.push(value)
    }

    rankings.sort((a,b)=>{return b['occurrences']-a['occurrences']})

    let opts = ''
    for(let ranking of rankings){
        opts = `${opts}<option value="${ranking.id}">${ranking.occurrences + ' - ' + ranking.company.name}</option>`
    }
    this.$content.find('select.suppliers').html(opts)
    this.$content.find('select.suppliers').selectpicker('refresh')
    
    let supplier = this.products_rankings['glittereyelash']
    this.load_supplier(supplier, '#000000')
}

Tab_products_ranking.prototype.load_keyword_groups = function(){
    let file = "hot_searched_keywords_sorting_out.json"
    let that = this
    this.socket.emit('deserialize', this.market, [], file, true, function(data){
        that.binding = {}
        if(data.binding){
            that.binding = data.binding
        }
    })
}
export {Tab_products_ranking}