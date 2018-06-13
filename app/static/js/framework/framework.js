let $notify = $('#main > .notify')

let fw = {}
fw.load_from_template = function(css_selector){
    let tpl = document.querySelector(css_selector).content.cloneNode(true).querySelector('.template_content')
    tpl.classList.remove("template_content")
    return $(tpl)
}

$notify.on('click', 'span.remove_btn', function(){
    let $div = $(this).parent()
    let timer = $div.data('timer')
    clearTimeout(timer)
    $div.fadeOut().remove()
})
fw.notify = function(msg, cls='default', timeout=10000){

    let div = `<span>${msg.content}</span>`
    div = `${div}<span class="remove_btn"><i class="ion-close-round"></i></span>`
    div = `<div class="alert alert-${msg.type} ${cls}" role="alert" style="z-index:1;">${div}</div>`
    let $div = $(div)
    $notify.html($div)

    if(timeout){
        (function($div, timeout){
            let timer = setTimeout(function(){
                            $div.fadeOut().remove()
                        }, timeout)
            $div.data('timer', timer)
        })($div, timeout)
    }
}
