import {Tab} from '../framework/tab.js'
import {Tabs} from '../framework/tabs.js'
import {Tab_attributes} from './tab_attributes.js'
import {Tab_template} from './tab_template.js'
import {Tab_preview} from './tab_preview.js'
import {Attributes} from './attributes.js'
import {Template} from './template.js'

function Tab_products(socket, market, categories=undefined, directory=undefined, filename=undefined){
    Tab.call(this, socket, market, categories, directory, filename)
    this.name = 'products'
    this.title = '产 品'

    let buttons = `<input class="form-check-input post_similar_product" type="checkbox" checked="">`
    buttons = `${buttons}<label class="form-check-label" for="post_similar_product">发布相似产品</label>`
    buttons = `${buttons}<input class="similar_product_id" type="text" placeholder="阿里产品ID">`
    buttons = `${buttons}<div class="input-group-append">`
    buttons = `${buttons}<button type="button" class="btn btn-sm btn-primary post_product">发布产品</button>`
    // buttons = `${buttons}<button type="button" class="btn btn-sm btn-primary change_products_price">修改价格</button>&ndash;&gt;&ndash;&gt;&ndash;&gt;&ndash;&gt;-->`
    buttons = `${buttons}</div>`
    buttons = `<div class="input-group">${buttons}</div>`
    this.$button_group = $(`<div class="btn-group mr-2 products" role="group">${buttons}</div>`)

    this.$content = fw.load_from_template('#template_products')
    
    this.$series = this.$content.find('.series')
    this.$list = this.$content.find('.product_list')
    this.$settings = this.$content.find('.settings')

    // this.posted_products = {}
    this.series = undefined
    this.products = undefined

    let that = this
    this.get_products()
        .then(function(data){
            let attrs = data['attributes']
            for(let folder of data['folders']){
                let isSeried = false
                if(folder.toLowerCase().endsWith(' serie')){
                    isSeried = true
                    if(!that.series){
                        that.series = {}
                    }
                }
                
                if(isSeried){
                    if(!(folder in that.series)){
                        that.series[folder] = {}
                    }
                    for(let file of data['files'][folder]){
                        if(!file.toLowerCase().endsWith('.jpg')){
                            continue
                        }
                        let parts = file.split('_')
                        if(parts.length != 4){
                            if(!('common_files' in that.series[folder])){
                                that.series[folder]['common_files'] = []
                            }
                            that.series[folder]['common_files'].push(file)
                            continue
                        }
                        let pid = parts[0]
                        if(!(pid in that.series[folder])){
                            that.series[folder][pid] = {'files':[file], 'pid': pid, 'psid': parts[1], 'folder':folder}
                        }else{
                            that.series[folder][pid]['files'].push(file)
                            that.series[folder][pid]['folder'] = folder
                            that.series[folder][pid]['pid'] = pid
                            that.series[folder][pid]['psid'] = parts[1]
                        }
                        that.series[folder][pid]['categories'] = that.categories
                        let key = folder+'_'+pid
                        if(key in attrs){
                            that.series[folder][pid]['ali_id'] = attrs[key].alibaba_id
                        }
                    }
                }else{
                    if(!that.products){
                        that.products = {}
                    }
                    let file = data['files'][folder][0]
                    let parts = file.split('_')
                    let files = data['files'][folder]
                    that.products[parts[0]] = {'files': files, 'pid': parts[0], 'psid': parts[1], 'folder': folder}
                    that.products[parts[0]]['categories'] = that.categories
                    let key = folder+'_'+pid
                    if(key in attrs){
                        that.series[folder][pid]['ali_id'] = attrs[key].alibaba_id
                    }
                }
            }

            if(that.series){
                if(that.products){
                    that.series['_individual'] = that.products
                }
                that.$series.empty().show()
                for(let [serie, products] of Object.entries(that.series)){
                    let name = serie
                    if(name == '_individual'){
                        name = 'Others not in series'
                    }

                    that.$series.append(`<span class="badge badge-secondary" name='${serie}'>${name}</span>`)
                }
            }else if(that.products){
                that.$series.hide()
                that.load_product_list(products)
            }

        }).catch(error => console.log(error))

    // this.get_posted_products()
    //     .then(function(data){
    //         if(data[0]){
    //             that.posted_products = data[0]
    //         }
    //     }).catch(error => console.log(error))

    this.$series.on('click', 'span.badge', function(){
        let serie = $(this).attr('name')
        if($(this).hasClass('badge-primary')){
            that.$list.find('.selected').removeClass('selected')
        }else{
            $(this).removeClass('badge-secondary').addClass('badge-primary')
            $(this).siblings('.badge-primary').removeClass('badge-primary').addClass('badge-secondary')
            that.load_product_list(that.series[serie])
        }

        let tabs = new Tabs()
        tabs.init(that.$settings)
        tabs.append_tab(new Tab_attributes(socket, market, categories, serie))
        tabs.append_tab(new Tab_template(socket, market, categories, serie))
    })

    this.$list.on('click', '.card', function(){
        $(this).addClass('selected').siblings('.selected').removeClass('selected')
        let product = $(this).data('product')
        let folder = product.folder
        let pid = product.pid
        let tabs = new Tabs()
        tabs.init(that.$settings)
        tabs.append_tab(new Tab_attributes(socket, market, categories, folder, pid+"_attributes.json"))
        tabs.append_tab(new Tab_template(socket, market, categories, folder, pid+"_template.json"))
        tabs.append_tab(new Tab_preview(socket, market, categories, folder, pid, product))

        if('ali_id' in product){
            that.$button_group.find('input.similar_product_id').val(product.ali_id)
            console.log(that.$button_group.find('input.similar_product_id'), product.ali_id)
        }
    })

    // this.$button_group.find('button.change_products_price').click(function(){
    //     let text = prompt(`请输入 最低价格 和 最高价格，以空格隔开：`)
    //     let price_range = text.trim().split(' ')
    //
    //     let objects = []
    //     let $cards = that.$content.find('.product_list .card.posted')
    //     for(let card of $cards){
    //         let product = $(card).data('product')
    //         let obj = {}
    //         obj['ali_id'] = product.ali_id
    //         obj['price_range'] = price_range
    //         objects.push(obj)
    //     }
    //
    //     that.socket.emit('change_products_price', objects)
    // })

    this.$button_group.find('button.post_product').click(function(){

        let similar_product_selected = $('input.post_similar_product').prop('checked')
        let similar_product_id = $('input.similar_product_id').val().trim()

        let $cards = that.$content.find('.product_list .card.selected')
        if($cards.length == 0){
            $cards = that.$content.find('.product_list .card')
        }

        let products = []
        for(let card of $cards){
            if(!$(card).hasClass('posted') && !$(card).hasClass('new_posted')){
                let product = $(card).data('product')
                products.push(product)
            }
        }

        if(products.length==0){
            let msg = {'type':'primary'}
            msg['content'] = '所选产品已经发布 或 没有需要上传的产品'
            fw.notify(msg)
            return
        }

        // console.log(products)

        let market = {'name': that.market.name, 'directory': that.market.directory}
        that.socket.emit('get_products_data', market, products, function(data){
            // console.log(data)
            if(!data || data.length == 0){
                return
            }
// let kws = []
            for(let p of data){
                let attributes_list = p['attributes_list']
                let attributes = new Attributes()
                for(let result of attributes_list){
                    attributes.merge(result)
                }
                p['attributes'] = attributes
// for(let k of attributes['keywords']){
//     if(kws.indexOf(k) == -1){
//         kws.push(k)
//     }
// }
                let template_list = p['template_list']
                let template = new Template()
                for(let result of template_list){
                    template.merge(result)
                }
                p['template'] = template

                let $card = that.$content.find('.product_list .card.'+p.pid)

                let pictures = []
                let counter = 6

                if(!template.isIndividual && template.product_picture){
                    let pcode = template.product_picture.pcode
                    let pscode = template.product_picture.pscode
                    // let $card = $('.product_list .card.'+that.product.pid)
                    do{
                        let product = $card.data('product')
                        let pid = product.pid
                        let psid = product.psid
                        let fname = `${pid}_${psid}_${pcode}_${pscode}.jpg`
                        let path_root = that.market.directory + '\\' + product.categories.join('\\') + '\\' + product.folder
                        pictures.push(path_root + '\\' + fname)

                        let $next = $card.next()
                        if($next.length==0){
                            $next = $card.siblings(':first-child')
                        }
                        $card = $next
                        counter--
                    }while(counter>0)
                }else if(template.isIndividual && template.product_pictures.length==6){
                    do{
                        let index = 6 - counter
                        let pcode = template.product_pictures[index].pcode
                        let pscode = template.product_pictures[index].pscode

                        let fname = `${p.pid}_${p.psid}_${pcode}_${pscode}.jpg`
                        let path_root = that.market.directory + '\\' + p.categories.join('\\') + '\\' + p.folder
                        pictures.push(path_root + '\\' + fname)

                        counter--
                    }while(counter>0)
                }
                p['pictures'] = pictures

                let template_pictures = []
                for(let sel of template['selections']){
                    if(sel.type == 'tag_img'){
                        let path_root = that.market.directory + '\\' + p.categories.join('\\') + '\\' + p.folder
                        let fname = `${p.pid}_${p.psid}_${sel.pcode}_${sel.pscode}.jpg`
                        template_pictures.push(path_root+'\\'+fname)
                    }
                }
                p['template_pictures'] = template_pictures

            }

            if(similar_product_selected){
                if(!similar_product_id){
                    for(let p of data){
                        let folder = p.folder.split(' - ')
                        let key = folder[0] + ' - ' + 'serie'
                        let found = false
                        if(key in that.series){
                            if(p.pid in (that.series[key])){
                                let ali_id = that.series[key][p.pid]['ali_id']
                                if(ali_id){
                                    p['similar_ali_id'] = ali_id
                                    found = true
                                }

                            }
                        }
                        if(!found){
                            let msg = {'type':'danger'}
                            msg['content'] = '请先填入 相似产品的 阿里巴巴ID'
                            fw.notify(msg)
                            return
                        }
                    }
                }

                console.log('post_similar_products', data, similar_product_id)
                that.socket.emit('post_similar_products', data, similar_product_id, function(){
                })
                that.socket.on('product_posting', function(product){
                    let new_posted_products = that.market['new_posted_products']
                    new_posted_products[product.pid] = product
                    product['title'] = product['attributes']['name']

                    delete product['attributes_list']
                    delete product['template_list']
                    delete product['template']
                    delete product['attributes']
                    delete product['pictures']
                    delete product['template_pictures']

                    let $card = that.$content.find('.product_list .card.'+product.pid)
                    $card.addClass('new_posted')

                    let market = {'name': that.market.name, 'directory': that.market.directory}
                    that.socket.emit('serialize', new_posted_products, market, [], 'new_posted_products.json')
                })
            }else{
                let msg = {'type':'warning'}
                msg['content'] = 'post new product, not implemented yet!'
                fw.notify(msg)
            }

            // console.log(data)
        })
        // let products = {}
        // if(that.series){
        //     for(let key in that.series){
        //         for(let pid in that.series[key]){
        //             if(pid == 'common_files'){
        //                 continue
        //             }
        //             let product = that.series[key][pid]
        //             products[product.pid] = product
        //             product['title'] = ''
        //         }
        //     }
        // }else{
        //     for(let pid in that.products){
        //         let product = that.products[pid]
        //         products[product.pid] = product
        //         product['title'] = ''
        //     }
        // }

        // that.market['new_posted_products'] = products
        // let market = {'name': that.market.name, 'directory': that.market.directory}
        // that.socket.emit('serialize', products, market, [], 'new_posted_products.json')
    })
}

Tab_products.prototype = Tab.prototype

// Tab_products.prototype.get_posted_products = function(){
//     // let paths = this.relative_path_array()
//     let that = this

//     return new Promise(function(resolve, reject){
//         that.socket.emit('deserialize', that.market, [], 'posted_products.json', function(data){
//             resolve(data)
//         })
//     })
// }

Tab_products.prototype.get_products = function(){
    let market = {'name': this.market.name, 'directory': this.market.directory}
    let paths = this.relative_path_array()
    let that = this

    return new Promise(function(resolve, reject){
        that.socket.emit('get_products', market, paths, function(files){
            resolve(files)
        })
    })
}
Tab_products.prototype.load_product_list = function(products){
    // fill product list
    let paths = this.relative_path_array()
    this.$list.empty()
    for(let [id, product] of Object.entries(products)){
        if(id=='common_files'){
            continue
        }
        let folder = product['folder']

        let key = paths.join('/')+'/'+folder+'/'+id
        let file_name = product['files'][0]
        let src = `/markets/${this.market['name']}/${paths.join('/')}/${folder}/${file_name}`
        let html = `<img class="card-img-top" src="${src}" alt="Card image cap">`
        html = `${html}<div class="card-footer"><small class="text-muted">${id}</small></div>`
console.log(this.market)
        if('ali_id' in product && product.ali_id){
            html = `<div class="card ${id} posted">${html}</div>`
        }else if(id in this.market['new_posted_products']){
            html = `<div class="card ${id} new_posted">${html}</div>`
        }else{
            html = `<div class="card ${id}">${html}</div>`
        }
        
        let $card = $(html)
        this.$list.append($card)
        $card.data('product', product)
    }
}

export {Tab_products}