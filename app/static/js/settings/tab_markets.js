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

    this.$content.on('click', 'tbody tr', function(){
        $(this).addClass('selected').siblings('.selected').removeClass('selected')
    })

    this.socket.emit('get_all_markets', function(mkts){
        for(let name in mkts){
            that.append_market(mkts[name])
        }
    })

    this.$content.on('click', 'button.set_login_info', function(e){
        e.stopPropagation()
        let login_info = prompt("请输入 登录 阿里国际站 的 用户名 和 密码", '用户名 和 密码 请用 英文逗号 分开')
        
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
}

Tab_Markets.prototype.append_market = function(market){
    let html = `<td>${market.name}</td><td>${market.directory}</td>`
    html = `${html}<td><button type="button" class="btn btn-sm btn-primary set_login_info">登录信息</button></td>`
    html = `<tr>${html}</tr>`
    let $tr = $(html)
    this.$content.find('tbody').append($tr)
    $tr.data('market', market)
}

export {Tab_Markets}