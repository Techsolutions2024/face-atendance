import cv2
import numpy as np
from tkinter import messagebox, ttk
import tkinter as tk
from PIL import Image, ImageTk
import time
from sklearn.metrics.pairwise import cosine_similarity
import sqlite3
from datetime import datetime
import os
import uuid
from picamera2 import Picamera2
picam2 = Picamera2()
config = picam2.create_preview_configuration()
picam2.configure(config)
picam2.start()
# Từ điển tạm thời để lưu embedding và số lượng ảnh của các nhóm Unknown
unknown_groups = {}  # {group_id: {'embeddings': [list of embeddings], 'count': int}}

def save_unknown_face(frame, face, timestamp, app, unknown_dir="unknown_faces", max_images_per_unknown=2,
                      similarity_threshold=0.3):
    """
    Lưu ảnh Unknown với giới hạn tối đa 2 ảnh cho mỗi người lạ.
    
    Args:
        frame: Frame hình ảnh từ video.
        face: Đối tượng khuôn mặt từ thư viện nhận diện.
        timestamp: Thời gian hiện tại để đặt tên file.
        app: Ứng dụng nhận diện khuôn mặt.
        unknown_dir: Thư mục lưu ảnh unknown (mặc định: "unknown_faces").
        max_images_per_unknown: Số ảnh tối đa cho mỗi nhóm unknown (mặc định: 2).
        similarity_threshold: Ngưỡng độ tương đồng để nhóm các khuôn mặt (mặc định: 0.3).
    
    Returns:
        Đường dẫn file ảnh đã lưu hoặc None nếu không lưu được.
    """
    if not os.path.exists(unknown_dir):
        os.makedirs(unknown_dir)

    box = face.bbox.astype(int)
    # Kiểm tra tính hợp lệ của bounding box
    if (box[0] >= box[2] or box[1] >= box[3] or
            box[0] < 0 or box[1] < 0 or
            box[2] > frame.shape[1] or box[3] > frame.shape[0]):
        print(f"Bounding box không hợp lệ: {box}")
        return None
    
    face_img = frame[box[1]:box[3], box[0]:box[2]]
    if face_img.size == 0:
        print("Ảnh khuôn mặt rỗng")
        return None

    current_embedding = face.embedding
    matched_group = None
    
    # So sánh với các nhóm unknown hiện có
    for group_id, group_info in unknown_groups.items():
        embeddings = group_info['embeddings']
        similarities = cosine_similarity([current_embedding], embeddings)[0]
        if np.max(similarities) > similarity_threshold:
            matched_group = group_id
            break

    if matched_group:
        if unknown_groups[matched_group]['count'] >= max_images_per_unknown:
            print(f"Đã đạt giới hạn {max_images_per_unknown} ảnh cho nhóm Unknown {matched_group}")
            return None
        unknown_groups[matched_group]['embeddings'].append(current_embedding)
        unknown_groups[matched_group]['count'] += 1
    else:
        new_group_id = str(uuid.uuid4().hex)
        unknown_groups[new_group_id] = {
            'embeddings': [current_embedding],
            'count': 1
        }
        matched_group = new_group_id

    filename = f"{unknown_dir}/unknown_{matched_group}_{timestamp}.jpg"
    cv2.imwrite(filename, face_img)
    print(f"Đã lưu ảnh Unknown tại: {filename}")
    return filename

def recognize_faces(frame, student_embeddings, app, conn, c, similarity_threshold=0.3):
    """
    Nhận diện khuôn mặt từ frame và so sánh với embeddings của sinh viên.

    Args:
        frame: Frame hình ảnh từ video.
        student_embeddings: Từ điển chứa embedding của sinh viên {mssv: embedding}.
        app: Ứng dụng nhận diện khuôn mặt.
        conn: Kết nối đến cơ sở dữ liệu SQLite.
        c: Con trỏ cơ sở dữ liệu SQLite.
        similarity_threshold: Ngưỡng độ tương đồng để xác định danh tính (mặc định: 0.3).

    Returns:
        Danh sách các khuôn mặt nhận diện được [(mssv, name, similarity, face)].
    """
    faces = app.get(frame)
    recognized_mssvs = []
    for face in faces:
        embedding = face.embedding
        best_match_mssv = None
        best_similarity = -1
        
        # So sánh embedding với danh sách sinh viên
        for mssv, student_embedding in student_embeddings.items():
            similarity = cosine_similarity([embedding], [student_embedding])[0][0]
            if similarity > best_similarity and similarity > similarity_threshold:
                best_similarity = similarity
                best_match_mssv = mssv
        
        if best_match_mssv:
            c.execute("SELECT name FROM students WHERE mssv=?", (best_match_mssv,))
            result = c.fetchone()
            name = result[0] if result else "Unknown Name"
            recognized_mssvs.append((best_match_mssv, name, best_similarity, face))
        else:
            recognized_mssvs.append(("unknown", "Unknown", 0.0, face))
    return recognized_mssvs

def start_attendance(device_index, entry_class, student_embeddings, app, save_unknown_face, conn, c, course_id,
                     start_time, end_time, late_threshold=15):
    """
    Bắt đầu phiên điểm danh thời gian thực với giao diện hiển thị video và danh sách sinh viên.

    Args:
        device_index: Chỉ số thiết bị camera.
        entry_class: Lớp học (không sử dụng trực tiếp trong hàm này).
        student_embeddings: Từ điển embedding của sinh viên.
        app: Ứng dụng nhận diện khuôn mặt.
        save_unknown_face: Hàm lưu ảnh unknown.
        conn: Kết nối SQLite.
        c: Con trỏ SQLite.
        course_id: Mã khóa học.
        start_time: Thời gian bắt đầu phiên (HH:MM:SS).
        end_time: Thời gian kết thúc phiên (HH:MM:SS).
        late_threshold: Ngưỡng phút muộn (mặc định: 15 phút).
    """
    # Tạo cửa sổ điểm danh
    attendance_window = tk.Toplevel()
    attendance_window.title("Điểm danh thời gian thực")
    attendance_window.geometry("1200x700")
    attendance_window.configure(bg="#f0f0f0")
    attendance_window.protocol("WM_DELETE_WINDOW", lambda: end_session())

    # Khung bên trái cho video và ảnh nhận diện
    left_frame = tk.Frame(attendance_window, bg="#f0f0f0")
    left_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)

    video_frame = tk.Frame(left_frame, bg="#ffffff", relief="groove", bd=2)
    video_label = tk.Label(video_frame, bg="#ffffff")
    video_label.pack(fill="both", expand=False)
    video_frame.pack(fill="x", pady=(0, 10))

    recognition_frame = tk.Frame(left_frame, bg="#ffffff", relief="groove", bd=2)
    recognition_label = tk.Label(recognition_frame, bg="#ffffff")
    recognition_label.pack(side="left", padx=10, pady=10)
    info_label = tk.Label(recognition_frame, text="", font=("Arial", 11), bg="#ffffff", justify="left")
    info_label.pack(side="left", padx=10)
    recognition_frame.pack(fill="x", pady=(0, 10))

    # Khung bên phải cho danh sách sinh viên
    student_frame = tk.Frame(attendance_window, bg="#ffffff", relief="groove", bd=2)
    student_tree = ttk.Treeview(student_frame, columns=("MSSV", "Tên", "Trạng thái", "Phút muộn", "Ghi chú"),
                                show="headings", height=20)
    student_tree.heading("MSSV", text="MSSV")
    student_tree.heading("Tên", text="Tên")
    student_tree.heading("Trạng thái", text="Trạng thái")
    student_tree.heading("Phút muộn", text="Phút muộn")
    student_tree.heading("Ghi chú", text="Ghi chú")
    student_tree.column("MSSV", width=100, anchor="center")
    student_tree.column("Tên", width=150, anchor="w")
    student_tree.column("Trạng thái", width=100, anchor="center")
    student_tree.column("Phút muộn", width=80, anchor="center")
    student_tree.column("Ghi chú", width=100, anchor="center")

    scrollbar_y = ttk.Scrollbar(student_frame, orient="vertical", command=student_tree.yview)
    student_tree.configure(yscrollcommand=scrollbar_y.set)
    scrollbar_y.pack(side="right", fill="y")

    scrollbar_x = ttk.Scrollbar(student_frame, orient="horizontal", command=student_tree.xview)
    student_tree.configure(xscrollcommand=scrollbar_x.set)
    scrollbar_x.pack(side="bottom", fill="x")

    student_tree.pack(side="left", fill="both", expand=True)
    student_frame.pack(side="right", fill="y", padx=10, pady=10)

    # Lấy danh sách sinh viên theo course_id
    c.execute("SELECT s.mssv, s.name FROM students s JOIN course_students cs ON s.mssv = cs.student_id WHERE cs.course_id=?", 
              (course_id,))
    all_students = {row[0]: row[1] for row in c.fetchall()}

    # Tạo phiên điểm danh trong cơ sở dữ liệu
    c.execute("INSERT INTO sessions (course_id, start_time, end_time) VALUES (?, ?, ?)",
              (course_id, start_time, end_time))
    session_id = c.lastrowid
    conn.commit()

    current_time = time.strftime("%Y-%m-%d %H:%M:%S")
    for mssv in all_students:
        c.execute(
            "INSERT INTO attendance (student_id, date, timestamp, status, late_minutes, session_id, course_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (mssv, current_time.split()[0], current_time, "Absent", 0, session_id, course_id))
        c.execute("INSERT OR IGNORE INTO course_attendance_summary (student_id, course_id) VALUES (?, ?)",
                  (mssv, course_id))
        c.execute(
            "UPDATE course_attendance_summary SET total_classes = total_classes + 1, total_absences = total_absences + 1 WHERE student_id=? AND course_id=?",
            (mssv, course_id))
        student_tree.insert("", "end", values=(mssv, all_students[mssv], "Absent", 0, ""))
    conn.commit()

    session_start_time = datetime.strptime(start_time, "%H:%M:%S")
    session_end_time = datetime.strptime(end_time, "%H:%M:%S")
    detected_faces = set()

    recognized_dir = "recognized_faces"
    if not os.path.exists(recognized_dir):
        os.makedirs(recognized_dir)
    unknown_dir = "unknown_faces"
    if not os.path.exists(unknown_dir):
        os.makedirs(unknown_dir)

    def update_video():
        """Cập nhật video và xử lý nhận diện khuôn mặt."""
        if not attendance_window.winfo_exists():
            return

        x = picam2.capture_array()
        frame = cv2.cvtColor(x, cv2.COLOR_BGRA2RGB)

        recognized_faces = recognize_faces(frame, student_embeddings, app, conn, c)
        current_time = time.strftime("%Y-%m-%d %H:%M:%S")
        current_time_dt = datetime.strptime(current_time.split()[1], "%H:%M:%S")
        timestamp = time.strftime("%Y%m%d%H%M%S")

        for mssv, name, similarity, face in recognized_faces:
            box = face.bbox.astype(int)
            box[0] = max(0, box[0])
            box[1] = max(0, box[1])
            box[2] = min(frame.shape[1], box[2])
            box[3] = min(frame.shape[0], box[3])

            color = (0, 255, 0) if mssv != "unknown" else (0, 0, 255)
            cv2.rectangle(frame, (box[0], box[1]), (box[2], box[3]), color, 2)
            label = f"MSSV: {mssv} | Name: {name} | Acc: {similarity:.2f}" if mssv != "unknown" else "Unknown"
            cv2.putText(frame, label, (box[0], box[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

            face_img = frame[box[1]:box[3], box[0]:box[2]]
            if mssv != "unknown":
                filename = f"{recognized_dir}/{mssv}_{timestamp}.jpg"
                cv2.imwrite(filename, face_img)
                print(f"Đã lưu ảnh nhận diện tại: {filename}")
            else:
                filename = save_unknown_face(frame, face, timestamp, app, unknown_dir=unknown_dir)
                if filename:
                    print(f"Đã lưu ảnh Unknown tại: {filename}")

            if face_img.size > 0:
                face_img_rgb = cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB)
                face_img_pil = Image.fromarray(face_img_rgb)
                face_img_pil.thumbnail((100, 100))
                face_img_tk = ImageTk.PhotoImage(face_img_pil)
                recognition_label.config(image=face_img_tk)
                recognition_label.image = face_img_tk

                status = "Unknown"
                late_minutes = 0
                if mssv != "unknown":
                    late_minutes = max(0, int((current_time_dt - session_start_time).total_seconds() / 60))
                    status = "Late" if late_minutes > late_threshold else "Present"
                info_text = f"MSSV: {mssv}\nTên: {name}\nTrạng thái: {status}\nĐộ tương đồng: {similarity:.2f}"
                info_label.config(text=info_text)

            if mssv != "unknown" and mssv not in detected_faces:
                detected_faces.add(mssv)
                _, img_encoded = cv2.imencode('.jpg', face_img)
                late_minutes = max(0, int((current_time_dt - session_start_time).total_seconds() / 60))
                status = "Late" if late_minutes > late_threshold else "Present"

                c.execute(
                    "UPDATE attendance SET status=?, late_minutes=?, image=?, timestamp=? WHERE student_id=? AND session_id=?",
                    (status, late_minutes, img_encoded.tobytes(), current_time, mssv, session_id))

                if status == "Present":
                    c.execute(
                        "UPDATE course_attendance_summary SET total_absences = total_absences - 1 WHERE student_id=? AND course_id=?",
                        (mssv, course_id))
                elif status == "Late":
                    c.execute(
                        "UPDATE course_attendance_summary SET total_absences = total_absences - 1, total_lates = total_lates + 1, total_late_minutes = total_late_minutes + ? WHERE student_id=? AND course_id=?",
                        (late_minutes, mssv, course_id))
                conn.commit()

                for item in student_tree.get_children():
                    if student_tree.item(item)["values"][0] == mssv:
                        student_tree.item(item, values=(mssv, name, status, late_minutes, ""))

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        img = Image.fromarray(frame_rgb)
        img = img.resize((640, 480), Image.Resampling.LANCZOS)
        imgtk = ImageTk.PhotoImage(image=img)
        video_label.imgtk = imgtk
        video_label.configure(image=imgtk)

        if current_time_dt >= session_end_time:
            end_session()
            return

        attendance_window.after(30, update_video)

    def edit_student_status():
        """Chỉnh sửa trạng thái điểm danh của sinh viên."""
        selected = student_tree.selection()
        if not selected:
            messagebox.showerror("Lỗi", "Vui lòng chọn một sinh viên!")
            return

        mssv = student_tree.item(selected)["values"][0]
        edit_window = tk.Toplevel()
        edit_window.title(f"Chỉnh sửa trạng thái - {mssv}")
        edit_window.geometry("300x200")

        tk.Label(edit_window, text="Trạng thái:", font=("Arial", 12)).pack(pady=5)
        status_var = tk.StringVar(value=student_tree.item(selected)["values"][2])
        ttk.Combobox(edit_window, textvariable=status_var, values=["Present", "Late", "Absent", "Nghỉ phép"]).pack(pady=5)

        tk.Label(edit_window, text="Phút muộn:", font=("Arial", 12)).pack(pady=5)
        late_var = tk.IntVar(value=student_tree.item(selected)["values"][3])
        tk.Entry(edit_window, textvariable=late_var, width=10).pack(pady=5)

        tk.Label(edit_window, text="Ghi chú:", font=("Arial", 12)).pack(pady=5)
        note_var = tk.StringVar(value=student_tree.item(selected)["values"][4])
        tk.Entry(edit_window, textvariable=note_var, width=20).pack(pady=5)

        def save_changes():
            new_status = status_var.get()
            new_late_minutes = late_var.get()
            new_note = note_var.get()

            c.execute(
                "UPDATE attendance SET status=?, late_minutes=?, timestamp=? WHERE student_id=? AND session_id=?",
                (new_status, new_late_minutes, time.strftime("%Y-%m-%d %H:%M:%S"), mssv, session_id))

            c.execute("SELECT status FROM attendance WHERE student_id=? AND session_id=?", (mssv, session_id))
            old_status = c.fetchone()[0]

            if old_status != new_status:
                if old_status == "Absent":
                    c.execute(
                        "UPDATE course_attendance_summary SET total_absences = total_absences - 1 WHERE student_id=? AND course_id=?",
                        (mssv, course_id))
                elif old_status == "Late":
                    c.execute(
                        "UPDATE course_attendance_summary SET total_lates = total_lates - 1, total_late_minutes = total_late_minutes - ? WHERE student_id=? AND course_id=?",
                        (student_tree.item(selected)["values"][3], mssv, course_id))

                if new_status == "Absent":
                    c.execute(
                        "UPDATE course_attendance_summary SET total_absences = total_absences + 1 WHERE student_id=? AND course_id=?",
                        (mssv, course_id))
                elif new_status == "Late":
                    c.execute(
                        "UPDATE course_attendance_summary SET total_lates = total_lates + 1, total_late_minutes = total_late_minutes + ? WHERE student_id=? AND course_id=?",
                        (new_late_minutes, mssv, course_id))

            conn.commit()
            student_tree.item(selected,
                              values=(mssv, all_students[mssv], new_status, new_late_minutes, new_note))
            edit_window.destroy()

        tk.Button(edit_window, text="Lưu", command=save_changes, bg="#4CAF50", fg="white",
                  font=("Arial", 11, "bold")).pack(pady=10)

    def end_session():
        """Kết thúc phiên điểm danh, lưu thông tin và hiển thị danh sách sinh viên vắng học."""
        if attendance_window.winfo_exists():
            end_time_actual = time.strftime("%Y-%m-%d %H:%M:%S")
            c.execute("UPDATE sessions SET end_time=? WHERE session_id=?", (end_time_actual, session_id))
            conn.commit()
            cap.release()

            # Hiển thị danh sách sinh viên vắng học
            show_absent_students(session_id, course_id)
            attendance_window.destroy()
            
    def show_absent_students(session_id, course_id):
        """Hiển thị danh sách sinh viên vắng học trong phiên điểm danh."""
        absent_window = tk.Toplevel()
        absent_window.title(f"Sinh viên vắng học - Phiên {session_id}")
        absent_window.geometry("600x400")

        absent_tree = ttk.Treeview(absent_window, columns=("MSSV", "Tên", "Lớp"), show="headings", height=15)
        absent_tree.heading("MSSV", text="MSSV")
        absent_tree.heading("Tên", text="Tên")
        absent_tree.heading("Lớp", text="Lớp")
        absent_tree.column("MSSV", width=100, anchor="center")
        absent_tree.column("Tên", width=200, anchor="w")
        absent_tree.column("Lớp", width=100, anchor="center")
        scrollbar = ttk.Scrollbar(absent_window, orient="vertical", command=absent_tree.yview)
        absent_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        absent_tree.pack(fill="both", expand=True, padx=10, pady=10)

        # Truy vấn danh sách sinh viên vắng học
        c.execute("""
            SELECT s.mssv, s.name, s.class 
            FROM students s 
            JOIN course_students cs ON s.mssv = cs.student_id 
            LEFT JOIN attendance a ON s.mssv = a.student_id AND a.session_id = ?
            WHERE cs.course_id = ? AND (a.status = 'Absent' OR a.status IS NULL)
        """, (session_id, course_id))
        for mssv, name, class_name in c.fetchall():
            absent_tree.insert("", "end", values=(mssv, name, class_name))



    # Tạo nút điều khiển
    control_frame = tk.Frame(attendance_window, bg="#f0f0f0")
    control_frame.pack(side="bottom", fill="x", pady=10)

    tk.Button(control_frame, text="Chỉnh sửa trạng thái", command=edit_student_status, bg="#2196F3", fg="white",
              font=("Arial", 11, "bold")).pack(side="left", padx=10)
    tk.Button(control_frame, text="Kết thúc phiên", command=end_session, bg="#F44336", fg="white",
              font=("Arial", 11, "bold")).pack(side="left", padx=10)

    update_video()
