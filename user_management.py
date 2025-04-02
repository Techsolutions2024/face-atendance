import hashlib
import sqlite3
from tkinter import messagebox
import tkinter as tk

rtsp_url = "rtsp://192.168.0.147:8554/stream1"
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def login(entry_username, entry_password, login_frame, main_frame, load_students, conn, c):
    username = entry_username.get()
    password = hash_password(entry_password.get())
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    if c.fetchone():
        login_frame.pack_forget()
        main_frame.pack(fill='both', expand=True, padx=15, pady=15)
        load_students()
    else:
        messagebox.showerror("Lỗi", "Sai thông tin đăng nhập!")

def register_user(conn, c):
    register_window = tk.Toplevel()
    register_window.title("Đăng ký")
    register_window.geometry("300x200")
    tk.Label(register_window, text="Tên đăng nhập:", font=("Arial", 12)).pack(pady=(10, 2))
    entry_register_username = tk.Entry(register_window, width=25, font=("Arial", 11), bd=2, relief="groove")
    entry_register_username.pack(pady=5)
    tk.Label(register_window, text="Mật khẩu:", font=("Arial", 12)).pack(pady=(5, 2))
    entry_register_password = tk.Entry(register_window, show="*", width=25, font=("Arial", 11), bd=2, relief="groove")
    entry_register_password.pack(pady=5)

    def save_new_user():
        username = entry_register_username.get()
        password = entry_register_password.get()
        if username and password:
            hashed_password = hash_password(password)
            try:
                c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
                conn.commit()
                messagebox.showinfo("Thành công", "Đăng ký thành công!")
                register_window.destroy()
            except sqlite3.IntegrityError:
                messagebox.showerror("Lỗi", "Tên đăng nhập đã tồn tại!")
        else:
            messagebox.showerror("Lỗi", "Vui lòng nhập đầy đủ thông tin!")

    tk.Button(register_window, text="Đăng ký", command=save_new_user, bg="#2196F3", fg="white",
              font=("Arial", 11, "bold"), width=10, bd=0, pady=5).pack(pady=15)