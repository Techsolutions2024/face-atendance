import sqlite3
import numpy as np
import cv2
from tkinter import messagebox, filedialog, ttk
import tkinter as tk
from PIL import Image, ImageTk
from picamera2 import Picamera2


def load_embeddings(student_embeddings, conn, c):
    """Tải embedding của sinh viên từ cơ sở dữ liệu và lưu vào student_embeddings."""
    try:
        student_embeddings.clear()
        c.execute("SELECT mssv FROM students")
        student_mssvs = [row[0] for row in c.fetchall()]
        for mssv in student_mssvs:
            c.execute("SELECT embedding FROM student_images WHERE student_id=?", (mssv,))
            embeddings = [np.frombuffer(row[0], dtype=np.float32) for row in c.fetchall() if row[0]]
            if embeddings:
                student_embeddings[mssv] = np.mean(embeddings, axis=0)
    except sqlite3.Error as e:
        print(f"Lỗi khi tải embeddings: {e}")

# Khai báo biến toàn cục cho camera
picam2 = None

def add_student(entry_mssv, entry_name, entry_gender, entry_dob, entry_major, entry_class, app, load_students, conn, c, student_embeddings):
    """Thêm một sinh viên mới vào cơ sở dữ liệu."""
    def start_add_student(source_type):
        global picam2  # Sử dụng biến toàn cục
        source_window.destroy()
        mssv = entry_mssv.get().strip()
        name = entry_name.get().strip()
        gender = entry_gender.get().strip()
        dob = entry_dob.get().strip()
        major = entry_major.get().strip()
        class_name = entry_class.get().strip()

        if not all([mssv, name, gender, dob, major, class_name]):
            messagebox.showerror("Lỗi", "Vui lòng nhập đầy đủ thông tin!")
            return

        if len(mssv) > 50 or len(name) > 100 or len(gender) > 10 or len(dob) > 10 or len(major) > 100 or len(class_name) > 50:
            messagebox.showerror("Lỗi", "Thông tin nhập vào quá dài!")
            return

        try:
            c.execute("INSERT OR IGNORE INTO students (mssv, name, gender, dob, major, class) VALUES (?, ?, ?, ?, ?, ?)",
                      (mssv, name, gender, dob, major, class_name))
            conn.commit()

            embeddings = []
            images = []
            if source_type == "webcam":
                if picam2 is None:  # Kiểm tra xem camera đã được khởi tạo chưa
                    picam2 = Picamera2()
                    config = picam2.create_preview_configuration()
                    picam2.configure(config)
                    picam2.start()
                
                print("Nhấn 'c' để chụp ảnh, 'q' để dừng.")
                while True:
                    frame = picam2.capture_array()
                    if frame is None:
                        break
                    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                    cv2.imshow('Chụp ảnh khuôn mặt', frame)
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord('c'):
                        faces = app.get(frame)
                        if faces:
                            embeddings.append(faces[0].embedding)
                            images.append(frame)
                            print(f"Đã chụp {len(embeddings)} ảnh.")
                    elif key == ord('q'):
                        break
                picam2.stop()
                picam2 = None  # Đặt lại biến camera
                cv2.destroyAllWindows()
            else:
                while True:
                    file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.png")])
                    if not file_path:
                        break
                    student_image = cv2.imread(file_path)
                    if student_image is None:
                        messagebox.showerror("Lỗi", "Không thể đọc file ảnh!")
                        continue
                    faces = app.get(student_image)
                    if faces:
                        embeddings.append(faces[0].embedding)
                        images.append(student_image)
                        if not messagebox.askyesno("Thêm ảnh", "Bạn có muốn thêm ảnh khác không?"):
                            break
                    else:
                        messagebox.showerror("Lỗi", "Không tìm thấy khuôn mặt trong ảnh này!")

            if not embeddings:
                messagebox.showerror("Lỗi", "Phải có ít nhất một ảnh chứa khuôn mặt!")
                c.execute("DELETE FROM students WHERE mssv=?", (mssv,))
                conn.commit()
                return

            for img, embedding in zip(images, embeddings):
                _, img_encoded = cv2.imencode('.jpg', img)
                c.execute("INSERT INTO student_images (student_id, embedding, image) VALUES (?, ?, ?)",
                          (mssv, embedding.tobytes(), img_encoded.tobytes()))
            conn.commit()
            load_embeddings(student_embeddings, conn, c)
            messagebox.showinfo("Thành công", f"Đã thêm sinh viên {name} với {len(embeddings)} ảnh!")
            load_students()
        except sqlite3.Error as e:
            conn.rollback()
            messagebox.showerror("Lỗi", f"Thêm sinh viên thất bại: {e}")

    source_window = tk.Toplevel()
    source_window.title("Chọn nguồn ảnh")
    source_window.geometry("300x200")
    tk.Label(source_window, text="Chọn nguồn để thêm sinh viên:", font=("Arial", 12)).pack(pady=10)
    tk.Button(source_window, text="Webcam", command=lambda: start_add_student("webcam"), bg="#4CAF50", fg="white",
              font=("Arial", 11), width=10).pack(pady=5)
    tk.Button(source_window, text="Tải ảnh", command=lambda: start_add_student("file"), bg="#2196F3", fg="white",
              font=("Arial", 11), width=10).pack(pady=5)

def load_students(student_tree, conn, c):
    """Tải danh sách sinh viên từ cơ sở dữ liệu vào student_tree."""
    try:
        for row in student_tree.get_children():
            student_tree.delete(row)
        c.execute("SELECT mssv, name, gender, dob, major, class FROM students")
        for row in c.fetchall():
            student_tree.insert("", "end", values=row)
    except sqlite3.Error as e:
        print(f"Lỗi khi tải danh sách sinh viên: {e}")

def edit_student(student_tree, app, load_embeddings, load_students, conn, c, student_embeddings):
    """Chỉnh sửa thông tin và ảnh của sinh viên."""
    selected = student_tree.selection()
    if not selected:
        messagebox.showerror("Lỗi", "Vui lòng chọn một sinh viên để chỉnh sửa!")
        return

    mssv = str(student_tree.item(selected)['values'][0])
    try:
        c.execute("SELECT * FROM students WHERE mssv=?", (mssv,))
        student = c.fetchone()
        if not student:
            messagebox.showerror("Lỗi", "Không tìm thấy sinh viên!")
            return

        edit_window = tk.Toplevel()
        edit_window.title(f"Chỉnh sửa sinh viên {mssv}")
        edit_window.geometry("400x600")
        edit_window.configure(bg="#f0f0f0")

        tk.Label(edit_window, text="Thông tin sinh viên", font=("Arial", 14, "bold"), bg="#f0f0f0").pack(pady=10)
        tk.Label(edit_window, text="Tên:", font=("Arial", 11), bg="#f0f0f0").pack()
        entry_edit_name = tk.Entry(edit_window, width=25, font=("Arial", 11))
        entry_edit_name.insert(0, student[1])
        entry_edit_name.pack(pady=5)

        tk.Label(edit_window, text="Giới tính:", font=("Arial", 11), bg="#f0f0f0").pack()
        entry_edit_gender = tk.Entry(edit_window, width=25, font=("Arial", 11))
        entry_edit_gender.insert(0, student[2])
        entry_edit_gender.pack(pady=5)

        tk.Label(edit_window, text="Ngày sinh (DD-MM-YYYY):", font=("Arial", 11), bg="#f0f0f0").pack()
        entry_edit_dob = tk.Entry(edit_window, width=25, font=("Arial", 11))
        entry_edit_dob.insert(0, student[3])
        entry_edit_dob.pack(pady=5)

        tk.Label(edit_window, text="Chuyên ngành:", font=("Arial", 11), bg="#f0f0f0").pack()
        entry_edit_major = tk.Entry(edit_window, width=25, font=("Arial", 11))
        entry_edit_major.insert(0, student[4])
        entry_edit_major.pack(pady=5)

        tk.Label(edit_window, text="Lớp:", font=("Arial", 11), bg="#f0f0f0").pack()
        entry_edit_class = tk.Entry(edit_window, width=25, font=("Arial", 11))
        entry_edit_class.insert(0, student[5])
        entry_edit_class.pack(pady=5)

        tk.Label(edit_window, text="Ảnh hiện tại", font=("Arial", 11, "bold"), bg="#f0f0f0").pack(pady=5)
        image_frame = tk.Frame(edit_window, bg="#ffffff", relief="groove", bd=2)
        image_tree = ttk.Treeview(image_frame, columns=("ID", "Thumbnail"), show="headings", height=5)
        image_tree.heading("ID", text="ID Ảnh")
        image_tree.heading("Thumbnail", text="Ảnh")
        image_tree.column("ID", width=80, anchor="center")
        image_tree.column("Thumbnail", width=120, anchor="center")
        scrollbar = ttk.Scrollbar(image_frame, orient="vertical", command=image_tree.yview)
        image_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        image_tree.pack(fill="both", expand=True, padx=5, pady=5)
        image_frame.pack(fill="x", padx=10, pady=5)

        image_tree.image_refs = []
        c.execute("SELECT id, image FROM student_images WHERE student_id=?", (mssv,))
        for img_id, img_data in c.fetchall():
            img = cv2.imdecode(np.frombuffer(img_data, dtype=np.uint8), cv2.IMREAD_COLOR)
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            img_pil = Image.fromarray(img_rgb)
            img_pil.thumbnail((50, 50))
            img_tk = ImageTk.PhotoImage(img_pil)
            image_tree.image_refs.append(img_tk)
            image_tree.insert("", "end", values=(img_id, img_tk))

        new_images = []

        def view_image(event):
            selected = image_tree.selection()
            if selected:
                img_id = image_tree.item(selected)["values"][0]
                c.execute("SELECT image FROM student_images WHERE id=?", (img_id,))
                img_data = c.fetchone()[0]
                img = cv2.imdecode(np.frombuffer(img_data, dtype=np.uint8), cv2.IMREAD_COLOR)
                cv2.imshow(f"Ảnh ID {img_id}", img)
                cv2.waitKey(0)
                cv2.destroyAllWindows()

        image_tree.bind("<Double-1>", view_image)

        def choose_new_image(new_images, image_tree):
            def select_image_source(source_type):
                source_window.destroy()
                if source_type == "webcam":
                    picam2 = Picamera2()
                    config = picam2.create_preview_configuration()
                    picam2.configure(config)
                    picam2.start()
                    
                    while True:
                        frame = picam2.capture_array()
                        if frame is None:
                            break
                        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                        cv2.imshow('Chụp ảnh khuôn mặt', frame)
                        key = cv2.waitKey(1) & 0xFF
                        if key == ord('c'):
                            faces = app.get(frame)
                            if faces and len(new_images) < 5:
                                new_images.append((frame, faces[0].embedding))
                                update_image_list()
                            elif len(new_images) >= 5:
                                messagebox.showwarning("Cảnh báo", "Đã đạt giới hạn 5 ảnh mới!")
                        elif key == ord('q'):
                            break
                    picam2.stop()
                    cv2.destroyAllWindows()
                else:
                    while len(new_images) < 5:
                        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.png")])
                        if not file_path:
                            break
                        img = cv2.imread(file_path)
                        if img is None:
                            messagebox.showerror("Lỗi", "Không thể đọc file ảnh!")
                            continue
                        faces = app.get(img)
                        if faces:
                            new_images.append((img, faces[0].embedding))
                            update_image_list()
                            if not messagebox.askyesno("Thêm ảnh", "Bạn có muốn thêm ảnh khác không?"):
                                break
                        else:
                            messagebox.showerror("Lỗi", "Không tìm thấy khuôn mặt trong ảnh này!")
                    if len(new_images) >= 5:
                        messagebox.showwarning("Cảnh báo", "Đã đạt giới hạn 5 ảnh mới!")

            def update_image_list():
                img_id = f"new_{len(new_images)}"
                img, _ = new_images[-1]
                img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                img_pil = Image.fromarray(img_rgb)
                img_pil.thumbnail((50, 50))
                img_tk = ImageTk.PhotoImage(img_pil)
                image_tree.image_refs.append(img_tk)
                image_tree.insert("", "end", values=(img_id, img_tk))

            source_window = tk.Toplevel()
            source_window.title("Chọn nguồn ảnh")
            source_window.geometry("300x200")
            tk.Label(source_window, text="Chọn nguồn để thêm ảnh:", font=("Arial", 12)).pack(pady=10)
            tk.Button(source_window, text="Webcam", command=lambda: select_image_source("webcam"), bg="#4CAF50", fg="white",
                      font=("Arial", 11), width=10).pack(pady=5)
            tk.Button(source_window, text="Tải ảnh", command=lambda: select_image_source("file"), bg="#2196F3", fg="white",
                      font=("Arial", 11), width=10).pack(pady=5)

        def delete_selected_image(image_tree):
            selected = image_tree.selection()
            if not selected:
                messagebox.showerror("Lỗi", "Vui lòng chọn một ảnh để xóa!")
                return
            img_id = image_tree.item(selected)["values"][0]
            if "new" not in str(img_id):
                c.execute("DELETE FROM student_images WHERE id=?", (img_id,))
                conn.commit()
            image_tree.delete(selected)

        def save_changes_with_images(mssv, name, gender, dob, major, class_name, edit_window, new_images, conn, c, student_embeddings, load_students ):
            try:
                c.execute("UPDATE students SET name=?, gender=?, dob=?, major=?, class=? WHERE mssv=?",
                          (name, gender, dob, major, class_name, mssv))
                for img, embedding in new_images:
                    _, img_encoded = cv2.imencode('.jpg', img)
                    c.execute("INSERT INTO student_images (student_id, embedding, image) VALUES (?, ?, ?)",
                              (mssv, embedding.tobytes(), img_encoded.tobytes()))
                conn.commit()
                load_embeddings(student_embeddings, conn, c)
                load_students()
                messagebox.showinfo("Thành công", f"Đã cập nhật thông tin sinh viên {name}!")
                edit_window.destroy()
            except sqlite3.Error as e:
                conn.rollback()
                messagebox.showerror("Lỗi", f"Cập nhật thất bại: {e}")

        button_frame = tk.Frame(edit_window, bg="#f0f0f0")
        tk.Button(button_frame, text="Thêm ảnh", command=lambda: choose_new_image(new_images, image_tree),
                  bg="#2196F3", fg="white", font=("Arial", 10, "bold"), width=10, height=1).pack(side="left", padx=5)
        tk.Button(button_frame, text="Xóa ảnh", command=lambda: delete_selected_image(image_tree),
                  bg="#F44336", fg="white", font=("Arial", 10, "bold"), width=10, height=1).pack(side="left", padx=5)
        tk.Button(button_frame, text="Lưu", command=lambda: save_changes_with_images(mssv, entry_edit_name.get(),
                                                                                     entry_edit_gender.get(),
                                                                                     entry_edit_dob.get(),
                                                                                     entry_edit_major.get(),
                                                                                     entry_edit_class.get(),
                                                                                     edit_window, new_images, conn, c,
                                                                                     student_embeddings, load_students),
                  bg="#4CAF50", fg="white", font=("Arial", 10, "bold"), width=10, height=1).pack(side="left", padx=5)
        tk.Button(button_frame, text="Hủy", command=edit_window.destroy,
                  bg="#9E9E9E", fg="white", font=("Arial", 10, "bold"), width=10, height=1).pack(side="left", padx=5)
        button_frame.pack(pady=10)
    except sqlite3.Error as e:
        messagebox.showerror("Lỗi", f"Lỗi khi chỉnh sửa sinh viên: {e}")

def delete_student(student_tree, load_embeddings, load_students, conn, c, student_embeddings):
    """Xóa sinh viên khỏi cơ sở dữ liệu."""
    selected = student_tree.selection()
    if not selected:
        messagebox.showerror("Lỗi", "Vui lòng chọn một sinh viên để xóa!")
        return

    mssv = str(student_tree.item(selected)['values'][0])
    if messagebox.askyesno("Xác nhận", f"Bạn có chắc muốn xóa sinh viên {mssv}?"):
        try:
            c.execute("DELETE FROM students WHERE mssv=?", (mssv,))
            c.execute("DELETE FROM student_images WHERE student_id=?", (mssv,))
            c.execute("DELETE FROM attendance WHERE student_id=?", (mssv,))
            c.execute("DELETE FROM course_attendance_summary WHERE student_id=?", (mssv,))
            c.execute("DELETE FROM course_students WHERE student_id=?", (mssv,))
            conn.commit()
            load_embeddings(student_embeddings, conn, c)
            load_students()
            messagebox.showinfo("Thành công", f"Đã xóa sinh viên {mssv}!")
        except sqlite3.Error as e:
            conn.rollback()
            messagebox.showerror("Lỗi", f"Xóa sinh viên thất bại: {e}")