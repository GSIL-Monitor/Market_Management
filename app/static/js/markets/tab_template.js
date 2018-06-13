import {Tab} from '../framework/tab.js'
import {Template} from './template.js'

function Tab_template(socket, market, categories=undefined, directory=undefined, filename='template.json'){
    Tab.call(this, socket, market, categories, directory, filename)
    
    this.name = 'template'
    this.title = '模 板'

    let buttons = ""
    if(categories){
        buttons = `${buttons}<button type="button" class="btn btn-sm btn-primary attrs copy_to">复制到</button>`
    }
    buttons= `${buttons}<button type="button" class="btn btn-sm btn-primary save">保 存</button>`
    this.$button_group = $(`<div class="btn-group mr-2 template" role="group">${buttons}</div>`)

    this.$content = fw.load_from_template('#template_template')

    let that = this

    this.$content.on('click', '.form-check', function(){
        let $div = $(this).parents('ul')
        $(this).find('input').prop('checked', true)
        $(this).siblings().find('input').prop('checked', false)

        if($div.find('input.type_series').is(':checked')){
            $div.find('li.type_series').show()
            $div.find('li.type_individual').hide()
        }else{
            $div.find('li.type_series').hide()
            $div.find('li.type_individual').show()
        }
    })

    this.$content.on('click', 'span.new_field', function(){
        appendSelection($(this))
    })

    this.$content.on('click', 'span.del_field', function(){
        $(this).parent().remove()
    })

    this.$content.on('change', 'select', function(){
        let type = $(this).find('option:selected').prop('value')
        let $e = $(this).parent().next().find(`.tag_img`)
        if(type=="tag_img"){
            $e.show()
        }else{
            $e.hide()
        }
    })

    this.template = undefined
    this.fetch_values_from_server()
        .then(function(results){

            let tmpl = that.market.template_copy

            if(!tmpl){
                tmpl = new Template()
                tmpl.init(results.shift())
            }else{
                delete that.market.template_copy
            }

            let template = new Template()
            for(let result of results){
                template.merge(result)
            }
            that.template = template

            console.log(tmpl)
            tmpl.merge(template)
            tmpl.fill_form(that.$content)

        }).catch(error => console.log(error))

    this.$button_group.on('click', 'button.save', function(){
        let tmpl = new Template()
        tmpl.load(that.$content)

        if(that.tempalte){
            that.save_values_to_server(tmpl.differ(that.template))
        }else{
            that.save_values_to_server(tmpl)
        }
    })

    this.$button_group.on('click', 'button.copy_to', function(){
        let templ = new Template()
        templ.load(that.$content)

        that.market['template_copy'] = templ
    })
}

Tab_template.prototype = Tab.prototype

function appendSelection($elem){
    let $li = $elem.parent()
    let $html = $($li[0].outerHTML)
    $html.find('input').val('')
    $html.find('span.tag_img').show()
    $html.insertBefore($li.siblings('.template'))
    $li.find('span.new_field').removeClass('new_field').addClass('del_field')
    $li.find('.ion-plus-round').removeClass('ion-plus-round').addClass('ion-minus-round')
}

export {Tab_template}