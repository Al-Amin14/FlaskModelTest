import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.tree import DecisionTreeClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from flask import Flask, request, jsonify
import pyodbc

from dotenv import load_dotenv
import os


load_dotenv()

def get_connection():
    return pyodbc.connect(
        'DRIVER={ODBC Driver 17 for SQL Server};'
        f'SERVER={os.getenv("DB_SERVER")};'
        f'DATABASE={os.getenv("DB_NAME")};'
        f'UID={os.getenv("DB_USER")};'
        f'PWD={os.getenv("DB_PASSWORD")};'
        'Encrypt=Yes;'
        'TrustServerCertificate=Yes;'
        'MultipleActiveResultSets=True;'
    )

def get_data_from_db():
    conn = get_connection()
    query = """..."""
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def get_all_courses_from_db():
    conn = get_connection()
    query = "SELECT Course_Id, Title, Description, Classes_id FROM Courses"
    df = pd.read_sql(query, conn)
    conn.close()
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

    # If student has no enrollment history
    if student_id not in df['Student_Id'].values:
        # Recommend top N most popular courses
        popular = df.groupby(['Course_Id', 'Title', 'Description']) \
                    .size() \
                    .reset_index(name='Popularity') \
                    .sort_values('Popularity', ascending=False)

        # Filter out enrolled
        popular = popular[~popular['Course_Id'].isin(enrolled_course_ids)]

        suggestions = []
        for _, row in popular.head(top_n).iterrows():
            suggestions.append({
                "course_id": int(row['Course_Id']),
                "title": row['Title'],
                "description": row['Description'],
                "reason": "Most popular course among all students"
            })

        return {
            "student_id": student_id,
            "suggestions": suggestions,
            "model_accuracy": None,
            "reason": "No enrollment history found — showing most popular courses"
        }

    # -------- ML Part --------
    # Build student-course matrix
    pivot = df.pivot_table(
        index='Student_Id',
        columns='Course_Id',
        values='Enrolled' if 'Enrolled' in df.columns else 'Course_Popularity',
        fill_value=0
    )
    df['Enrolled'] = 1
    pivot = df.pivot_table(
        index='Student_Id',
        columns='Course_Id',
        values='Enrolled',
        fill_value=0
    )

    # Score each unenrolled course using ML
    suggestions = []
    best_score = 0

    for course_id in not_enrolled['Course_Id'].tolist():
        if course_id not in pivot.columns:
            continue

        y = pivot[course_id]
        X = pivot.drop(columns=[course_id])

        # Need at least 2 classes to train
        if y.nunique() < 2:
            continue

        imputer = SimpleImputer(strategy='median')
        X_imputed = imputer.fit_transform(X)

        X_train, X_test, y_train, y_test = train_test_split(
            X_imputed, y, test_size=0.2, random_state=42
        )

        # Train models and pick best
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

        # Predict if this student will enroll in this course
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

    # Sort by confidence score
    suggestions = sorted(suggestions, key=lambda x: x['confidence'], reverse=True)

    # If ML found no suggestions fall back to popular courses
    if not suggestions:
        popular = df.groupby(['Course_Id', 'Title', 'Description']) \
                    .size() \
                    .reset_index(name='Popularity') \
                    .sort_values('Popularity', ascending=False)
        popular = popular[~popular['Course_Id'].isin(enrolled_course_ids)]

        for _, row in popular.head(top_n).iterrows():
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
