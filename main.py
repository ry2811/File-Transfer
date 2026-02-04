import socket
import threading
import time
import os

class FileShareApp:
    def __init__(self): #khoi tao
        self.online_devices = {} # Lưu dưới dạng {IP: Tên_Máy}
        self.my_name = socket.gethostname()
        self.magic_word = "ikary"
        
    # --- PHẦN 1: KHÁM PHÁ (UDP) ---
    def start_broadcast(self):
        def run(): #Khoi tao socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            while True:
                msg = f"{self.magic_word}:{self.my_name}"
                sock.sendto(msg.encode(), ('<broadcast>', 5001))
                time.sleep(5)
        threading.Thread(target=run, daemon=True).start()

    def start_discovery(self):
        def run():
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.bind(('', 5001))
            while True:
                data, addr = sock.recvfrom(1024)
                msg = data.decode()
                if msg.startswith(self.magic_word):
                    name = msg.split(":")[1]
                    self.online_devices[addr[0]] = name # Cập nhật danh sách
                    # Ở đây bạn sẽ ra lệnh cho UI cập nhật danh sách hiển thị
        threading.Thread(target=run, daemon=True).start()

    # --- PHẦN 2: NHẬN FILE (TCP SERVER) ---
    def start_receiver(self):
        def run():
            server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_sock.bind(('0.0.0.0', 6000))
            server_sock.listen(5)
            while True:
                client, addr = server_sock.accept()
                print(f"Đang nhận file từ {addr}...")
                filename = client.recv(1024).decode().strip()
                print(f"Tên file: {filename}")
                
                # Nhận kích thước file
                filesize = int(client.recv(1024).decode().strip())
                print(f"Kích thước: {filesize} bytes")
                
                # Tạo thư mục "received" nếu chưa có
                os.makedirs("received", exist_ok=True)
                filepath = os.path.join("received", filename)
                
                # Nhận nội dung file
                with open(filepath, 'wb') as f:
                    received = 0
                    while received < filesize:
                        chunk = client.recv(4096)
                        if not chunk:
                            break
                        f.write(chunk)
                        received += len(chunk)
                        # In tiến trình
                        progress = (received / filesize) * 100
                        print(f"\rĐang nhận: {progress:.1f}%", end='')
                
                print(f"\n✓ Nhận file thành công: {filepath}")
                # Logic nhận file đã học ở bước trước viết ở đây
                client.close()
        threading.Thread(target=run, daemon=True).start()

    # --- PHẦN 3: GỬI FILE (TCP CLIENT) ---
        # --- PHẦN 3: GỬI FILE (TCP CLIENT) ---
    def send_file(self, target_ip, file_path):
        # Hàm này sẽ được gọi khi bạn nhấn nút "Gửi" trên giao diện
        def run():
            if not os.path.exists(file_path):
                print(f"❌ Lỗi: File không tồn tại - {file_path}")
                return
                
            client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                client_sock.connect((target_ip, 6000))
                
                # Gửi tên file (padding đến 1024 bytes)
                filename = os.path.basename(file_path)
                client_sock.send(filename.ljust(1024).encode())
                
                # Gửi kích thước file
                filesize = os.path.getsize(file_path)
                client_sock.send(str(filesize).ljust(1024).encode())
                
                print(f"📤 Đang gửi: {filename} ({filesize} bytes)")
                
                # Gửi nội dung file
                with open(file_path, 'rb') as f:
                    sent = 0
                    while True:
                        chunk = f.read(4096)
                        if not chunk:
                            break
                        client_sock.send(chunk)
                        sent += len(chunk)
                        # In tiến trình
                        progress = (sent / filesize) * 100
                        print(f"\r📊 Tiến trình: {progress:.1f}%", end='')
                
                print(f"\n✅ Gửi thành công tới {target_ip}!")
            except ConnectionRefusedError:
                print(f"❌ Lỗi: Không thể kết nối đến {target_ip} (máy đích không mở cổng 6000)")
            except Exception as e:
                print(f"❌ Lỗi khi gửi: {e}")
            finally:
                client_sock.close()
        threading.Thread(target=run).start()

# --- CHẠY APP ---
app = FileShareApp()
app.start_broadcast()  # Bắt đầu cho máy khác thấy mình
app.start_discovery()  # Bắt đầu tìm máy khác
app.start_receiver()   # Bắt đầu mở cổng nhận file
