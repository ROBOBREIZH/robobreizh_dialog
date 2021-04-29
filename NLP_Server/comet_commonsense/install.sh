sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt-get update
sudo apt-get install python3.7 -y
sudo apt-get install python3-pip -y
pip install gdown

git init
git remote add origin https://github.com/atcbosselut/comet-commonsense.git
git fetch
git checkout -f master

bash scripts/setup/get_atomic_data.sh -y
bash scripts/setup/get_conceptnet_data.sh -y
bash scripts/setup/get_model_files.sh -y
sudo python3.7 -m pip install -r requirements.txt
sudo python3.7 -m spacy download en

python3.7 scripts/data/make_atomic_data_loader.py
python3.7 scripts/data/make_conceptnet_data_loader.py

if [[ -f "./pretrained_models.tar.gz" ]]
then
	echo "Skipping downloading weights."
else
	sudo gdown https://drive.google.com/uc?id=1nYlm-jbnrtnfYVyFmOXq1jS9_qRpaaN4
fi

tar -xvzf pretrained_models.tar.gz
#python3.7 scripts/interactive/atomic_single_example.py --model_file pretrained_models/atomic_pretrained_model.pickle
#python3.7 scripts/interactive/conceptnet_single_example.py --model_file pretrained_models/conceptnet_pretrained_model.pickle

