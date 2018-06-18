import {Tab} from '../framework/tab.js'
import {Utils} from '../../libs/utils/utils.js'

function Tab_update(socket, market, categories=undefined, directory=undefined, filename="product_list.json"){
    Tab.call(this, socket, market, categories, directory, filename)

    this.name = "update";
    this.title = "批量更新";
    this.filename = filename;
    this.products = undefined;

    let buttons = `<button type="button" class="btn btn-sm btn-primary synchronize">同步产品信息</button>`;
    buttons = `${buttons}<button type="button" class="btn btn-sm btn-primary update_products">更新所选产品</button>`
    this.$button_group = $(`<div class="btn-group mr-2 update" role="group">${buttons}</div>`);

    this.$content = fw.load_from_template('#template_update');
    let that = this;

    this.$button_group.find('button.synchronize').click(function(){
        that.socket.emit('get_posted_product_info', 10000);
        that.socket.once('get_posted_product_info_result', function(products){
            that.products = products;
            that.socket.emit('serialize', products, market, [], 'product_list.json');
            that.load_products(products, true)
        })
    });

    this.$button_group.find('button.update_products').click(function(){
        let min_price = that.$content.find('.update_content input.min_price').val().trim();
        let max_price = that.$content.find('.update_content input.max_price').val().trim();
        let data = [];
        let price = undefined;
        if(min_price && max_price && !isNaN(min_price) && !isNaN(max_price)){
            price = {'isTieredPricing': false, 'price_range': [min_price, max_price], 'tieredPricing': []}
        }
        let detail_pictures = []
        for(let div of that.$content.find('div.picture_pair')){
            let old_src = $(div).find('img.old').attr('src');
            let new_src = $(div).find('img.new').attr('src');
            detail_pictures.push({'old': old_src, 'new': new_src})
        }
        let $trs = that.$content.find('table.product_list tbody tr')
        for(let tr of $trs) {
            let $tr = $(tr);
            let product = {};
            product['ali_id'] = $tr.data('id');
            if (price) {
                product['price'] = price
            }
            if(detail_pictures.length > 0){
                product['detail_pictures'] = detail_pictures
            }
            data.push(product)
        }
        // console.log(data)
        socket.emit('update_products', data)
    });

    this.$content.find('.detail_pictures button.add').click(function(){
        let old_src = that.$content.find('.detail_pictures input.old_src').val().trim();
        let new_src = that.$content.find('.detail_pictures input.new_src').val().trim();
        let old_img = `<img src="${old_src}" class="img-thumbnail old">`;
        let new_img = `<img src="${new_src}" class="img-thumbnail new">`;
        that.$content.find('.detail_picture_list').append(`<div class="mb-2 picture_pair">${old_img}${new_img}</div>`)

        that.$content.find('.detail_pictures input.old_src').val('');
        that.$content.find('.detail_pictures input.new_src').val('');
    });

    this.$content.find('.detail_picture_list').on('click', 'div.picture_pair', function(){
        $(this).toggleClass('selected')
    });

    this.fetch_values_from_server()
        .then(function(data){
            if(data.length === 0 || !data[0]){
                return
            }
            that.products = data[0];
            that.load_products(that.products, true)
        }).catch(error => console.log(error));

    this.$content.find('thead').on('click', 'th', function(){
        let $th = $(this);
        if($th.index() === 1 || $th.index() === 2){
            return
        }
        Utils.table_sort($th.parents('table'), $th)
    });

    this.$content.find('tbody').on('click', 'tr', function(e){
        if(e.shiftKey){
            let last_selected = $(this).parent().find('.last_selected');
            let idx = $(this).index();
            if(last_selected.length === 0 || last_selected.index() === idx){
                $(this).addClass('selected').siblings('.selected').removeClass('selected');
                $(this).addClass('last_selected').siblings('.last_selected').removeClass('last_selected')
            }else{
                last_selected.siblings('.selected').removeClass('selected');
                let last_idx = last_selected.index();
                let $e = $(this);
                while($e.index() !== last_idx){
                    $e.addClass('selected');
                    if(idx > last_idx){
                        $e = $e.prev()
                    }else if(idx < last_idx){
                        $e = $e.next()
                    }
                }
            }
        }else if(e.ctrlKey){
            $(this).addClass('selected');
            $(this).addClass('last_selected').siblings('.last_selected').removeClass('last_selected')
        }else{
            $(this).addClass('selected').siblings('.selected').removeClass('selected');
            $(this).addClass('last_selected').siblings('.last_selected').removeClass('last_selected')
        }
    });

    this.$content.find('tbody').on('click', 'a', function(e){
        e.preventDefault()
    });

    this.$content.find('select.category').change(function(){
        let key = $(this).find('option:selected').prop('value');
        if(key === 'all'){
            that.load_products(that.products);
            return
        }
        let objects = [];
        for(let p of that.products){
            if(p.category === key){
                objects.push(p)
            }
        }
        that.load_products(objects);
    });

    $('body').on("keydown", function(e){
        console.log('keydown: ', e.key);
        if(e.key === 'Delete'){
            that.$content.find('tbody tr.selected').remove();
            let count = that.$content.find('tbody tr').length;
            that.$content.find('thead th.title span').text(`(${count})`)
            that.$content.find('.detail_picture_list div.picture_pair.selected').remove()
        }
        if(e.key === 'Escape'){
            that.$content.find('tbody tr.selected').removeClass('selected');
            that.$content.find('tbody tr.last_selected').removeClass('last_selected')
        }
    })
}

Tab_update.prototype = Tab.prototype;

Tab_update.prototype.load_products = function (products, load_category=false) {
    let trs = '';
    let re = /(\$[^\/]+)/;
    let categories = [];
    for(let product of products){
        let tds = "";
        // tds = `<td class="ali_id">${product.ali_id}</td>`;
        tds = `${tds}<td class="type">${product.pid}</td>`;
        tds = `${tds}<td class="title"><a href="${product.href}">${product.title}</a></td>`;
        tds = `${tds}<td class="category">${product.category}</td>`;
        if(categories.indexOf(product.category) === -1){
            categories.push(product.category)
        }
        let tag_spans = "";
        for(let tag of product.tags){
            tag_spans = `${tag_spans}<span class="badge badge-info tag">${tag}</span>`;
        }
        tds = `${tds}<td class="tags">${tag_spans}</td>`;
        // console.log(product.price, re.exec(product.price))
        let price = re.exec(product.price)[1].replace(/ /g, '');
        tds = `${tds}<td class="price">${price}</td>`;

        let quality_spans = `<span>${product.quality[0]}</span><span>${product.quality[1]}</span>`;
        tds = `${tds}<td class="quality">${quality_spans}</td>`;
        trs = `${trs}<tr class="${product.ali_id}" data-id="${product.ali_id}">${tds}</tr>`
    }
    this.$content.find('table.product_list tbody').html(trs);

    this.$content.find('table.product_list thead th.title span').text('('+products.length+')');

    if(load_category){
        let options = '<option class="selected" value="all">全部分组</option>';
        for(let category of categories){
            options = `${options}<option class="selected" value="${category}">${category}</option>`
        }
        this.$content.find('select.category').html(options)
    }
};
export {Tab_update}