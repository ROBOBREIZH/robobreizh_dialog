cd NLP_Server
git clone https://github.com/facebookresearch/DrQA.git && cd DrQA
python3.7 -m pip install -r requirements.txt
python3.7 setup.py develop
bash install_corenlp.sh
