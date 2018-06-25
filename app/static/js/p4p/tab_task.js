import {Tab} from '../framework/tab.js'

function Tab_Task(socket, market=undefined, categories=undefined, directory=undefined, filename=undefined){
    Tab.call(this, socket, market, categories, directory, filename)

    this.name = 'task'
    this.title = '任 务'
    let buttons = `<button type="button" class="btn btn-sm btn-primary refresh">刷 新</button>`
    this.$button_group = $(`<div class="btn-group mr-2 task" role="group">${buttons}</div>`)

    this.$content = fw.load_from_template('#template_task')
    let that = this

    this.$button_group.find('button.refresh').click(function(){
        that.refresh()
    })

    this.$content.find('#task_interval').val(30)
    this.$content.find('#task_start_date').bootstrapMaterialDatePicker({
        format:'YYYY-MM-DD',
        time: false,
        currentDate: moment()
    }).on('change', function(e, date){
        that.$content.find('#task_end_date').bootstrapMaterialDatePicker('setMinDate', date)
        if(moment(that.$content.find('#task_start_date').val()).isAfter(that.$content.find('#task_end_date').val())){
            that.$content.find('#task_end_date').val(that.$content.find('#task_start_date').val())
        }
    })
    this.$content.find('#task_start_time').bootstrapMaterialDatePicker({
        format:'HH:mm',
        year: false,
        date: false,
        currentDate: moment()
    });

    this.$content.find('#task_end_date').bootstrapMaterialDatePicker({
        format:'YYYY-MM-DD',
        time: false,
        currentDate: moment().add('10', 'm')
    });
    this.$content.find('#task_end_date').bootstrapMaterialDatePicker('setMinDate', moment().add('5', 'm'))

    this.$content.find('#task_end_time').bootstrapMaterialDatePicker({
        format:'HH:mm',
        year: false,
        date: false,
        currentDate: moment().add('10', 'm')
    });
    this.$content.find('#task_end_date').bootstrapMaterialDatePicker('setMinDate', moment().add('5', 'm'))

    this.$content.find('button.add_task').click(function(){

        let task = {}
        task['interval'] = $('#task_interval').val().trim()
        task['start_date'] = $('#task_start_date').val().trim()+' '+$('#task_start_time').val().trim()+":00"
        task['end_date'] = $('#task_end_date').val().trim()+' '+$('#task_end_time').val().trim()+":00"
        task['group'] = $('#keywords_group').val().trim()
        task['type'] = $('#task_type').val().trim()

        if(moment(task['start_date']).isAfter(task['end_date'])){
            alert("开始时间 必须 早于 结束时间");
        }else{
            socket.emit('add_task', market, task, function(tasks){
                console.log(tasks)
            })
        }
    })

    this.$content.find('table.task').on('click', 'button.toggle_task', function(){
        let btn_name = $(this).text()
        let task_id = $(this).parents('tr').data('id')
        if(btn_name == 'pause'){
            socket.emit('pause_task', task_id, function(){
            })
        }else{
            socket.emit('resume_task', task_id, function(){
            })
        }
    })

    this.$content.find('table.task').on('click', 'button.remove_task', function(){
        let task_id = $(this).parents('tr').data('id')
        socket.emit('remove_task', task_id, function(){
            that.$content.find('table.task tbody tr.'+task_id).remove()
            that.$content.find('table.task tbody div.'+task_id).remove()
        })
    })

    socket.on('event_task_added', function(task){
        if(task.market_name != market.name){
            return
        }

        let count = that.$content.find('table.task tbody tr').length + 1
        let tr = task_to_tr(task, count)
        that.$content.find('table.task tbody').append(tr)
    })

    socket.on('event_task_executed', function(task){
        console.log('event_task_executed', task)
        if(task.market_name != market.name){
            return
        }
        let $tr = that.$content.find('tr.'+task.id)
        $tr.find('td:nth-child(7)').text(task.next_run_time)
        $tr.attr('class', task.id)
        that.remove_progress(task.id)
    })

    socket.on('event_task_removed', function(task_id){
        console.log('event_task_removed', task_id)
    })

    socket.on('event_task_paused', function(task){
        console.log('event_task_paused', task)
        if(task.market_name != market.name){
            return
        }
        let $tr = that.$content.find('tr.'+task.id)
        $tr.find('td:nth-child(7)').text('暂 停')
        $tr.find('button.toggle_task i').text('play_arrow')
        $tr.attr('class', task.id+' paused')
    })

    socket.on('event_task_resumed', function(task){
        console.log('event_task_resumed', task)
        if(task.market_name != market.name){
            return
        }
        let $tr = that.$content.find('tr.'+task.id)
        $tr.find('td:nth-child(7)').text(task.next_run_time)
        $tr.find('button.toggle_task i').text('pause')
        $tr.attr('class', task.id)
    })

    socket.on('event_task_submitted', function(task){
        console.log('event_task_submitted', task)
        if(task.market_name != market.name){
            return
        }
        let $tr = that.$content.find('tr.'+task.id)
        $tr.attr('class', task.id+' running')
        // that.update_progress(task.id, 0)
    })

    socket.on('event_task_start_running', function(obj){
        console.log('event_task_start_running', obj)
    })
    socket.on('event_task_last_run_finished', function(obj){
        console.log('event_task_last_run_finished', obj)
        that.$content.find('table.task tbody tr.'+obj.tid).remove()
        that.$content.find('table.task tbody div.'+obj.tid).remove()
    })

    socket.on('event_task_progress', function(obj){
        let $tr = that.$content.find('tr.'+obj.tid)
        if($tr.length == 0){
            return
        }
        that.update_progress(obj.tid, obj.progress)
    })

    that.refresh()
}

Tab_Task.prototype.update_progress = function(tid, progress){
    let that = this
    let $progress = this.$content.find('table.task tbody>div.progress.'+tid)
    if($progress.length == 0){
        let $tr = this.$content.find('tr.'+tid)

        // let interval = setInterval(function(){
        //     let height = $tr.height()
        //     let top = $tr.position().top
        //     if(height == 0 || top == 0){
        //         return
        //     }else{
        //         let bg_color = $tr.css("background-color")

        //         let html = `<div class="progress-bar" role="progressbar" style="width: ${progress}%;" aria-valuenow="${progress}" aria-valuemin="0" aria-valuemax="100"></div>`
        //         html = `<div class="progress ${tid}" style="height: ${height}px;position: absolute;top: ${top}px;left: 0px;right: 0px;z-index: -1; background-color: ${bg_color};">${html}</div>`
        //         $progress = $(html)
        //         that.$content.find('table.task tbody').append($progress)

        //         clearInterval(interval)
        //     }
        // }, 500)
        let height = $tr.height()
        let top = $tr.position().top
        let bg_color = $tr.css("background-color")

        let html = `<div class="progress-bar" role="progressbar" style="width: ${progress}%;" aria-valuenow="${progress}" aria-valuemin="0" aria-valuemax="100"></div>`
        html = `<div class="progress ${tid}" style="height: ${height}px;position: absolute;top: ${top}px;left: 0px;right: 0px;z-index: -1; background-color: ${bg_color};">${html}</div>`
        $progress = $(html)
        this.$content.find('table.task tbody').append($progress)
    }else{
        $progress.find('.progress-bar').attr('style', `width:${progress}%;`).attr('aria-valuenow', progress)
    }
}



Tab_Task.prototype.remove_progress = function(tid){
    this.$content.find('table.task tbody>div.progress.'+tid).remove()
}


Tab_Task.prototype.refresh = function(){
    let that = this
    // p4p_keywords_list.json
    this.socket.emit('deserialize', that.market, [], 'p4p_keywords_list.json', true, function(data){
        let $select = $('#keywords_group')
        let group = []
        let html = '<option selected value="all">全 部</option>'
        for(let kw of data){
            if(group.indexOf(kw.group) == -1){
                group.push(kw.group)
                html = `${html}<option value="${kw.group}">${kw.group}</option>`
            }
        }
        $select.html(html)
    })
    this.load_tasks()
}

Tab_Task.prototype.load_tasks = function(){
    let that = this
    this.socket.emit('get_all_tasks', that.market, function(data){
        data.sort(function(a, b){
            return a.id > b.id
        })
        let $tbody = that.$content.find('table.task tbody')
        $tbody.empty()
        let trs = ''
        let count = 0
        for(let task of data){
            count ++
            $tbody.append(task_to_tr(task, count))
        }

        function try_do(){
            if (!$tbody.width()) {
                window.requestAnimationFrame(try_do);
            }else {
                for(let task of data){
                    if(task.is_running && 'progress' in task)
                    that.update_progress(task.id, task.progress)
                }
            }
        }
        try_do()
        console.log(data, $tbody)
    })
}

function task_to_tr(task, count=''){
    let group = task.group
    if(group == 'all'){
        group = '全 部'
    }
    let cls = [task.id]
    let tds = `<td>${count}</td>`
    if(task.trigger_type == 'interval'){
        tds = `${tds}<td>${task.interval}</td>`
        tds = `${tds}<td>${task.start_date}</td>`
        tds = `${tds}<td>${task.end_date}</td>`
        tds = `${tds}<td>${group}</td>`
        tds = `${tds}<td>${task.type}</td>`
    }else if(task.trigger_type == 'date'){
        tds = `${tds}<td> - </td>`
        tds = `${tds}<td>${task.run_date}</td>`
        tds = `${tds}<td> -------- --:--:-- </td>`
        tds = `${tds}<td>${group}</td>`
        tds = `${tds}<td>${task.type}</td>`
    }

    if(task.is_running){
        cls.push('running')
    }

    let paused = false
    if(task.next_run_time){
        tds = `${tds}<td>${task.next_run_time}</td>`
    }else{
        tds = `${tds}<td>暂 停</td>`
        paused = true
        cls.push('paused')
    }

    let buttons = ""
    let toggle_icon = ""
    if(paused){
        toggle_icon = '<i class="material-icons">play_arrow</i>'
    }else{
        toggle_icon = '<i class="material-icons">pause</i>'
    }
    let remove_icon = '<i class="material-icons">delete</i>'
    buttons = `<button type='button' class="btn btn-sm btn-dark toggle_task">${toggle_icon}</button>`
    buttons = `${buttons}<button type='button' class="btn btn-sm btn-dark remove_task">${remove_icon}</button>`
    tds = `${tds}<td>${buttons}</td>`

    console.log(cls)
    return `<tr class="${cls.join(' ')}" data-id="${task.id}">${tds}</tr>`
}

export {Tab_Task}