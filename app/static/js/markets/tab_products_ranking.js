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

    this.load_keyword_groups()
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

    this.$content.find('#load_keywords').on('click', function(){
        that.load_keywords($('select.kws_grp').val())
    })

    this.fetch_values_from_server()
        .then(function(results){
            that.hot_searched_keywords = results[0]
            console.log(that.hot_searched_keywords.length)
        }).catch(error => console.log(error))
}

Tab_products_ranking.prototype = Tab.prototype

Tab_products_ranking.prototype.load_keywords = function(grp){
    let tbody = this.$content.find('table.products_ranking tbody')
    let trs = ''
    let idx = 1
    for(let item of this.hot_searched_keywords){

        if(!(item.keyword in this.binding) || this.binding[item.keyword] != grp){
            continue
        }
        
        let key = item.keyword
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
                    tds = `${tds}<td class="place_holder page_even" style="border: 1px solid lightgrey;padding:0px;"></td>`
                }else{
                    tds = `${tds}<td class="place_holder" style="border: 1px solid lightgrey;padding:0px;"></td>`
                }
            }
        }

        trs = `${trs}<tr class="${key.split(' ').join('_')}" data-word="${key}">${tds}</tr>`
        idx ++
    }
    tbody.empty().append(trs)
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