import {Tab} from '../framework/tab.js'

function Tab_pictures(socket, market, categories=undefined, directory=undefined, filename=undefined){
    Tab.call(this, socket, market, categories, directory, filename)
    
    this.name = 'pictures'
    this.title = '图 片'

    // let buttons = `<button type="button" class="btn btn-sm btn-primary">保 存</button>`
    let buttons = ``
    this.$button_group = $(`<div class="btn-group mr-2 pictures" role="group">${buttons}</div>`)

    this.$content = fw.load_from_template('#template_pictures')

    let that = this
    this.get_file_list()
        .then(function(files){

            let a = that.relative_path_array()
            a.unshift(market.name)
            a.unshift(window.location.pathname)
            let figures = ''
            for(let file of files){
                if(!file.toLowerCase().endsWith('.jpg')){
                    continue
                }
                a.push(file)
                let figure = `<img src="${a.join('/')}" class="figure-img img-fluid rounded" alt="${file}">`
                figure = `${figure}<figcaption class="figure-caption text-center">${file}</figcaption>`
                figure = `<figure class="figure">${figure}</figure>`
                a.pop()
                figures = `${figures}${figure}`
            }
            that.$content.html(figures)
        }).catch(error => console.log(error))
}
Tab_pictures.prototype = Tab.prototype

Tab_pictures.prototype.get_file_list = function(){
    let market = {'name': this.market.name, 'directory': this.market.directory}
    let paths = this.relative_path_array()
    let that = this

    return new Promise(function(resolve, reject){
        that.socket.emit('get_file_list', market, paths, function(files){
            resolve(files)
        })
    })
}
export {Tab_pictures}