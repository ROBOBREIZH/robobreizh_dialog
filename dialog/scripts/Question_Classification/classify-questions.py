#!/usr/bin/env python3.6


from sklearn.preprocessing import LabelEncoder
from sklearn import metrics
#from sklearn.externals import joblib
import joblib
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

from create_vectors import create_vector

# def precision(y_true, y_pred, strategy='weighted'):
#     return metrics.precision_score(y_true, y_pred, average=strategy)

# def recall(y_true, y_pred, strategy='weighted'):
#     return metrics.recall_score(y_true, y_pred, average=strategy)

# def f1_score(y_true, y_pred, strategy='weighted'):
#     return metrics.f1_score(y_true, y_pred, average=strategy)

# def training_error(y_true, y_pred):
#     prec = precision(y_true, y_pred)
#     rec = recall(y_true, y_pred)
#     f1 = f1_score(y_true, y_pred)
#     return prec, rec, f1

class classify_question(object):
   
            
    def predict_question_category(question):
        categories = ['when', 'what', 'who', 'affirmation', 'unknown']
        encoder = LabelEncoder()
        encoder.fit(categories)

        clf = joblib.load('model/trained_model.pkl')
   
        predicted_cat = encoder.inverse_transform(clf.predict([create_vector(question.lower())]))
        print("Predicted Category:", predicted_cat[0])
