function Tabs(compat=false){
    this.$root
    this.compat = compat
}

Tabs.prototype.init = function($container){
    this.$root = $(fw.load_from_template('#template_tabs'))
    if(this.compat){
        this.$root.find('.card-body').attr('style', 'padding:0px;')
    }
    $container.empty().append(this.$root)

    let $root = this.$root
    this.$root.find('.card-header-tabs').on('click', 'li', function(){

        let name = $(this).data('name')
        console.log(name)
        if(name == 'products_ranking'){
            $('#left').hide()
            $('#right').hide()
        }else{
            $('#left').show()
            $('#right').show()
        }
        $(this).find('a').addClass('active')
        $(this).siblings().find('a').removeClass('active')

        $root.find(`>.card-header .btn-toolbar>.${name}`).show().siblings().hide()
        $root.find(`>.card-body>.${name}`).show().siblings().hide()
    })
}

Tabs.prototype.append_tab = function(tab){
    let $title = $(`<li class="nav-item"><a class="nav-link" href="#">${tab.title}</a></li>`)
    $title.data('name', tab.name)

    this.$root.find('>.card-header .card-header-tabs').append($title)
    this.$root.find('>.card-header .btn-toolbar').append(tab.$button_group)
    this.$root.find('>.card-body').append(tab.$content)

    if(this.$root.find('>.card-header .card-header-tabs li').length == 1){
        $title.find('a').addClass('active')
    }else{
        tab.$button_group.hide()
        tab.$content.hide()
    }
}

export {Tabs}