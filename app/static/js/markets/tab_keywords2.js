import {Tab} from '../framework/tab.js'

function Tab_keywords2(socket, market, categories=undefined, directory=undefined, filename='hot_searched_keywords.json', compact=false){
    Tab.call(this, socket, market, categories, directory, filename)
    
    this.name = 'keywords2'
    this.title = '关键词2'
    this.hot_searched_keywords = []
    this.keyword_groups = {}
    this.main_keywords = {}
    this.one_words = []
    this.brands = []
    this.binding = {}

    this.load()
    // let buttons = `<button type="button" class="btn btn-sm btn-primary">保 存</button>`
    let buttons = ``
    this.$button_group = $(`<div class="btn-group mr-2 keywords2" role="group">${buttons}</div>`)

    this.$content = fw.load_from_template('#template_keywords2')

    let that = this

    this.$content.find('#add_keywords_group').on('click', function(){
        let name = $(this).parent().prev().val().trim()
        if(name){
            $('#keywords_group_container').append(`<span class="badge badge-secondary">${name}</span>`)
            that.keyword_groups[name] = []
        }
        that.save()
    })
    this.$content.find('#keywords_group_container').on('click', 'span.badge', function(){
        $(this).siblings('.badge-primary').removeClass('badge-primary').addClass('badge-secondary')
        if($(this).hasClass('badge-secondary')){
            $(this).removeClass('badge-secondary').addClass('badge-primary')
        }
        $('#main_keywords_container').empty()
        let group = $(this).text().trim()
        for(let key of that.keyword_groups[group]){
            $('#main_keywords_container').append(`<span class="badge badge-secondary">${key}</span>`)
        }
    })
    this.$content.find('#del_keywords_group').on('click', function(){
        let badge = that.$content.find('#keywords_group_container span.badge-primary')
        if(!badge){
            return
        }
        let name = badge.text()
        badge.remove()
        for(let key of that.keyword_groups[name]){
            delete that.main_keywords[key]
        }
        delete that.keyword_groups[name]
        that.save()
    })

    this.$content.find('#add_main_keyword').on('click', function(){
        let group = that.$content.find('#keywords_group_container span.badge-primary')
        if(!group){
            console.log('no group for this main keyword was selected')
            return
        }
        group = group.text().trim()
        let name = $(this).parent().prev().val().trim()
        if(!name){
            console.log('no main keyword was inputed')
            return
        }
        $('#main_keywords_container').append(`<span class="badge badge-secondary">${name}</span>`)
        that.keyword_groups[group].push(name)
        that.main_keywords[name] = {}
        that.save()
    })
    this.$content.find('#main_keywords_container').on('click', 'span.badge', function(){
        $(this).siblings('.badge-primary').removeClass('badge-primary').addClass('badge-secondary')
        if($(this).hasClass('badge-secondary')){
            $(this).removeClass('badge-secondary').addClass('badge-primary')
        }
        let main_keyword = $(this).text().trim()
        that.load_main_keyword_list(main_keyword)
    })
    this.$content.find('#del_main_keyword').on('click', function(){
        let group = that.$content.find('#keywords_group_container span.badge-primary')
        if(!group){
            console.log('no group for this main keyword was selected')
            return
        }
        group = group.text().trim()
        let span = that.$content.find('#main_keywords_container span.badge-primary')
        if(!span){
            return
        }
        let main_keyword = span.text().trim()
        span.remove()

        delete that.main_keywords[main_keyword]
        let index = that.keyword_groups[group].indexOf(main_keyword)
        if (index > -1) {
            that.keyword_groups[group].splice(index, 1);
        }
        that.save()
    })

    this.$content.find('#add_one_word').on('click', function(){
        let name = $(this).parent().prev().val().trim()
        if(!name){
            console.log('no one_word was inputed')
            return
        }
        console.log(name)
        let $container = that.$content.find('#one_words_container')
        $container.append(`<span class="badge badge-secondary">${name}</span>`)
        that.one_words.push(name)
        that.save()
    })
    this.$content.find('#one_words_container').on('click', 'span.badge', function(){
        $(this).siblings('.badge-primary').removeClass('badge-primary').addClass('badge-secondary')
        if($(this).hasClass('badge-secondary')){
            $(this).removeClass('badge-secondary').addClass('badge-primary')
        }
    })
    this.$content.find('#del_one_word').on('click', function(){
        let $container = that.$content.find('#one_words_container')
        let span = $container.find('span.badge-primary')
        if(!span){
            return
        }
        let ow = span.text().trim()
        span.remove()

        let index = that.one_words.indexOf(ow)
        if (index > -1) {
            that.one_words.splice(index, 1);
        }
        that.save()
    })
    this.$content.find('#add_brands').on('click', function(){
        let name = $(this).parent().prev().val().trim()
        if(!name){
            console.log('no brand name was inputed')
            return
        }
        console.log(name)
        let $container = that.$content.find('#brands_container')
        $container.append(`<span class="badge badge-secondary">${name}</span>`)
        that.brands.push(name)
        that.save()
    })
    this.$content.find('#brands_container').on('click', 'span.badge', function(){
        $(this).siblings('.badge-primary').removeClass('badge-primary').addClass('badge-secondary')
        if($(this).hasClass('badge-secondary')){
            $(this).removeClass('badge-secondary').addClass('badge-primary')
        }
    })
    this.$content.find('#del_brands').on('click', function(){
        let $container = that.$content.find('#brands_container')
        let span = $container.find('span.badge-primary')
        if(!span){
            return
        }
        let brand = span.text().trim()
        span.remove()

        let index = that.brands.indexOf(brand)
        if (index > -1) {
            that.brands.splice(index, 1);
        }
        that.save()
    })
    this.$content.find('#all_keywords').on('click', function(){
        that.load_keyword_list(that.hot_searched_keywords)
    })

    this.$content.find('#keyword_list_filter').on('click', function(){
        let name = $(this).parent().prev().val().trim()
        if(!name){
            console.log('no word was inputed')
            return
        }
        console.log(name)
        that.load_keyword_list(that.hot_searched_keywords, name)
        // let trs = that.$content.find('table.keywords_list tbody tr')
        // for(let tr of trs){
        //     let $tr = $(tr)
        //     let key = $tr.data('word')
        //     let count = 0
        //     for(let w of name.split(' ')){
        //         if(key.search(w) != -1){
        //             count ++
        //         }
        //     }

        //     if(count == name.split(' ').length){
        //         $tr.show()
        //     }else{
        //         $tr.hide()
        //     }
        // }
    })
    // this.$content.find('#keyword_list_reset').on('click', function(){
    //     that.$content.find('table.keywords_list tbody tr').show()
    // })
    this.$content.find('table.keywords_list tbody').on('click', 'tr', function(){
        let $tr = $(this)
        $tr.toggleClass("selected")
    })

    $('body').on("keydown", function(e){
        console.log('keydown: ', e.key);
        if(e.key === 'Escape'){
            that.$content.find('table.keywords_list tbody tr').removeClass('selected')
        }
        if(e.key == 'Shift'){
            that.shift_pressed = true
        }
    })
    $('body').on("keyup", function(e){
        console.log('keyup: ', e.key);
        if(e.key == 'Shift'){
            that.shift_pressed = false
        }
    })
    this.$content.find('#binding_main_keyword_button').click(function(){
        let $trs = that.$content.find('table.keywords_list tr.selected')
        $trs.find('td.main_keywrod').empty()

        let mkw = $(this).parent().prev().val().trim()
        for(let tr of $trs){
            let $tr = $(tr)
            let kw = $tr.data('word')
            console.log(mkw)
            $tr.find('td.main_keyword').text(mkw)
            that.binding[$tr.find('td.keyword').text().trim()] = mkw

            console.log(kw, mkw)
        }
        that.save()
        that.$content.find('table.keywords_list tr.selected').removeClass('selected')
    })

    this.$content.find('#unbinded_keywords_filter').click(function(){

        let name = $(this).parent().prev().val().trim()
        if(!name){
            console.log('no word was inputed')
            return
        }
        console.log(name)

        that.load_keyword_list(that.hot_searched_keywords, name, false)
    })

    this.$content.find('#unbinded_keywords').click(function(){
        that.load_keyword_list(that.hot_searched_keywords, '', false)
    })

    this.fetch_values_from_server()
        .then(function(results){
            
            let brands = '\\b'+that.brands.join('\\b|\\b')+'\\b'
            // let brands = that.brands.join('|')
            console.log(brands)
            for(let item of results[0]){
                let keyword = item.keyword
                if(keyword.search(brands) != -1){
                    continue
                }
                for(let ow of that.one_words){
                    keyword = keyword.replace(ow, ow.split(' ').join('_'))
                }

                item.keyword = keyword
                that.hot_searched_keywords.push(item)
            }
            console.log(that.hot_searched_keywords.length)
        }).catch(error => console.log(error))
}
Tab_keywords2.prototype = Tab.prototype

Tab_keywords2.prototype.load_main_keyword_list = function(mkw){
    let tbody = $('.keyword_sort_out table.keywords_list tbody')
    let trs = ''
    let idx = 1
    for(let item of this.hot_searched_keywords){
        let words = []
        let indices = []

        let ws = mkw.split(' ')
        let last_index = undefined
        for(let word of item.keyword.split(' ')){
            let index = ws.indexOf(word)
            if(index == -1){
                words.push(word)
            }else{
                words.push(`<span class="mark">${word}</span>`)
                if(last_index == undefined || last_index < index){
                    indices.push(index)
                    last_index = index
                }else{
                    break
                }
            }
        }

        if(!(item.keyword in this.binding) || this.binding[item.keyword] != mkw){
            continue
        }
        
        let key = item.keyword.replace('_', ' ')
        let tds =''
        tds = `${tds}<td class="number">${idx}</td>`
        tds = `${tds}<td class="number">${item.supplier_competition}</td>`
        tds = `${tds}<td class="number">${item.showroom_count}</td>`
        tds = `${tds}<td class="number">${item.search_frequency}</td>`
        tds = `${tds}<td class="keyword">${words.join(' ')}</td>`
        if(item.keyword in this.binding){
            tds = `${tds}<td class="main_keyword">${this.binding[item.keyword]}</td>`
        }else{
            tds = `${tds}<td class="main_keyword"></td>`
        }
        tds = `${tds}<td></td>`
        trs = `${trs}<tr data-word="${key}">${tds}</tr>`
        idx++
    }
    tbody.empty().append(trs)

}

Tab_keywords2.prototype.load_keyword_list = function(result, keyword="", binded=undefined){
    let tbody = $('.keyword_sort_out table.keywords_list tbody')
    let trs = ''
    let idx = 1
    for(let item of result){
        let words = []
        let indices = []

        let ws = keyword.split(' ')

        if(keyword){
            for(let word of item.keyword.split(' ')){
                let index = ws.indexOf(word)
                if(index == -1){
                    words.push(word)
                }else{
                    words.push(`<span class="mark">${word}</span>`)
                    indices.push(index)
                    // if(last_index == undefined || last_index < index){
                    //     indices.push(index)
                    //     last_index = index
                    // }else{
                    //     break
                    // }
                }
            }

            // if(indices.length!=keyword.split(' ').length && keyword){
            //     continue
            // }

            if(!(indices.length && keyword)){
                continue
            }
        }

        console.log(binded===false)
        if(binded===false && item.keyword in this.binding){
            continue
        }

        let key = item.keyword.replace('_', ' ')
        let tds =''
        tds = `${tds}<td class="number">${idx}</td>`
        tds = `${tds}<td class="number">${item.supplier_competition}</td>`
        tds = `${tds}<td class="number">${item.showroom_count}</td>`
        tds = `${tds}<td class="number">${item.search_frequency}</td>`
        tds = `${tds}<td class="keyword">${item.keyword}</td>`
        if(item.keyword in this.binding){
            tds = `${tds}<td class="main_keyword">${this.binding[item.keyword]}</td>`
        }else{
            tds = `${tds}<td class="main_keyword"></td>`
        }
        tds = `${tds}<td></td>`
        trs = `${trs}<tr data-word="${key}">${tds}</tr>`
        idx++
    }
    tbody.empty().append(trs)
}

Tab_keywords2.prototype.save = function(){
    let file = "hot_searched_keywords_sorting_out.json"
    let obj = {'keyword_groups':this.keyword_groups, 'main_keywords':this.main_keywords}
    obj['one_words'] = this.one_words
    obj['brands'] = this.brands
    obj['binding'] = this.binding
    this.socket.emit('serialize', obj, this.market, [], file)
}

Tab_keywords2.prototype.load = function(){
    let file = "hot_searched_keywords_sorting_out.json"
    let that = this
    this.socket.emit('deserialize', this.market, [], file, true, function(data){
        that.keyword_groups = data.keyword_groups
        that.main_keywords = data.main_keywords
        that.one_words = []
        if(data.one_words){
            that.one_words = data.one_words
        }
        that.brands = []
        if(data.brands){
            that.brands = data.brands
        }
        that.binding = {}
        if(data.binding){
            that.binding = data.binding
        }

        let opts = ''
        for(let key in that.keyword_groups){
            let group = that.keyword_groups[key]
            for(let mkw of group){
                opts = `${opts}<option value="${mkw}">${mkw}</option>`
            }
        }
        $('#binding_main_keyword').empty().html(opts)


        let div_groups = that.$content.find('#keywords_group_container')
        for(let group in that.keyword_groups){
            div_groups.append(`<span class="badge badge-secondary">${group}</span>`)
        }
        that.$content.find('#main_keywords_container').empty()

        let div_one_words = $('#one_words_container').empty()
        for(let ow of that.one_words){
            div_one_words.append(`<span class="badge badge-secondary">${ow}</span>`)
        }
        let div_brands = $('#brands_container').empty()
        for(let brand of that.brands){
            div_brands.append(`<span class="badge badge-secondary">${brand}</span>`)
        }

        console.log(that.one_words,div_one_words)
    })
}

export {Tab_keywords2}