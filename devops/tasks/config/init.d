#!/bin/bash

# The world's simplest, stupidest init script.
#
# THIS IS CURRENTLY UNUSED, SINCE WE USE A SYSTEMD SCRIPT

### BEGIN INIT INFO
# Provides:          learning_observer
# Required-Start:    mountkernfs $local_fs
# Required-Stop:
# Should-Start:
# X-Start-Before:
# Default-Start:     S
# Default-Stop:
# Short-Description: Runs the Learning Observer platform
# Description: This is a part of a larger dev-ops infrastructure. This is unlikely to work in isolation.
### END INIT INFO
#
# written by Piotr Mitros <pmitros@ets.org>


case "$1" in
start)
	cd /home/ubuntu/writing_observer/learning_observer/
        setsid -f su ubuntu ./lo.sh
;;
status)
	printf "For status, run: ps aux | grep learning_observer\n"
;;
stop)
	pkill -f learning_observer
;;

restart)
  	$0 stop
  	$0 start
;;

*)
        echo "Usage: $0 {status|start|stop|restart}"
        exit 1
esac
