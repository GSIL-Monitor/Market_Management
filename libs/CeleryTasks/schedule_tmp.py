from celery import Celery
from celery.schedules import crontab

minutes_0_60_2_0 = ','.join([str(x) for x in range(0, 60, 2)])
minutes_0_60_2_1 = ','.join([str(x) for x in range(1, 60, 2)])

minutes_0_60_5_0 = ','.join([str(x) for x in range(0, 60, 5)])
minutes_0_60_5_1 = ','.join([str(x) for x in range(1, 60, 5)])
minutes_0_60_5_2 = ','.join([str(x) for x in range(2, 60, 5)])
minutes_0_60_5_3 = ','.join([str(x) for x in range(3, 60, 5)])
minutes_0_60_5_4 = ','.join([str(x) for x in range(4, 60, 5)])

minutes_0_45_2_1 = ','.join([str(x) for x in range(1, 45, 2)])

app = Celery('scheduler')
app.config_from_object('conf.celeryconfig')
app.conf.beat_schedule = {
    'Eyelashes_inquiry_check': {
        'task': 'tasks.inquiry_check',
        'schedule': crontab(minute=minutes_0_60_5_0, hour='0-23'),
        'options': {'queue': 'Eyelashes_inquiry'}
    },
    'Eyelashes_inquiry_Emily_check': {                                              # Emily
        'task': 'tasks.inquiry_check',
        'schedule': crontab(minute=minutes_0_60_5_2, hour='0-23'),
        'options': {'queue': 'Eyelashes_inquiry_Emily'}
    },
    'Eyelashes_inquiry_Ada_check': {                                              # Ada
        'task': 'tasks.inquiry_check',
        'schedule': crontab(minute=minutes_0_60_5_4, hour='0-23'),
        'options': {'queue': 'Eyelashes_inquiry_Ada'}
    }
}