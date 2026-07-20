"""train_model.py — trains Random Forest congestion classifier"""
import argparse, json, joblib, pandas as pd, numpy as np
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, classification_report

FEATURE_COLS=["hour","hour_sin","hour_cos","dow","is_weekend","mins_to_class","mins_since_class",
              "in_class_now","class_soon","type_lecture","type_lab","type_library","type_cafe",
              "type_gym","type_landmark","area_engineering","area_chemistry","area_bioscience",
              "area_central","area_south","area_northside","area_east"]
TARGET_COL="congestion_id"
LABEL_NAMES=["low","medium","high"]
THRESH_LOW_MED=0.18; THRESH_MED_HIGH=0.68; MARGIN=0.06

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--data",default="traffic_data.csv")
    parser.add_argument("--output",default="congestion_model.pkl")
    parser.add_argument("--trees",type=int,default=300)
    parser.add_argument("--report",action="store_true")
    args=parser.parse_args()

    df=pd.read_csv(args.data)
    ambig=((df["raw_score"]-THRESH_LOW_MED).abs()<MARGIN)|((df["raw_score"]-THRESH_MED_HIGH).abs()<MARGIN)
    df=df[~ambig]
    X=df[FEATURE_COLS].values; y=df[TARGET_COL].values
    X_train,X_test,y_train,y_test=train_test_split(X,y,test_size=0.2,random_state=42,stratify=y)

    clf=RandomForestClassifier(n_estimators=args.trees,max_depth=20,min_samples_split=6,
        min_samples_leaf=3,max_features="sqrt",class_weight="balanced",random_state=42,n_jobs=-1)
    clf.fit(X_train,y_train)

    train_acc=accuracy_score(y_train,clf.predict(X_train))
    test_acc=accuracy_score(y_test,clf.predict(X_test))
    cv=cross_val_score(clf,X_train,y_train,cv=5,scoring="accuracy")
    print(f"Train: {train_acc*100:.1f}%  Test: {test_acc*100:.1f}%  CV: {cv.mean()*100:.1f}%±{cv.std()*100:.1f}%")
    if args.report: print(classification_report(y_test,clf.predict(X_test),target_names=LABEL_NAMES))

    meta={"feature_cols":FEATURE_COLS,"target_col":TARGET_COL,"label_names":LABEL_NAMES,
          "n_estimators":clf.n_estimators,"test_accuracy":round(float(test_acc),4)}
    joblib.dump({"model":clf,"metadata":meta},args.output)
    with open(args.output.replace(".pkl","_metadata.json"),"w") as f: json.dump(meta,f,indent=2)
    print(f"Saved to {args.output}")
