import {Tab} from '../framework/tab.js'

function Tab_Markets(socket, market=undefined, categories=undefined, directory=undefined, filename=undefined){
    Tab.call(this, socket, market, categories, directory, filename)

    this.name = 'markets'
    this.title = '市 场'

    let buttons = `<button type="button" class="btn btn-sm btn-primary add_market">添 加</button>`
    buttons = `${buttons}<button type="button" class="btn btn-sm btn-primary remove_market">删 除</button>`
    this.$button_group = $(`<div class="btn-group mr-2" role="group">${buttons}</div>`)

    this.$content = fw.load_from_template('#template_markets')
    let that = this

    this.$button_group.on('click', 'button.add_market', function(){
        socket.emit('add_market', function(market){
            if(!market){
                return
            }
            that.append_market(market)
        })
    })

    this.$button_group.on('click', 'button.remove_market', function(){
        let $tr = that.$content.find('tr.selected')

        let market = $tr.data('market')
        socket.emit('remove_market', market, function(successful){
            $tr.remove()
        })
    })

    this.$content.on('click', 'table.markets tbody tr', function(){
        $(this).toggleClass('selected')

        if($(this).hasClass('selected')){
            $(this).siblings('.selected').removeClass('selected')
            let market = $(this).data('market')
            that.load_accounts(market)
        }else{
            that.$content.find('table.accounts tbody').html('')
        }
    })

    this.socket.emit('get_all_markets', function(mkts){
        for(let name in mkts){
            that.append_market(mkts[name])
        }
    })

    this.$content.on('click', 'button.set_homepage', function(e){
        // e.stopPropagation()
        let homepage = prompt("请输入 公司主页 网址", 'http(s)://url/to/company/homepage')
        
        let market = $(this).parents('tr').data('market')
        market['homepage'] = homepage

        that.socket.emit('update_market', market)
    })

    this.$content.on('click', 'button.set_main_account', function(e){
        // e.stopPropagation()
        let login_info = prompt("请输入 登录 主账号 的 用户名 和 密码", '用户名 和 密码 请用 英文逗号 分开')
        
        if(login_info.split(',').length != 2){
            let msg = {'type': 'danger', 'content': '输入格式错误'}
            fw.notify(msg)
            return
        }
        let market = $(this).parents('tr').data('market')
        let [lid, lpwd] = login_info.split(',')
        market['lid'] = lid.trim()
        market['lpwd'] = lpwd.trim()

        that.socket.emit('update_market', market)
    })
    
    this.$content.on('click', 'button.set_account', function(e){
        // e.stopPropagation()
        let login_info = prompt("请输入 登录 子账号 的 用户名 和 密码", '用户名 和 密码 请用 英文逗号 分开')
        
        if(login_info.split(',').length != 2){
            let msg = {'type': 'danger', 'content': '输入格式错误'}
            fw.notify(msg)
            return
        }

        let [lid, lpwd] = login_info.split(',')
        lid = lid.trim()
        lpwd = lpwd.trim()

        let market = $(this).parents('tr').data('market')
        if(!( 'accounts' in market)){
            market['accounts'] = []
        }

        let found = false
        for(let account of market.accounts){
            if(account.lid == lid){
                account.lpwd = lpwd
                found = true
                break
            }
        }
        if(!found){
            market.accounts.push({'lid': lid, 'lpwd': lpwd})
        }
        that.socket.emit('update_market', market)
    })

    this.$content.on('click', 'button.remove_account', function(e){
        // e.stopPropagation()
        let idx = $(this).parents('tr').index()
        let lid = $(this).parents('tr').find('td:first-child').text().trim()
        let market = that.$content.find('table.markets tr.selected').data('market')

        if(idx==0){
            window.alert('不能删除主账号！')
            return
        }

        market.accounts.splice((idx-1), 1)
        that.socket.emit('update_market', market, function(){
            that.load_accounts(market)
        })
    })
}

Tab_Markets.prototype.append_market = function(market){
    let html = `<td>${market.name}</td><td>${market.directory}</td>`
    if('homepage' in market){
        html = `${html}<td>${market.homepage}</td>`
    }
    let buttons = `<button type="button" class="btn btn-primary set_homepage">主 页</button>`
    buttons = `${buttons}<button type="button" class="btn btn-primary set_main_account">主账号</button>`
    buttons = `${buttons}<button type="button" class="btn btn-primary set_account">子账号</button>`
    buttons = `<div class="btn-group btn-group-sm", role="group">${buttons}</div>`
    html = `${html}<td>${buttons}</td>`
    html = `<tr>${html}</tr>`
    let $tr = $(html)
    this.$content.find('.table.markets tbody').append($tr)
    $tr.data('market', market)
}

Tab_Markets.prototype.load_accounts = function(market){

    let trs = this.account_to_tr({'lid':market.lid, 'lpwd':market.lpwd})

    if('accounts' in market){
        for(let account of market.accounts){
            trs = `${trs}${this.account_to_tr(account)}`
        }
    }
    this.$content.find('.table.accounts tbody').html(trs)
}

Tab_Markets.prototype.account_to_tr = function(account){
    let tds = `<td>${account.lid}</td>`
    let buttons = `<button type="button" class="btn btn-primary remove_account"><i class="material-icons">delete</i></button>`
    buttons = `<div class="btn-group btn-group-sm", role="group">${buttons}</div>`
    tds = `${tds}<td>${buttons}</td>`
    return `<tr>${tds}</tr>`
}

export {Tab_Markets}