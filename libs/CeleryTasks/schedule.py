from celery import Celery
from celery.schedules import crontab

minutes_0_60_2_0 = ','.join([str(x) for x in range(0, 60, 2)])
minutes_0_60_2_1 = ','.join([str(x) for x in range(1, 60, 2)])

minutes_0_60_5_0 = ','.join([str(x) for x in range(0, 60, 5)])
minutes_0_60_5_1 = ','.join([str(x) for x in range(1, 60, 5)])
minutes_0_60_5_2 = ','.join([str(x) for x in range(2, 60, 5)])
minutes_0_60_5_3 = ','.join([str(x) for x in range(3, 60, 5)])
minutes_0_60_5_4 = ','.join([str(x) for x in range(4, 60, 5)])

minutes_0_60_3_1 = ','.join([str(x) for x in range(1, 60, 3)])
minutes_0_45_3_1 = ','.join([str(x) for x in range(1, 45, 3)])

minutes_0_45_2_0 = ','.join([str(x) for x in range(0, 45, 2)])
minutes_0_45_2_1 = ','.join([str(x) for x in range(1, 45, 2)])

minutes_0_30_2_0 = ','.join([str(x) for x in range(0, 29, 2)])
minutes_0_30_2_1 = ','.join([str(x) for x in range(1, 29, 2)])

minutes_30_60_2 = ','.join([str(x) for x in range(30, 60, 2)])
minutes_20_60_2 = ','.join([str(x) for x in range(20, 60, 2)])

app = Celery('scheduler')
app.config_from_object('conf.celeryconfig')
app.conf.beat_schedule = {

    'Eyelashes_p4p_check_00': {                                          # 直通车App
        'task': 'tasks.p4p_check',
        'schedule': crontab(minute=minutes_0_45_3_1, hour='14'),
        'kwargs': {'group': '直通车App'},
        'options': {'queue': 'Eyelashes_p4p_1'}
    },
    'Eyelashes_p4p_check_01': {                                          # 直通车App
        'task': 'tasks.p4p_check',
        'schedule': crontab(minute=minutes_0_60_5_1, hour='0-13,21-23'),
        'kwargs': {'group': '直通车App'},
        'options': {'queue': 'Eyelashes_p4p_1'}
    },
    'Eyelashes_p4p_turn_all_off_02': {                                   # 直通车App
        'task': 'tasks.p4p_turn_all_off',
        'schedule': crontab(minute='49', hour='14'),
        'kwargs': {'group': '直通车App'},
        'options': {'queue': 'Eyelashes_p4p_1'}
    },

    'Eyelashes_p4p_check_15': {                                          # 直通车高消费词
        'task': 'tasks.p4p_check',
        'schedule': crontab(minute=minutes_30_60_2, hour='21'),
        'kwargs': {'group': '直通车高消费词'},
        'options': {'queue': 'Eyelashes_p4p_2'}
    },
    'Eyelashes_p4p_check_16': {                                          # 直通车高消费词
        'task': 'tasks.p4p_check',
        'schedule': crontab(minute=minutes_0_60_2_1, hour='0-5,22,23'),
        'kwargs': {'group': '直通车高消费词'},
        'options': {'queue': 'Eyelashes_p4p_2'}
    },
    'Eyelashes_p4p_turn_all_off_17': {                                   # 直通车高消费词
        'task': 'tasks.p4p_turn_all_off',
        'schedule': crontab(minute='4', hour='6'),
        'kwargs': {'group': '直通车高消费词'},
        'options': {'queue': 'Eyelashes_p4p_2'}
    },

    # 'Eyelashes_inquiry_check': {
    #     'task': 'tasks.inquiry_check',
    #     'schedule': crontab(minute=minutes_0_60_5_0, hour='0-23'),
    #     'options': {'queue': 'Eyelashes_inquiry'}
    # },
    # 'Eyelashes_webww_check': {
    #     'task': 'tasks.webww_check',
    #     'schedule': crontab(minute=minutes_0_60_5_1, hour='0-23'),
    #     'options': {'queue': 'Eyelashes_webww'}
    # },
    # 'Eyelashes_inquiry_Emily_check': {                                              # Emily
    #     'task': 'tasks.inquiry_check',
    #     'schedule': crontab(minute=minutes_0_60_5_2, hour='0-23'),
    #     'options': {'queue': 'Eyelashes_inquiry_Emily'}
    # },
    # 'Eyelashes_webww_Emily_check': {                                                # Emily
    #     'task': 'tasks.webww_check',
    #     'schedule': crontab(minute=minutes_0_60_5_3, hour='0-23'),
    #     'options': {'queue': 'Eyelashes_webww_Emily'}
    # },
    # 'Eyelashes_inquiry_Ada_check': {                                              # Ada
    #     'task': 'tasks.inquiry_check',
    #     'schedule': crontab(minute=minutes_0_60_5_4, hour='0-23'),
    #     'options': {'queue': 'Eyelashes_inquiry_Ada'}
    # },
    # 'Eyelashes_webww_Ada_check': {                                                # Ada
    #     'task': 'tasks.webww_check',
    #     'schedule': crontab(minute=minutes_0_60_5_0, hour='0-23'),
    #     'options': {'queue': 'Eyelashes_webww_Ada'}
    # },
    # 'Tools_p4p_check_0': {
    #     'task': 'tasks.p4p_check',
    #     'schedule': crontab(minute=minutes_0_45_2_1, hour='14'),
    #     'kwargs': {'group': '0直通车'},
    #     'options': {'queue': 'Tools_p4p'}
    # },
    # 'Tools_p4p_check_1': {
    #     'task': 'tasks.p4p_check',
    #     'schedule': crontab(minute=minutes_0_60_2_1, hour='0-13,20-23'),
    #     'kwargs': {'group': '0直通车'},
    #     'options': {'queue': 'Tools_p4p'}
    # },
    # 'Tools_p4p_turn_all_off': {
    #     'task': 'tasks.p4p_turn_all_off',
    #     'schedule': crontab(minute='45', hour='14'),
    #     'kwargs': {'group': '0直通车'},
    #     'options': {'queue': 'Tools_p4p'}
    # },
    # 'Reboot': {
    #     'task': 'tasks.reboot',
    #     'schedule': crontab(minute='57', hour='14'),
    #     'options': {'queue': 'celery'}
    # },
    # 'OSOECO_checkin': {
    #     'task': 'tasks.osoeco_checkin',
    #     'schedule': crontab(minute='23', hour='9'),
    #     'options': {'queue': 'celery'}
    # }
}