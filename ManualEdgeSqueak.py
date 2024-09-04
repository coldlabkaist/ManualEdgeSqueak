import cv2
import numpy as np
from tkinter import Tk, Label, Entry, Button, Canvas, filedialog, Toplevel
from PIL import Image, ImageTk
from scipy.signal import find_peaks
import os

# 전역 변수 초기화
current_frame = None
current_video_path = None

# GetThreshold 함수 정의
def GetThreshold(input_video_path, distance=30, prominence=1000):
    cap = cv2.VideoCapture(input_video_path)
    
    if not cap.isOpened():
        print(f"Error: Unable to open video file {input_video_path}")
        return
    
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    hist_accum = np.zeros((256,), dtype=np.float32)

    for _ in range(frame_count):
        res, frame = cap.read()
        if not res:
            break
        
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        hist = cv2.calcHist([gray_frame], [0], None, [256], [0, 256])
        
        hist_accum += hist.flatten()

    hist_avg = hist_accum / frame_count
    
    for i in range(1, len(hist_avg) - 1):
        if hist_avg[i] == 0:
            hist_avg[i] = (hist_avg[i - 1] + hist_avg[i + 1]) / 2
    
    if hist_avg[0] == 0:
        hist_avg[0] = hist_avg[1]
    if hist_avg[-1] == 0:
        hist_avg[-1] = hist_avg[-2]

    peaks, _ = find_peaks(-hist_avg, distance=distance, prominence=prominence)

    return peaks[0] if len(peaks) > 0 else 0  # 기본값 0 추가

def ContourMasking(frame, threshold, thickness=5):
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray_frame_copy = gray_frame.copy()
    
    gray_frame_copy[gray_frame > threshold + (thickness // 2)] = 0
    gray_frame_copy[gray_frame < threshold - (thickness // 2)] = 0
    
    gray_frame_copy[gray_frame_copy != 0] = 255
    
    gray_frame[gray_frame_copy == 255] = 255
    gray_frame = cv2.cvtColor(gray_frame, cv2.COLOR_GRAY2BGR)

    return gray_frame

def VideoModification(input_video_path, output_video_path, threshold, thickness=5):
    cap = cv2.VideoCapture(input_video_path)
    
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_video_path, fourcc, fps, (frame_width, frame_height))
    
    for _ in range(frame_count):
        res, frame = cap.read()
        if not res:
            break
        
        masked_frame = ContourMasking(frame, threshold, thickness)
        out.write(masked_frame)
    
    cap.release()
    out.release()
    cv2.destroyAllWindows()
    
    print('Video Creation Completed.')

def open_video():
    global current_frame, current_video_path
    video_path = filedialog.askopenfilename(filetypes=[("Video files", "*.mp4;*.avi;*.mov")])
    if video_path:
        cap = cv2.VideoCapture(video_path)
        ret, frame = cap.read()
        if ret:
            current_frame = frame
            current_video_path = video_path
            default_threshold = GetThreshold(video_path)
            threshold_entry.delete(0, "end")
            threshold_entry.insert(0, str(default_threshold))
            show_frame()  # show_frame에 frame 전달하지 않고 호출만
            cap.release()

def show_frame(event=None):
    if current_frame is None:
        return  # current_frame이 없으면 아무것도 하지 않음

    threshold = int(threshold_entry.get())
    thickness = int(thickness_entry.get())

    img_rgb = cv2.cvtColor(current_frame, cv2.COLOR_BGR2RGB)
    masked_img = ContourMasking(img_rgb, threshold, thickness)
    height, width, _ = masked_img.shape

    canvas_width = canvas.winfo_width()
    canvas_height = canvas.winfo_height()

    scale = min(canvas_width / width, canvas_height / height)
    new_width = int(width * scale)
    new_height = int(height * scale)
    img_resized = cv2.resize(masked_img, (new_width, new_height))

    img_pil = Image.fromarray(img_resized)
    img_tk = ImageTk.PhotoImage(image=img_pil)
    canvas.create_image(0, 0, anchor="nw", image=img_tk)
    canvas.image = img_tk

def apply_and_export():
    if current_video_path:
        # 원본 파일 이름에서 파일명과 확장자 분리
        original_name, ext = os.path.splitext(os.path.basename(current_video_path))
        # 기본 파일 이름 설정 (preprocessed_ 원본이름)
        default_output_name = f"preprocessed_{original_name}{ext}"

        # 사용자에게 저장할 디렉토리 선택을 묻는 대화상자 표시
        output_directory = filedialog.askdirectory(title="저장할 디렉토리 선택")
        if output_directory:
            # 디렉토리와 기본 파일 이름 결합하여 출력 파일 경로 생성
            output_path = os.path.join(output_directory, default_output_name)

            # 비디오 수정 함수 호출
            threshold = int(threshold_entry.get())
            thickness = int(thickness_entry.get())
            VideoModification(current_video_path, output_path, threshold, thickness)
            print(f"Video saved as {output_path}")

def update_frame():
    show_frame()

def increase_threshold():
    current_value = int(threshold_entry.get())
    threshold_entry.delete(0, "end")
    threshold_entry.insert(0, str(current_value + 1))
    update_frame()

def decrease_threshold():
    current_value = int(threshold_entry.get())
    threshold_entry.delete(0, "end")
    threshold_entry.insert(0, str(current_value - 1))
    update_frame()

def increase_thickness():
    current_value = int(thickness_entry.get())
    thickness_entry.delete(0, "end")
    thickness_entry.insert(0, str(current_value + 1))
    update_frame()

def decrease_thickness():
    current_value = int(thickness_entry.get())
    thickness_entry.delete(0, "end")
    thickness_entry.insert(0, str(current_value - 1))
    update_frame()

# Entry에서 Enter 키를 누를 때 값이 반영되도록 함수를 추가합니다.
def update_threshold(event):
    update_frame()

def update_thickness(event):
    update_frame()

def close_gui():
    root.destroy()

root = Tk()
root.title("Contour Masking")

canvas = Canvas(root, width=600, height=400)
canvas.pack(side="left", fill="both", expand=True)

# 창 크기 변경 이벤트에 show_frame 함수 연결
canvas.bind("<Configure>", show_frame)

control_frame = Canvas(root)
control_frame.pack(side="right", fill="y", padx=10)

open_button = Button(control_frame, text="Open Video", command=open_video)
open_button.grid(row=0, column=0, columnspan=3, pady=10)

# Threshold 컨트롤
threshold_label = Label(control_frame, text="threshold")
threshold_label.grid(row=1, column=1)

threshold_minus_button = Button(control_frame, text="-", command=decrease_threshold)
threshold_minus_button.grid(row=2, column=0)

threshold_entry = Entry(control_frame, width=5)
threshold_entry.grid(row=2, column=1)
threshold_entry.insert(0, "26")  # 기본값 설정
# Enter 키 이벤트와 연동
threshold_entry.bind("<Return>", update_threshold)

threshold_plus_button = Button(control_frame, text="+", command=increase_threshold)
threshold_plus_button.grid(row=2, column=2)

# Thickness 컨트롤
thickness_label = Label(control_frame, text="thickness")
thickness_label.grid(row=3, column=1)

thickness_minus_button = Button(control_frame, text="-", command=decrease_thickness)
thickness_minus_button.grid(row=4, column=0)

thickness_entry = Entry(control_frame, width=5)
thickness_entry.grid(row=4, column=1)
thickness_entry.insert(0, "5")  # 기본값 설정
# Enter 키 이벤트와 연동
thickness_entry.bind("<Return>", update_thickness)

thickness_plus_button = Button(control_frame, text="+", command=increase_thickness)
thickness_plus_button.grid(row=4, column=2)

# Apply & Export 버튼
apply_button = Button(control_frame, text="Apply & Export", command=apply_and_export)
apply_button.grid(row=6, column=0, columnspan=3, pady=10)

# Close 버튼
close_button = Button(control_frame, text="Close", command=close_gui)
close_button.grid(row=7, column=0, columnspan=3, pady=10)

root.mainloop()