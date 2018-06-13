import {Tabs} from '../framework/tabs.js'
import {Tab} from '../framework/tab.js'
import {Attributes} from './attributes.js'
import {Tab_keywords} from './tab_keywords.js'

function Tab_attributes(socket, market, categories=undefined, directory=undefined, filename='attributes.json'){
    Tab.call(this, socket, market, categories, directory, filename)

    this.name = 'attributes'
    this.title = '属 性'

    let buttons = ""
    if(filename.includes('_')){
        buttons = `${buttons}<button type="button" class="btn btn-sm btn-primary attrs keywords">关键字</button>`
        buttons = `${buttons}<button type="button" class="btn btn-sm btn-primary attrs set_posted">已发布</button>`
    }
    if(categories){
        buttons = `${buttons}<button type="button" class="btn btn-sm btn-primary attrs copy_to">复制到</button>`
    }
    buttons = `${buttons}<button type="button" class="btn btn-sm btn-primary save">保 存</button>`

    this.$button_group = $(`<div class="btn-group mr-2 attributes" role="group">${buttons}</div>`)

    this.$content = fw.load_from_template('#template_attributes')

    this.$content.find('.general_info span.name').text(market.name)


    let that = this
    if(filename.includes('_')){
        this.$content.find('input.product_category').val(categories.slice().pop())
        this.$content.find('input.product_type').val(filename.split('_')[0])
    }else if(categories){
        this.$content.find('li.keywords').prev().hide()
        this.$content.find('li.keywords').hide()
        this.$content.find('input.product_category').val(categories.slice().pop())
    }else if(!directory){
        this.$content.find('li.special').hide()
    }

    this.$content.find('div.trade_info li:first-child').on('click', '.form-check', function(){
        let $div = $(this).parents('div.trade_info')
        $(this).find('input').prop('checked', true)
        $(this).siblings().find('input').prop('checked', false)

        if($div.find('.tiered_pricing_switcher').is(':checked')){
            $div.find('li.tiered_pricing').show()
            $div.find('li.range_pricing').hide()
        }else{
            $div.find('li.tiered_pricing').hide()
            $div.find('li.range_pricing').show()
        }
    })

    this.attributes = undefined
    this.fetch_values_from_server()
        .then(function(results){

            let attrs = that.market.attributes_copy

            if(!attrs){
                attrs = new Attributes()
                attrs.init(results.shift())
            }else{
                delete that.market.attributes_copy
            }

            if(that.filename.includes('_')){
                if(!attrs.type){
                    attrs.type = that.filename.split('_')[0]
                }
            }

            let attributes = new Attributes()
            for(let result of results){
                attributes.merge(result)
            }
            that.attributes = attributes

            attrs.merge(attributes)
            attrs.fill_form(that.$content)

        }).catch(error => console.log(error))

    this.$button_group.on('click', 'button.save', function(){
        let attrs = new Attributes()
        attrs.load(that.$content)
        let title = attrs.name.toLowerCase()
        that.reserve_title(title)
        that.save_values_to_server(attrs.differ(that.attributes))
    })
    this.$button_group.on('click', 'button.copy_to', function(){
        let attrs = new Attributes()
        attrs.load(that.$content)

        attrs.name = ""
        attrs.keywords = []
        attrs.type = ""
        that.market['attributes_copy'] = attrs
    })
    this.$button_group.on('click', 'button.keywords', function(){
        if($(this).hasClass('btn-primary')){
            $(this).removeClass('btn-primary').addClass('btn-secondary')
            let $right = $('#right').empty()
            let tabs = new Tabs(true)
            tabs.init($right)
            tabs.append_tab(new Tab_keywords(socket, market, undefined, undefined, 'keywords.json', true))
            $('#left').hide()
        }else{
            $(this).addClass('btn-primary').removeClass('btn-secondary')
            let $right = $('#right').empty()
            $('#left').show()
        }

    })

    this.$button_group.find('button.set_posted').click(function(){


        let $card = $('.products .product_list .card.selected')
        if(!$card.length){
            return
        }
        let product = $card.data('product')
        let pid = product.pid
        let ali_id = prompt(`请输入该产品(${pid})在阿里巴巴的ID：`)
        if(!ali_id){
            return
        }
        ali_id = ali_id.trim()

        socket.emit('crawl_product_data_from_alibaba', ali_id, function(data){
            // console.log(data)

            // let $card_product = $('#left_navbar .products .card')
            // let path = product['directory']
            // let posted_products = $card_product.data('posted_products')
            // posted_products[category + '_' + folder + '_' + pid] = ali_id
            // socket.emit('serialize', posted_products, path, configFolder, 'posted_products.json')

            // let used_titles = $card_product.data('used_titles')
            // let title = data['attributes']['name'].toLowerCase()
            // used_titles[title] = category + '_' + folder + '_' + pid + '_' + ali_id
            // socket.emit('serialize', used_titles, path, configFolder, 'used_titles.json')

            // let used_keywords = $card_product.data('used_keywords')
            // let keywords = []
            // keywords.push(category + '_' + folder + '_' + pid + '_' + ali_id)
            // for(let kw of data['attributes']['keywords']){
            //     keywords.push(kw.toLowerCase())
            // }
            // used_keywords.push(keywords)
            // socket.emit('serialize', used_keywords, path, configFolder, 'used_keywords.json')
        })
        socket.once('crawl_product_data_from_alibaba_result', function(data){
            console.log(data)
            if(!data || !data['attributes']){
                return
            }

            let folder = product.folder

            let pAttributes = new Attributes()
            pAttributes.init(data['attributes'])

            // if(pAttributes){
            //     console.log(pAttributes, that.attributes)
            //     pAttributes.merge(that.attributes)
            //     pAttributes.fill_form(that.$content)
            // }else{
            //     that.attributes.fill_form($pAttributes)
            // }
            product['ali_id'] = pAttributes.alibaba_id
            $card.addClass('posted').removeClass('new_posted')

            let market = {'name': that.market.name, 'directory': that.market.directory}
            let paths = that.categories.slice()
            paths.push(directory)
            pAttributes.fill_form(that.$content)
            that.socket.emit('serialize', pAttributes, market, paths, pid+'_attributes.json')

            let title  = pAttributes.name.toLowerCase()
            product['title'] = title
            let new_posted_products = that.market['new_posted_products']
            new_posted_products[product.pid] = product
            that.socket.emit('serialize', that.market['new_posted_products'], market, [], 'new_posted_products.json')

            let used_titles = that.market['used_titles']
            if(title in used_titles){
                fw.notify({'type':'warning', 'content':'duplicated title was found: ' + title})
                console.log('duplicated title was found: ' + title)
                console.log('products with duplicated title: ', used_titles[title], product)
            }else{
                used_titles[title] = product
            }

            if(!data['template']){
                return
            }
            let html = data.template.html
            that.$content.parent().find('div.template textarea.template').val(html)
        })
    })

    this.$content.on('keydown', 'input.product_name', function(e){
        if(e.which != 13){
            return
        }
        let title = $(this).val().toLowerCase()
        that.is_title_used(title)
    })
}

Tab_attributes.prototype = Tab.prototype

Tab_attributes.prototype.reserve_title = function(title){

    let used_titles = this.market['used_titles']
    if(title in used_titles){
        let msg = {'type':'danger'}
        msg['content'] ='该标题已经被使用，'+ used_titles[title].category + ', ' + used_titles[title].pid + ', ' +  used_titles[title].ali_id
        fw.notify(msg)
        return
    }

    let product = {}
    product['pid'] = this.filename.split('_')[0]
    product['categories'] = this.categories.slice()
    product['directory'] = this.directory

    let market = {'name': this.market.name, 'directory': this.market.directory}
    this.socket.emit('reserve_title', title, product, market, function(result){
        if(result.success){
            let msg = {'type':'success'}
            msg['content'] = '该标题尚未被使用'
            fw.notify(msg)
        }else{
            let msg = {'type':'danger'}
            msg['content'] ='该标题已经被占用，'+ result.product.categories + ', ' + result.product.directory + ', ' +  result.product.pid
            fw.notify(msg)
        }
    })
}
Tab_attributes.prototype.is_title_used = function(title){

    let used_titles = this.market['used_titles']
    if(title in used_titles){
        let msg = {'type':'danger'}
        msg['content'] ='该标题已经被使用，'+ used_titles[title].category + ', ' + used_titles[title].pid + ', ' +  used_titles[title].ali_id
        fw.notify(msg)
        return
    }
    
    let market = {'name': this.market.name, 'directory': this.market.directory}
    this.socket.emit('is_title_reserved', title, market, function(result){
        if(result.success){
            let msg = {'type':'success'}
            msg['content'] = '该标题尚未被使用'
            fw.notify(msg)
        }else{
            let msg = {'type':'danger'}
            msg['content'] ='该标题已经被占用，'+ result.product.categories + ', ' + result.product.directory + ', ' +  result.product.pid
            fw.notify(msg)
        }
    })
}

export {Tab_attributes}