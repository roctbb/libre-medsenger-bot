supervisorctl stop agents-libre-queue
ps -A | grep chrome | awk '{print $1}' | xargs kill -9 $1
supervisorctl start agents-libre-queue