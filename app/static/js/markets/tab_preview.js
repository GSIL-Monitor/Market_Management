import {Tab} from '../framework/tab.js'
import {Attributes} from './attributes.js'
import {Template} from './template.js'

function Tab_preview(socket, market, categories=undefined, directory=undefined, filename=undefined, product=undefined){
    Tab.call(this, socket, market, categories, directory, filename)
    this.product = product

    this.name = 'preview'
    this.title = '预 览'


    let buttons = ``
    buttons = `<button type="button" class="btn btn-sm btn-primary refresh">刷 新</button>`
    this.$button_group = $(`<div class="btn-group mr-2 preview" role="group">${buttons}</div>`)

    this.$content = fw.load_from_template('#template_preview')

    let that = this

    this.$button_group.find('button.refresh').click(function(){
        that.load_preview()
    })
}
Tab_preview.prototype = Tab.prototype

Tab_preview.prototype.load_preview = function(){
    let $pictures = this.$content.find('.pictures').empty()
    let $detail = this.$content.find('.detail').empty()
    let that = this
    let market = {'name': this.market.name, 'directory': this.market.directory}
    let paths = this.categories.slice()
    paths.push(this.directory)
    this.socket.emit('get_products_data', market, [this.product], function(data){
        if(data.length != 1){
            return
        }

        let attributes_list = data[0]['attributes_list']
        let attributes = new Attributes()
        for(let result of attributes_list){
            attributes.merge(result)
        }

        let template_list = data[0]['template_list']
        let template = new Template()
        for(let result of template_list){
            template.merge(result)
        }

        let pid = that.product.pid
        let psid = that.product.psid
        let url =  `/markets/${market['name']}/${paths.join('/')}`

        let pictures = []
        let counter = 6
        
        if(!template.isIndividual && template.product_picture){
            let pcode = template.product_picture.pcode
            let pscode = template.product_picture.pscode
            let $card = $('.product_list .card.'+that.product.pid)
            do{
                let product = $card.data('product')
                let pid = product.pid
                let psid = product.psid
                let fname = `${pid}_${psid}_${pcode}_${pscode}.jpg`
                pictures.push(url + '\\' + fname)
                $pictures.append(`<img src="${url + '\\' + fname}" class="img-thumbnail">`)
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

                let fname = `${pid}_${psid}_${pcode}_${pscode}.jpg`
                pictures.push(url + '\\' + fname)
                $pictures.append(`<img src="${url + '\\' + fname}" class="img-thumbnail">`)

                counter--
            }while(counter>0)
        }

        let $template = $(template['template'])
        for(let sel of template['selections']){
            let $e = $template.find(sel.selector)
            if(sel.type == 'title'){
                $e.text(attributes.name)
            }else if(sel.type == 'tag_img'){
                let fname = `${pid}_${psid}_${sel.pcode}_${sel.pscode}.jpg`
                $e.attr('src', url + '\\' + fname)
            }
        }
        // console.log(products)
        $detail.append($template)
    })
}
export {Tab_preview}