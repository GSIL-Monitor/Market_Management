from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger
from datetime import datetime
import arrow

class Task():
    def __init__(self, job):
        self.id = job.id
        self.name = job.name
        if self.name != 'shutdown':
            self.market_name = job.func.__self__.market['name']
        
        if job.name == 'P4P.crawl':
            self.type = '记 录'
        elif job.name == 'P4P.monitor':
            self.type = '监 控'
        elif job.name == 'P4P.turn_all_off':
            self.type = '关闭监控'
        elif job.name == 'shutdown':
            self.type = "关机"

        if job.kwargs and 'group' in job.kwargs:
            self.group = job.kwargs['group']

        trigger = job.trigger
        if type(trigger) == IntervalTrigger:
            self.trigger_type = 'interval'
            self.interval = int(trigger.interval.seconds/60)
            self.start_date = arrow.get(trigger.start_date).format('YYYY-MM-DD HH:mm:ss')
            self.end_date = arrow.get(trigger.end_date).format('YYYY-MM-DD HH:mm:ss')
        elif type(trigger) == DateTrigger:
            self.trigger_type = 'date'
            self.run_date = arrow.get(trigger.run_date).format('YYYY-MM-DD HH:mm:ss')
        
        if job.next_run_time:
            next_run_time = job.next_run_time
            # if next_run_time < datetime.now().replace(tzinfo=next_run_time.tzinfo):
            #     next_run_time = next_run_time + trigger.interval
            self.next_run_time = arrow.get(next_run_time).format('YYYY-MM-DD HH:mm:ss')
        else:
            self.next_run_time = None