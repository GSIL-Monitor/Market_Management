$env:FORKED_BY_MULTIPROCESSING=1
D:
cd /workspace/"Market Management"
#Start-Sleep -Seconds 120
.\venv\Scripts\activate
start-process celery -ArgumentList "worker -A tasks -c 1 -l info -Q Eyelashes_p4p -n Eyelashes@localhost"
start-process celery -ArgumentList "worker -A tasks -c 1 -l info -Q Tools_p4p -n Tools@localhost"
start-process celery -ArgumentList "worker -A tasks -c 1 -l info -Q Eyelashes_inquiry -n Eyelashes@localhost"
start-process celery -ArgumentList "beat -A schedule -l info --pidfile="