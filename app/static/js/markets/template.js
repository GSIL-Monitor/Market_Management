function Template(){
    this.isIndividual = undefined
    this.product_pictures = []
    this.product_picture = undefined

    this.selections = []
    this.template = ''
}

Template.prototype.init = function(values){
    if(!values){
        return
    }
    this.isIndividual = values.isIndividual
    this.product_pictures = values.product_pictures
    this.product_picture = values.product_picture

    this.selections = values.selections
    this.template = values.template
}

Template.prototype.fill_form = function($div){
    if(this.isIndividual==true){
        $div.find('input.type_individual').prop('checked', true)
        $div.find('input.type_series').prop('checked', false)
        let $lis = $div.find('li.type_individual').show()
        $div.find('li.type_series').hide()
        if(this.product_pictures.length != 0){
            let index = 0
            for(let li of $lis){
                let pPic = this.product_pictures[index]
                $(li).find('input.pcode').val(pPic['pcode'])
                $(li).find('input.pscode').val(pPic['pscode'])
                index++
            }   
        }
    }else if(this.isIndividual == false || this.isIndividual == undefined){
        $div.find('input.type_individual').prop('checked', false)
        $div.find('input.type_series').prop('checked', true)
        let $li = $div.find('li.type_series').show()
        $div.find('li.type_individual').hide()
        if(this.product_picture){
            $li.find('input.pcode').val(this.product_picture['pcode'])
            $li.find('input.pscode').val(this.product_picture['pscode'])
        }
    }

    if(this.selections.length>0){
        while(this.selections.length > $div.find('li.css_selection').length){
            this.appendSelection($div)
        }
        while(this.selections.length < $div.find('li.css_selection').length){
            $div.find('li.css_selection').first().remove()
        }
        let index = 0
        for(let li  of $div.find('li.css_selection')){
            let sel = this.selections[index]
            $(li).find('input.css_selector').val(sel['selector'])
            let type = sel['type']
            $(li).find(`select option[value="${type}"]`).prop('selected', true)
            if(type=='tag_img'){
                $(li).find('span.tag_img').show()
                $(li).find('input.pcode').val(sel['pcode'])
                $(li).find('input.pscode').val(sel['pscode'])
            }else{
                $(li).find('span.tag_img').hide()
            }
            index++
        }
    }

    if('template' in this){
        $div.find('textarea.template').val(this.template)
    }
}

Template.prototype.load = function($div){
    this.isIndividual = $div.find('input.type_individual').prop('checked')
    if(!this.isIndividual && !$div.find('input.type_series').prop('checked')){
        this.isIndividual = undefined
    }
    if(this.isIndividual == true){
        this.product_pictures.length = 0
        for(let li of $div.find('li.type_individual')){
            let obj = {}
            obj['pcode'] = $(li).find('input.pcode').val().trim()
            obj['pscode'] = $(li).find('input.pscode').val().trim()
            this.product_pictures.push(obj)
        }
    }else if(this.isIndividual == false){
        this.product_picture = {}
        let $li = $div.find('li.type_series')
        this.product_picture['pcode'] = $li.find('input.pcode').val().trim()
        this.product_picture['pscode'] = $li.find('input.pscode').val().trim()
    }

    let $lis = $div.find('li.css_selection')
    for(let li of $lis){
        let selection = {}
        selection['selector'] = $(li).find('input.css_selector').val().trim()
        selection['type'] = $(li).find('select option:selected').prop('value')
        if(selection['type'] == 'tag_img'){
            selection['pcode'] = $(li).find('input.pcode').val().trim()
            selection['pscode'] = $(li).find('input.pscode').val().trim()
        }
        if(selection['selector']){
            this.selections.push(selection)
        }
    }

    this.template = $div.find('textarea.template').val().trim()
}

Template.prototype.merge = function(values){

    if(!values){
        return
    }

    if(this.isIndividual == undefined){
        this.isIndividual = values.isIndividual
        if(values.isIndividual == true){
            this.product_pictures.length = 0
            for(let item of values.product_pictures){
                this.product_pictures.push(item.slice())
            }
        }else if(values.isIndividual == false){
            this.product_picture = {'pcode': values.product_picture.pcode, 'pscode': values.product_picture.pscode}
        }
    }

    if(this.selections.length == 0){
        for(let item of values.selections){
            let selection = {}
            selection['selector'] = item['selector']
            selection['type'] = item['type']
            if(selection['type'] == 'tag_img'){
                selection['pcode'] = item['pcode']
                selection['pscode'] = item['pscode']
            }
            this.selections.push(selection)
        }
    }

    if(!this.template){
        this.template = values.template
    }

}
Template.prototype.differ = function(values){
    let obj = {}

    if(this.isIndividual == undefined){
        obj['product_pictures'] = []
        obj['product_picture'] = undefined
    }else{
        let changed = false
        if(this.isIndividual == values.isIndividual){
            if(this.isIndividual && this.product_pictures.length == 6 && values.product_pictures.length == 6){
                let idx = 0
                for(let item of this.product_pictures){
                    let vitem = values.product_pictures[idx]
                    if(item.pcode != vitem.pcode || item.pscode != vitem.pscode){
                        break
                    }
                    idx++
                }
                if(idx<6){
                    changed = true
                }
            }else if(!this.isIndividual){
                if(this.product_picture.pcode != value.product_picture.pcode){
                    changed = true
                }
                if(this.product_picture.pscode != value.product_picture.pscode){
                    changed = true
                }
            }
        }else{
            changed = true
        }

        if(changed){
            obj.isIndividual = this.isIndividual
            if(obj.isIndividual){
                obj.product_pictures = []
                for(let item of this.product_pictures){
                    obj.product_pictures.push({'pcode': item['pcode'], 'pscode': item['pscode']})
                }
            }else{
                obj.product_picture = {'pcode': this.product_picture.pcode, 'pscode': this.product_picture.pscode}
            }
        }
    }

    let changed = false
    if(this.selections.length != 0 && this.selections.length == values.selections.length){
        let idx = 0
        for(let item of this.selections){
            let vitem = values.selections[idx]

            if(item['selector'] != vitem['selector']){
                break
            }

            if(item['type'] != vitem['type']){
                break
            }

            if(item['type'] == 'tag_img'){
                if(item['pcode'] != vitem['pcode']){
                    break
                }
                if(item['pscode'] != vitem['pscode']){
                    break
                }
            }

            idx++
        }

        if(idx == this.selections.length){
            changed = false
        }else{
            changed = true
        }
    }else if(this.selections.length != 0){
        changed = true
    }

    if(changed){
        for(let item of this.selections){
            let selection = {}
            selection['selector'] = item['selector']
            selection['type'] = item['type']
            if(selection['type'] == 'tag_img'){
                selection['pcode'] = item['pcode']
                selection['pscode'] = item['pscode']
            }
            obj.selections.push(selection)
        }
    }else{
        obj.selections = []
    }

    if(this.template != values.template){
        obj.template = this.template
    }else{
        obj.template = ''
    }

    return obj
}

Template.prototype.appendSelection = function($div){
    let $li = $div.find('span.new_field').parent()
    let $html = $($li[0].outerHTML)
    $html.find('input').val('')
    $html.find('span.tag_img').show()
    $html.insertBefore($div.find('li.template'))
    $li.find('span.new_field').removeClass('new_field').addClass('del_field')
    $li.find('.ion-plus-round').removeClass('ion-plus-round').addClass('ion-minus-round')
}

export { Template }