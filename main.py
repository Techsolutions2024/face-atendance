import sqlite3
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import hashlib
from gui import GUI
from student_management import add_student, load_students, edit_student, delete_student, load_embeddings
from face_recognition import start_attendance, save_unknown_face
from insightface.app import FaceAnalysis
import os
import cv2
import numpy as np
from PIL import Image, ImageTk

student_embeddings = {}

def create_database(conn, c):
    """Tạo các bảng trong cơ sở dữ liệu nếu chưa tồn tại."""
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT NOT NULL
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS students (
        mssv TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        gender TEXT NOT NULL,
        dob TEXT NOT NULL,
        major TEXT NOT NULL,
        class TEXT NOT NULL
    )''')

    # Cập nhật bảng courses để bao gồm start_time và end_time
    c.execute('''CREATE TABLE IF NOT EXISTS courses (
        course_id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_name TEXT NOT NULL,
        course_code TEXT NOT NULL,
        start_time TEXT,  -- Thời gian bắt đầu môn học (ví dụ: "08:00:00")
        end_time TEXT     -- Thời gian kết thúc môn học (ví dụ: "10:00:00")
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS course_students (
        course_id INTEGER,
        student_id TEXT,
        PRIMARY KEY (course_id, student_id),
        FOREIGN KEY (course_id) REFERENCES courses(course_id),
        FOREIGN KEY (student_id) REFERENCES students(mssv)
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS student_images (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id TEXT,
        embedding BLOB,
        image BLOB,
        FOREIGN KEY (student_id) REFERENCES students(mssv)
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS sessions (
        session_id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_id INTEGER,
        start_time TEXT NOT NULL,
        end_time TEXT NOT NULL,
        session_number INTEGER,
        FOREIGN KEY (course_id) REFERENCES courses(course_id)
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id TEXT,
        date TEXT,
        timestamp TEXT,
        status TEXT,
        late_minutes INTEGER,
        image BLOB,
        session_id INTEGER,
        course_id INTEGER,
        FOREIGN KEY (student_id) REFERENCES students(mssv),
        FOREIGN KEY (session_id) REFERENCES sessions(session_id),
        FOREIGN KEY (course_id) REFERENCES courses(course_id)
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS course_attendance_summary (
        student_id TEXT,
        course_id INTEGER,
        total_classes INTEGER DEFAULT 0,
        total_absences INTEGER DEFAULT 0,
        total_lates INTEGER DEFAULT 0,
        total_late_minutes INTEGER DEFAULT 0,
        PRIMARY KEY (student_id, course_id),
        FOREIGN KEY (student_id) REFERENCES students(mssv),
        FOREIGN KEY (course_id) REFERENCES courses(course_id)
    )''')

    conn.commit()

def login(entry_username, entry_password, login_frame, main_frame, refresh_students, conn, c):
    """Xử lý đăng nhập người dùng."""
    username = entry_username.get().strip()
    password = entry_password.get().strip()
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, hashed_password))
    if c.fetchone():
        login_frame.pack_forget()
        main_frame.pack(fill="both", expand=True)
        refresh_students()
    else:
        messagebox.showerror("Lỗi", "Tên đăng nhập hoặc mật khẩu không đúng!")

def register_user(conn, c):
    """Đăng ký người dùng mới."""
    reg_window = tk.Toplevel()
    reg_window.title("Đăng ký tài khoản")
    reg_window.geometry("300x200")

    tk.Label(reg_window, text="Tên đăng nhập:", font=("Arial", 12)).pack(pady=5)
    entry_reg_username = tk.Entry(reg_window, font=("Arial", 11))
    entry_reg_username.pack(pady=5)

    tk.Label(reg_window, text="Mật khẩu:", font=("Arial", 12)).pack(pady=5)
    entry_reg_password = tk.Entry(reg_window, show="*", font=("Arial", 11))
    entry_reg_password.pack(pady=5)

    def save_user():
        username = entry_reg_username.get().strip()
        password = entry_reg_password.get().strip()
        if username and password:
            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            try:
                c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
                conn.commit()
                messagebox.showinfo("Thành công", "Đăng ký thành công!")
                reg_window.destroy()
            except sqlite3.IntegrityError:
                messagebox.showerror("Lỗi", "Tên đăng nhập đã tồn tại!")
        else:
            messagebox.showerror("Lỗi", "Vui lòng nhập đầy đủ thông tin!")

    tk.Button(reg_window, text="Đăng ký", command=save_user, bg="#4CAF50", fg="white",
              font=("Arial", 11, "bold")).pack(pady=10)

def add_from_unknown(app, load_embeddings, conn, c, student_embeddings):
    """Thêm sinh viên từ ảnh Unknown."""
    unknown_dir = "unknown_faces"
    if not os.path.exists(unknown_dir) or not os.listdir(unknown_dir):
        messagebox.showerror("Lỗi", "Không có ảnh Unknown nào để thêm!")
        return

    add_window = tk.Toplevel()
    add_window.title("Thêm sinh viên từ Unknown")
    add_window.geometry("600x400")

    canvas = tk.Canvas(add_window, bg="#ffffff")
    scrollbar = ttk.Scrollbar(add_window, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas, bg="#ffffff")

    scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    images = []
    thumbnails = []

    def load_unknown_images():
        for file in os.listdir(unknown_dir):
            img_path = os.path.join(unknown_dir, file)
            img = cv2.imread(img_path)
            if img is not None:
                faces = app.get(img)
                if faces:
                    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                    img_pil = Image.fromarray(img_rgb)
                    img_pil.thumbnail((100, 100))
                    img_tk = ImageTk.PhotoImage(img_pil)
                    images.append((img, faces[0].embedding, img_path))
                    thumbnails.append(img_tk)

    load_unknown_images()
    if not images:
        messagebox.showerror("Lỗi", "Không tìm thấy khuôn mặt nào trong ảnh Unknown!")
        add_window.destroy()
        return

    selected_images = []

    def toggle_selection(index):
        if index in selected_images:
            selected_images.remove(index)
            labels[index].config(bg="#ffffff")
        else:
            selected_images.append(index)
            labels[index].config(bg="#90EE90")

    labels = []
    for i, thumb in enumerate(thumbnails):
        frame = tk.Frame(scrollable_frame, bg="#ffffff", relief="groove", bd=2)
        label = tk.Label(frame, image=thumb, bg="#ffffff")
        label.image = thumb
        label.pack(pady=5)
        label.bind("<Button-1>", lambda e, idx=i: toggle_selection(idx))
        labels.append(label)
        frame.pack(side="left", padx=10, pady=10)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    input_frame = tk.Frame(add_window, bg="#f0f0f0", pady=10)
    tk.Label(input_frame, text="MSSV:", bg="#f0f0f0").pack()
    entry_mssv = tk.Entry(input_frame)
    entry_mssv.pack(pady=5)
    tk.Label(input_frame, text="Tên:", bg="#f0f0f0").pack()
    entry_name = tk.Entry(input_frame)
    entry_name.pack(pady=5)
    tk.Label(input_frame, text="Giới tính:", bg="#f0f0f0").pack()
    entry_gender = tk.Entry(input_frame)
    entry_gender.pack(pady=5)
    tk.Label(input_frame, text="Ngày sinh (DD-MM-YYYY):", bg="#f0f0f0").pack()
    entry_dob = tk.Entry(input_frame)
    entry_dob.pack(pady=5)
    tk.Label(input_frame, text="Chuyên ngành:", bg="#f0f0f0").pack()
    entry_major = tk.Entry(input_frame)
    entry_major.pack(pady=5)
    tk.Label(input_frame, text="Lớp:", bg="#f0f0f0").pack()
    entry_class = tk.Entry(input_frame)
    entry_class.pack(pady=5)
    input_frame.pack(side="bottom", fill="x")

    def save_from_unknown():
        mssv = entry_mssv.get().strip()
        name = entry_name.get().strip()
        gender = entry_gender.get().strip()
        dob = entry_dob.get().strip()
        major = entry_major.get().strip()
        class_name = entry_class.get().strip()

        if not all([mssv, name, gender, dob, major, class_name]):
            messagebox.showerror("Lỗi", "Vui lòng nhập đầy đủ thông tin!")
            return
        if not selected_images:
            messagebox.showerror("Lỗi", "Vui lòng chọn ít nhất một ảnh!")
            return

        try:
            c.execute("INSERT OR IGNORE INTO students (mssv, name, gender, dob, major, class) VALUES (?, ?, ?, ?, ?, ?)",
                      (mssv, name, gender, dob, major, class_name))
            for idx in selected_images:
                img, embedding, img_path = images[idx]
                _, img_encoded = cv2.imencode('.jpg', img)
                c.execute("INSERT INTO student_images (student_id, embedding, image) VALUES (?, ?, ?)",
                          (mssv, embedding.tobytes(), img_encoded.tobytes()))
                os.remove(img_path)
            conn.commit()
            load_embeddings(student_embeddings, conn, c)
            messagebox.showinfo("Thành công", f"Đã thêm sinh viên {name} từ ảnh Unknown!")
            add_window.destroy()
        except sqlite3.Error as e:
            conn.rollback()
            messagebox.showerror("Lỗi", f"Thêm sinh viên thất bại: {e}")

    tk.Button(add_window, text="Lưu", command=save_from_unknown, bg="#4CAF50", fg="white",
              font=("Arial", 11, "bold")).pack(side="bottom", pady=10)

def main():
    """Hàm chính để khởi chạy ứng dụng."""
    # Khởi tạo cơ sở dữ liệu
    conn = sqlite3.connect('attendance.db')
    c = conn.cursor()
    create_database(conn, c)

    # Tải mô hình nhận diện khuôn mặt
    app = FaceAnalysis(name='buffalo_sc', providers=['CPUExecutionProvider'])
    app.prepare(ctx_id=0, det_size=(640, 640))

    # Tải embeddings sinh viên
    load_embeddings(student_embeddings, conn, c)

    # Khởi tạo giao diện
    root = tk.Tk()
    gui = GUI(root, conn, c, student_embeddings, app, login, register_user, add_student, load_students,
              edit_student, delete_student, start_attendance, save_unknown_face, add_from_unknown, load_embeddings)
    root.mainloop()

    # Đóng kết nối khi thoát
    conn.close()

if __name__ == "__main__":
    main()