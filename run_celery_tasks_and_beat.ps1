$env:FORKED_BY_MULTIPROCESSING=1
D:
cd /workspace/"Market Management"
Start-Sleep -Seconds 120
.\venv\Scripts\activate
start-process celery -ArgumentList "worker -A tasks -c 2 -l info -Q Eyelashes_p4p,celery -n Eyelashes[p4p]@localhost"
start-process celery -ArgumentList "worker -A tasks -c 1 -l info -Q Tools_p4p,celery -n Tools[p4p]@localhost"
start-process celery -ArgumentList "worker -A tasks -c 1 -l info -Q Eyelashes_inquiry,celery -n Eyelashes[inquiry]@localhost"
start-process celery -ArgumentList "worker -A tasks -c 1 -l info -Q Tools_webww,celery -n Tools[webww]@localhost"
start-process celery -ArgumentList "worker -A tasks -c 1 -l info -Q Eyelashes_webww,celery -n Eyelashes[webww]@localhost"

start-process celery -ArgumentList "beat -A schedule -l info --pidfile="
start-process flower -ArgumentList "--port=5555 --broker=redis://localhost:6379/0 --broker_api=redis://localhost:6379/0"