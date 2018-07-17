from celery.schedules import crontab
beat_schedule = {
    'Eyelashes_p4p_info': {
    'task': 'tasks.p4p_info',
    'schedule': crontab(minute='*/2'),
    'kwargs': {'group': '0直通车'},
    'options': {'queue': 'Eyelashes_p4p'}
    }
}