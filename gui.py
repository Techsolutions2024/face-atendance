import tkinter as tk
from tkinter import ttk, messagebox, Checkbutton, IntVar, filedialog
from PIL import Image, ImageTk
import cv2
import numpy as np
import pandas as pd
from face_recognition import save_unknown_face  # Giả định đây là module xử lý nhận diện khuôn mặt

rtsp_url = "rtsp://192.168.0.147:8554/stream1"
class GUI:
    def __init__(self, root, conn, c, student_embeddings, app, login, register_user, add_student, load_students,
                 edit_student, delete_student, start_attendance, save_unknown_face, add_from_unknown, load_embeddings):
        """Khởi tạo GUI với các tham số cần thiết."""
        self.root = root
        self.conn = conn  # Kết nối cơ sở dữ liệu
        self.c = c        # Con trỏ cơ sở dữ liệu
        self.student_embeddings = student_embeddings  # Embedding của sinh viên
        self.app = app    # Ứng dụng chính
        self.login = login
        self.register_user = register_user
        self.add_student = add_student
        self.load_students = load_students
        self.edit_student = edit_student
        self.delete_student = delete_student
        self.start_attendance = start_attendance
        self.save_unknown_face = save_unknown_face
        self.add_from_unknown = add_from_unknown
        self.load_embeddings = load_embeddings
        self.setup_gui()

    def setup_gui(self):
        """Thiết lập giao diện người dùng chính."""
        self.root.title("Hệ thống điểm danh sinh viên")
        self.root.geometry("1200x700")
        self.root.configure(bg="#F0F0F0")

        # **Màn hình đăng nhập**
        self.login_frame = tk.Frame(self.root, bg="#1E90FF", padx=30, pady=30, relief="raised", bd=3,
                                    highlightbackground="#b0b0b0", highlightthickness=1)

        # Logo
        logo_path = "logo.png"  # Đường dẫn đến logo (cần tồn tại trong thư mục)
        logo_img = Image.open(logo_path)
        logo_img = logo_img.resize((100, 100), Image.Resampling.LANCZOS)
        self.logo = ImageTk.PhotoImage(logo_img)
        tk.Label(self.login_frame, image=self.logo, bg="#1E90FF").pack(pady=(0, 20))

        tk.Label(self.login_frame, text="Đăng nhập hệ thống", font=("Arial", 18, "bold"), bg="#1E90FF").pack(pady=(0, 20))
        tk.Label(self.login_frame, text="Vui lòng nhập thông tin đăng nhập", font=("Arial", 12), bg="#1E90FF").pack(pady=(0, 10))

        tk.Label(self.login_frame, text="Tên đăng nhập:", bg="#1E90FF", font=("Arial", 12)).pack(pady=(5, 0))
        self.entry_username = tk.Entry(self.login_frame, width=35, font=("Arial", 12), bd=2, relief="groove")
        self.entry_username.pack(pady=10)

        tk.Label(self.login_frame, text="Mật khẩu:", bg="#1E90FF", font=("Arial", 12)).pack(pady=(5, 0))
        self.entry_password = tk.Entry(self.login_frame, show="*", width=35, font=("Arial", 12), bd=2, relief="groove")
        self.entry_password.pack(pady=10)

        self.show_password_var = IntVar()
        self.show_password_check = Checkbutton(self.login_frame, text="Hiển thị mật khẩu",
                                               variable=self.show_password_var,
                                               command=self.toggle_password, bg="#1E90FF", font=("Arial", 10))
        self.show_password_check.pack(pady=(0, 10))

        btn_frame = tk.Frame(self.login_frame, bg="#1E90FF")
        tk.Button(btn_frame, text="Đăng nhập", command=self.on_login, bg="#4CAF50", fg="white",
                  font=("Arial", 12, "bold"), width=12, bd=0, pady=5).pack(side="left", padx=10)
        tk.Button(btn_frame, text="Đăng ký", command=lambda: self.register_user(self.conn, self.c), bg="#FF9800",
                  fg="white", font=("Arial", 12, "bold"), width=12, bd=0, pady=5).pack(side="left", padx=10)
        btn_frame.pack(pady=20)
        self.login_frame.pack(expand=True)

        # **Giao diện chính**
        self.main_frame = tk.Frame(self.root, bg="#f0f0f0")
        header_frame = tk.Frame(self.main_frame, bg="#4CAF50", pady=10)
        tk.Label(header_frame, text="Học Viện Hàng Không Việt Nam - Hệ thống điểm danh", font=("Arial", 20, "bold"),
                 bg="#4CAF50", fg="white").pack()
        header_frame.pack(side="top", fill="x", padx=10, pady=10)

        # **Khung nhập thông tin sinh viên**
        self.input_frame = tk.Frame(self.main_frame, bg="#ffffff", padx=5, pady=5, relief="groove", bd=2)
        tk.Label(self.input_frame, text="Nhập thông tin sinh viên", font=("Arial", 16, "bold"), bg="#ffffff").pack(pady=(0, 5))
        tk.Label(self.input_frame, text="MSSV:", bg="#ffffff", font=("Arial", 11)).pack(pady=(5, 2))
        self.entry_mssv = tk.Entry(self.input_frame, width=15, font=("Arial", 11), bd=2, relief="groove")
        self.entry_mssv.pack(pady=(0, 5))
        tk.Label(self.input_frame, text="Tên:", bg="#ffffff", font=("Arial", 11)).pack(pady=(5, 2))
        self.entry_name = tk.Entry(self.input_frame, width=15, font=("Arial", 11), bd=2, relief="groove")
        self.entry_name.pack(pady=(0, 5))
        tk.Label(self.input_frame, text="Giới tính:", bg="#ffffff", font=("Arial", 11)).pack(pady=(5, 2))
        self.entry_gender = tk.Entry(self.input_frame, width=15, font=("Arial", 11), bd=2, relief="groove")
        self.entry_gender.pack(pady=(0, 5))
        tk.Label(self.input_frame, text="Ngày sinh (DD-MM-YYYY):", bg="#ffffff", font=("Arial", 11)).pack(pady=(5, 2))
        self.entry_dob = tk.Entry(self.input_frame, width=15, font=("Arial", 11), bd=2, relief="groove")
        self.entry_dob.pack(pady=(0, 5))
        tk.Label(self.input_frame, text="Chuyên ngành:", bg="#ffffff", font=("Arial", 11)).pack(pady=(5, 2))
        self.entry_major = tk.Entry(self.input_frame, width=15, font=("Arial", 11), bd=2, relief="groove")
        self.entry_major.pack(pady=(0, 5))
        tk.Label(self.input_frame, text="Lớp:", bg="#ffffff", font=("Arial", 11)).pack(pady=(5, 2))
        self.entry_class = tk.Entry(self.input_frame, width=15, font=("Arial", 11), bd=2, relief="groove")
        self.entry_class.pack(pady=(0, 5))
        tk.Button(self.input_frame, text="Thêm sinh viên", command=self.on_add_student, bg="#4CAF50", fg="white",
                  font=("Arial", 11, "bold"), width=15, bd=0, pady=5).pack(pady=15)
        tk.Button(self.input_frame, text="Nhập từ CSV", command=self.import_from_csv, bg="#FF5722", fg="white",
                  font=("Arial", 11, "bold"), width=15, bd=0, pady=5).pack(pady=10)
        self.input_frame.pack(side="left", fill="y", padx=(0, 20), pady=5)

        # **Khung tìm kiếm**
        self.search_frame = tk.Frame(self.main_frame, bg="#ffffff", padx=20, pady=15, relief="groove", bd=2)
        tk.Label(self.search_frame, text="Tìm kiếm sinh viên", font=("Arial", 16, "bold"), bg="#ffffff").pack(pady=(0, 10))
        search_inner = tk.Frame(self.search_frame, bg="#ffffff")
        tk.Label(search_inner, text="Tìm kiếm:", bg="#ffffff", font=("Arial", 11)).pack(side="left", pady=5)
        self.entry_search = tk.Entry(search_inner, width=40, font=("Arial", 11), bd=2, relief="groove")
        self.entry_search.pack(side="left", padx=10)
        tk.Button(search_inner, text="Tìm", command=self.search_students, bg="#2196F3", fg="white",
                  font=("Arial", 11, "bold"), width=10, bd=0, pady=5).pack(side="left")
        search_inner.pack()
        self.search_frame.pack(side="top", fill="x", pady=(0, 15))

        # **Khung danh sách sinh viên**
        self.tree_frame = tk.Frame(self.main_frame, bg="#ffffff", relief="groove", bd=2, pady=5)
        self.student_tree = ttk.Treeview(self.tree_frame, columns=("MSSV", "Tên", "Giới tính", "Ngày sinh", "Chuyên ngành", "Lớp"),
                                         show="headings", height=15)
        self.student_tree.heading("MSSV", text="MSSV")
        self.student_tree.heading("Tên", text="Tên")
        self.student_tree.heading("Giới tính", text="Giới tính")
        self.student_tree.heading("Ngày sinh", text="Ngày sinh")
        self.student_tree.heading("Chuyên ngành", text="Chuyên ngành")
        self.student_tree.heading("Lớp", text="Lớp")
        self.student_tree.column("MSSV", width=80, anchor="center")
        self.student_tree.column("Tên", width=120, anchor="w")
        self.student_tree.column("Giới tính", width=60, anchor="center")
        self.student_tree.column("Ngày sinh", width=100, anchor="center")
        self.student_tree.column("Chuyên ngành", width=120, anchor="center")
        self.student_tree.column("Lớp", width=80, anchor="center")
        scrollbar = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.student_tree.yview)
        self.student_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.student_tree.pack(side="left", fill="both", expand=True, padx=5)
        self.tree_frame.pack(side="left", fill="both", expand=True, pady=(0, 5))

        # **Khung ảnh sinh viên**
        self.student_thumbnail_frame = tk.Frame(self.main_frame, bg="#ffffff", relief="groove", bd=2, padx=10, pady=10)
        self.student_thumbnail_label = tk.Label(self.student_thumbnail_frame, bg="#ffffff")
        self.student_thumbnail_label.pack()
        self.close_thumbnail_btn = tk.Button(self.student_thumbnail_frame, text="X", command=self.close_thumbnail,
                                             bg="#F44336", fg="white", font=("Arial", 10, "bold"), width=2, height=1,
                                             bd=0)
        self.student_thumbnail_label.bind("<Button-1>", self.on_thumbnail_click)
        self.student_thumbnail_frame.pack(side="left", fill="y", padx=(15, 0), pady=10)
        self.student_tree.bind("<<TreeviewSelect>>", self.show_student_thumbnail)

        # **Khung nút điều khiển**
        self.button_frame = tk.Frame(self.main_frame, bg="#ffffff", padx=20, pady=20, relief="groove", bd=2)
        buttons = [
            ("Tạo môn học", self.create_course, "#2196F3"),
            ("Xem môn học", self.view_courses, "#2196F3"),
            ("Điểm danh", self.on_start_attendance, "#FF9800"),
            ("Chỉnh sửa", self.on_edit_student, "#FFC107"),
            ("Xóa", self.on_delete_student, "#F44336"),
            ("Xem ảnh", self.view_student_image, "#9C27B0"),
            ("Lịch sử", self.view_attendance_history, "#3F51B5"),
            ("Tổng hợp", self.view_attendance_summary, "#3F51B5"),
            ("Thêm từ Unknown", self.on_add_from_unknown, "#9C27B0"),
            ("Nhập từ CSV", self.import_from_csv, "#FF5722"),
            ("Back", self.on_back, "#607D8B")
        ]
        for text, cmd, color in buttons:
            tk.Button(self.button_frame, text=text, command=cmd, bg=color, fg="white",
                      font=("Arial", 11, "bold"), width=15, bd=0, pady=8).pack(side="top", pady=10)
        self.button_frame.pack(side="right", fill="y", padx=(15, 0), pady=10)

    # **Các hàm hỗ trợ giao diện**

    def show_student_thumbnail(self, event):
        """Hiển thị ảnh thumbnail của sinh viên khi chọn trong danh sách."""
        selected = self.student_tree.selection()
        if selected:
            mssv = str(self.student_tree.item(selected)['values'][0])
            self.c.execute("SELECT image FROM student_images WHERE student_id=? LIMIT 1", (mssv,))
            result = self.c.fetchone()
            if result and result[0]:
                img_data = np.frombuffer(result[0], dtype=np.uint8)
                img = cv2.imdecode(img_data, cv2.IMREAD_COLOR)
                img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                img_pil = Image.fromarray(img_rgb)
                img_pil.thumbnail((150, 150))
                img_tk = ImageTk.PhotoImage(img_pil)
                self.student_thumbnail_label.config(image=img_tk)
                self.student_thumbnail_label.image = img_tk
                self.close_thumbnail_btn.pack(pady=5)

    def on_thumbnail_click(self, event):
        """Hiển thị ảnh đầy đủ khi nhấp vào thumbnail."""
        selected = self.student_tree.selection()
        if selected:
            mssv = str(self.student_tree.item(selected)['values'][0])
            self.c.execute("SELECT image FROM student_images WHERE student_id=? LIMIT 1", (mssv,))
            result = self.c.fetchone()
            if result and result[0]:
                img_data = np.frombuffer(result[0], dtype=np.uint8)
                img = cv2.imdecode(img_data, cv2.IMREAD_COLOR)
                cv2.imshow(f"Ảnh của sinh viên {mssv}", img)
                cv2.waitKey(0)
                cv2.destroyAllWindows()

    def close_thumbnail(self):
        """Đóng thumbnail."""
        self.student_thumbnail_label.config(image='')
        self.close_thumbnail_btn.pack_forget()

    def view_student_image(self):
        """Xem tất cả ảnh của sinh viên được chọn."""
        selected = self.student_tree.selection()
        if selected:
            mssv = str(self.student_tree.item(selected)['values'][0])
            self.c.execute("SELECT image FROM student_images WHERE student_id=?", (mssv,))
            images = self.c.fetchall()
            if images:
                for i, (img_data,) in enumerate(images):
                    img = cv2.imdecode(np.frombuffer(img_data, dtype=np.uint8), cv2.IMREAD_COLOR)
                    cv2.imshow(f"Ảnh {i + 1} của sinh viên {mssv}", img)
                cv2.waitKey(0)
                cv2.destroyAllWindows()
            else:
                messagebox.showerror("Lỗi", "Không tìm thấy ảnh!")

    def search_students(self):
        """Tìm kiếm sinh viên theo MSSV, tên hoặc lớp."""
        query = self.entry_search.get().lower()
        for row in self.student_tree.get_children():
            self.student_tree.delete(row)
        self.c.execute(
            "SELECT mssv, name, gender, dob, major, class FROM students WHERE LOWER(mssv) LIKE ? OR LOWER(name) LIKE ? OR LOWER(class) LIKE ?",
            ('%' + query + '%', '%' + query + '%', '%' + query + '%'))
        for row in self.c.fetchall():
            self.student_tree.insert("", "end", values=row)

    def export_attendance_history(self):
        """Xuất lịch sử điểm danh ra file CSV."""
        self.c.execute("SELECT student_id, date, timestamp, status, session_id FROM attendance ORDER BY timestamp DESC")
        data = self.c.fetchall()
        df = pd.DataFrame(data, columns=["MSSV", "Ngày", "Thời gian", "Trạng thái", "Phiên"])
        df.to_csv("attendance_history.csv", index=False)
        messagebox.showinfo("Thành công", "Đã xuất báo cáo ra attendance_history.csv")

    def view_attendance_history(self):
        """Hiển thị lịch sử điểm danh."""
        history_window = tk.Toplevel()
        history_window.title("Lịch sử điểm danh")
        history_window.geometry("800x600")
        history_frame = tk.Frame(history_window, bg="#ffffff", relief="groove", bd=2, pady=10)
        history_tree = ttk.Treeview(history_frame, columns=("MSSV", "Ngày", "Thời gian", "Trạng thái", "Phiên"),
                                    show="headings", height=15)
        history_tree.heading("MSSV", text="MSSV")
        history_tree.heading("Ngày", text="Ngày")
        history_tree.heading("Thời gian", text="Thời gian")
        history_tree.heading("Trạng thái", text="Trạng thái")
        history_tree.heading("Phiên", text="Phiên")
        history_tree.column("MSSV", width=100, anchor="center")
        history_tree.column("Ngày", width=150, anchor="center")
        history_tree.column("Thời gian", width=150, anchor="center")
        history_tree.column("Trạng thái", width=100, anchor="center")
        history_tree.column("Phiên", width=100, anchor="center")
        scrollbar = ttk.Scrollbar(history_frame, orient="vertical", command=history_tree.yview)
        history_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        history_tree.pack(side="left", fill="both", expand=True, padx=10)
        history_frame.pack(side="top", fill="both", expand=True, padx=10, pady=(10, 0))

        self.c.execute("SELECT student_id, date, timestamp, status, session_id FROM attendance ORDER BY timestamp DESC")
        for row in self.c.fetchall():
            history_tree.insert("", "end", values=row)

        attendance_thumbnail_frame = tk.Frame(history_window, bg="#ffffff", relief="groove", bd=2, padx=10, pady=10)
        attendance_thumbnail_label = tk.Label(attendance_thumbnail_frame, bg="#ffffff")
        attendance_thumbnail_label.pack()
        attendance_thumbnail_frame.pack(side="top", fill="x", pady=10)

        def show_attendance_thumbnail(event):
            selected = history_tree.selection()
            if selected:
                mssv = history_tree.item(selected)['values'][0]
                timestamp = history_tree.item(selected)['values'][2]
                session_id = history_tree.item(selected)['values'][4]
                self.c.execute("SELECT image FROM attendance WHERE student_id=? AND timestamp=? AND session_id=?",
                               (mssv, timestamp, session_id))
                result = self.c.fetchone()
                if result and result[0]:
                    img_data = np.frombuffer(result[0], dtype=np.uint8)
                    img = cv2.imdecode(img_data, cv2.IMREAD_COLOR)
                    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                    img_pil = Image.fromarray(img_rgb)
                    img_pil.thumbnail((150, 150))
                    img_tk = ImageTk.PhotoImage(img_pil)
                    attendance_thumbnail_label.config(image=img_tk)
                    attendance_thumbnail_label.image = img_tk

        def view_attendance_image():
            selected = history_tree.selection()
            if selected:
                mssv = history_tree.item(selected)['values'][0]
                timestamp = history_tree.item(selected)['values'][2]
                session_id = history_tree.item(selected)['values'][4]
                self.c.execute("SELECT image FROM attendance WHERE student_id=? AND timestamp=? AND session_id=?",
                               (mssv, timestamp, session_id))
                result = self.c.fetchone()
                if result and result[0]:
                    img_data = np.frombuffer(result[0], dtype=np.uint8)
                    img = cv2.imdecode(img_data, cv2.IMREAD_COLOR)
                    cv2.imshow(f"Ảnh điểm danh của {mssv} lúc {timestamp}", img)
                    cv2.waitKey(0)
                    cv2.destroyAllWindows()

        history_tree.bind("<<TreeviewSelect>>", show_attendance_thumbnail)
        tk.Button(history_window, text="Xem ảnh điểm danh", command=view_attendance_image, bg="#2196F3", fg="white",
                  font=("Arial", 11, "bold"), width=15, bd=0, pady=5).pack(side="left", padx=5, pady=10)
        tk.Button(history_window, text="Xuất CSV", command=self.export_attendance_history, bg="#4CAF50", fg="white",
                  font=("Arial", 11, "bold"), width=15, bd=0, pady=5).pack(side="left", padx=5, pady=10)

    def on_login(self):
        """Xử lý đăng nhập."""
        self.login(self.entry_username, self.entry_password, self.login_frame, self.main_frame,
                   self.refresh_students, self.conn, self.c)

    def on_add_student(self):
        """Thêm sinh viên mới."""
        self.add_student(self.entry_mssv, self.entry_name, self.entry_gender, self.entry_dob, self.entry_major,
                         self.entry_class, self.app, self.refresh_students, self.conn, self.c, self.student_embeddings)

    def on_start_attendance(self):
        """Bắt đầu quá trình điểm danh."""
        attendance_window = tk.Toplevel()
        attendance_window.title("Chọn môn học để điểm danh")
        attendance_window.geometry("400x400")

        tk.Label(attendance_window, text="Chọn môn học:", font=("Arial", 12)).pack(pady=5)
        course_combobox = ttk.Combobox(attendance_window, font=("Arial", 11))
        self.c.execute("SELECT course_id, course_name FROM courses")
        courses = self.c.fetchall()
        course_combobox['values'] = [f"{course[0]} - {course[1]}" for course in courses]
        course_combobox.pack(pady=5)

        tk.Label(attendance_window, text="Ngưỡng trễ (phút):", font=("Arial", 12)).pack(pady=5)
        late_threshold_var = tk.IntVar(value=15)
        tk.Entry(attendance_window, textvariable=late_threshold_var, font=("Arial", 11)).pack(pady=5)

        def start_session():
            selected_course = course_combobox.get()
            if not selected_course:
                messagebox.showerror("Lỗi", "Vui lòng chọn môn học!")
                return
            course_id = int(selected_course.split(" - ")[0])
            late_threshold = late_threshold_var.get()

            # Lấy start_time và end_time từ cơ sở dữ liệu
            self.c.execute("SELECT start_time, end_time FROM courses WHERE course_id=?", (course_id,))
            result = self.c.fetchone()
            if not result:
                messagebox.showerror("Lỗi", "Không tìm thấy thông tin môn học!")
                return
            start_time, end_time = result

            self.start_attendance(0, self.entry_class, self.student_embeddings, self.app, self.save_unknown_face,
                                 self.conn, self.c, course_id, start_time, end_time, late_threshold)
            attendance_window.destroy()

        tk.Button(attendance_window, text="Bắt đầu điểm danh", command=start_session, bg="#4CAF50", fg="white",
                  font=("Arial", 11, "bold")).pack(pady=20)

    def on_edit_student(self):
        """Chỉnh sửa thông tin sinh viên."""
        self.edit_student(self.student_tree, self.app, self.load_embeddings, self.refresh_students,
                          self.conn, self.c, self.student_embeddings)

    def on_delete_student(self):
        """Xóa sinh viên."""
        self.delete_student(self.student_tree, self.load_embeddings, self.refresh_students,
                            self.conn, self.c, self.student_embeddings)

    def on_add_from_unknown(self):
        """Thêm sinh viên từ danh sách unknown."""
        self.add_from_unknown(self.app, self.load_embeddings, self.conn, self.c, self.student_embeddings)

    def on_back(self):
        """Quay lại màn hình đăng nhập."""
        self.main_frame.pack_forget()
        self.login_frame.pack()

    def refresh_students(self):
        """Làm mới danh sách sinh viên."""
        self.load_students(self.student_tree, self.conn, self.c)

    def refresh_embeddings(self):
        """Làm mới embedding của sinh viên."""
        self.load_embeddings(self.student_embeddings, self.conn, self.c)

    def toggle_password(self):
        """Hiển thị/ẩn mật khẩu."""
        if self.show_password_var.get():
            self.entry_password.config(show="")
        else:
            self.entry_password.config(show="*")

    def view_attendance_summary(self):
        """Hiển thị tổng hợp điểm danh theo môn học."""
        summary_window = tk.Toplevel()
        summary_window.title("Tổng hợp điểm danh theo môn học")
        summary_window.geometry("800x600")
        summary_tree = ttk.Treeview(summary_window, columns=("MSSV", "Môn học", "Tổng buổi", "Vắng", "Muộn", "Phút muộn"),
                                    show="headings")
        summary_tree.heading("MSSV", text="MSSV")
        summary_tree.heading("Môn học", text="Môn học")
        summary_tree.heading("Tổng buổi", text="Tổng buổi")
        summary_tree.heading("Vắng", text="Vắng")
        summary_tree.heading("Muộn", text="Muộn")
        summary_tree.heading("Phút muộn", text="Phút muộn")
        summary_tree.column("MSSV", width=100, anchor="center")
        summary_tree.column("Môn học", width=150, anchor="center")
        summary_tree.column("Tổng buổi", width=100, anchor="center")
        summary_tree.column("Vắng", width=80, anchor="center")
        summary_tree.column("Muộn", width=80, anchor="center")
        summary_tree.column("Phút muộn", width=100, anchor="center")
        summary_tree.pack(fill="both", expand=True)
        self.c.execute(
            "SELECT s.student_id, c.course_name, s.total_classes, s.total_absences, s.total_lates, s.total_late_minutes FROM course_attendance_summary s JOIN courses c ON s.course_id = c.course_id")
        for row in self.c.fetchall():
            summary_tree.insert("", "end", values=row)

    def import_from_csv(self):
        """Nhập dữ liệu từ file CSV (sinh viên hoặc môn học)."""
        file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if file_path:
            try:
                df = pd.read_csv(file_path)
                if "mssv" in df.columns:  # Nhập sinh viên
                    required_columns = ["mssv", "name", "gender", "dob", "major", "class"]
                    if not all(col in df.columns for col in required_columns):
                        messagebox.showerror("Lỗi", "File CSV phải chứa các cột: mssv, name, gender, dob, major, class!")
                        return
                    for _, row in df.iterrows():
                        self.c.execute("INSERT OR IGNORE INTO students (mssv, name, gender, dob, major, class) VALUES (?, ?, ?, ?, ?, ?)",
                                       (str(row["mssv"]), row["name"], row["gender"], row["dob"], row["major"], row["class"]))
                    self.conn.commit()
                    self.refresh_students()
                    messagebox.showinfo("Thành công", f"Đã nhập {len(df)} sinh viên từ file CSV!")
                elif "course_name" in df.columns:  # Nhập môn học
                    required_columns = ["course_name", "course_code", "start_time", "end_time"]
                    if not all(col in df.columns for col in required_columns):
                        messagebox.showerror("Lỗi", "File CSV phải chứa các cột: course_name, course_code, start_time, end_time!")
                        return
                    for _, row in df.iterrows():
                        self.c.execute("INSERT OR IGNORE INTO courses (course_name, course_code, start_time, end_time) VALUES (?, ?, ?, ?)",
                                       (row["course_name"], row["course_code"], row["start_time"], row["end_time"]))
                    self.conn.commit()
                    messagebox.showinfo("Thành công", f"Đã nhập {len(df)} môn học từ file CSV!")
                else:
                    messagebox.showerror("Lỗi", "File CSV không hợp lệ!")
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể nhập file CSV: {str(e)}")

    def create_course(self):
        """Tạo môn học mới với thời gian bắt đầu và kết thúc."""
        course_window = tk.Toplevel()
        course_window.title("Tạo môn học mới")
        course_window.geometry("400x300")

        tk.Label(course_window, text="Tên môn học:", font=("Arial", 12)).pack(pady=5)
        entry_course_name = tk.Entry(course_window, font=("Arial", 11))
        entry_course_name.pack(pady=5)

        tk.Label(course_window, text="Mã môn học:", font=("Arial", 12)).pack(pady=5)
        entry_course_code = tk.Entry(course_window, font=("Arial", 11))
        entry_course_code.pack(pady=5)

        tk.Label(course_window, text="Thời gian bắt đầu (HH:MM:SS):", font=("Arial", 12)).pack(pady=5)
        entry_start_time = tk.Entry(course_window, font=("Arial", 11))
        entry_start_time.pack(pady=5)

        tk.Label(course_window, text="Thời gian kết thúc (HH:MM:SS):", font=("Arial", 12)).pack(pady=5)
        entry_end_time = tk.Entry(course_window, font=("Arial", 11))
        entry_end_time.pack(pady=5)

        def save_course():
            course_name = entry_course_name.get().strip()
            course_code = entry_course_code.get().strip()
            start_time = entry_start_time.get().strip()
            end_time = entry_end_time.get().strip()
            if not (course_name and course_code and start_time and end_time):
                messagebox.showerror("Lỗi", "Vui lòng nhập đầy đủ thông tin môn học!")
                return
            self.c.execute("INSERT INTO courses (course_name, course_code, start_time, end_time) VALUES (?, ?, ?, ?)", 
                           (course_name, course_code, start_time, end_time))
            self.conn.commit()
            messagebox.showinfo("Thành công", "Đã tạo môn học mới!")
            course_window.destroy()

        tk.Button(course_window, text="Lưu", command=save_course, bg="#4CAF50", fg="white",
                  font=("Arial", 11, "bold")).pack(pady=20)

    def view_courses(self):
        """Hiển thị danh sách môn học."""
        courses_window = tk.Toplevel()
        courses_window.title("Danh sách môn học")
        courses_window.geometry("800x600")

        courses_tree = ttk.Treeview(courses_window, columns=("ID", "Tên môn học", "Mã môn học", "Thời gian bắt đầu", "Thời gian kết thúc"), 
                                    show="headings", height=15)
        courses_tree.heading("ID", text="ID")
        courses_tree.heading("Tên môn học", text="Tên môn học")
        courses_tree.heading("Mã môn học", text="Mã môn học")
        courses_tree.heading("Thời gian bắt đầu", text="Thời gian bắt đầu")
        courses_tree.heading("Thời gian kết thúc", text="Thời gian kết thúc")
        courses_tree.column("ID", width=50, anchor="center")
        courses_tree.column("Tên môn học", width=200, anchor="w")
        courses_tree.column("Mã môn học", width=100, anchor="center")
        courses_tree.column("Thời gian bắt đầu", width=150, anchor="center")
        courses_tree.column("Thời gian kết thúc", width=150, anchor="center")
        scrollbar = ttk.Scrollbar(courses_window, orient="vertical", command=courses_tree.yview)
        courses_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        courses_tree.pack(side="top", fill="both", expand=True, padx=10, pady=10)

        self.c.execute("SELECT course_id, course_name, course_code, start_time, end_time FROM courses")
        for row in self.c.fetchall():
            courses_tree.insert("", "end", values=row)

        def add_students_to_course():
            selected = courses_tree.selection()
            if not selected:
                messagebox.showerror("Lỗi", "Vui lòng chọn một môn học!")
                return
            course_id = courses_tree.item(selected)["values"][0]

            add_students_window = tk.Toplevel()
            add_students_window.title(f"Thêm sinh viên vào môn học {course_id}")
            add_students_window.geometry("600x400")

            tk.Label(add_students_window, text="Chọn sinh viên để thêm:", font=("Arial", 12)).pack(pady=5)
            student_frame = tk.Frame(add_students_window)
            student_tree = ttk.Treeview(student_frame, columns=("MSSV", "Tên"), show="headings", height=10)
            student_tree.heading("MSSV", text="MSSV")
            student_tree.heading("Tên", text="Tên")
            student_tree.column("MSSV", width=100)
            student_tree.column("Tên", width=200)
            scrollbar = ttk.Scrollbar(student_frame, orient="vertical", command=student_tree.yview)
            student_tree.configure(yscrollcommand=scrollbar.set)
            scrollbar.pack(side="right", fill="y")
            student_tree.pack(side="left", fill="both", expand=True)
            student_frame.pack(fill="both", expand=True, padx=10, pady=5)

            self.c.execute("SELECT mssv, name FROM students WHERE mssv NOT IN (SELECT student_id FROM course_students WHERE course_id=?)", (course_id,))
            for mssv, name in self.c.fetchall():
                student_tree.insert("", "end", values=(mssv, name), tags=("unchecked",))
            student_tree.tag_configure("unchecked", background="white")

            def toggle_selection(event):
                item = student_tree.identify_row(event.y)
                if item:
                    tags = student_tree.item(item, "tags")
                    if "unchecked" in tags:
                        student_tree.item(item, tags=("checked",))
                        student_tree.tag_configure("checked", background="#90EE90")
                    else:
                        student_tree.item(item, tags=("unchecked",))
                        student_tree.tag_configure("unchecked", background="white")

            student_tree.bind("<Button-1>", toggle_selection)

            def save_students():
                selected_students = [student_tree.item(item)["values"][0] 
                                     for item in student_tree.get_children() 
                                     if "checked" in student_tree.item(item, "tags")]
                for mssv in selected_students:
                    self.c.execute("INSERT INTO course_students (course_id, student_id) VALUES (?, ?)", 
                                   (course_id, mssv))
                self.conn.commit()
                messagebox.showinfo("Thành công", "Đã thêm sinh viên vào môn học!")
                add_students_window.destroy()

            tk.Button(add_students_window, text="Lưu", command=save_students, bg="#4CAF50", fg="white",
                      font=("Arial", 11, "bold")).pack(pady=10)

        tk.Button(courses_window, text="Thêm sinh viên vào môn học", command=add_students_to_course, bg="#2196F3", fg="white",
                  font=("Arial", 11, "bold")).pack(pady=10)
