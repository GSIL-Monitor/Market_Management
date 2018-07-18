from celery import Celery
from celery.schedules import crontab

app = Celery('scheduler')
app.config_from_object('celeryconfig')
app.conf.beat_schedule = {
    'Eyelashes_p4p_check': {
	    'task': 'tasks.p4p_check',
	    'schedule': crontab(minute='0-59/2', hour='2-9'),
	    'kwargs': {'group': '直通车App'},
	    'options': {'queue': 'Eyelashes_p4p'}
    },
    'Eyelashes_p4p_turn_all_off': {
	    'task': 'tasks.p4p_turn_all_off',
	    'schedule': crontab(minute='2', hour='9'),
	    'kwargs': {'group': '直通车App'},
	    'options': {'queue': 'Eyelashes_p4p'}
    },
    'Eyelashes_inquiry_check': {
	    'task': 'tasks.inquiry_check',
	    'schedule': crontab(minute='0-59/5', hour='0-23'),
	    # 'kwargs': {'group': '直通车App'},
	    'options': {'queue': 'Eyelashes_inquiry'}
    },
    'Tools_p4p_check_0': {
	    'task': 'tasks.p4p_check',
	    'schedule': crontab(minute='0-43/2', hour='14'),
	    'kwargs': {'group': '0直通车'},
	    'options': {'queue': 'Tools_p4p'}
    },
    'Tools_p4p_check_1': {
	    'task': 'tasks.p4p_check',
	    'schedule': crontab(minute='0-59/2', hour='0-13,20-23'),
	    'kwargs': {'group': '0直通车'},
	    'options': {'queue': 'Tools_p4p'}
    },
    'Tools_p4p_turn_all_off': {
	    'task': 'tasks.p4p_turn_all_off',
	    'schedule': crontab(minute='45', hour='14'),
	    'kwargs': {'group': '0直通车'},
	    'options': {'queue': 'Tools_p4p'}
    }, 
    'power_off': {
	    'task': 'tasks.power_off',
	    'schedule': crontab(minute='5', hour='9'),
	    # 'kwargs': {'group': '直通车App'},
	    'options': {'queue': 'Eyelashes_p4p'}
    }
    # ,
    # 'Eyelashes_p4p_check_1': {
	   #  'task': 'tasks.p4p_check',
	   #  'schedule': crontab(minute='1-12/2', hour='13'),
	   #  'kwargs': {'group': '直通车App'},
	   #  'options': {'queue': 'Eyelashes_p4p'}
    # },
    # 'Tools_p4p_check_1': {
	   #  'task': 'tasks.p4p_check',
	   #  'schedule': crontab(minute='1-12/2', hour='13'),
	   #  'kwargs': {'group': '0直通车'},
	   #  'options': {'queue': 'Tools_p4p'}
    # }
}