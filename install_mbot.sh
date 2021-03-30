#!/bin/bash
sudo apt-get install python3.7 -y
sudo apt-get install python3.7-dev -y
sudo apt-get install python-pip -y
sudo apt-get install python3-pip -y
cd mbot_natural_language_processing
sudo ./repository.debs
cd ../..
catkin_make --only-pkg-with-deps mbot_nlu
catkin_make --only-pkg-with-deps mbot_nlu_classifiers
catkin_make --only-pkg-with-deps mbot_nlu_filter
catkin_make --only-pkg-with-deps mbot_nlu_training
catkin_make -DCATKIN_WHITELIST_PACKAGES=""
echo "export CUDA_VISIBLE_DEVICES=0" >> ~/.bashrc
source ~/.bashrc
