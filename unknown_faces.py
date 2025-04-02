import os
import cv2
import uuid
import sqlite3
from tkinter import messagebox, filedialog
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import time
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# Từ điển tạm thời để lưu embedding và số lượng ảnh của các nhóm Unknown
unknown_groups = {}  # {group_id: {'embeddings': [list of embeddings], 'count': int}}

def save_unknown_face(frame, face, timestamp, app, unknown_dir="unknown_faces", max_images_per_unknown=3, similarity_threshold=0.3):
    """
    Lưu ảnh Unknown với giới hạn tối đa 3 ảnh cho mỗi người lạ.
    
    Parameters:
    - frame: Frame ảnh từ video
    - face: Đối tượng khuôn mặt từ FaceAnalysis
    - timestamp: Thời gian để đánh dấu ảnh
    - app: Đối tượng FaceAnalysis để lấy embedding
    - unknown_dir: Thư mục lưu ảnh Unknown
    - max_images_per_unknown: Số lượng ảnh tối đa cho mỗi người lạ (mặc định là 3)
    - similarity_threshold: Ngưỡng tương đồng để xác định cùng một người (mặc định là 0.7)
    """
    box = face.bbox.astype(int)
    if (box[0] >= box[2] or box[1] >= box[3] or 
        box[0] < 0 or box[1] < 0 or 
        box[2] > frame.shape[1] or box[3] > frame.shape[0]):
        print(f"Bounding box không hợp lệ: {box}")
        return None
    face_img = frame[box[1]:box[3], box[0]:box[2]]
    if face_img.size == 0:
        print("Ảnh khuôn mặt rỗng")
        return None

    # Lấy embedding của khuôn mặt hiện tại
    current_embedding = face.embedding

    # Kiểm tra xem khuôn mặt này có thuộc nhóm Unknown nào đã lưu không
    matched_group = None
    for group_id, group_info in unknown_groups.items():
        embeddings = group_info['embeddings']
        similarities = cosine_similarity([current_embedding], embeddings)[0]
        if np.max(similarities) > similarity_threshold:
            matched_group = group_id
            break

    if matched_group:
        # Nếu tìm thấy nhóm khớp, kiểm tra số lượng ảnh
        if unknown_groups[matched_group]['count'] >= max_images_per_unknown:
            print(f"Đã đạt giới hạn {max_images_per_unknown} ảnh cho nhóm Unknown {matched_group}")
            return None
        # Thêm embedding mới vào nhóm
        unknown_groups[matched_group]['embeddings'].append(current_embedding)
        unknown_groups[matched_group]['count'] += 1
    else:
        # Tạo nhóm mới nếu không khớp với nhóm nào
        new_group_id = str(uuid.uuid4().hex)
        unknown_groups[new_group_id] = {
            'embeddings': [current_embedding],
            'count': 1
        }
        matched_group = new_group_id

    # Lưu ảnh vào thư mục unknown_faces
    filename = f"{unknown_dir}/unknown_{matched_group}_{timestamp}.jpg"
    cv2.imwrite(filename, face_img)
    print(f"Đã lưu ảnh Unknown tại: {filename}")
    return filename

def add_from_unknown(app, load_embeddings, conn, c, student_embeddings, unknown_dir="unknown_faces"):
    selected_file = [None]

    def load_unknown_faces():
        for widget in grid_frame.winfo_children():
            widget.destroy()
        unknown_files = [f for f in os.listdir(unknown_dir) if f.endswith('.jpg')]
        if not unknown_files:
            tk.Label(grid_frame, text="Không có ảnh nào trong thư mục Unknown", font=("Arial", 12), bg="#FFFFFF").grid(
                row=0, column=0, columnspan=5, pady=20)
        else:
            for i, file in enumerate(unknown_files):
                img_path = os.path.join(unknown_dir, file)
                try:
                    img = cv2.imread(img_path)
                    if img is not None:
                        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                        img_pil = Image.fromarray(img_rgb)
                        img_pil.thumbnail((150, 100))
                        img_tk = ImageTk.PhotoImage(img_pil)
                        creation_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(os.path.getmtime(img_path)))
                        thumbnail_frame = tk.Frame(grid_frame, bg="#FFFFFF", relief="flat", bd=1,
                                                   highlightbackground="#d3d3d3", highlightthickness=1)
                        thumbnail_label = tk.Label(thumbnail_frame, image=img_tk, bg="#FFFFFF")
                        thumbnail_label.image = img_tk
                        thumbnail_label.pack(pady=(5, 0))
                        time_label = tk.Label(thumbnail_frame, text=creation_time, font=("Arial", 10), bg="#FFFFFF",
                                              fg="#666666")
                        time_label.pack(pady=(0, 5))

                        def on_thumbnail_click(event, f=file):
                            selected_file[0] = f
                            for child in grid_frame.winfo_children():
                                child.config(highlightbackground="#d3d3d3", highlightthickness=1)
                            thumbnail_frame.config(highlightbackground="#007BFF", highlightthickness=2)
                            show_unknown_thumbnail(f)

                        thumbnail_label.bind("<Button-1>", on_thumbnail_click)
                        thumbnail_frame.grid(row=i // 5, column=i % 5, padx=5, pady=5, sticky="n")
                except Exception as e:
                    print(f"Lỗi khi tải ảnh {file}: {e}")

    def show_unknown_thumbnail(filename):
        img_path = os.path.join(unknown_dir, filename)
        if os.path.exists(img_path):
            img = cv2.imread(img_path)
            if img is not None:
                img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                img_pil = Image.fromarray(img_rgb)
                img_pil.thumbnail((150, 150))
                img_tk = ImageTk.PhotoImage(img_pil)
                unknown_thumbnail_label.config(image=img_tk)
                unknown_thumbnail_label.image = img_tk

    def delete_unknown_face():
        if not selected_file[0]:
            messagebox.showerror("Lỗi", "Vui lòng chọn một ảnh để xóa!")
            return
        filename = selected_file[0]
        if messagebox.askyesno("Xác nhận", f"Bạn có chắc muốn xóa ảnh {filename}?"):
            img_path = os.path.join(unknown_dir, filename)
            if os.path.exists(img_path):
                os.remove(img_path)
                messagebox.showinfo("Thành công", f"Đã xóa ảnh {filename}!")
                selected_file[0] = None
                load_unknown_faces()
                unknown_thumbnail_label.config(image='')

    def save_unknown_student():
        if not selected_file[0]:
            messagebox.showerror("Lỗi", "Vui lòng chọn một ảnh từ danh sách!")
            return
        filename = selected_file[0]
        id = entry_unknown_id.get().strip()
        name = entry_unknown_name.get().strip()
        class_name = entry_unknown_class.get().strip()
        major = entry_unknown_major.get().strip()

        if not (id and name and class_name and major):
            messagebox.showerror("Lỗi", "Vui lòng nhập đầy đủ thông tin!")
            return
        if len(id) > 50 or len(name) > 100 or len(class_name) > 50 or len(major) > 100:
            messagebox.showerror("Lỗi", "Thông tin nhập vào quá dài!")
            return

        c.execute("INSERT OR IGNORE INTO students (id, name, class, major) VALUES (?, ?, ?, ?)",
                  (id, name, class_name, major))
        c.execute("UPDATE students SET name=?, class=?, major=? WHERE id=?", (name, class_name, major, id))

        if use_new_image.get():
            new_image_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.png")])
            if not new_image_path:
                return
            img = cv2.imread(new_image_path)
        else:
            img = cv2.imread(os.path.join(unknown_dir, filename))

        if img is None:
            messagebox.showerror("Lỗi", "Không thể tải ảnh!")
            return

        faces = app.get(img)
        if not faces:
            messagebox.showerror("Lỗi", "Không tìm thấy khuôn mặt trong ảnh!")
            return

        embedding = faces[0].embedding
        _, img_encoded = cv2.imencode('.jpg', img)
        c.execute("INSERT INTO student_images (student_id, embedding, image) VALUES (?, ?, ?)",
                  (id, embedding.tobytes(), img_encoded.tobytes()))
        conn.commit()
        load_embeddings(student_embeddings, conn, c)

        img_path = os.path.join(unknown_dir, filename)
        if os.path.exists(img_path) and not use_new_image.get():
            os.remove(img_path)
        load_unknown_faces()
        messagebox.showinfo("Thành công", f"Đã thêm sinh viên {name} với ảnh mới!")

    unknown_window = tk.Toplevel()
    unknown_window.title("Thêm sinh viên từ Unknown")
    unknown_window.geometry("1200x600")

    unknown_frame = tk.Frame(unknown_window, bg="#FFFFFF", relief="groove", bd=2, pady=10)
    canvas = tk.Canvas(unknown_frame, bg="#FFFFFF")
    scrollbar = ttk.Scrollbar(unknown_frame, orient="vertical", command=canvas.yview)
    grid_frame = tk.Frame(canvas, bg="#FFFFFF")

    canvas.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)
    canvas.create_window((0, 0), window=grid_frame, anchor="nw")

    def on_frame_configure(event):
        canvas.configure(scrollregion=canvas.bbox("all"))

    grid_frame.bind("<Configure>", on_frame_configure)
    unknown_frame.pack(side="top", fill="both", expand=True, padx=10, pady=(10, 0))

    detail_frame = tk.Frame(unknown_window, bg="#ffffff", relief="groove", bd=2, padx=10, pady=10)
    unknown_thumbnail_label = tk.Label(detail_frame, bg="#ffffff")
    unknown_thumbnail_label.pack(side="left", padx=10)

    info_frame = tk.Frame(detail_frame, bg="#ffffff")
    tk.Label(info_frame, text="ID:", font=("Arial", 11), bg="#ffffff").pack(side="left", padx=5)
    entry_unknown_id = tk.Entry(info_frame, width=15, font=("Arial", 11))
    entry_unknown_id.pack(side="left")
    tk.Label(info_frame, text="Tên:", font=("Arial", 11), bg="#ffffff").pack(side="left", padx=5)
    entry_unknown_name = tk.Entry(info_frame, width=15, font=("Arial", 11))
    entry_unknown_name.pack(side="left")
    tk.Label(info_frame, text="Lớp:", font=("Arial", 11), bg="#ffffff").pack(side="left", padx=5)
    entry_unknown_class = tk.Entry(info_frame, width=15, font=("Arial", 11))
    entry_unknown_class.pack(side="left")
    tk.Label(info_frame, text="Ngành học:", font=("Arial", 11), bg="#ffffff").pack(side="left", padx=5)
    entry_unknown_major = tk.Entry(info_frame, width=15, font=("Arial", 11))
    entry_unknown_major.pack(side="left")

    use_new_image = tk.BooleanVar(value=False)
    tk.Checkbutton(info_frame, text="Tải ảnh mới", variable=use_new_image, font=("Arial", 11), bg="#ffffff").pack(
        side="left", padx=5)
    tk.Button(info_frame, text="Lưu", command=save_unknown_student, bg="#4CAF50", fg="white",
              font=("Arial", 11, "bold"), width=10, bd=0, pady=5).pack(side="left", padx=5)
    tk.Button(info_frame, text="Xóa ảnh", command=delete_unknown_face, bg="#F44336", fg="white",
              font=("Arial", 11, "bold"), width=10, bd=0, pady=5).pack(side="left", padx=5)
    info_frame.pack(side="left", fill="x", pady=5)
    detail_frame.pack(side="top", fill="x", pady=10)

    load_unknown_faces()