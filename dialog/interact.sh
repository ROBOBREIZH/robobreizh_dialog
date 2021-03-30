#!/bin/bash
IP="$1"


if [ -z ${IP} ]
	then echo "Not enough arguments"
	exit
fi

#gnome-terminal --command=" bash -c 'source ~/catkin_ws/devel/setup.bash; roslaunch mbot_nlu mbot_nlu.launch nlu_classifier:=gspr_classifier; $SHELL'"&
#sleep 7
gnome-terminal --command=" bash -c 'roslaunch interact interact.launch ip:=${IP}; $SHELL'"
