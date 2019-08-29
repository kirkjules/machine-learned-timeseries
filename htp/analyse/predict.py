import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split


def random_forest(results_with_properties):
    """
    Where data_ind is the ticker_data with indicator values concatenated,
    and data is results data with P & L calculations.
    """

    # Machine learning setup
    categorical_features = ["iky_cat"]
    categorical_transformer = ColumnTransformer(
        transformers=[
            ("iky_cat", OneHotEncoder(handle_unknown="ignore"),
             categorical_features)], remainder="passthrough")

    clf = Pipeline(
        steps=[("cat_trans", categorical_transformer),
               ("random_forest", RandomForestClassifier(n_estimators=100))])

    train = results_with_properties[0:400].copy()
    X_train, X_test, y_train, y_test = train_test_split(
        train.drop("win_loss", axis=1), train["win_loss"], random_state=42)

    # Train random forest
    clf.fit(X_train, y_train)
    # print("\nmodel score: %.3f\n" % clf.score(X_test, y_test))

    # Test random forest
    pred_test = clf.predict(X_test)

    # pprint(list(zip(X_train, clf.steps[1][1].feature_importances_)))

    pred_results = pd.crosstab(
        y_test, pred_test, rownames=["Actual"], colnames=["Predicted"])

    pred_win_rate = np.round(
        (pred_results.loc[1, 1] / pred_results[1].sum() * 100), decimals=2)

    # print(f"{pred_win_rate}\n")
    if pred_win_rate < 55.:
        return "Predicted win rate less than 55%", None, pred_win_rate

    live = results_with_properties[400:].copy()
    X_live = live.drop("win_loss", axis=1)
    y_live = live["win_loss"].copy()

    pred_live = clf.predict(X_live)
    pred_df = pd.DataFrame(
        columns=["win_loss"], data=pred_live, index=y_live.index,
        copy=True)

    pred_win_df = pred_df[pred_df["win_loss"] == 1].copy()
    base_line_df = y_live.to_frame(name="win_loss")

    return base_line_df, pred_win_df, pred_win_rate
