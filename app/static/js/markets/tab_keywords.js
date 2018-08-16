import {Tab} from '../framework/tab.js'

function Tab_keywords(socket, market, categories=undefined, directory=undefined, filename='keywords.json', compact=false){
    Tab.call(this, socket, market, categories, directory, filename)
    
    this.name = 'keywords'
    this.title = '关键字'

    // let buttons = `<button type="button" class="btn btn-sm btn-primary">保 存</button>`
    let buttons = ``
    this.$button_group = $(`<div class="btn-group mr-2 keywords" role="group">${buttons}</div>`)

    this.$content = fw.load_from_template('#template_keywords')

    if(compact){
        // this.$button_group.empty().append('<button type="button" class="btn btn-sm btn-primary toggle">统 计</button>')
        this.$content.find('div.fetch_keywords').hide()
        // this.$content.find('.card.frequency').hide()
        this.$content.find('.section_title').hide()
        this.$content.find('.card.frequency').attr('style','max-width: 120px;')
    }

    this.results = {}
    this.$card_result = this.$content.find('.card.result')
    this.$results_selection = this.$card_result.find('.crawl_results_selection')
    this.$card_frequency = this.$content.find('.card.frequency')

    let that = this

    this.$content.on('click', '.web_sites .form-check', function(){
        $(this).find('input').prop('checked', true)
        $(this).siblings().find('input').prop('checked', false)
        if($(this).find('input').val()=='alibaba_sp'){
            $(this).parent().next().text('网 址:')
        }else{
            $(this).parent().next().text('关键词:')
        }
    })

    this.$content.on('click', '.fetch_keywords .btn.search', function(){
        if($(this).hasClass('disabled')){
            return
        }
        let $btn_search = $(this)
        $(this).addClass('disabled')
        let website = $(this).siblings('.web_sites').find('input:checked').val().trim()
        let keyword = $(this).parent().find('input.keywords_searched').val().trim()
        let page_quantity = $(this).parent().find('input.page_quantity').val().trim()

        let market = {'name': that.market.name, 'directory': that.market.directory}
        that.socket.emit('crawl_keywords', keyword, website, page_quantity, market, function(data){})

        that.socket.once('keyword_crawling_result', function(data){
            console.log(data)
            $btn_search.removeClass('disabled')
            that.results[data['key']] = data['result']
            that.loadResultsSelection(Object.keys(that.results))
            that.$results_selection.find(`option[value="${data['key']}"]`).prop('selected', true)
            that.loadResults(data['result'])
        })
    })

    this.$card_frequency.on('click', '.card-header button', function(){
        $(this).removeClass('btn-secondary').addClass('btn-primary')
        $(this).siblings().addClass('btn-secondary').removeClass('btn-primary')

        let elements = undefined
        if($(this).hasClass('title')){
            elements = that.$card_result.find('span.title')
        }else{
            elements = that.$card_result.find('li.keyword')
        }
        that.loadWrodsFrequency(elements)
    })

    this.$results_selection.change(function(){
        $(this).find('option.place_holder').hide()
        let key = $(this).find('option:selected').prop('value')
        let result = that.results[key]
        that.loadResults(result)
    })

    this.$card_result.find('button.remove_result').click(function(){
        let $option = that.$results_selection.find('option:selected')
        if($option.hasClass('place_holder')){
            return
        }
        let key = $option.prop('value')
        delete that.results[key]
        that.loadResultsSelection(Object.keys(that.results))
        that.$card_result.find('.card-body>ul').empty()

        let market = {'name': that.market.name, 'directory': that.market.directory}
        that.socket.emit('serialize', that.results, market, [], 'keywords.json')
    })

    this.fetch_values_from_server()
        .then(function(results){
            if(!results[0]){
                return
            }
            that.results = results[0]
            let keys = Object.keys(results[0])
            that.loadResultsSelection(keys)
        }).catch(error => console.log(error))

    if(compact){
        this.$content.on('click', 'span.title', function(){
            console.log($(this).text().toLowerCase())
            let title = $(this).text().trim()
            $('#main .products .attributes input.product_name').val(title)
            var e = jQuery.Event("keydown")
            e.which = 13
            $('#main .products .attributes input.product_name').trigger(e)
        })
        this.$content.on('click', 'li.keyword', function(){
            let kw = $(this).text().trim()

            for(let input of $('#main .products .attributes li.keywords input')){
                if(!$(input).val().trim()){
                    $(input).val(kw)
                    break
                }
            }
        })
    }
}
Tab_keywords.prototype = Tab.prototype


Tab_keywords.prototype.loadResults = function(results){
    
    let used_titles = this.market.used_titles
    let reserved_titles = this.market.reserved_titles

    let counter = 1
    let $ul = this.$card_result.find('.card-body>ul').empty()
    for(let result of results){
        for(let item of result){
            let title = item['title']
            let keywords = item['keywords']
            let src = item['img']
            let href = item['href']

            let title_cls = ''
            if(used_titles && title.toLowerCase() in used_titles){
                title_cls = 'used'
            }
            if(reserved_titles && title.toLowerCase() in reserved_titles){
                title_cls = 'reserved'
            }

            let ts = `<span class="title ${title_cls}">${title}</span>`
            let badge_class = 'badge-dark'
            if(item['isCrowned']){
                badge_class = 'badge-warning'
            }
            if(item['isAd']){
                badge_class = 'badge-success'
            }
            let cs = `<span class="badge ${badge_class}">${counter}</span>`
            let is = `<a href="${href}"><img src="${src}"></a>${cs}`
            let ks = ''
            for(let word of keywords){
                ks = `${ks}<li class='keyword'>${word}</li>`
            }
            ks = `<ul>${ks}</ul>`


            let li = ""
            if(keywords.length>0){
                li = `<div>${ts}</div><div><span>${is}</span><span>${ks}</span></div>`
            }else{
                li = `<span>${is}</span>${ts}`
            }

            $ul.append(`<li class="list-group-item">${li}</li>`)
            counter++
        }
    }
}

Tab_keywords.prototype.loadResultsSelection = function(keys){
    this.$results_selection.find('option.place_holder').show().siblings().remove()
    keys.sort()
    for(let key of keys){
        this.$results_selection.append(`<option value="${key}">${key}</option>`)
    }
}

Tab_keywords.prototype.loadWrodsFrequency = function($elements){
    let words = {}
    for(let e of $elements){
        let text = $(e).text()
        text = text.replace('  ', ' ')
        text = text.replace('[', ' ')
        text = text.replace(']', ' ')
        text = text.replace('(', ' ')
        text = text.replace(')', ' ')
        text = text.replace('/', ' ')
        text = text.replace(',', ' ')
        text = text.replace('100%', '100% ')
        let ws = text.split(' ')
        for(let w of ws){
            if(!w || w==" "){
                continue
            }
            w = w.toLowerCase()
            if(w in words){
                words[w] = words[w]+1
            }else{
                words[w] = 1
            }
        }
    }
    let list = Object.keys(words)
    list.sort(function(a, b){
        return words[b] - words[a]
    })
    console.log(list, words['quality'])
    let divs = ''
    for(let w of list){
        divs = `${divs}<div><span class="word">${w}</span><span class="frequency float-right">${words[w]}</span></div>`
    }
    this.$card_frequency.find('.card-body').empty().append(divs)
}

export {Tab_keywords}