function Tab(socket, market, categories=undefined, directory=undefined, filename){
    this.socket = socket
    this.filename = filename
    this.market = market
    this.categories = categories
    this.directory = directory
}

Tab.prototype.relative_path_array = function(){
    if(!this.categories){
        return []
    }else if(!this.directory){
        return this.categories.slice()
    }else{
        let paths = this.categories.slice()
        paths.push(this.directory)
        return paths
    }
}

Tab.prototype.fetch_values_from_server = function(){
    let market = {'name': this.market.name, 'directory': this.market.directory}
    let paths = this.relative_path_array()
    let that = this

    return new Promise(function(resolve, reject){
        that.socket.emit('deserialize', market, paths, that.filename, function(results){
            resolve(results)
        })
    })
}

Tab.prototype.save_values_to_server = function(obj){
    let market = {'name': this.market.name, 'directory': this.market.directory}
    let paths = this.relative_path_array()
    let that = this
    
    return new Promise(function(resolve, reject){
        that.socket.emit('serialize', obj, market, paths, that.filename, function(result){
            resolve(result)
        })
    })
}

    // directory.toLowerCase().endsWith(' serie')
export {Tab}