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

minutes_0_30_2_0 = ','.join([str(x) for x in range(0, 29, 2)])
minutes_0_30_2_1 = ','.join([str(x) for x in range(1, 29, 2)])

minutes_30_60_2 = ','.join([str(x) for x in range(30, 60, 2)])
minutes_20_60_2 = ','.join([str(x) for x in range(20, 60, 2)])

app = Celery('scheduler')
app.config_from_object('conf.celeryconfig')
app.conf.beat_schedule = {
    # 'Eyelashes_p4p_record': {
    #     'task': 'tasks.p4p_record',
    #     'schedule': crontab(minute=minutes_0_60_5_0, hour='0-23'),
    #     'kwargs': {'group': '关注词'},
    #     'options': {'queue': 'Eyelashes_p4p'}
    # },
    'Eyelashes_p4p_check_00': {                                          # 直通车App
        'task': 'tasks.p4p_check',
        'schedule': crontab(minute=minutes_0_45_2_0, hour='14'),
        'kwargs': {'group': '直通车App'},
        'options': {'queue': 'Eyelashes_p4p'}
    },
    'Eyelashes_p4p_check_01': {                                          # 直通车App
        'task': 'tasks.p4p_check',
        'schedule': crontab(minute=minutes_0_60_2_0, hour='0,3-13,21-22'),
        'kwargs': {'group': '直通车App'},
        'options': {'queue': 'Eyelashes_p4p'}
    },
    'Eyelashes_p4p_check_02': {                                          # 直通车App
        'task': 'tasks.p4p_check',
        'schedule': crontab(minute=minutes_0_30_2_0, hour='1'),
        'kwargs': {'group': '直通车App'},
        'options': {'queue': 'Eyelashes_p4p'}
    },
    'Eyelashes_p4p_turn_all_off_00': {                                   # 直通车App
        'task': 'tasks.p4p_turn_all_off',
        'schedule': crontab(minute='1', hour='23'),
        'kwargs': {'group': '直通车App'},
        'options': {'queue': 'Eyelashes_p4p'}
    },
    'Eyelashes_p4p_turn_all_off_01': {                                   # 直通车App
        'task': 'tasks.p4p_turn_all_off',
        'schedule': crontab(minute='31', hour='1'),
        'kwargs': {'group': '直通车App'},
        'options': {'queue': 'Eyelashes_p4p'}
    },
    'Eyelashes_p4p_turn_all_off_02': {                                   # 直通车App
        'task': 'tasks.p4p_turn_all_off',
        'schedule': crontab(minute='46', hour='14'),
        'kwargs': {'group': '直通车App'},
        'options': {'queue': 'Eyelashes_p4p'}
    },

    'Eyelashes_p4p_set_sub_budget_0': {                                          # 设置 sub budget
        'task': 'tasks.set_sub_budget',
        'schedule': crontab(minute='30', hour='21'),
        'kwargs': {'sub_budget': '85.00'},
        'options': {'queue': 'Eyelashes_p4p'}
    },
    'Eyelashes_p4p_unset_sub_budget_0': {                                          # 取消 sub budget
        'task': 'tasks.unset_sub_budget',
        'schedule': crontab(minute='2', hour='23'),
        'options': {'queue': 'Eyelashes_p4p'}
    },
    'Eyelashes_p4p_set_sub_budget_1': {                                          # 设置 sub budget
        'task': 'tasks.set_sub_budget',
        'schedule': crontab(minute='0', hour='0'),
        'kwargs': {'sub_budget': '85.00'},
        'options': {'queue': 'Eyelashes_p4p'}
    },
    'Eyelashes_p4p_unset_sub_budget_1': {                                          # 取消 sub budget
        'task': 'tasks.unset_sub_budget',
        'schedule': crontab(minute='31', hour='1'),
        'options': {'queue': 'Eyelashes_p4p'}
    },
    'Eyelashes_p4p_set_sub_budget_2': {                                          # 设置 sub budget
        'task': 'tasks.set_sub_budget',
        'schedule': crontab(minute='20', hour='4'),
        'kwargs': {'sub_budget': '60.00'},
        'options': {'queue': 'Eyelashes_p4p'}
    },
    'Eyelashes_p4p_unset_sub_budget_2': {                                          # 取消 sub budget
        'task': 'tasks.unset_sub_budget',
        'schedule': crontab(minute='2', hour='5'),
        'options': {'queue': 'Eyelashes_p4p'}
    },
    'Eyelashes_p4p_check_10': {                                          # 直通车高消费词
        'task': 'tasks.p4p_check',
        'schedule': crontab(minute=minutes_30_60_2, hour='21'),
        'kwargs': {'group': '直通车高消费词', 'sub_budget_limited': True},
        'options': {'queue': 'Eyelashes_p4p'}
    },
    'Eyelashes_p4p_check_11': {                                          # 直通车高消费词
        'task': 'tasks.p4p_check',
        'schedule': crontab(minute=minutes_0_60_2_1, hour='0,22'),
        'kwargs': {'group': '直通车高消费词', 'sub_budget_limited': True},
        'options': {'queue': 'Eyelashes_p4p'}
    },
    'Eyelashes_p4p_check_12': {                                          # 直通车高消费词
        'task': 'tasks.p4p_check',
        'schedule': crontab(minute=minutes_0_30_2_1, hour='1'),
        'kwargs': {'group': '直通车高消费词', 'sub_budget_limited': True},
        'options': {'queue': 'Eyelashes_p4p'}
    },
    'Eyelashes_p4p_check_13': {                                          # 直通车高消费词
        'task': 'tasks.p4p_check',
        'schedule': crontab(minute=minutes_20_60_2, hour='4'),
        'kwargs': {'group': '直通车高消费词', 'sub_budget_limited': True},
        'options': {'queue': 'Eyelashes_p4p'}
    },
    'Eyelashes_p4p_turn_all_off_10': {                                   # 直通车高消费词
        'task': 'tasks.p4p_turn_all_off',
        'schedule': crontab(minute='1', hour='23'),
        'kwargs': {'group': '直通车高消费词'},
        'options': {'queue': 'Eyelashes_p4p'}
    },
    'Eyelashes_p4p_turn_all_off_11': {                                   # 直通车高消费词
        'task': 'tasks.p4p_turn_all_off',
        'schedule': crontab(minute='31', hour='1'),
        'kwargs': {'group': '直通车高消费词'},
        'options': {'queue': 'Eyelashes_p4p'}
    },
    'Eyelashes_p4p_turn_all_off_12': {                                   # 直通车高消费词
        'task': 'tasks.p4p_turn_all_off',
        'schedule': crontab(minute='1', hour='5'),
        'kwargs': {'group': '直通车高消费词'},
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

    'Eyelashes_inquiry_Emily_check': {                                              # Emily
        'task': 'tasks.inquiry_check',
        'schedule': crontab(minute=minutes_0_60_5_2, hour='0-23'),
        'options': {'queue': 'Eyelashes_inquiry_Emily'}
    },
    'Eyelashes_webww_Emily_check': {                                                # Emily
        'task': 'tasks.webww_check',
        'schedule': crontab(minute=minutes_0_60_5_3, hour='0-23'),
        'options': {'queue': 'Eyelashes_webww_Emily'}
    },
    'Eyelashes_inquiry_Ada_check': {                                              # Ada
        'task': 'tasks.inquiry_check',
        'schedule': crontab(minute=minutes_0_60_5_4, hour='0-23'),
        'options': {'queue': 'Eyelashes_inquiry_Ada'}
    },
    'Eyelashes_webww_Ada_check': {                                                # Ada
        'task': 'tasks.webww_check',
        'schedule': crontab(minute=minutes_0_60_5_0, hour='0-23'),
        'options': {'queue': 'Eyelashes_webww_Ada'}
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
    # 'Tools_webww_check': {
    #     'task': 'tasks.webww_check',
    #     'schedule': crontab(minute=minutes_0_60_5_2, hour='0-23'),
    #     'options': {'queue': 'Tools_webww'}
    # },
    'Tools_p4p_turn_all_off': {
        'task': 'tasks.p4p_turn_all_off',
        'schedule': crontab(minute='45', hour='14'),
        'kwargs': {'group': '0直通车'},
        'options': {'queue': 'Tools_p4p'}
    },
    'Reboot': {
        'task': 'tasks.reboot',
        'schedule': crontab(minute='10', hour='17'),
        'options': {'queue': 'celery'}
    },
    'OSOECO_checkin': {
        'task': 'tasks.osoeco_checkin',
        'schedule': crontab(minute='23', hour='9'),
        'options': {'queue': 'celery'}
    }
}