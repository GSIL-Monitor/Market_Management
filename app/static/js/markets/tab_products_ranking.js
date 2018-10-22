import {Tab} from '../framework/tab.js'

function Tab_products_ranking(socket, market, categories=undefined, directory=undefined, filename='hot_searched_keywords.json', compact=false){
    Tab.call(this, socket, market, categories, directory, filename)
    
    this.name = 'products_ranking'
    this.title = '产品排名'
    this.hot_searched_keywords = []
    this.keyword_groups = {}
    this.main_keywords = {}
    this.one_words = []
    this.brands = []
    this.binding = {}

    this.load()
    let buttons = `<button type="button" class="btn btn-sm btn-primary">保 存</button>`
    // let buttons = ``
    this.$button_group = $(`<div class="btn-group mr-2 products_ranking" role="group">${buttons}</div>`)

    this.$content = fw.load_from_template('#template_products_ranking')

    let that = this

    $('body').on("keyup", function(e){
        console.log('keyup: ', e.key);
        if(e.key == 'Shift'){
            that.shift_pressed = false
        }
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

Tab_products_ranking.prototype = Tab.prototype

export {Tab_products_ranking}