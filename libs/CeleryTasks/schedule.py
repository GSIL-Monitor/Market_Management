from celery import Celery
from celery.schedules import crontab

minutes_0_60_2_0 = ','.join([str(x) for x in range(0,60,2)])
minutes_0_60_2_1 = ','.join([str(x) for x in range(1,60,2)])

minutes_0_60_5_0 = ','.join([str(x) for x in range(0,60,5)])
minutes_0_60_5_1 = ','.join([str(x) for x in range(1,60,5)])
minutes_0_60_5_2 = ','.join([str(x) for x in range(2,60,5)])

minutes_0_45_2_1 = ','.join([str(x) for x in range(1,45,2)])

app = Celery('scheduler')
app.config_from_object('conf.celeryconfig')
app.conf.beat_schedule = {
    'Eyelashes_p4p_record': {
        'task': 'tasks.p4p_record',
        'schedule': crontab(minute=minutes_0_60_5_0, hour='0-23'),
        'kwargs': {'group': '关注词'},
        'options': {'queue': 'Eyelashes_p4p'}
    },
    'Eyelashes_p4p_check': {
        'task': 'tasks.p4p_check',
        'schedule': crontab(minute=minutes_0_60_2_0, hour='0-8'),
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
        'schedule': crontab(minute=minutes_0_60_5_0, hour='0-23'),
        'options': {'queue': 'Eyelashes_inquiry'}
    },
    'Eyelashes_webww_check': {
        'task': 'tasks.webww_check',
        'schedule': crontab(minute=minutes_0_60_5_1, hour='0-23'),
        'options': {'queue': 'Eyelashes_webww'}
    },
    'Tools_p4p_check_0': {
        'task': 'tasks.p4p_check',
        'schedule': crontab(minute=minutes_0_45_2_1, hour='14'),
        'kwargs': {'group': '0直通车'},
        'options': {'queue': 'Tools_p4p'}
    },
    'Tools_p4p_check_1': {
        'task': 'tasks.p4p_check',
        'schedule': crontab(minute=minutes_0_60_2_1, hour='0-13,20-23'),
        'kwargs': {'group': '0直通车'},
        'options': {'queue': 'Tools_p4p'}
    },
    'Tools_webww_check': {
        'task': 'tasks.webww_check',
        'schedule': crontab(minute=minutes_0_60_5_2, hour='0-23'),
        'options': {'queue': 'Tools_webww'}
    },
    'Tools_p4p_turn_all_off': {
        'task': 'tasks.p4p_turn_all_off',
        'schedule': crontab(minute='45', hour='14'),
        'kwargs': {'group': '0直通车'},
        'options': {'queue': 'Tools_p4p'}
    },
    'reboot': {
        'task': 'tasks.reboot',
        'schedule': crontab(minute='20', hour='17'),
        'options': {'queue': 'celery'}
    }
}