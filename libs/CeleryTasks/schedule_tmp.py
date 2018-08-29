from celery import Celery
from celery.schedules import crontab

minutes_0_60_2_0 = ','.join([str(x) for x in range(0, 60, 2)])
minutes_0_60_2_1 = ','.join([str(x) for x in range(1, 60, 2)])

minutes_0_60_5_0 = ','.join([str(x) for x in range(0, 60, 5)])
minutes_0_60_5_1 = ','.join([str(x) for x in range(1, 60, 5)])
minutes_0_60_5_2 = ','.join([str(x) for x in range(2, 60, 5)])
minutes_0_60_5_3 = ','.join([str(x) for x in range(3, 60, 5)])
minutes_0_60_5_4 = ','.join([str(x) for x in range(4, 60, 5)])

minutes_0_45_2_0 = ','.join([str(x) for x in range(0, 45, 2)])
minutes_0_45_2_1 = ','.join([str(x) for x in range(1, 45, 2)])

minutes_30_60_2 = ','.join([str(x) for x in range(30, 60, 2)])
minutes_20_60_2 = ','.join([str(x) for x in range(20, 60, 2)])

app = Celery('scheduler')
app.config_from_object('conf.celeryconfig')
app.conf.beat_schedule = {

    'Eyelashes_p4p_set_sub_budget': {                                          # 设置 sub budget
        'task': 'tasks.set_sub_budget',
        'schedule': crontab(minute='3', hour='16'),
        'kwargs': {'sub_budget': '90.00'},
        'options': {'queue': 'Eyelashes_p4p'}
    },
    'Eyelashes_p4p_unset_sub_budget': {                                          # 取消 sub budget
        'task': 'tasks.unset_sub_budget',
        'schedule': crontab(minute='32', hour='16'),
        'options': {'queue': 'Eyelashes_p4p'}
    },

    'Eyelashes_p4p_check_2': {                                          # 直通车高消费词
        'task': 'tasks.p4p_check',
        'schedule': crontab(minute=minutes_0_60_2_0, hour='15,16'),
        'kwargs': {'group': '直通车App', 'sub_budget_limited': True},
        'options': {'queue': 'Eyelashes_p4p'}
    },
    'Eyelashes_p4p_turn_all_off_1': {                                   # 直通车高消费词
        'task': 'tasks.p4p_turn_all_off',
        'schedule': crontab(minute='30', hour='16'),
        'kwargs': {'group': '直通车App'},
        'options': {'queue': 'Eyelashes_p4p'}
    }
}