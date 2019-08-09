import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix


def random_forest(data_ind, data):
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

    # Data preparation
    def win_loss(row):
        if row["P/L AUD"] >= 0:
            return 1
        else:
            return 0

    data["win_loss"] = data.apply(win_loss, axis=1)
    data_smp = data.copy()  # [:500].copy()
    data_smp_indx = data_smp[["entry", "win_loss"]].copy()
    data_smp_indx.set_index("entry", inplace=True)

    data_ind_smp = data_ind.drop(["open", "high", "low", "close"],
                                 axis=1).copy()
    data_ind_smp_shift = data_ind_smp.shift(1).copy()

    data_RF = data_smp_indx.merge(
        data_ind_smp_shift, how="left", left_index=True, right_index=True,
        validate="1:1")
    data_RF_clean = data_RF.dropna().copy()

    X_trial = data_RF_clean.drop("win_loss", axis=1)[:500]
    y_trial = data_RF_clean["win_loss"][:500]
    X_train, X_test, y_train, y_test = train_test_split(
        X_trial, y_trial, random_state=42)

    X_true = data_RF_clean.drop("win_loss", axis=1)[500:750]
    y_true = data_RF_clean["win_loss"][500:750]

    # Train random forest
    clf.fit(X_train, y_train)
    print("\nmodel score: %.3f\n" % clf.score(X_test, y_test))

    
    # Test random forest
    rf_pred_test = clf.predict(X_test)
    # print(classification_report(y_test, rf_pred_test))

    rf_pred_true = clf.predict(X_true)
    # print(classification_report(y_true, rf_pred_true))

    # Evaluate random forest
    rf_cm_test = confusion_matrix(y_test, rf_pred_test)

    rf_cm_true = confusion_matrix(y_true, rf_pred_true)

    def plot_confusion_matrix(cm, classes,
                              normalize=False,
                              title='Confusion matrix'):
        """
        Taken from http://scikit-learn.org/stable/auto_examples/model_selection
        /plot_confusion_matrix.html

        This function prints the confusion matrix.
        Normalization can be applied by setting `normalize=True`.
        """
        if normalize:
            cm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
            print("\nNormalized confusion matrix\n")
        else:
            print("\nConfusion matrix, without normalization\n")

        return cm

    print("\nSplit Test\n")
    # print(plot_confusion_matrix(
    #    rf_cm_test, classes=[0, 1], normalize=True, title="Test"))
    print(pd.crosstab(
        y_test, rf_pred_test, rownames=["Actual"], colnames=["Predicted"]))

    print("\nTrue (Forward) Test\n")
    # print(plot_confusion_matrix(
    #    rf_cm_true, classes=[0, 1], normalize=True, title="Test"))
    print(pd.crosstab(
        y_true, rf_pred_true, rownames=["Actual"], colnames=["Predicted"]))

    # Prepare data for strategy calculation
    pred_df = pd.DataFrame(
        columns=["predict_win_loss"], data=rf_pred_true, index=y_true.index,
        copy=True)
    comp = pd.concat([y_true, pred_df], axis=1)
    comp.sort_index(inplace=True)
    comp_pred_win = comp[comp["predict_win_loss"] == 1].copy()
    base_line = comp.copy()

    return comp_pred_win, base_line
