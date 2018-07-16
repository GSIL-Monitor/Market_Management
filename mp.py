from multiprocessing import Process

from libs.alibaba.p4p import P4P
from libs.json import JSON

import time
import os


def execute(market):
	print(market['name'])
	p4p = P4P(market, market['lid'], market['lpwd'])

	if market['name'] == 'Eyelashes':
		time.sleep(3)
		group = '直通车App'
	if market['name'] == 'Tools':
		group = '0直通车'

	p4p.monitor(group=group)
	time.sleep(30)
	p4p.turn_all_off(group=group)


if __name__ == '__main__':
	
	market_eyelash = JSON.deserialize('.', 'storage', 'markets.json')['Eyelashes']
	market_tools = JSON.deserialize('.', 'storage', 'markets.json')['Tools']

	proc_eyelash = Process(target=execute, args=[market_eyelash])
	proc_eyelash.daemon = True
	proc_tools = Process(target=execute, args=[market_tools])
	proc_tools.daemon = True
	proc_eyelash.start()
	proc_tools.start()
	proc_eyelash.join()
	proc_tools.join()
	print('process is end')