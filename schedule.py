from celery import Celery
from celery.schedules import crontab

app = Celery('scheduler')
app.config_from_object('celeryconfig')
app.conf.beat_schedule = {
    'Eyelashes_p4p_check': {
    'task': 'tasks.p4p_check',
    'schedule': crontab(minute='*/2'),
    'kwargs': {'group': '直通车App'},
    'options': {'queue': 'Eyelashes_p4p'}
    }
}