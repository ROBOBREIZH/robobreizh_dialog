import argparse
import os
import pandas as pd
import sys
import torch
from transformers import AutoTokenizer

from config import config
from Trainer import LightningModel


class DialogClassifier:
    """
    Class to perform inference from a pre-saved checkpoint
    """

    def __init__(self, checkpoint_path, config):
        self.config = config
        self.tokenizer = AutoTokenizer.from_pretrained(config['model_name'])
        self.model = LightningModel(config=config)
        self.model = self.model.to(config['device'])
        self.model.load_state_dict(torch.load(checkpoint_path, map_location=config['device'])['state_dict'])

    def get_classes(self):
        return self.model.classes

    def dataloader(self, data):
        if not isinstance(data, list):
            data = list(data)

        inputs = dict()

        input_encoding = self.tokenizer.batch_encode_plus(
            data,
            truncation=True,
            max_length=self.config['max_len'],
            return_tensors='pt',
            return_attention_mask=True,
            padding='max_length',
        ).to(self.config['device'])
        seq_len = [len(self.tokenizer.tokenize(utt)) for utt in data]

        inputs['input_ids'] = input_encoding['input_ids']
        inputs['attention_mask'] = input_encoding['attention_mask']
        inputs['seq_len'] = torch.Tensor(seq_len).to(self.config['device'])

        return inputs

    def predict(self, df):
        input = self.dataloader(df)
        with torch.no_grad():
            # model prediction labels
            outputs = self.model.model(input).argmax(dim=-1).tolist()
        return outputs


def main():
    """
    Predict speech acts for the utterances in input file
    :param argv: Takes 1 argument. File with utterances to classify, one per line.
    :return: Prints file with utterances tagged with speech act
    """

    ap = argparse.ArgumentParser()
    ap.add_argument("input_file", help="Input file")
    ap.add_argument("-t", "--training", default="grace", choices=["frozen", "grace", "unfrozen"], help="Training round. Default: 'grace'")

    args = vars(ap.parse_args())

    if args['training'] == 'frozen':
        ckpt_path = 'checkpoints/epoch=28-val_accuracy=0.746056.ckpt'  # Modify to use your checkpoint
    if args['training'] == 'grace':
        ckpt_path = 'checkpoints/epoch=5-val_accuracy=0.665573.ckpt'  # Modify to use your checkpoint
    elif args['training'] == "unfrozen":
        ckpt_path = 'checkpoints/epoch=5-val_accuracy=0.665573.ckpt'  # Modify to use your checkpoint

    clf = DialogClassifier(checkpoint_path=ckpt_path, config=config)
    classes = clf.get_classes()
    inv_classes = {v: k for k, v in classes.items()}  # Invert classes dictionary

    with open(args['input_file'], 'r') as fi:
        utterances = fi.read().splitlines()

    predictions = clf.predict(utterances)
    predicted_acts = [inv_classes[prediction] for prediction in predictions]

    results = pd.DataFrame(list(zip(predicted_acts, utterances)), columns=["DamslActTag", "Text"])
    filename = os.path.basename(args['input_file'])
    if not os.path.exists('output'):
        os.makedirs('output')
    results.to_csv('output/' + os.path.splitext(filename)[0] + ".out", index=False)

    print("-------------------------------------")
    print("Predicted Speech Act, Utterance")
    print("-------------------------------------")

    for utterance, prediction in zip(utterances, predicted_acts):
        print(f"{prediction}, {utterance}")


if __name__ == '__main__':
    main()
