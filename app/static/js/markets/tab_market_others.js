import {Tab} from '../framework/tab.js'
import {Attributes} from './attributes.js'

function Tab_market_others(socket, market, categories=undefined, directory=undefined, filename='others.json'){
    Tab.call(this, socket, market, categories, directory, filename)
    
    this.name = 'market_others'
    this.title = '其 它'

    // let buttons = `<button type="button" class="btn btn-sm btn-primary">保 存</button>`
    let buttons = ``
    this.$button_group = $(`<div class="btn-group mr-2 market_others" role="group">${buttons}</div>`)

    this.$content = fw.load_from_template('#template_market_others')
    let that = this

    this.$content.find('.login_setup button.login').click(function(){
        let lid = that.$content.find('.login_setup input.login_id').val().trim()
        let lpwd = that.$content.find('.login_setup input.login_pwd').val().trim()
        that.socket.emit('login_alibaba', lid, lpwd)
    })

    this.$content.find('.update_all_posted_products_info').click(function(){

        that.socket.emit('get_posted_product_info', 1000)
        that.socket.once('get_posted_product_info_result', function(products){
            that.update_products_info(products)
        })
    })
    this.$content.find('.update_new_posted_products_info').click(function(){
        let page_quantity = that.$content.find('input.page_quantity').val()

        that.socket.emit('get_posted_product_info', page_quantity)
        that.socket.once('get_posted_product_info_result', function(products){
            that.update_products_info(products)
        })
    })
}

Tab_market_others.prototype = Tab.prototype

Tab_market_others.prototype.update_products_info = function(products){
    if(!products){
        return
    }

    let posted_products = this.market['posted_products']
    let used_titles = this.market['used_titles']
    let new_posted_products = this.market['new_posted_products']
    console.log(new_posted_products)

    for(let product of products){
        let pid = product.pid
        let ali_id = product.ali_id
        if(pid in new_posted_products){
            let p = new_posted_products[pid]
            p['ali_id'] = product.ali_id
            product['psid'] = p.psid
            product['categories'] = p.categories
            product['folder'] = p.folder
            this.update_product_config(p)
            delete new_posted_products[pid]
        }
        posted_products[product.ali_id] = product
        let title = product.title.toLowerCase()
        if(title in used_titles){
            fw.notify({'type':'warning', 'content':'duplicated title was found: ' + title})
            console.log('duplicated title was found: ' + title)
            console.log('products with duplicated title: ', used_titles[title], product)
        }else{
            used_titles[title] = product
        }
    }

    let market = {'name': this.market.name, 'directory': this.market.directory}
    this.socket.emit('serialize', posted_products, market, [], 'posted_products.json')
    this.socket.emit('serialize', new_posted_products, market, [], 'new_posted_products.json')
}
Tab_market_others.prototype.update_product_config = function(product){
    let market = {'name': this.market.name, 'directory': this.market.directory}
    let paths = product.categories.slice()
    paths.push(product.folder)
    let filename = product.pid + '_attributes.json'

    let that = this
    this.socket.emit('deserialize', market, paths, filename, true, function(attributes){
        let attrs = new Attributes()
        if(attributes){
            attrs.init(attributes)
        }
        attrs.alibaba_id = product.ali_id

        that.socket.emit('serialize', attrs, market, paths, filename)
    })
}

export {Tab_market_others}
