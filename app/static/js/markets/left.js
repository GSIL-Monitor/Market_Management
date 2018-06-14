import {Tabs} from '../framework/tabs.js'
import {Tab_attributes} from './tab_attributes.js'
import {Tab_template} from './tab_template.js'
import {Tab_keywords} from './tab_keywords.js'
import {Tab_market_others} from './tab_market_others.js'
import {Tab_pictures} from './tab_pictures.js'
import {Tab_products} from './tab_products.js'
import {Tab_update} from './tab_update.js'

let $container = undefined
let socket = undefined
let $root = undefined

let markets = undefined

function init(data){
    $container = data.$container
    socket = data.socket
    markets = data.markets

    $root = $container.find('.left_content.markets')

    $root.on('click', '.card.market', function(e){
        if($(this).data('market')){
            return
        }
        $(this).addClass('selected').siblings('.selected').removeClass('selected')

        load_categories($(this))

        if(e.target.tagName.toLowerCase() == "button"){
            return
        }else{
            $root.find('.list-group-item.selected').removeClass('selected')
        }

        let market = current_market()

        let $main_content = $('#main .main_content').empty()
        let tabs = new Tabs()
        tabs.init($main_content)
        tabs.append_tab(new Tab_attributes(socket, market))
        tabs.append_tab(new Tab_template(socket, market))
        tabs.append_tab(new Tab_keywords(socket, market))
        tabs.append_tab(new Tab_pictures(socket, market))
        tabs.append_tab(new Tab_market_others(socket, market))

        let m = {'name':market.name, 'directory':market.directory}
        socket.emit('deserialize', m, [], 'posted_products.json', function(products){
            if(!products[0]){
                market['posted_products'] = {}
                return
            }
            if(!('used_titles' in market)){
                market['used_titles'] = {}
            }
            let used_titles = market['used_titles']

            for(let key in products[0]){
                let product = products[0][key]
                let title = product.title.toLowerCase()
                if(title in used_titles){
                    fw.notify({'type':'warning', 'content':'duplicated title was found: ' + title})
                    console.log('duplicated title was found: ' + title)
                    console.log('products with duplicated title: ', used_titles[title], product)
                }else{
                    used_titles[title] = product
                }
            }
            market['used_titles'] = used_titles
            market['posted_products'] = products[0]
            console.log(used_titles)
        })
        socket.emit('deserialize', m, [], 'new_posted_products.json', function(products){
            if(!products[0]){
                market['new_posted_products'] = {}
                return
            }
            if(!('used_titles' in market)){
                market['used_titles'] = {}
            }
            let used_titles = market['used_titles']

            console.log(used_titles)
            for(let key in products[0]){
                let product = products[0][key]
                let title = product.title.toLowerCase()
                if(title in used_titles){
                    fw.notify({'type':'warning', 'content':'duplicated title was found: ' + title})
                    console.log('duplicated title was found: ' + title)
                    console.log('products with duplicated title: ', used_titles[title], product)
                }else{
                    used_titles[title] = product
                }
            }
            market['new_posted_products'] = products[0]
            console.log(market['new_posted_products'])
        })
        socket.emit('deserialize', m, [], 'reserved_titles.json', function(titles){
            if(!titles[0]){
                market['reserved_titles'] = {}
            }else{
                market['reserved_titles'] = titles[0]
            }
            console.log(market['reserved_titles'])
        })

    })

    $root.on('click', '.list-group-item', function(){
        $root.find('.list-group-item.selected').removeClass('selected')
        $(this).addClass('selected')

        let categories = current_category()
        let market = current_market()

        let $main_content = $('#main .main_content').empty()
        let tabs = new Tabs()
        tabs.init($main_content)
        tabs.append_tab(new Tab_attributes(socket, market, categories))
        tabs.append_tab(new Tab_template(socket, market, categories))
        tabs.append_tab(new Tab_pictures(socket, market, categories))
        if($(this).find('i').length == 0){
            tabs.append_tab(new Tab_products(socket, market, categories))
        }
    })

    $root.on('click', 'button i', function(e){
        e.stopPropagation()
        if($(this).hasClass('ion-plus')){
            $(this).removeClass('ion-plus').addClass('ion-minus')
            $(this).parent().next().show()
        }else{
            $(this).addClass('ion-plus').removeClass('ion-minus')
            $(this).parent().next().hide()
        }
    })

    $root.on('click', '.card.market .toggle', function(){
        let $i = $(this).find('i')
        if($i.hasClass('ion-chevron-down')){
            $i.removeClass('ion-chevron-down').addClass('ion-chevron-up')
            $(this).parent().next().show()
        }else{
            $i.removeClass('ion-chevron-up').addClass('ion-chevron-down')
            $(this).parent().next().hide()
        }
    })
}

function append_market(market){
    let $card = fw.load_from_template('#template_left_markets_card')
    $card.find('.title').text(market['name'])
    $root.append($card)
}

function load_categories($card){
    if($card.find('.list-group-item').length != 0){
        return
    }

    let market = current_market()
    
    socket.emit('get_categories', {'name': market.name, 'directory': market.directory}, function(data){
        let categories = data['categories']
        let sub_categories = data['sub_categories']

        let entries = ''
        for(let item of categories){
            if(item in sub_categories){
                let sub_entries = ''
                for(let sub_item of sub_categories[item]){
                    sub_entries= `${sub_entries}<button type="button" class="list-group-item list-group-item-action">${sub_item}</button>`
                }
                entries= `${entries}<button type="button" class="list-group-item list-group-item-action"><i class="ion-plus"></i>${item}</button>`
                entries = `${entries}<div class="list-group sub_categories" style="display:none;">${sub_entries}</div>`
            }else{
                entries= `${entries}<button type="button" class="list-group-item list-group-item-action">${item}</button>`
            }
        }

        $card.find('.card-body .categories').html(entries)
        $card.find('.card-body').show()
    })
}

function current_market(){
    let $card = $root.find('.market.selected')
    let market = $card.data('market')
    if(!market){
        market = {}
        market['name'] = $card.data('name')
        market['directory'] = $card.data('directory')
        $card.data('market', market)
    }
    return market
}

function current_category(){
    let category = []
    let $btn = $root.find('button.selected')
    if($btn.length == 0){
        return category
    }
    category.push($btn.text().trim())
    if ($btn.parent().hasClass('sub_categories')){
        category.unshift($btn.parent().prev().text().trim())
    }

    return category
}

export{ init, current_market, current_category }