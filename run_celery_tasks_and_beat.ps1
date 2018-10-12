#Start-Sleep -Seconds 120

#D:
#cd \workspace\"Market Management"

E:
cd \workspace\python\"Market Management"
.\venv\Scripts\activate.ps1

$env:FORKED_BY_MULTIPROCESSING=1

#start-process celery -WindowStyle Hidden -ArgumentList "worker -A libs.CeleryTasks.tasks -c 2 -l info -Q Eyelashes_p4p,celery -n Eyelashes[p4p]@localhost"
#start-process celery -WindowStyle Hidden -ArgumentList "worker -A libs.CeleryTasks.tasks -c 1 -l info -Q Tools_p4p,celery -n Tools[p4p]@localhost"
#start-process celery -WindowStyle Hidden -ArgumentList "worker -A libs.CeleryTasks.tasks -c 1 -l info -Q Eyelashes_inquiry,celery -n Eyelashes[inquiry]@localhost"
#start-process celery -WindowStyle Hidden -ArgumentList "worker -A libs.CeleryTasks.tasks -c 1 -l info -Q Tools_webww,celery -n Tools[webww]@localhost"
#start-process celery -WindowStyle Hidden -ArgumentList "worker -A libs.CeleryTasks.tasks -c 1 -l info -Q Eyelashes_webww,celery -n Eyelashes[webww]@localhost"

#start-process celery -WindowStyle Hidden -ArgumentList "worker -A libs.CeleryTasks.tasks -c 1 -l info -Q Eyelashes_inquiry_Emily,celery -n Eyelashes[inquiry]:Emily@localhost"
#start-process celery -WindowStyle Hidden -ArgumentList "worker -A libs.CeleryTasks.tasks -c 1 -l info -Q Eyelashes_webww_Emily,celery -n Eyelashes[webww]:Emily@localhost"

#start-process celery -WindowStyle Hidden -ArgumentList "beat -A libs.CeleryTasks.schedule -l info --pidfile="
#start-process flower -WindowStyle Hidden -ArgumentList "--port=5555 --broker=redis://localhost:6379/0 --broker_api=redis://localhost:6379/0"

start-process celery -ArgumentList "worker -A libs.CeleryTasks.tasks -c 1 -l info -Q Eyelashes_p4p_1,celery -n Eyelashes[p4p]@localhost"
start-process celery -ArgumentList "worker -A libs.CeleryTasks.tasks -c 1 -l info -Q Eyelashes_p4p_2,celery -n Eyelashes[p4p]@localhost"

#start-process celery -ArgumentList "worker -A libs.CeleryTasks.tasks -c 1 -l info -Q Tools_p4p,celery -n Tools[p4p]@localhost"
#start-process celery -ArgumentList "worker -A libs.CeleryTasks.tasks -c 1 -l info -Q Eyelashes_inquiry,celery -n Eyelashes[inquiry]@localhost"
##start-process celery -ArgumentList "worker -A libs.CeleryTasks.tasks -c 1 -l info -Q Tools_webww,celery -n Tools[webww]@localhost"
#start-process celery -ArgumentList "worker -A libs.CeleryTasks.tasks -c 1 -l info -Q Eyelashes_webww,celery -n Eyelashes[webww]@localhost"

#start-process celery -ArgumentList "worker -A libs.CeleryTasks.tasks -c 1 -l info -Q Eyelashes_inquiry_Emily,celery -n Eyelashes[inquiry]:Emily@localhost"
#start-process celery -ArgumentList "worker -A libs.CeleryTasks.tasks -c 1 -l info -Q Eyelashes_webww_Emily,celery -n Eyelashes[webww]:Emily@localhost"

#start-process celery -ArgumentList "worker -A libs.CeleryTasks.tasks -c 1 -l info -Q Eyelashes_inquiry_Ada,celery -n Eyelashes[inquiry]:Ada@localhost"
#start-process celery -ArgumentList "worker -A libs.CeleryTasks.tasks -c 1 -l info -Q Eyelashes_webww_Ada,celery -n Eyelashes[webww]:Ada@localhost"

start-process celery -ArgumentList "beat -A libs.CeleryTasks.schedule -l info --pidfile="
start-process flower -ArgumentList "--port=5555 --broker=redis://localhost:6379/0 --broker_api=redis://localhost:6379/0"