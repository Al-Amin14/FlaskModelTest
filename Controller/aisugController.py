import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.tree import DecisionTreeClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.metrics import precision_score
from sklearn.metrics import recall_score
from sklearn.metrics import f1_score
from flask import jsonify


def getpatientvalue():
    df=pd.read_csv('X_train_2025.csv')


    dfy=df['In-hospital_death'].values
    df=df.drop('In-hospital_death',axis=1)

    # Imputer for replacing empty value with Median
    imputer=SimpleImputer(strategy='median')
    df=imputer.fit_transform(df)
    # Convert to int
    df=df.astype(int)

    # seperating Test And Train Data
    xtest,xtrain,ytest,ytrain=train_test_split(df,dfy,test_size=0.2,random_state=42)

    print("--------------- Decision Tree Classifier -----------------")
    decisiontree=DecisionTreeClassifier()
    decisiontree=decisiontree.fit(xtrain,ytrain)
    yprediction1=decisiontree.predict(xtest) 
    AccurrayScore1=accuracy_score(ytest,yprediction)
    


    print("------------------- Naive Base Classifier -----------------")
    naivebaseClassifier=GaussianNB()
    naivebaseClassifier=naivebaseClassifier.fit(xtrain,ytrain)
    yprediction2=naivebaseClassifier.predict(xtest)
    AccurrayScore2=accuracy_score(ytest,yprediction)


    print("------------------ KNN Classifier ----------------")
    knnclassifire=KNeighborsClassifier()
    knnclassifire=knnclassifire.fit(xtrain,ytrain)
    yprediction3=knnclassifire.predict(xtest)
    AccurrayScore3=accuracy_score(ytest,yprediction)
    
    maxthree=max(AccurrayScore1,AccurrayScore2,AccurrayScore3)
    
    if(maxthree==AccurrayScore1):
        return yprediction1
    elif (maxthree==AccurrayScore2):
        return yprediction2
    else :
        return yprediction3
    
