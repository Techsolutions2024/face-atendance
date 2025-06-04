from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import hashlib
import numpy as np
import cv2
from insightface.app import FaceAnalysis
from .models import User, Student
from .database import get_connection, create_database

app = FastAPI()

conn = get_connection()
create_database(conn)
c = conn.cursor()

# Load face recognition model
face_app = FaceAnalysis(name='buffalo_sc', providers=['CPUExecutionProvider'])
face_app.prepare(ctx_id=0, det_size=(640, 640))

@app.post('/register')
def register(user: User):
    hashed = hashlib.sha256(user.password.encode()).hexdigest()
    try:
        c.execute('INSERT INTO users (username, password) VALUES (?, ?)', (user.username, hashed))
        conn.commit()
        return {'message': 'registered'}
    except Exception:
        raise HTTPException(status_code=400, detail='username exists')

@app.post('/login')
def login(user: User):
    hashed = hashlib.sha256(user.password.encode()).hexdigest()
    c.execute('SELECT * FROM users WHERE username=? AND password=?', (user.username, hashed))
    if c.fetchone():
        return {'message': 'success'}
    raise HTTPException(status_code=401, detail='invalid credentials')

@app.post('/students')
def add_student(student: Student):
    try:
        c.execute('INSERT INTO students (mssv, name, gender, dob, major, class) VALUES (?, ?, ?, ?, ?, ?)',
                  (student.mssv, student.name, student.gender, student.dob, student.major, student.class_name))
        conn.commit()
        return {'message': 'student added'}
    except Exception:
        raise HTTPException(status_code=400, detail='cannot add student')

@app.get('/students')
def list_students():
    c.execute('SELECT mssv, name, gender, dob, major, class FROM students')
    rows = c.fetchall()
    students = [dict(zip(['mssv', 'name', 'gender', 'dob', 'major', 'class'], row)) for row in rows]
    return {'students': students}

@app.post('/recognize')
def recognize(image: UploadFile = File(...)):
    data = image.file.read()
    img_array = np.frombuffer(data, np.uint8)
    img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
    if img is None:
        raise HTTPException(status_code=400, detail='invalid image')
    faces = face_app.get(img)
    results = []
    for face in faces:
        embedding = face.embedding
        # simple recognition by comparing with stored embeddings
        c.execute('SELECT student_id, embedding FROM student_images')
        best_match = None
        best_sim = 0
        for student_id, emb in c.fetchall():
            emb_arr = np.frombuffer(emb, dtype=np.float32)
            sim = np.dot(embedding, emb_arr) / (np.linalg.norm(embedding) * np.linalg.norm(emb_arr))
            if sim > best_sim:
                best_sim = sim
                best_match = student_id
        results.append({'mssv': best_match if best_sim>0.3 else 'unknown', 'similarity': float(best_sim)})
    return {'results': results}
