let Utils = {}

Utils['table_sort'] = function($table, $th){
	let ascending = undefined
	if($th[0].hasAttribute('ascending')){
		ascending = true
	}
	if($th[0].hasAttribute('descending')){
		ascending = false
	}


	let idx = $th.index()
	idx++
	$table.find('tbody tr').remove().sort(function(a, b){
		let av = $(a).find(`td:nth-child(${idx})`).text().trim().replace(/[%,\+]/g, '')
		let bv = $(b).find(`td:nth-child(${idx})`).text().trim().replace(/[%,\+]/g, '')

		if(isNaN(av) || isNaN(bv)){
			if(ascending == undefined){
				ascending = true
			}
			if(ascending)
				return (av < bv) ? -1 : ((av > bv) ? 1 : 0)
			else
				return (av > bv) ? -1 : ((av < bv) ? 1 : 0)
		}else{
			if(ascending == undefined){
				ascending = false
			}
			if(ascending){
				// console.log(0+av-bv)
				return 0+av-bv
			}else{
				// console.log(0+bv-av)
				return 0+bv-av
			}
		}
	}).appendTo($table.find('tbody'))

	if(ascending){
		$th[0].removeAttribute('ascending')
		$th[0].setAttribute('descending', '')
	}else{
		$th[0].removeAttribute('descending')
		$th[0].setAttribute('ascending', '')
	}
}

export {Utils}