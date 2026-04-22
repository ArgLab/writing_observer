#!/usr/bin/bash

# This is a script to start up Learning Observer with it's own process
# name. This is convenient for being able to start / stop the process.

. /usr/share/virtualenvwrapper/virtualenvwrapper.sh
workon learning_observer
cd /home/ubuntu/writing_observer/learning_observer
bash -c "exec -a learning_observer python learning_observer" >> /home/ubuntu/lo.log 2>> /home/ubuntu/lo.err
