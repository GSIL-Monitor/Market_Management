function Attributes(){
    this.alibaba_id = ""
    this.alibaba_category = ""
    this.name = ""
    this.keywords = []
    this.type = ""
    this.brand = ""
    this.origin = ['China (Mainland)', '']
    this.material = ""
    this.production_method = ""

    this.custom_attributes = []

    this.isTieredPricing = undefined
    this.sales_unit = ""
    this.currency = "USD"
    this.price_range = []
    this.MOQ = 100
    this.additional_trading_infomation = ""
    this.tieredPricing = []
    this.payment_methods = {}
    this.other_payment_method = "Paypal"

    this.delivery_time = ""
    this.port = ""
    this.supply_ability = []
    this.additional_delivery_information = ""
    this.packaging = ""
}
Attributes.prototype.init = function(values){
    if(!values){
        return
    }
    this.alibaba_id = values.alibaba_id
    this.alibaba_category = values.alibaba_category
    this.name = values.name
    this.keywords = values.keywords
    this.type = values.type
    this.brand = values.brand
    this.origin = values.origin
    this.material = values.material
    this.production_method = values.production_method

    this.custom_attributes = values.custom_attributes

    this.isTieredPricing = values.isTieredPricing
    this.sales_unit = values.sales_unit
    this.currency = values.currency
    this.price_range = values.price_range
    this.MOQ = values.MOQ
    this.additional_trading_infomation = values.additional_trading_infomation
    this.tieredPricing = values.tieredPricing ? values.tieredPricing : []
    this.payment_methods = values.payment_methods
    this.other_payment_method = values.other_payment_method

    this.delivery_time = values.delivery_time
    this.port = values.port
    this.supply_ability = values.supply_ability
    this.additional_delivery_information = values.additional_delivery_information
    this.packaging = values.packaging
}
// Attributes.prototype.clone = function(){
//     obj = new Attributes()
//     obj.alibaba_id = this.alibaba_id
//     obj.alibaba_category = this.alibaba_category
//     obj.name = this.name
//     obj.keywords = this.keywords.slice()
//     obj.type = this.type
//     obj.brand = this.brand
//     obj.origin = this.origin.slice()
//     obj.material = this.material
//     obj.production_method = this.production_method

//     for(let item of this.custom_attributes){
//         obj.push(item.slice(0))
//     }

//     obj.isTieredPricing = this.isTieredPricing
//     obj.sales_unit = this.sales_unit
//     obj.currency = this.currency
//     obj.price_range = this.price_range.slice()
//     obj.MOQ = this.MOQ
//     obj.additional_trading_infomation = this.additional_trading_infomation
//     for(let item of this.tieredPricing){
//         obj.tieredPricing.push(item.slice())
//     }
//     for(let [pm, status] of Object.entries(this.payment_methods)){
//         obj.payment_methods[pm] = status
//     }
//     obj.other_payment_method = this.other_payment_method

//     obj.delivery_time = this.delivery_time
//     obj.port = this.port
//     obj.supply_ability = this.supply_ability.slice()
//     obj.additional_delivery_information = this.additional_delivery_information
//     obj.packaging = this.packaging
//     return obj
// }

Attributes.prototype.fill_form = function($div){
    $div.find('.alibaba_category').val(this.alibaba_category)
    $div.find('.product_name').val(this.name)
    $div.find('.keyword_1').val(this.keywords[0])
    $div.find('.keyword_2').val(this.keywords[1])
    $div.find('.keyword_3').val(this.keywords[2])
    $div.find('.product_type').val(this.type)
    $div.find('.product_brand').val(this.brand)
    $div.find('.land').val(this.origin[0])
    $div.find('.province').val(this.origin[1])
    $div.find('.product_material').val(this.material)
    $div.find('.production_method').val(this.production_method)
    // custom attributes
    
    let n = 0
    for(let item of this.custom_attributes){
        $div.find(`.custom_attr_${n}_name`).val(item[0])
        $div.find(`.custom_attr_${n}_value`).val(item[1])
        n++
    }


    /***   trading info   ***/
    $div.find('.sales_unit').val(this.sales_unit)
    $div.find('.currency').val(this.currency)
    if(this.isTieredPricing == true){
        $div.find('.tiered_pricing_switcher').prop('checked', true)
        $div.find('.range_pricing_switcher').prop('checked', false)
        $div.find('.tiered_pricing').show()
        $div.find('.range_pricing').hide()
    }else if(this.isTieredPricing == false){
        $div.find('.tiered_pricing_switcher').prop('checked', false)
        $div.find('.range_pricing_switcher').prop('checked', true)
        $div.find('.tiered_pricing').hide()
        $div.find('.range_pricing').show()
    }else if(this.isTieredPricing == undefined){
        $div.find('.tiered_pricing_switcher').prop('checked', false)
        $div.find('.range_pricing_switcher').prop('checked', false)
        $div.find('.tiered_pricing').show()
        $div.find('.range_pricing').hide()
    }
    for(let [i, item] of this.tieredPricing.entries()){
        let index = 1 + i
        $div.find(`.tp_volume_${index}`).val(item[0])
        $div.find(`.tp_price_${index}`).val(item[1])
    }
    $div.find('.rp_price_min').val(this.price_range[0])
    $div.find('.rp_price_max').val(this.price_range[1])
    $div.find('.moq').val(this.MOQ)
    $div.find('.add_tra_inf').val(this.additional_trading_infomation)
    for(let [pm, status] of Object.entries(this.payment_methods)){
        $div.find(`input[value="${pm}"]`).prop('checked', status)
    }
    if(this.other_payment_method && this.other_payment_method != 'undefined' ){
        $div.find('.pm_other').prop('checked', true)
        $div.find('.pm_other').siblings('input').show().val(this.other_payment_method)
    }else{
        $div.find('.pm_other').prop('checked', false)
        $div.find('.pm_other').siblings('input').hide()
    }

    /***   delivery info   ***/
    $div.find('.delivery_time').val(this.delivery_time)
    $div.find('.port').val(this.port)
    $div.find('.sa_volume').val(this.supply_ability[0])
    $div.find('.sa_unit').val(this.supply_ability[1])
    $div.find('.sa_time').val(this.supply_ability[2])
    $div.find('.add_del_inf').val(this.additional_delivery_information)
    $div.find('.packaging').val(this.packaging)
}

// load from html
Attributes.prototype.load = function($div){
    this.alibaba_category = $div.find('.alibaba_category').val().trim()
    this.name = $div.find('.product_name').val().trim()
    this.keywords.length = 0

    let keywords = []
    let keyword = ''
    keyword = $div.find('.keyword_1').val().trim()
    keywords.push(keyword)
    if(keyword){
        this.keywords = keywords
    }
    keyword = $div.find('.keyword_2').val().trim()
    keywords.push(keyword)
    if(keyword){
        this.keywords = keywords
    }
    keyword = $div.find('.keyword_3').val().trim()
    keywords.push(keyword)
    if(keyword){
        this.keywords = keywords
    }
    this.type = $div.find('.product_type').val().trim()
    this.brand = $div.find('.product_brand').val().trim()
    this.origin[0] = $div.find('.land').val().trim()
    this.origin[1] = $div.find('.province').val().trim()
    this.material = $div.find('.product_material').val().trim()
    this.production_method = $div.find('.production_method').val().trim()
    // custom attributes
    if(this.custom_attributes.length > 0){
        this.custom_attributes.length = 0
    }
    for(let li of $div.find('li.custom_attrs')){
        let $inputs = $(li).find('input')
        let key = $inputs[0].value.trim()
        let value = $inputs[1].value.trim()
        if(key && value){
            this.custom_attributes.push([key, value])
        }else{
            this.custom_attributes.push(['', ''])
        }
    }

    /***   trading info   ***/
    this.isTieredPricing = $div.find('.tiered_pricing_switcher').is(':checked')
    if(!this.isTieredPricing){
        let isRangePricing = $div.find('.range_pricing_switcher').is(':checked')
        if(!isRangePricing){
            this.isTieredPricing = undefined
        }
    }
    this.sales_unit = $div.find('.sales_unit').val().trim()
    this.currency = $div.find('.currency').val().trim()

    this.tieredPricing = []
    let volume1 = $div.find('.tp_volume_1').val().trim()
    let price1 = $div.find('.tp_price_1').val().trim()
    if(volume1 && price1){
        this.tieredPricing.push([volume1, price1])
    }
    let volume2 = $div.find('.tp_volume_2').val().trim()
    let price2 = $div.find('.tp_price_2').val().trim()
    if(volume2 && price2){
        this.tieredPricing.push([volume2, price2])
    }
    let volume3 = $div.find('.tp_volume_3').val().trim()
    let price3 = $div.find('.tp_price_3').val().trim()
    if(volume3 && price3){
        this.tieredPricing.push([volume3, price3])
    }
    let volume4 = $div.find('.tp_volume_4').val().trim()
    let price4 = $div.find('.tp_price_4').val().trim()
    if(volume4 && price4){
        this.tieredPricing.push([volume4, price4])
    }
    this.price_range[0] = $div.find('.rp_price_min').val().trim()
    this.price_range[1] = $div.find('.rp_price_max').val().trim()
    this.MOQ = $div.find('.moq').val().trim()
    this.additional_trading_infomation = $div.find('.add_tra_inf').val().trim()

    for(let input of $div.find('li.payment_methods input')){
        this.payment_methods[input.value.trim()] = input.checked
    }

    if($div.find('.pm_other').prop('checked')){
        this.other_payment_method = $div.find('.pm_other').siblings('input').val().trim()
    }else{
        this.other_payment_method = ""
    }

    /***   delivery info   ***/
    this.delivery_time = $div.find('.delivery_time').val().trim()
    this.port = $div.find('.port').val().trim()
    this.supply_ability[0] = $div.find('.sa_volume').val().trim()
    this.supply_ability[1] = $div.find('.sa_unit').val().trim()
    this.supply_ability[2] = $div.find('.sa_time').val().trim()
    this.additional_delivery_information = $div.find('.add_del_inf').val().trim()
    this.packaging = $div.find('.packaging').val().trim()
}

// a deserialized object merges a calculated one and become a calculated one
Attributes.prototype.merge = function(attrs){ // attrs is calculated
    if(!attrs){
        return
    }
    this.alibaba_category = this.alibaba_category ? this.alibaba_category : attrs.alibaba_category
    this.name = this.name ? this.name : attrs.name
    this.keywords = this.keywords.length != 0 ? this.keywords : attrs.keywords.slice(0)
    this.type = this.type ? this.type : attrs.type
    this.brand = this.brand ? this.brand : attrs.brand
    this.origin = this.origin.length == 2 ? this.origin : attrs.origin.slice(0)
    this.material = this.material ? this.material : attrs.material
    this.production_method = this.production_method ? this.production_method : attrs.production_method

    if(this.custom_attributes.length == 0){
        for(let item of attrs.custom_attributes){
            this.custom_attributes.push(item.slice(0))
        }
    }else{
        let idx = 0
        for(let item of this.custom_attributes){
            if(item[0] && item[1]){
                continue
            }
            if(idx < attrs.custom_attributes.length){
                this.custom_attributes[idx] = attrs.custom_attributes[idx].slice()
            }else{
                this.custom_attributes[idx] = ['', '']
            }

            idx++
            if(idx == attrs.custom_attributes.length){
                break
            }
        }
        if(idx < attrs.custom_attributes.length){
            do{
                this.custom_attributes.push(attrs.custom_attributes[idx].slice(0))
                idx++
            }while(idx < attrs.custom_attributes.length)
        }
    }

    /*** trading info   ***/
    this.isTieredPricing = this.isTieredPricing != undefined ? this.isTieredPricing : attrs.isTieredPricing
    this.currency = this.currency ? this.currency : attrs.currency
    this.sales_unit = this.sales_unit ? this.sales_unit : attrs.sales_unit
    if(this.tieredPricing.length == 0){
        for(let pricing of attrs.tieredPricing){
            this.tieredPricing.push(pricing.slice(0))
        }
    }
    if(this.price_range.length == 0){
        this.price_range = attrs.price_range.slice(0)
    }
    this.MOQ = this.MOQ ? this.MOQ : attrs.MOQ
    this.additional_trading_infomation = this.additional_trading_infomation ? this.additional_trading_infomation : attrs.additional_trading_infomation
    // payments methods
    if(Object.keys(this.payment_methods).length == 0){
        for(let [pm, status] of Object.entries(attrs.payment_methods)){
            this.payment_methods[pm] = status
        }
    }
    this.other_payment_method = this.other_payment_method ? this.other_payment_method : attrs.other_payment_method

    /*** delivery info   ***/
    this.delivery_time = this.delivery_time ? this.delivery_time : attrs.delivery_time
    this.port = this.port ? this.port : attrs.port
    if(this.supply_ability.length == 0){
        this.supply_ability = attrs.supply_ability.slice(0)
    }
    this.additional_delivery_information = this.additional_delivery_information ? this.additional_delivery_information : attrs.additional_delivery_information
    this.packaging = this.packaging ? this.packaging : attrs.packaging
}

// Attributes.prototype.isTieredPricingReady = function(){
//     if(!this.isTieredPricing){
//         return false
//     }
//     if(this.tieredPricing.length < 2){
//         return false
//     }
//     return true
// }

// Attributes.prototype.isRangePricingReady = function(){
//     if(this.isTieredPricing){
//         return false
//     }
//     if(this.price_range.length == 0){
//         return false
//     }
//     if(!this.MOQ){
//         return false
//     }
//     return true
// }

// oject loaded from html is differed to a calculated one
// the returned object is to be saved in local file system
Attributes.prototype.differ = function(attrs){ // attrs is calculated
    let obj = new Attributes()
    // this.alibaba_id = ""
    if(this.alibaba_category != attrs.alibaba_category){
        obj.alibaba_category = this.alibaba_category
    }
    if(this.name != attrs.name){
        obj.name = this.name
    }
    
    let keywordsTouched = false
    if(this.keywords.length != 0 && this.keywords.length != attrs.keywords.length){
        keywordsTouched = true
    }else if(this.keywords.length != 0){
        for(let [i, kw] of this.keywords.entries()){
            if(attrs.keywords[i] != kw){
                keywordsTouched = true
                break
            }
        }
    }
    if(keywordsTouched){
        obj.keywords = this.keywords.slice()
    }

    if(this.type != attrs.type){
        obj.type = this.type
    }
    if(this.brand != attrs.brand){
        obj.brand = this.brand
    }
    if(this.origin[0] != attrs.origin[0] || this.origin[1] != attrs.origin[1]){
        obj.origin = this.origin.slice(0)
    }
    if(this.material != attrs.material){
        obj.material = this.material
    }
    if(this.production_method != attrs.production_method){
        obj.production_method = this.production_method
    }

    let idx = 0
    for(let item of this.custom_attributes){
        let a = attrs.custom_attributes[idx]
        if(item[0] && item[1] && (!a || item[0] != a[0] || item[1] != a[1])){
            obj.custom_attributes.push(item.slice())
        }else{
            obj.custom_attributes.push(['', ''])
        }
    }

    /***   trading info   ***/
    obj.isTieredPricing = this.isTieredPricing
    // if(this.isTieredPricing != attrs.isTieredPricing){
    //     obj.isTieredPricing = this.isTieredPricing
    // }
    if(this.sales_unit != attrs.sales_unit){
        obj.sales_unit = this.sales_unit
    }
    if(this.currency != attrs.currency){
        obj.currency = this.currency
    }
    // tiered pricing
    let tieredPricingChanged = false
    if(this.tieredPricing.length != attrs.tieredPricing.length){
        tieredPricingChanged = true
    }else{
        for(let [i, pricing] of this.tieredPricing.entries()){
            if(pricing[0] != attrs.tieredPricing[i][0]){
                tieredPricingChanged = true
            }else if(pricing[1] != attrs.tieredPricing[i][1]){
                tieredPricingChanged = true
            }
            if(tieredPricingChanged){
                break
            }
        }
    }
    if(tieredPricingChanged){
        for(let pricing of this.tieredPricing){
            obj.tieredPricing.push(pricing.slice(0))
        }
    }
    // range pricing
    let rangePricingChanged = false
    if(this.price_range[0] != attrs.price_range[0]){
        rangePricingChanged = true
    }else if(this.price_range[1] != attrs.price_range[1]){
        rangePricingChanged = true
    }
    if(rangePricingChanged){
        obj.price_range = this.price_range.slice(0)
    }
    if(this.MOQ != attrs.MOQ){
        obj.MOQ = this.MOQ
    }
    if(this.additional_trading_infomation != attrs.additional_trading_infomation){
        obj.additional_trading_infomation = this.additional_trading_infomation
    }
    // payment methods
    let paymentMethodsChanged = false
    for(let [pm, status] of Object.entries(this.payment_methods)){
        if(attrs.payment_methods[pm] != status){
            paymentMethodsChanged = true
            break
        }
    }
    if(paymentMethodsChanged){
        for(let [pm, status] of Object.entries(this.payment_methods)){
            obj.payment_methods[pm] = status
        }
    }
    if(this.other_payment_method != attrs.other_payment_method){
        if(!this.other_payment_method){
            obj.other_payment_method = 'undefined'
        }else{
            obj.other_payment_method = this.other_payment_method
        }
    }


    /***   delivery info   ***/
    if(this.delivery_time != attrs.delivery_time){
        obj.delivery_time = this.delivery_time
    }
    if(this.port != attrs.port){
        obj.port = this.port
    }
    let supplyAbilityChanged = false
    for(let [i, item] of this.supply_ability.entries()){
        if(item != attrs.supply_ability[i]){
            supplyAbilityChanged = true
            break
        }
    }
    if(supplyAbilityChanged){
        obj.supply_ability = this.supply_ability.slice(0)
    }
    if(this.additional_delivery_information != attrs.additional_delivery_information){
        obj.additional_delivery_information = this.additional_delivery_information
    }
    if(this.packaging != attrs.packaging){
        obj.packaging = this.packaging
    }

    return obj
}

export {Attributes}