import numpy as np
import pandas as pd
from pprint import pprint
from scipy.stats import randint as sp_randint
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.model_selection import RandomizedSearchCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split as data_split


class Predict:

    def __init__(self, results_with_properties, training_size, shuffle=True,
                 test_size=0.1, feature_selection=True):

        train = results_with_properties[0:training_size].copy()

        self.X_train, self.X_test, self.y_train, self.y_test = data_split(
            train.drop("win_loss", axis=1), train["win_loss"], random_state=42,
            shuffle=shuffle, test_size=test_size)

        self.model = self.setup(self.X_train.columns)
        self.model.fit(self.X_train, self.y_train)

    def setup(self, column_labels):

        categorical_features = []
        for feature in column_labels:
            if "iky_cat" in feature:
                categorical_features.append(feature)

        if len(categorical_features) > 0:

            categorical_transformer = ColumnTransformer(
                transformers=[
                    ("iky_cat", OneHotEncoder(handle_unknown="ignore"),
                     categorical_features)], remainder="passthrough")
            clf = Pipeline(
                steps=[
                    ("cat_trans", categorical_transformer),
                    ("random_forest", RandomForestClassifier(n_estimators=100))
                ])
        else:
            clf = Pipeline(
                steps=[
                    ("random_forest", RandomForestClassifier(n_estimators=100))
                ])
        return clf

    @classmethod
    def feature_selection(cls, *args, **kwargs):

        p = cls(*args, **kwargs)

        feature_dictionary = {}
        for feature in list(
          zip(p.X_train, p.model.steps[1][1].feature_importances_)):
            feature_dictionary[feature[0]] = feature[1]

        features = pd.Series(feature_dictionary)
        top_features = list(features.nlargest(n=10, keep="first").index)

        X_train = p.X_train[top_features].copy()
        X_test = p.X_test[top_features].copy()

        model_select_feat = p.setup(X_train.columns)
        model_select_feat.fit(X_train, p.y_train)

        return p.model, p.X_train, p.X_test, model_select_feat, X_train, \
            X_test, p.y_train, p.y_test

    @staticmethod
    def random_search(model, X_train, y_train):

        # specify parameters and distributions to sample from
        param_dist = {"random_forest__max_depth": [3, None],
                      "random_forest__max_features": sp_randint(1, 11),
                      "random_forest__min_samples_split": sp_randint(2, 11),
                      "random_forest__bootstrap": [True, False],
                      "random_forest__criterion": ["gini", "entropy"]}

        n_iter_search = 20
        search = RandomizedSearchCV(
            model, param_distributions=param_dist, n_iter=n_iter_search,
            cv=5, iid=False)
        search.fit(X_train, y_train)

        return search


def predict(results_with_properties, training_size, random_search=False):

    # print("\nFeature Selection\n")
    all_feat_model, all_feat_X_train, all_feat_X_test, select_feat_model,\
        select_feat_X_train, select_feat_X_test, y_train, y_test = \
        Predict.feature_selection(results_with_properties, training_size)

    # print("\nModel Scoring\n")
    all_feat_model_score = all_feat_model.score(all_feat_X_test, y_test)
    select_feat_model_score = select_feat_model.score(
        select_feat_X_test, y_test)

    # print("\nModel Assignment\n")
    if select_feat_model_score > all_feat_model_score:
        model_score = select_feat_model_score
        model = select_feat_model
        X_train = select_feat_X_train
        X_test = select_feat_X_test
    else:
        model_score = all_feat_model_score
        model = all_feat_model
        X_train = all_feat_X_train
        X_test = all_feat_X_test

    if random_search:
        print("\nRandom Search\n")
        opt_model = Predict.random_search(model, X_train, y_train)
        opt_model_score = opt_model.score(X_test, y_test)
        if opt_model_score > model_score:
            print("\nRandom search produces better model with following "
                  "parameters:\n")
            pprint(opt_model.cv_results_['params'][opt_model.best_index_])
            del model
            model = opt_model
        else:
            print("\nModel parameters used are:\n")
            pprint(model["random_forest"].get_params())

    # print("\nModel Test Evaluation\n")
    pred_test = model.predict(X_test)
    pred_results = pd.crosstab(
        y_test, pred_test, rownames=["Actual"], colnames=["Predicted"])

    try:
        pred_win_rate = np.round(
            (pred_results.loc[1, 1] / pred_results[1].sum() * 100), decimals=2)
    except KeyError:
        return None, "NA", all_feat_model_score, select_feat_model_score

    if pred_results[1].sum() < 5:
        return None, "NA", all_feat_model_score, select_feat_model_score

    # This is the important threshold, not the original system win rate.
    if pred_win_rate < 70.:
        return None, pred_win_rate, all_feat_model_score, \
            select_feat_model_score

    live = results_with_properties[training_size:].copy()
    X_live = live[X_test.columns].copy()
    y_live = live["win_loss"].copy()

    # print("\nModel Prediction\n")
    pred_live = model.predict(X_live)
    pred_df = pd.DataFrame(
        columns=["win_loss"], data=pred_live, index=y_live.index,
        copy=True)
    pred_win_df = pred_df[pred_df["win_loss"] == 1].copy()

    return pred_win_df, pred_win_rate, all_feat_model_score, \
        select_feat_model_score
