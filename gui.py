import customtkinter as ctk
from tkinter import filedialog, messagebox
import socket
import threading
import time
from main import FileShareApp

# Thiết lập giao diện
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class AppUI(ctk.CTk):
    def __init__(self, file_share_app):
        super().__init__()
        
        # Liên kết backend
        self.file_share = file_share_app
        
        self.title("File Transfer")
        self.geometry("700x450")
        
        # Cấu hình Layout Grid
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # --- SIDEBAR (Bên trái) ---
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        self.logo_label = ctk.CTkLabel(
            self.sidebar, 
            text="FILE TRANSFER", 
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.logo_label.pack(pady=20, padx=20)
        
        self.info_label = ctk.CTkLabel(
            self.sidebar, 
            text=f"My Name: {self.file_share.my_name}\nIP: {self.get_local_ip()}", 
            anchor="w"
        )
        self.info_label.pack(pady=10, padx=20)
        
        self.refresh_btn = ctk.CTkButton(
            self.sidebar, 
            text="Làm mới danh sách", 
            command=self.refresh_devices
        )
        self.refresh_btn.pack(pady=10, padx=20)
        
        # Nút test localhost
        self.test_btn = ctk.CTkButton(
            self.sidebar, 
            text="🧪 Test Localhost", 
            command=self.test_localhost,
            fg_color="green"
        )
        self.test_btn.pack(pady=10, padx=20)
        #Description :
        self.test_btn.pack(pady=10, padx=20)

        self.author_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.author_frame.pack(side="bottom", pady=20, padx=20)
        
        self.author_label = ctk.CTkLabel(
            self.author_frame,
            text="👨‍💻 Author: Nguyen Dang Khoi\n📧 Email: ndangkhoi2811@example.com",
            font=ctk.CTkFont(size=10),
            text_color="gray",
            anchor="w"
        )
        self.author_label.pack()
        
        # --- MAIN AREA (Danh sách thiết bị) ---
        self.main_frame = ctk.CTkFrame(self, corner_radius=10)
        self.main_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        
        self.label_title = ctk.CTkLabel(
            self.main_frame, 
            text="Thiết bị đang trực tuyến", 
            font=ctk.CTkFont(size=16)
        )
        self.label_title.pack(pady=10)
        
        # Khung chứa danh sách thiết bị (Scrollable)
        self.device_list_frame = ctk.CTkScrollableFrame(
            self.main_frame, 
            label_text="Chọn thiết bị để gửi"
        )
        self.device_list_frame.pack(padx=20, pady=10, fill="both", expand=True)
        
        # --- BOTTOM AREA (Gửi file & Progress) ---
        self.progress_bar = ctk.CTkProgressBar(self.main_frame)
        self.progress_bar.pack(padx=20, pady=10, fill="x")
        self.progress_bar.set(0)
        
        self.status_label = ctk.CTkLabel(self.main_frame, text="Sẵn sàng")
        self.status_label.pack(pady=5)
        
        # Tự động refresh mỗi 3 giây
        self.auto_refresh()
    
    def get_local_ip(self):
        """Lấy IP của máy này"""
        try:
            return socket.gethostbyname(socket.gethostname())
        except:
            return "N/A"
    
    def refresh_devices(self):
        """Cập nhật danh sách thiết bị từ backend"""
        # Xóa các widget cũ
        for widget in self.device_list_frame.winfo_children():
            widget.destroy()
        
        # Lấy dữ liệu thật từ backend
        devices = self.file_share.online_devices.copy()
        
        if not devices:
            no_device_label = ctk.CTkLabel(
                self.device_list_frame, 
                text="Chưa tìm thấy thiết bị nào...", 
                text_color="gray"
            )
            no_device_label.pack(pady=20)
        else:
            for ip, name in devices.items():
                btn = ctk.CTkButton(
                    self.device_list_frame,
                    text=f"{name} ({ip})",
                    command=lambda i=ip: self.select_file_and_send(i)
                )
                btn.pack(pady=5, fill="x")
        
        # Cập nhật số lượng thiết bị
        self.label_title.configure(
            text=f"Thiết bị đang trực tuyến ({len(devices)})"
        )
    
    def auto_refresh(self):
        """Tự động refresh danh sách mỗi 3 giây"""
        self.refresh_devices()
        self.after(3000, self.auto_refresh)  # Gọi lại sau 3 giây
    
    def test_localhost(self):
        """Test gửi file cho chính mình qua localhost"""
        # Tự động thêm localhost vào danh sách
        self.file_share.online_devices["127.0.0.1"] = f"{self.file_share.my_name} (Localhost)"
        
        # Refresh để hiển thị
        self.refresh_devices()
        
        # Hiển thị thông báo
        messagebox.showinfo(
            "Success"
        )
    
    def select_file_and_send(self, target_ip):
        """Chọn file và gửi"""
        file_path = filedialog.askopenfilename(
            title="Chọn file để gửi",
            filetypes=[("All Files", "*.*")]
        )
        
        if file_path:
            # Cập nhật UI
            self.status_label.configure(text=f"Đang gửi tới {target_ip}...")
            self.progress_bar.set(0)
            
            # Gửi file trong thread riêng với callback
            threading.Thread(
                target=self.send_with_progress,
                args=(target_ip, file_path),
                daemon=True
            ).start()
    
    def send_with_progress(self, target_ip, file_path):
        """Gửi file và cập nhật progress bar"""
        import os
        
        if not os.path.exists(file_path):
            self.after(0, lambda: messagebox.showerror(
                "Lỗi", 
                f"File không tồn tại: {file_path}"
            ))
            return
        
        client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            client_sock.connect((target_ip, 6000))
            
            # Gửi tên file
            filename = os.path.basename(file_path)
            client_sock.send(filename.ljust(1024).encode())
            
            # Gửi kích thước file
            filesize = os.path.getsize(file_path)
            client_sock.send(str(filesize).ljust(1024).encode())
            
            # Gửi nội dung file
            with open(file_path, 'rb') as f:
                sent = 0
                while True:
                    chunk = f.read(4096)
                    if not chunk:
                        break
                    client_sock.send(chunk)
                    sent += len(chunk)
                    
                    # Cập nhật progress bar (phải dùng after để thread-safe)
                    progress = sent / filesize
                    self.after(0, lambda p=progress: self.progress_bar.set(p))
                    self.after(0, lambda p=progress: self.status_label.configure(
                        text=f"Đang gửi: {p*100:.1f}%"
                    ))
            
            # Hoàn thành
            self.after(0, lambda: self.progress_bar.set(1))
            self.after(0, lambda: self.status_label.configure(
                text=f"✅ Gửi thành công!"
            ))
            self.after(0, lambda: messagebox.showinfo(
                "Thành công", 
                f"Đã gửi {filename} tới {target_ip}!"
            ))
            
        except ConnectionRefusedError:
            self.after(0, lambda: messagebox.showerror(
                "Lỗi kết nối",
                f"Không thể kết nối đến {target_ip}\nMáy đích có thể chưa mở ứng dụng."
            ))
        except Exception as e:
            self.after(0, lambda: messagebox.showerror(
                "Lỗi", 
                f"Lỗi khi gửi file: {str(e)}"
            ))
        finally:
            client_sock.close()
            self.after(0, lambda: self.progress_bar.set(0))


# --- KHỞI ĐỘNG ỨNG DỤNG ---
if __name__ == "__main__":
    # Khởi tạo backend
    file_share = FileShareApp()
    file_share.start_broadcast()
    file_share.start_discovery()
    file_share.start_receiver()
    
    print("🚀 Backend đã khởi động!")
    print(f"📡 Tên máy: {file_share.my_name}")
    print(f"🔍 Đang tìm thiết bị trên mạng LAN...")
    
    # Khởi động GUI
    app = AppUI(file_share)
    app.mainloop()