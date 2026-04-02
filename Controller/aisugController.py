import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.tree import DecisionTreeClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from flask import Flask, request, jsonify
# import pymssql
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine



load_dotenv()



def get_connection():
    server = os.getenv("DB_SERVER")
    database = os.getenv("DB_NAME")
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")

    engine = create_engine(
        f"mssql+pymssql://{user}:{password}@{server}/{database}"
    )
    return engine

def get_data_from_db():
    engine = get_connection()
    query = """
        SELECT 
            e.Student_Id,
            e.Course_Id,
            c.Title,
            c.Description,
            c.Classes_id,
            COUNT(e.Course_Id) OVER (PARTITION BY e.Course_Id) AS Course_Popularity
        FROM Enroll AS e
        JOIN Courses AS c ON e.Course_Id = c.Course_Id
    """
    df = pd.read_sql(query, engine)
    return df


def get_all_courses_from_db():
    engine = get_connection()
    query = "SELECT Course_Id, Title, Description, Classes_id FROM Courses"
    df = pd.read_sql(query, engine)
    return df


def get_course_suggestions(student_id, top_n=10):
    df = get_data_from_db()
    all_courses = get_all_courses_from_db()

    # Courses student is already enrolled in
    enrolled_course_ids = df[df['Student_Id'] == student_id]['Course_Id'].tolist()

    # Courses student is NOT enrolled in
    not_enrolled = all_courses[~all_courses['Course_Id'].isin(enrolled_course_ids)]

    if not_enrolled.empty:
        return {
            "message": "Student is already enrolled in all available courses.",
            "suggestions": [],
            "model_accuracy": None
        }

    # If student has no enrollment history OR not enough data for ML
    if student_id not in df['Student_Id'].values or len(df) < 5:
        suggestions = []
        for _, row in not_enrolled.head(top_n).iterrows():
            suggestions.append({
                "course_id": int(row['Course_Id']),
                "title": row['Title'],
                "description": row['Description'],
                "confidence": None,
                "reason": "Recommended course — explore and enroll!"
            })

        return {
            "student_id": student_id,
            "total_suggestions": len(suggestions),
            "suggestions": suggestions,
            "overall_best_accuracy": None,
            "reason": "Not enough data for ML — showing all available courses"
        }

    # -------- ML Part --------
    df['Enrolled'] = 1
    pivot = df.pivot_table(
        index='Student_Id',
        columns='Course_Id',
        values='Enrolled',
        fill_value=0
    )

    suggestions = []
    best_score = 0

    for course_id in not_enrolled['Course_Id'].tolist():
        if course_id not in pivot.columns:
            continue

        y = pivot[course_id]
        X = pivot.drop(columns=[course_id])

        if y.nunique() < 2:
            continue

        imputer = SimpleImputer(strategy='median')
        X_imputed = imputer.fit_transform(X)

        X_train, X_test, y_train, y_test = train_test_split(
            X_imputed, y, test_size=0.2, random_state=42
        )

        models = {
            "Decision Tree": DecisionTreeClassifier(),
            "Naive Bayes": GaussianNB(),
            "KNN": KNeighborsClassifier()
        }

        course_best_score = 0
        course_best_model = None
        course_best_model_name = ""

        for name, model in models.items():
            try:
                model.fit(X_train, y_train)
                preds = model.predict(X_test)
                acc = accuracy_score(y_test, preds)
                if acc > course_best_score:
                    course_best_score = acc
                    course_best_model = model
                    course_best_model_name = name
            except:
                continue

        if course_best_model is None:
            continue

        if student_id in pivot.index:
            student_row = pivot.loc[student_id].drop(course_id).values.reshape(1, -1)
            student_row = imputer.transform(student_row)
            prediction = course_best_model.predict(student_row)[0]
            probability = course_best_model.predict_proba(student_row)[0][1] \
                if hasattr(course_best_model, 'predict_proba') else course_best_score

            if prediction == 1:
                course_info = not_enrolled[not_enrolled['Course_Id'] == course_id].iloc[0]
                suggestions.append({
                    "course_id": int(course_id),
                    "title": course_info['Title'],
                    "description": course_info['Description'],
                    "confidence": round(float(probability), 4),
                    "best_model": course_best_model_name,
                    "model_accuracy": round(course_best_score, 4),
                    "reason": "Based on your enrollment history"
                })

                if course_best_score > best_score:
                    best_score = course_best_score

    # Sort by confidence
    suggestions = sorted(suggestions, key=lambda x: x['confidence'], reverse=True)

    # Final fallback — always return something
    if not suggestions:
        for _, row in not_enrolled.head(top_n).iterrows():
            suggestions.append({
                "course_id": int(row['Course_Id']),
                "title": row['Title'],
                "description": row['Description'],
                "confidence": None,
                "reason": "Popular course — fallback recommendation"
            })

    return {
        "student_id": student_id,
        "total_suggestions": len(suggestions[:top_n]),
        "suggestions": suggestions[:top_n],
        "overall_best_accuracy": round(best_score, 4) if best_score > 0 else None
    }