import tkinter as tk
from ctypes import windll
import ctypes
import sys
from datetime import datetime
from tkinter import filedialog
import os
import numpy as np
import threading
import shutil
import time
import cv2
from PIL import Image, ImageTk

currentmodel = "default.yml"


def get_output():
    try:
        with open("var.txt", "r") as file:
            for line in file:
                if line.startswith("output="):
                    s =line.strip().split("=")[1]
                    if not os.path.exists(s):
                        with open(s, "w") as file:
                            pass
                    return s
    except FileNotFoundError:
        pass
    if not os.path.exists("output.txt"):
        with open("output.txt", "w") as file:
            pass
    return "output.txt"

def get_theme():
    try:
        with open("var.txt", "r") as file:
            for line in file:
                if line.startswith("theme="):
                    return line.strip().split("=")[1]
    except FileNotFoundError:
        pass
    return "Dark"

def get_font():
    try:
        with open("var.txt", "r") as file:
            for line in file:
                if line.startswith("font="):
                    return line.strip().split("=")[1]
    except FileNotFoundError:
        pass
    return "Century Gothic"

def set_appwindow(window, windll):
    hwnd = windll.user32.GetParent(window.winfo_id())
    style = windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
    style = style & ~WS_EX_TOOLWINDOW
    style = style | WS_EX_APPWINDOW
    windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)
    window.wm_withdraw()
    window.after(10, lambda: window.wm_deiconify())

def minimize_window(root):
    global minimized
    root.state('withdrawn')
    root.overrideredirect(False)
    root.state('iconic')
    minimized = True

def get_camera_indexes(max_cams=10):
    available_cameras = []
    for i in range(max_cams):
        cap = cv2.VideoCapture(i)
        if cap.read()[0]:
            available_cameras.append(i)
        cap.release()
    return available_cameras

def Quit(cap, root):
    cap.release()
    cv2.destroyAllWindows()
    root.quit()

def start_move(event, root):
    root.x = event.x_root
    root.y = event.y_root

def on_move(event, root):
    dx = event.x_root - root.x
    dy = event.y_root - root.y
    root.geometry(f"+{root.winfo_x() + dx}+{root.winfo_y() + dy}")
    root.x = event.x_root
    root.y = event.y_root

def on_map(event, root, windll):
    global minimized
    root.overrideredirect(True)
    if minimized:
        set_appwindow(root, windll=windll)
        minimized = False

def load_recognizer(model):
    try:
        new_recognizer = cv2.face.LBPHFaceRecognizer_create()
        new_recognizer.read(f'Models/{model}')
        

        new_names = []
        txt_file = f'Models/{model.split(".")[0]}.txt'
        with open(txt_file, "r") as f:
            for line in f:
                _, name = line.strip().split(" : ")
                new_names.append(name)
        
        
        with recognizer_lock:
            global recognizer, names
            recognizer = new_recognizer
            names = new_names
        print(f"Loaded model: {model}")
    except Exception as e:
        print(f"Error loading model {model}: {e}")

def ShowLiveFeed(LiveFeedFrame, Panels):
    for i in Panels:
        i.place_forget()
    LiveFeedFrame.place(relx=0.5, rely=0.5, anchor="center")
    update_models()

def ShowTrain(TrainFrame, Panels):
    global showRec
    for i in Panels:
        i.place_forget()
    TrainFrame.place(relx=0.5, rely=0.5, anchor="center")
    showRec = False
    if theme == "Dark":
        ShowButton.config(bg="#591919")
    elif theme == "Light":
        ShowButton.config(bg="#d74848")

def ShowSettings(SettingsFrame, Panels):
    try:
        ConfirmOutputButton.config(bg=SecondaryColor)
    except:
        pass
    for i in Panels:
        i.place_forget()
    SettingsFrame.place(relx=0.5, rely=0.5, anchor="center")

def ShowGather(GatherFrame, Panels):
    global yml_files
    yml_files = [f for f in os.listdir("Models") if f.endswith('.yml')]
    for i in Panels:
        i.place_forget()
    try:
        for i in filesWidget:
            i.pack_forget()
    except:
        pass

   

    GatherFrame.place(relx=0.5, rely=0.5, anchor="center")

    for i in yml_files:
        k = FileWidget(scrollable_frame, f"Models/{i}", "Models/")
        k.pack()
        filesWidget.append(k)

def change_camera(selected_cam):
    global cap
    cap.release()
    cap = cv2.VideoCapture(selected_cam.get())

def showRecHandler():
    global showRec
    if showRec == True:
        showRec = False
        if theme=="Dark":
            ShowButton.config(bg="#591919", activebackground="#591919")
        else:
           ShowButton.config(bg="#d74848", activebackground="#d74848") 
    elif showRec == False:
        showRec = True
        if theme=="Dark":
            ShowButton.config(bg="#265919", activebackground="#265919")
        else:
            ShowButton.config(bg="#34e086", activebackground="#34e086")

def update_frame(label1, width, height):
    global Threshold
    global showRec
    global prev_detected_faces
    global recognizer
    global names
    global outputGlobalFolder


    ret, frame = cap.read()
    if ret:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = faceCascade.detectMultiScale(
            gray,
            scaleFactor=1.2,
            minNeighbors=5,
            minSize=(int(width * 0.1), int(height * 0.1)),
        )
        
        current_detected_faces = set()
        with open(outputGlobalFolder, "a") as f:
            for (x, y, w, h) in faces:
                if showRec:
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

                id, confidence = recognizer.predict(gray[y:y + h, x:x + w])

                if confidence < Threshold:
                    id = names[id - 1]
                    confidence_text = f"{round(Threshold - confidence)}%"
                else:
                    id = "unknown"
                    confidence_text = f"{round(Threshold - confidence)}%"

                if showRec:
                    cv2.putText(frame, str(id), (x + 5, y - 5), font, 1, (255, 255, 255), 2)
                    cv2.putText(frame, confidence_text, (x + 5, y + h - 5), font, 1, (255, 255, 0), 1)

                now = datetime.now()
                f.write(f"{now.strftime('%H:%M:%S')}  :  {id} - x:{x}, y:{y}, w:{w}, h:{h}  :   Confidence: {confidence_text}\n")

                current_detected_faces.add(id)
        f.close()
                    
        new_faces = current_detected_faces - prev_detected_faces
        lost_faces = prev_detected_faces - current_detected_faces
        now = datetime.now()

        for face in new_faces:
            insert_text_Console(f" + Spotted:\t{face}\t   {now.strftime('%H:%M:%S')}\t{int(confidence)}%\t\tx:{x}y:{y}w:{w}h:{h}", "+")
        for face in lost_faces:
            insert_text_Console(f" - Lost:\t{face}\t   {now.strftime('%H:%M:%S')}", "-")
            
        
        
        prev_detected_faces = current_detected_faces
        
        text = ", ".join(current_detected_faces)
        FacesLabel.config(text=text)

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = cv2.resize(frame, (width, height))
        img = Image.fromarray(frame)
        img_tk = ImageTk.PhotoImage(image=img)
        label1.img_tk = img_tk
        label1.config(image=img_tk)
    
        try:
            OutputWindowDataset.img_tk = img_tk
            OutputWindowDataset.config(image=img_tk)
        except:
            pass


        

    label1.after(10, lambda: update_frame(label1, width, height))

def update_threshold(*args):
    global Threshold
    try:
        Threshold = int(SensitivityEntry.get())
    except ValueError:
        Threshold = 0 

def change_model(selected_model):
    global currentmodel
    currentmodel = selected_model.get()
    threading.Thread(target=load_recognizer, args=(currentmodel,)).start()

def update_models():
    global dropdownModel

    models = [f for f in os.listdir("Models") if f.endswith(".yml")]

    if dropdownModel:
        dropdownModel.destroy()

    selected_model.set(models[0] if models else "") 
    dropdownModel = tk.OptionMenu(temp0, selected_model, *models, command=lambda _: change_model(selected_model))

    dropdownModel.config(width=17, bg=PrimaryColor, fg=ForeGround, bd=0, highlightthickness=0, 
                         activebackground=PrimaryColor, activeforeground=ForeGround, cursor="hand2")
    dropdownModel.place(x=120, rely=0.5, anchor='w')
    PrimaryElements.append(dropdownModel)

def insert_text_Console(text, id):

    tab_width = 8
    text_with_spaces = ""
    

    for char in text:
        if char == '\t':

            spaces_needed = tab_width - (len(text_with_spaces) % tab_width)
            text_with_spaces += ' ' * spaces_needed
        else:
            text_with_spaces += char


    text_with_spaces = text_with_spaces.ljust(79)

    if len(text_with_spaces)>79:
        text_with_spaces = text_with_spaces[:79]

    Console.config(state="normal")
    
    if id == "+":
        Console.insert("end", text_with_spaces, "spotted")
    elif id == "-":
        Console.insert("end", text_with_spaces, "lost")
    else:
        Console.insert("end", text_with_spaces)
    
    Console.see("end")
    Console.config(state="disabled")

def insertNames(text, id):
        with open("DatasetSetup/IndexNames.txt", 'a') as f:
            f.write(f"{id} : {text}\n")

def craftingImages(name, startOver=False):
    def sub_process():
        process_time = 10
        WebcamStart.config(state="disabled")
        BackWeb.config(state="disabled")
        LiveFeedButton.config(state="disabled")
        TrainButton.config(state="disabled")
        GatherButton.config(state="disabled")
        SettingsButton.config(state="disabled")
                
        output = "DatasetSetup"
        if startOver:
            if os.path.exists(output):
                shutil.rmtree(output)
            os.makedirs(output)
        
        existing_ids = [int(f.split('.')[1]) for f in os.listdir(output) if f.endswith('.jpg')]
        if existing_ids:
            face_id = max(existing_ids) + 1
        else:
            face_id = 1
        face_detector = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
        start_time = time.time()
        count = 0

        insertNames(name, face_id)

        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_detector.detectMultiScale(gray, 1.3, 5)
            
            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
                count += 1
                cv2.imwrite(f"{output}/User.{face_id}.{count}.jpg", gray[y:y + h, x:x + w])
            
            tt = time.time()
            WebcamStart.config(text=f"{(int(tt-start_time)-process_time)*-1}s")

            
            
            if tt - start_time >= process_time:
                WebcamStart.config(state="normal")
                BackWeb.config(state="normal")
                LiveFeedButton.config(state="normal")
                TrainButton.config(state="normal")
                GatherButton.config(state="normal")
                SettingsButton.config(state="normal")
                WebcamStart.place_forget()
                NameLabel.place_forget()
                NameEntry.place_forget()
                ttt = tk.Label(TrainFrame, text="Completed", font=(Global_font, 30), fg="green", bg=PrimaryColor)
                ttt.place(x=60, y=625, anchor='nw')
                PrimaryElements.append(ttt)
                AddPersonButton.place(x=WIDTH-200-10-270, y=625, anchor='ne')
                ContinueWebButton.place(x=WIDTH-200-10-50, y=625, anchor='ne')
                break
                
            
    threading.Thread(target=sub_process).start()

def AddPerson():
    update_Dataset_step(1, None, 1)
    WebcamStart.config(command=lambda:craftingImages(NameEntry.get(), startOver=False))
def change_theme(selected_theme):
    global PrimaryColor
    global SecondaryColor
    global ForeGround
    global theme
    global Logo

    new_theme = selected_theme.get()
    theme = new_theme
    with open("var.txt", "r") as file:
        lines = file.readlines()

    with open("var.txt", "w") as file:
        for line in lines:
            if line.startswith("theme="):
                file.write(f"theme={new_theme}\n")
            else:
                file.write(line)

    if new_theme == "Dark":
        PrimaryColor = "#212121"
        SecondaryColor = "#161616"
        ForeGround = "#FAFAFA"

    elif new_theme == "Light":
        PrimaryColor = "#DDDDDD"
        SecondaryColor = "#FAFAFA"
        ForeGround = "#212121"

    for widget in SecondaryElements:
        try:
            widget.config(bg=SecondaryColor)
        except:
            pass
        try:
            widget.config(fg=ForeGround)
        except:
            pass
        try:
            widget.change_theme(PrimaryColor, SecondaryColor)
        except:
            pass
        try:
            widget.config(activebackground=SecondaryColor, activeforeground=ForeGround)
        except:
            pass



    for widget in PrimaryElements:
        try:
            widget.config(bg=PrimaryColor)
        except:
            pass
        try:
            widget.config(fg=ForeGround)
        except:
            pass
        try:
            widget.change_theme(PrimaryColor, SecondaryColor)
        except:
            pass
        try:
            widget.config(activebackground=SecondaryColor, activeforeground=ForeGround)
        except:
            pass

    if theme=="Light":
        CloseButton.config(bg="#d74848")
        ShowButton.config(bg="#d74848", activebackground="#d74848") 
        Console.tag_configure("spotted", background="#34e086")
        Console.tag_configure("lost", background="#d74848")
        ShowButton.update_idletasks()
        Logo = tk.PhotoImage(file="Assets/logoLight.png")
        LogoSpaceLabel.config(image=Logo)
    elif theme=="Dark":
        CloseButton.config(bg="#591919")
        ShowButton.config(bg="#591919", activebackground="#591919")
        Console.tag_configure("spotted", background="#265919")
        Console.tag_configure("lost", background="#591919")
        ShowButton.update_idletasks()
        Logo = tk.PhotoImage(file="Assets/logo.png")
        LogoSpaceLabel.config(image=Logo)

def change_font(selected_font):
    global Global_font
    new_font = selected_font.get()
    Global_font = new_font
    with open("var.txt", "r") as file:
        lines = file.readlines()

    with open("var.txt", "w") as file:
        for line in lines:
            if line.startswith("font="):
                file.write(f"font={new_font}\n")
            else:
                file.write(line)


    def update_font_for_elements(elements):
        for widget in elements:
            if not widget == Console:
                try:
                    current_font = widget.cget("font")
                    font_parts = current_font.split()
                    font_family = " ".join(font_parts[:-1])
                    font_size = font_parts[-1]
                    widget.config(font=(Global_font, font_size))
                except Exception as e:
                    pass

        
    update_font_for_elements(PrimaryElements)
    update_font_for_elements(SecondaryElements)

def SetOutputFolder():
    f = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
    oten.delete(0, 'end')
    oten.insert(tk.END, f)

def ApplyOutputFolder():
    global outputGlobalFolder
    with open("var.txt", "r") as file:
        lines = file.readlines()

        with open("var.txt", "w") as file:
            for line in lines:
                if line.startswith("output="):
                    file.write(f"output={oten.get()}\n")
                else:
                    file.write(line)

    ConfirmOutputButton.config(background="green")
    outputGlobalFolder = oten.get()

def on_mouse_wheel_Gather(event):
    canvas.yview_scroll(-1 * (event.delta // 120), "units")

def run_as_admin():
    if ctypes.windll.shell32.IsUserAnAdmin():
        return
    script = os.path.abspath(sys.argv[0])
    params = " ".join(f'"{arg}"' for arg in sys.argv[1:])
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, f'"{script}" {params}', None, 0
    )
    sys.exit()

def run_as_admin_console():
    if ctypes.windll.shell32.IsUserAnAdmin():
        return
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    sys.exit()


with open("output.txt", "w") as file:
    pass
Global_font = get_font()
outputGlobalFolder = get_output()
theme = get_theme()

class CustomButton(tk.Button):
    def __init__(self, master=None, text="-empty-", command=None,width=30,font=(Global_font, 18), **kwargs):
        super().__init__(master, text=text, command=command, **kwargs)
        self.config(relief="flat",
                    bd=0,
                    highlightthickness=0,
                    text=text,
                    height=2,
                    width=width,
                    bg=SecondaryColor,
                    fg=ForeGround,
                    cursor="hand2",
                    command=command,
                    font=font,
                    activebackground=PrimaryColor,
                    activeforeground=ForeGround)
        self.bind("<Enter>", lambda e:self.on_hover(e, PrimaryColor))
        self.bind("<Leave>", lambda e:self.on_leave(e, SecondaryColor))

    def on_hover(self, event, bg):
        self.config(bg=bg)

    def on_leave(self, event, bg):
        self.config(bg=bg)

    def change_theme(self, primary_color, secondary_color):
        global PrimaryColor, SecondaryColor
        PrimaryColor = primary_color
        SecondaryColor = secondary_color
        self.config(bg=SecondaryColor, activebackground=PrimaryColor)
        self.bind("<Enter>", lambda e: self.on_hover(e, PrimaryColor))
        self.bind("<Leave>", lambda e: self.on_leave(e, SecondaryColor))

class FileWidget(tk.Frame):
    def __init__(self, parent, file_path, folder, *args, **kwargs):
        super().__init__(parent, width=850, height=100, *args, **kwargs)
        self.file_path = file_path

        self.config(bg=PrimaryColor)
        
        self.Sub = tk.Frame(self,width=844, height=96, bg=SecondaryColor)
        self.Sub.place(relx=0.5, rely=0.5, anchor="center")
        
        file_name = os.path.basename(file_path)
        
        self.name_label = tk.Label(self, text=file_name, bg=SecondaryColor,font=(Global_font, 13), fg=ForeGround)
        self.name_label.place(x=20, rely=0.5, anchor="w")
        
        self.path_label = tk.Label(self, text=folder, bg=SecondaryColor,font=(Global_font, 13), fg=ForeGround)
        self.path_label.place(x=250,rely=0.5, anchor="w")
        
        self.delete_button = tk.Button(self, text="Delete", bg='#591919', command=self.delete_file,font=(Global_font, 13), fg=ForeGround, bd=0, highlightthickness=0, activebackground='#591919')
        if file_path == "Models/default.yml":
            self.delete_button.config(state="disabled")
        if theme == "Light":
            self.delete_button.config(fg=PrimaryColor, bg="#d74848", activebackground="#d74848", activeforeground=PrimaryColor)
        self.delete_button.place(x=830,rely=0.5, anchor="e")
        
    def delete_file(self):

        if os.path.exists(self.file_path):
            os.remove(self.file_path)
            os.remove(self.file_path.split(".")[0]+".txt")


        self.pack_forget()

if theme == "Dark":
    PrimaryColor = "#212121"
    SecondaryColor = "#161616"
    ForeGround = "#FAFAFA"
elif theme == "Light":
    PrimaryColor = "#DDDDDD"
    SecondaryColor = "#FAFAFA"
    ForeGround = "#212121"

GWL_EXSTYLE = -20
WS_EX_APPWINDOW = 0x00040000
WS_EX_TOOLWINDOW = 0x00000080
minimized = False
Panels = []

showRec = False
recognizer_lock = threading.Lock()

PrimaryElements = []
SecondaryElements = []

os.makedirs("Models", exist_ok=True)

recognizer = cv2.face.LBPHFaceRecognizer_create()
detector = cv2.CascadeClassifier("haarcascade_frontalface_default.xml");
load_recognizer(currentmodel)
cascadePath = "haarcascade_frontalface_default.xml"
faceCascade = cv2.CascadeClassifier(cascadePath)
font = cv2.FONT_HERSHEY_SIMPLEX
id = 1


root = tk.Tk()
root.title("FaceRec")
root.iconbitmap("Assets/logo.ico")
root.config(bg=PrimaryColor)
PrimaryElements.append(root)
WIDTH = 1100 
HEIGHT = 800
root.geometry(f"{WIDTH}x{HEIGHT}")
root.overrideredirect(True)
root.after(10, lambda: set_appwindow(root, windll=windll))
root.bind("<Map>", lambda e: on_map(e, root, windll))


TitleBar = tk.Frame(root, height=40, width=WIDTH, bg=SecondaryColor)
SecondaryElements.append(TitleBar)
TitleBar.place(x=0, y=0)
TitleBar.bind("<ButtonPress-1>", lambda e: start_move(e, root))
TitleBar.bind("<B1-Motion>", lambda e: on_move(e, root))

ActionFrame = tk.Frame(TitleBar,bg=SecondaryColor, width=80, height=30)
ActionFrame.place(x=WIDTH-5, rely=0.5, anchor='e')
SecondaryElements.append(ActionFrame)

CloseButton = tk.Button(ActionFrame, text="X", command=lambda: Quit(cap, root), cursor="hand2", relief="flat", bd=0, highlightthickness=0, height=2, width=3, bg="#591919", fg='#3a1010', font=(f'{Global_font} bold', 15), activebackground="#591919", activeforeground='#3a1010')

CloseButton.place(x=80, rely=0.5, anchor="e")

MinimizeButton = tk.Button(ActionFrame, text="─", command=lambda:minimize_window(root), cursor="hand2", relief="flat", bd=0, highlightthickness=0, height=2, width=3,bg=PrimaryColor, fg=ForeGround, font=(f'{Global_font} bold', 15), activebackground=PrimaryColor, activeforeground=SecondaryColor)
MinimizeButton.place(x=0, rely=0.5, anchor="w")
PrimaryElements.append(MinimizeButton)


PreviewFrame = tk.Frame(root, height=HEIGHT-40, width=WIDTH-200, bg=PrimaryColor)
PreviewFrame.place(x=WIDTH, y=HEIGHT, anchor="se")
PrimaryElements.append(PreviewFrame)

MenuBar = tk.Frame(root, height=HEIGHT-40, width=WIDTH-(WIDTH-200), bg=SecondaryColor)
SecondaryElements.append(MenuBar)
MenuBar.place(x=0, y=40)

LogoSpace = tk.Frame(MenuBar, height=75, width=WIDTH-(WIDTH-200), bg=SecondaryColor)
SecondaryElements.append(LogoSpace)
LogoSpace.place(x=0, y=0)
if theme == "Dark":
    Logo = tk.PhotoImage(file="Assets/logo.png")
elif theme == "Light":
    Logo = tk.PhotoImage(file="Assets/logoLight.png")
LogoSpaceLabel = tk.Label(LogoSpace, image=Logo, bd=0, bg=SecondaryColor)
LogoSpaceLabel.place(relx=0.5,rely=0.5, anchor='center')
SecondaryElements.append(LogoSpaceLabel)


LiveFeedFrame = tk.Frame(PreviewFrame, height=HEIGHT-40-10, width=WIDTH-200-10, bg=PrimaryColor)
PrimaryElements.append(LiveFeedFrame)
TrainFrame = tk.Frame(PreviewFrame, height=HEIGHT-40-10, width=WIDTH-200-10, bg=PrimaryColor)
PrimaryElements.append(TrainFrame)
GatherFrame = tk.Frame(PreviewFrame, height=HEIGHT-40-10, width=WIDTH-200-10, bg=SecondaryColor)
SecondaryElements.append(GatherFrame)
SettingsFrame = tk.Frame(PreviewFrame, height=HEIGHT-40-10, width=WIDTH-200-10, bg=PrimaryColor)
PrimaryElements.append(SettingsFrame)
Panels.append(LiveFeedFrame)
Panels.append(TrainFrame)
Panels.append(GatherFrame)
Panels.append(SettingsFrame)



LiveFeedButton = CustomButton(MenuBar, text="Live", command=lambda:ShowLiveFeed(LiveFeedFrame, Panels))
LiveFeedButton.place(relx=0.5, y=100, anchor='n')
SecondaryElements.append(LiveFeedButton)

TrainButton = CustomButton(MenuBar, text="Train", command=lambda:ShowTrain(TrainFrame, Panels))
TrainButton.place(relx=0.5, y=175, anchor='n')
SecondaryElements.append(TrainButton)

GatherButton = CustomButton(MenuBar, text="Dataset", command=lambda:ShowGather(GatherFrame, Panels))
GatherButton.place(relx=0.5, y=250, anchor='n')
SecondaryElements.append(GatherButton)

SettingsButton = CustomButton(MenuBar, text="Settings", command=lambda:ShowSettings(SettingsFrame, Panels))
SettingsButton.place(relx=0.5, y=650, anchor='n')
SecondaryElements.append(SettingsButton)




cameras = get_camera_indexes()
selected_cam = tk.IntVar(value=cameras[0] if cameras else -1)
cap = cv2.VideoCapture(selected_cam.get())


prev_detected_faces = set()





OutputWindow = tk.Label(LiveFeedFrame, borderwidth=0, highlightthickness=0)
OutputWindow.place(x=0, y=0)

SettingsFrameLiveFeed = tk.Frame(LiveFeedFrame, width=WIDTH-200-10, height=245, bg=PrimaryColor)
SettingsFrameLiveFeed.place(x=0,y=505)
PrimaryElements.append(SettingsFrameLiveFeed)
temp = tk.Frame(SettingsFrameLiveFeed, width=305, height=60, bg=SecondaryColor)
temp.place(x=10, y=10)
SecondaryElements.append(temp)
ttt = tk.Label(temp, text="Input Device:", bg=SecondaryColor, fg=ForeGround, font=(Global_font, 12))
ttt.place(x=10, rely=0.5, anchor='w')
SecondaryElements.append(ttt)
dropdown = tk.OptionMenu(temp, selected_cam, *cameras, command=lambda e: change_camera(selected_cam))
dropdown.config(width=20, bg=PrimaryColor, fg=ForeGround, bd=0, highlightthickness=0, activebackground=PrimaryColor, activeforeground=ForeGround, cursor="hand2")
dropdown.place(x=127, rely=0.5, anchor='w')
PrimaryElements.append(dropdown)

temp = tk.Frame(SettingsFrameLiveFeed, width=305, height=60, bg=SecondaryColor)
temp.place(x=10, y=80)
SecondaryElements.append(temp)
ttt = tk.Label(temp, text="Show Face Recognition:", bg=SecondaryColor, fg=ForeGround, font=(Global_font, 12))
ttt.place(x=10, rely=0.5, anchor='w')
SecondaryElements.append(ttt)

ShowButton = tk.Button(temp, text="", bg="#591919", command=showRecHandler, cursor="hand2", bd=0, highlightthickness=0, relief="flat", activebackground="#591919", height=2, width=11) 
if theme == "Light":
    ShowButton.config(bg='#d74848', activeforeground='#d74848')
ShowButton.place(rely=0.5, x=212, anchor='w')

CurrentFace = tk.Frame(SettingsFrameLiveFeed, width=305, height=85, bg=SecondaryColor)
CurrentFace.place(x=10, y=150)
SecondaryElements.append(CurrentFace)
ttt = tk.Label(CurrentFace, text="Detected Faces:", bg=SecondaryColor, fg=ForeGround, font=(f'{Global_font} bold', 12))
ttt.place(relx=0.5, y=5, anchor='n')
SecondaryElements.append(ttt)
FacesLabel = tk.Label(CurrentFace, text="", bg=SecondaryColor, fg=ForeGround, font=(f'{Global_font}', 10))
FacesLabel.place(relx=0.5, rely=0.4, anchor="n")
SecondaryElements.append(FacesLabel)

temp = tk.Frame(SettingsFrameLiveFeed, width=272, height=60, bg=SecondaryColor)
temp.place(x=325, y=10)
SecondaryElements.append(temp)
ttt = tk.Label(temp, text="Recognition Sensitivity:", bg=SecondaryColor, fg=ForeGround, font=(Global_font, 12))
ttt.place(x=10, rely=0.5, anchor='w')
SecondaryElements.append(ttt)
Threshold = 100
SensitivityEntry = tk.Entry(temp, width=5, justify="center", bg=PrimaryColor, fg=ForeGround, bd=0, font=(Global_font, 16), cursor="hand2")
SensitivityEntry.place(x=195, rely=0.5, anchor='w')
PrimaryElements.append(SensitivityEntry)
SensitivityEntry.insert(0, "100")
SensitivityEntry_var = tk.StringVar(value=SensitivityEntry.get())
SensitivityEntry.config(textvariable=SensitivityEntry_var)
SensitivityEntry_var.trace_add("write", update_threshold)


    

    


temp0 = tk.Frame(SettingsFrameLiveFeed, width=272, height=60, bg=SecondaryColor)
temp0.place(x=880, y=10, anchor='ne')
SecondaryElements.append(temp0)
ttt = tk.Label(temp0, text="Using Model:", bg=SecondaryColor, fg=ForeGround, font=(Global_font, 12))
ttt.place(x=10, rely=0.5, anchor='w')
SecondaryElements.append(ttt)
models = [f for f in os.listdir("Models") if f.endswith(".yml")]
selected_model = tk.StringVar(root)
for model in models:
    if model == currentmodel:
        selected_model.set(model)
        break
dropdownModel = tk.OptionMenu(temp0, selected_model, *models, command=lambda e:change_model(selected_model))
dropdownModel.config(width=17, bg=PrimaryColor, fg=ForeGround, bd=0, highlightthickness=0, activebackground=PrimaryColor, activeforeground=ForeGround, cursor="hand2")
dropdownModel.place(x=120, rely=0.5, anchor='w')
PrimaryElements.append(dropdownModel)



temp = tk.Frame(SettingsFrameLiveFeed, width=555, height=155, bg=SecondaryColor)
temp.place(x=325, y=80)
SecondaryElements.append(temp)
ttt = tk.Label(temp, text="C    O    N    S    O    L    E", bg=SecondaryColor, fg=ForeGround, font=(f'{Global_font}', 12))
ttt.place(relx=0.5, y=2, anchor='n')
SecondaryElements.append(ttt)
Console = tk.Text(temp, width=79, height=8, font=("Courier", 9), relief="flat", bg=SecondaryColor, fg=ForeGround)
Console.tag_configure("spotted", background="#265919")
Console.tag_configure("lost", background="#591919")
Console.config(state="disabled")
Console.place(x=0,y=30)
SecondaryElements.append(Console)








DatasetStep = 1

def update_Dataset_step(step, data=None, step2page=0):
    global temp
    global OutputWindowDataset
    global showRec
    global WebcamStart
    global AddPersonButton
    global BackWeb
    global ContinueWebButton
    global NameEntry
    global NameLabel
    global BccButton

    
    
    def DatasetUpload():
        def sub_process():
            path = filedialog.askdirectory()
            DirEntry.config(state="normal")
            DirEntry.delete(0, tk.END)
            DirEntry.insert(0, path)
            DirEntry.config(state="readonly") 

            if path:
                NextButton.config(text="Loading...")
                person_folders = [folder for folder in os.listdir(path) if os.path.isdir(os.path.join(path, folder))]

                face_detector = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')


                for person_id, person_folder in enumerate(person_folders, start=1):
                    person_path = os.path.join(path, person_folder)
                    insertNames(person_folder, person_id)

                    images = [img for img in os.listdir(person_path) if img.endswith('.jpg')]
                    
                    for img_index, image_name in enumerate(images, start=1):
                        image_path = os.path.join(person_path, image_name)
                        img = cv2.imread(image_path)
                        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                        faces = face_detector.detectMultiScale(gray, 1.3, 5)
                        for (x, y, w, h) in faces:
                            cropped_face = gray[y:y + h, x:x + w]
                            new_filename = f'User.{person_id}.{img_index}.jpg'
                            new_filepath = os.path.join("DatasetSetup/", new_filename)
                            cv2.imwrite(new_filepath, cropped_face)
                            

                        
                NextButton.config(state="normal", text="N  E  X  T")
                
        threading.Thread(target=sub_process).start()


    for widget in TrainFrame.winfo_children():
        widget.destroy()


    def on_scroll(event):
        try:
            cnv.yview_scroll(-1 * (event.delta // 120), "units")
        except:
            pass

    def update_scroll_region(event):
        try:
            cnv.configure(scrollregion=cnv.bbox("all"))
        except:
            pass



    def StartTrainer(name):
        recognizer = cv2.face.LBPHFaceRecognizer_create()
        def getImagesAndLabels(path):
            try:
                imagePaths = [os.path.join(path, f) for f in os.listdir(path)]
                faceSamples = []
                ids = []
                for imagePath in imagePaths:
                    PIL_img = Image.open(imagePath).convert('L')
                    img_numpy = np.array(PIL_img, 'uint8')
                    id = int(os.path.split(imagePath)[-1].split(".")[1])
                    faces = detector.detectMultiScale(img_numpy)
                    for (x, y, w, h) in faces:
                        faceSamples.append(img_numpy[y:y+h, x:x+w])
                        ids.append(id)
                return faceSamples, ids
            except PermissionError as e:
                pass
            except Exception as e:
                pass

        def get_unique_filename(base_name):
            count = 1
            base_name_yml = base_name
            base_name_txt = base_name.replace(".yml", ".txt")

            while os.path.exists(base_name_yml) or os.path.exists(base_name_txt):
                base_name_yml = f"{base_name.rsplit('.', 1)[0]}{count}.yml"
                base_name_txt = f"{base_name.rsplit('.', 1)[0]}{count}.txt"
                count += 1

            return base_name_yml, base_name_txt

        def sub_process(name):
            global models
            LiveFeedButton.config(state="disabled")
            TrainButton.config(state="disabled")
            GatherButton.config(state="disabled")
            SettingsButton.config(state="disabled")
            BccButton.place_forget()
            StartButton.config(state="disabled")
            if not name:
                name = "model"
            filename = f'Models/{name}.yml'
            unique_filename = get_unique_filename(filename)
            print(unique_filename)
            shutil.move("DatasetSetup/IndexNames.txt", unique_filename[1])
            faces, ids = getImagesAndLabels("DatasetSetup")
            recognizer.train(faces, np.array(ids))
            
            
            recognizer.write(unique_filename[0])
            LiveFeedButton.config(state="normal")
            TrainButton.config(state="normal")
            GatherButton.config(state="normal")
            SettingsButton.config(state="normal")
            TitleTrainModel.config(text="Completed!", fg="green")
            models = [f for f in os.listdir("Models") if f.endswith(".yml")]
            update_models()

            StartButton.config(text="Exit",state="normal", command=lambda:update_Dataset_step(1))


        threading.Thread(target=sub_process, args=(name,)).start()


            
    
    if step == 1:
        os.makedirs("dataset", exist_ok=True)
        if step2page==0:
            if os.path.exists("DatasetSetup"):
                shutil.rmtree("DatasetSetup")
            os.makedirs("DatasetSetup")

            ttt = tk.Label(TrainFrame, text="Choose an Option:", font=(Global_font, 30), bg=PrimaryColor, fg=ForeGround)
            ttt.place(relx=0.5, rely=0.2, anchor="n")
            PrimaryElements.append(ttt)

            ttt = CustomButton(TrainFrame, text="Webcam Input", command=lambda: update_Dataset_step(1, None, 1))
            ttt.place(relx=0.5, rely=0.45, anchor='n')
            SecondaryElements.append(ttt)
            ttt = CustomButton(TrainFrame, text="Photo Folder", command=lambda: update_Dataset_step(1, None, 2))
            ttt.place(relx=0.5, rely=0.6, anchor='n')
            SecondaryElements.append(ttt)





            ttt = tk.Label(TrainFrame, text="1", bg=PrimaryColor, fg=ForeGround, font=(f"{Global_font} bold", 20))
            ttt.place(x=5, y=745, anchor='sw')
            PrimaryElements.append(ttt)
        else:
            if step2page == 1:
                BackWeb = tk.Button(TrainFrame, text="<", command=lambda:update_Dataset_step(1, data), bg=PrimaryColor, fg=ForeGround, relief="flat", font=("Arial bold", 25),activebackground=PrimaryColor, activeforeground=SecondaryColor, bd=0, highlightthickness=0)
                BackWeb.place(x=-5, y=-5)
                PrimaryElements.append(BackWeb)
                ttt = tk.Label(TrainFrame, text="2", bg=PrimaryColor, fg=ForeGround, font=(f"{Global_font} bold", 20))
                ttt.place(x=5, y=745, anchor='sw')
                PrimaryElements.append(ttt)
                ttt = tk.Label(TrainFrame, text="Choose Webcam:", bg=PrimaryColor, fg=ForeGround, font=(Global_font, 30))
                ttt.place(relx=0.5, rely=0.065, anchor="n")
                PrimaryElements.append(ttt)

                ttt = tk.Label(TrainFrame, text="Webcam:", font=(Global_font, 12), bg=PrimaryColor, fg=ForeGround)
                ttt.place(x=720, y=8, anchor='ne')
                PrimaryElements.append(ttt)
                dropdown = tk.OptionMenu(TrainFrame, selected_cam, *cameras, command=lambda e: change_camera(selected_cam))
                dropdown.config(width=20, bg=SecondaryColor, fg=ForeGround, bd=0, highlightthickness=0, activebackground=SecondaryColor, activeforeground=ForeGround, cursor="hand2")
                dropdown.place(x=885, y=10, anchor='ne')
                SecondaryElements.append(dropdown)

                OutputWindowDataset = tk.Label(TrainFrame, borderwidth=0, highlightthickness=0)
                OutputWindowDataset.place(x=0,y=50)

                ttt = tk.Label(TrainFrame, text="Press 'START' and slowly move your head in a circular motion to capture all parts of your face.", font=(Global_font, 12), fg=ForeGround, bg=PrimaryColor)
                ttt.place(relx=0.5, y=575, anchor='n')
                PrimaryElements.append(ttt)

                WebcamStart = CustomButton(TrainFrame, text="S T A R T", command=lambda:craftingImages(NameEntry.get(), startOver=True))
                WebcamStart.place(x=WIDTH-200-10-20, y=625, anchor='ne')
                SecondaryElements.append(WebcamStart)
                
                NameLabel = tk.Label(TrainFrame, text="Name:", font=(Global_font, 30), bg=PrimaryColor, fg=ForeGround)
                NameLabel.place(x=20, y=660, anchor='w')
                PrimaryElements.append(NameLabel)
                NameEntry = tk.Entry(TrainFrame, width=12, justify="center", bg=SecondaryColor, fg=ForeGround, bd=0, font=(Global_font, 20), cursor="hand2")
                NameEntry.place(x=170, y=665, anchor='w')
                SecondaryElements.append(NameEntry)


                AddPersonButton = CustomButton(TrainFrame, text="Add Person?", width=13, command=lambda:AddPerson())
                SecondaryElements.append(AddPersonButton)
                ContinueWebButton = CustomButton(TrainFrame, text="Continue",width=13, command=lambda:update_Dataset_step(2, step2page=step2page))
                SecondaryElements.append(ContinueWebButton)
                
                

            elif step2page == 2:
                if os.path.exists("DatasetSetup"):
                    shutil.rmtree("DatasetSetup")
                os.makedirs("DatasetSetup")
                ttt = tk.Label(TrainFrame, text="2", bg=PrimaryColor, fg=ForeGround, font=(f"{Global_font} bold", 20))
                ttt.place(x=5, y=745, anchor='sw')
                PrimaryElements.append(ttt)
                ttt = tk.Label(TrainFrame, text="Choose Dataset Folder:", bg=PrimaryColor, fg=ForeGround, font=(Global_font, 30))
                ttt.place(relx=0.5, rely=0.065, anchor="n")
                PrimaryElements.append(ttt)
                temp = tk.PhotoImage(file='Assets/Upload.png')
                OpenTrainFolder = tk.Button(TrainFrame, image=temp, bg=SecondaryColor, relief="flat", 
                                            activebackground=PrimaryColor, bd=0, highlightthickness=0, 
                                            command=DatasetUpload, cursor="hand2")
                OpenTrainFolder.place(x=850, rely=0.4675, anchor="e")
                SecondaryElements.append(OpenTrainFolder)

                t = tk.Frame(TrainFrame, width=400, height=400, bg=SecondaryColor)
                t.place(x=50, rely=0.5, anchor="w")
                SecondaryElements.append(t)
                
                oo = tk.Frame(t, width=390, height=390, bg=PrimaryColor)
                oo.place(relx=0.5, rely=0.5, anchor="center")
                PrimaryElements.append(oo)

                p = tk.Frame(t, width=400, height=50, bg=SecondaryColor)
                p.place(x=0, y=0)
                SecondaryElements.append(p)
                ttt = tk.Label(p, text="Dataset Folder Strcture:", font=(Global_font, 17), bg=SecondaryColor, fg=ForeGround)
                ttt.place(x=5, y=5)
                SecondaryElements.append(ttt)

                ttt = tk.Label(oo, text="dataset/\n\tperson00/\n\t\timg00.jpg\n\t\timg01.jpg\n\t\t...\n\tperson01/\n\t\timg00.jpg\n\t\timg01.jpg\n\t\t...\n\tperson02/\n\t\timg00.jpg\n\t\timg01.jpg\n\t\t...\n\t...", font=(Global_font, 14), bg=PrimaryColor, fg=ForeGround)
                ttt.place(x=-65, y=65)
                PrimaryElements.append(ttt)
                DirEntry = tk.Entry(TrainFrame, width=23, justify="center", bg=SecondaryColor, fg=ForeGround, bd=0, font=(Global_font, 20), state="readonly", readonlybackground=SecondaryColor)
                DirEntry.place(x=848, rely=0.742, anchor='e')
                SecondaryElements.append(DirEntry)
                NextButton = CustomButton(TrainFrame, text="N  E  X  T", state="disabled", command=lambda: update_Dataset_step(2, step2page=step2page))
                NextButton.place(relx=0.5, rely=0.85, anchor='n')
                SecondaryElements.append(NextButton)
                ttt = tk.Button(TrainFrame, text="<", command=lambda:update_Dataset_step(1), bg=PrimaryColor, fg=ForeGround, relief="flat", font=("Arial bold", 25),activebackground=PrimaryColor, activeforeground=SecondaryColor, bd=0, highlightthickness=0)
                ttt.place(x=-5, y=-5)
                PrimaryElements.append(ttt)


            elif step2page == 3:
                ttt = tk.Label(TrainFrame, text="2", bg=PrimaryColor, fg=ForeGround, font=(f"{Global_font} bold", 20))
                ttt.place(x=5, y=745, anchor='sw')
                PrimaryElements.append(ttt)
                ttt = tk.Label(TrainFrame, text="Choose Video File:", bg=PrimaryColor, fg=ForeGround, font=(Global_font, 30))
                ttt.place(relx=0.5, rely=0.065, anchor="n")
                PrimaryElements.append(ttt)
                temp = tk.PhotoImage(file='Assets/Upload.png')
                OpenTrainFolder = tk.Button(TrainFrame, image=temp, bg=SecondaryColor, relief="flat", 
                                            activebackground=PrimaryColor, bd=0, highlightthickness=0, 
                                            command=DatasetUpload)
                OpenTrainFolder.place(relx=0.5, rely=0.4, anchor="center")
                SecondaryElements.append(OpenTrainFolder)
                DirEntry = tk.Entry(TrainFrame)
                DirEntry.place(relx=0.5, rely=0.7, anchor='n')
                NextButton = tk.Button(TrainFrame, text="NEXT", state="disabled", command=lambda: update_Dataset_step(3, DirEntry.get(), step2page=step2page))
                NextButton.place(relx=0.5, rely=0.9, anchor='n')
                BccButton = tk.Button(TrainFrame, text="<", command=lambda:update_Dataset_step(1), bg=PrimaryColor, fg=ForeGround, relief="flat", font=("Arial bold", 25),activebackground=PrimaryColor, activeforeground=SecondaryColor, bd=0, highlightthickness=0)
                BccButton.place(x=-5, y=-5)
                PrimaryElements.append(BccButton)




    elif step == 2:
        ttt = tk.Label(TrainFrame, text="Preview Dataset", font=(Global_font, 30), bg=PrimaryColor, fg=ForeGround)
        ttt.place(x=10, y=10)
        PrimaryElements.append(ttt)
    
        global cnv
        cnv = tk.Canvas(TrainFrame, width=870, height=550, bg=SecondaryColor, bd=0, highlightthickness=0)
        cnv.place(relx=0.5, y=80, anchor="n")
        SecondaryElements.append(cnv)
        
        frm = tk.Frame(cnv, width=870, height=550, bg=SecondaryColor)
        SecondaryElements.append(frm)
        scroll_window = cnv.create_window((0, 0), window=frm, anchor="nw")

        cnv.bind_all("<MouseWheel>", on_scroll)
        frm.bind("<Configure>", update_scroll_region)

        frm.image_list = []

        row, col = 0, 0
        for root, dirs, files in os.walk("DatasetSetup"):
            for file in files:
                if file.endswith(".jpg"):
                    img_path = os.path.join(root, file)
                    img = Image.open(img_path).resize((170, 170))
                    img_tk = ImageTk.PhotoImage(img)
                    frm.image_list.append(img_tk)

                    label = tk.Label(frm, image=img_tk, bd=0, highlightthickness=0)
                    label.grid(row=row, column=col, padx=2, pady=2)

                    col += 1
                    if col >= 5:
                        col = 0
                        row += 1

        frm.bind("<Configure>", update_scroll_region)



        ttt = CustomButton(TrainFrame, text="Retry", width=13, font=(Global_font, 20), command=lambda:update_Dataset_step(1, None, step2page=step2page))
        ttt.place(x=WIDTH-200-10-270, y=650, anchor='ne')
        SecondaryElements.append(ttt)
        ttt = CustomButton(TrainFrame, text="Continue",width=13, font=(Global_font, 20), command=lambda:update_Dataset_step(3, None, step2page=step2page))
        ttt.place(x=WIDTH-200-10-50, y=650, anchor='ne')
        SecondaryElements.append(ttt)
        ttt = CustomButton(TrainFrame, text="Exit",width=6, font=(Global_font, 20), command=lambda:update_Dataset_step(1))
        ttt.place(x=50, y=650, anchor='nw')
        SecondaryElements.append(ttt)
        ttt = tk.Label(TrainFrame, text="3", bg=PrimaryColor, fg=ForeGround, font=(f"{Global_font} bold", 20))
        ttt.place(x=5, y=745, anchor='sw')
        PrimaryElements.append(ttt)
        

            


    elif step == 3:
        TitleTrainModel = tk.Label(TrainFrame, text="Train Model", bg=PrimaryColor, fg=ForeGround, font=(Global_font,60))
        TitleTrainModel.place(relx=0.5, rely=0.2, anchor="center")
        PrimaryElements.append(TitleTrainModel)
        StartButton = CustomButton(TrainFrame, text="Start Training", font=(Global_font, 40), width=25, command=lambda:StartTrainer(Name1Entry.get()))
        StartButton.place(relx=0.5, rely=0.75, anchor='center')
        SecondaryElements.append(StartButton)
        ttt = tk.Label(TrainFrame, text="Model Name:", bg=PrimaryColor, fg=ForeGround, font=(Global_font,20))
        ttt.place(relx=0.5, rely=0.42, anchor="center")
        PrimaryElements.append(ttt)
        Name1Entry = tk.Entry(TrainFrame, width=20, justify="center", bg=SecondaryColor, fg=ForeGround, bd=0, font=(Global_font, 40), cursor="hand2")
        Name1Entry.place(relx=0.5, rely=0.5,anchor="center")
        SecondaryElements.append(Name1Entry)
        BccButton = tk.Button(TrainFrame, text="<", command=lambda:update_Dataset_step(2, None, step2page=step2page), bg=PrimaryColor, fg=ForeGround, relief="flat", font=("Arial bold", 25),activebackground=PrimaryColor, activeforeground=SecondaryColor, bd=0, highlightthickness=0)
        BccButton.place(x=-5, y=-5)
        PrimaryElements.append(BccButton)
        ttt = tk.Label(TrainFrame, text="4", bg=PrimaryColor, fg=ForeGround, font=(f"{Global_font} bold", 20))
        ttt.place(x=5, y=745, anchor='sw')
        PrimaryElements.append(ttt)
    
    TrainFrame.update()


temp = tk.Frame(SettingsFrame, width=880, height=200, background=SecondaryColor)
temp.place(relx=0.5, y=5, anchor='n')
SecondaryElements.append(temp)
temp1 = tk.Frame(temp, width=870, height=190, background=PrimaryColor)
temp1.place(relx=0.5, y=5, anchor='n')
PrimaryElements.append(temp1)
temp = tk.Frame(temp1, width=870, height=55, background=SecondaryColor)
temp.place(relx=0.5, y=0, anchor='n')
SecondaryElements.append(temp)
ttt = tk.Label(temp, text="Apperance", font=(f"{Global_font} bold", 27), bg=SecondaryColor, fg=ForeGround)
ttt.place(relx=0.5, y=0, anchor='n')
SecondaryElements.append(ttt)
ttt = tk.Label(temp1, text="Software Theme:", font=(Global_font, 20), bg=PrimaryColor, fg=ForeGround)
ttt.place(relx=0.4, y=70, anchor='ne')
PrimaryElements.append(ttt)

default_content = """theme=Dark
font=Century Gothic
output=output.txt"""
if not os.path.exists("var.txt"):
    with open("var.txt", "w") as file:
        file.write(default_content)




if theme=="Light":
        CloseButton.config(bg="#d74848")
        ShowButton.config(bg="#d74848", activebackground="#d74848") 
        Console.tag_configure("spotted", background="#34e086")
        Console.tag_configure("lost", background="#d74848")
        ShowButton.update_idletasks()
        Logo = tk.PhotoImage(file="Assets/logoLight.png")
        LogoSpaceLabel.config(image=Logo)
elif theme=="Dark":
    CloseButton.config(bg="#591919")
    ShowButton.config(bg="#591919", activebackground="#591919")
    Console.tag_configure("spotted", background="#265919")
    Console.tag_configure("lost", background="#591919")
    ShowButton.update_idletasks()
    Logo = tk.PhotoImage(file="Assets/logo.png")
    LogoSpaceLabel.config(image=Logo)


selected_theme = tk.StringVar(value=get_theme())
dropdownLightDark = tk.OptionMenu(temp1,selected_theme, *("Dark", "Light"), command=lambda e: change_theme(selected_theme))
dropdownLightDark.config(width=20, bg=SecondaryColor, fg=ForeGround, bd=0, highlightthickness=0, activebackground=SecondaryColor, activeforeground=ForeGround, cursor="hand2", font=(Global_font, 20))
dropdownLightDark.place(relx=0.45, y=70, anchor='nw')
SecondaryElements.append(dropdownLightDark)





ttt = tk.Label(temp1, text="Software Font:", font=(Global_font, 20), bg=PrimaryColor, fg=ForeGround)
ttt.place(relx=0.4, y=130, anchor='ne')
PrimaryElements.append(ttt)


selected_font = tk.StringVar(value=get_font())
dropdownFont = tk.OptionMenu(temp1,selected_font, *("Century Gothic", "Helvetica", "Arial", "Trebuchet MS"), command=lambda e: change_font(selected_font))
dropdownFont.config(width=20, bg=SecondaryColor, fg=ForeGround, bd=0, highlightthickness=0, activebackground=SecondaryColor, activeforeground=ForeGround, cursor="hand2", font=(Global_font, 20))
dropdownFont.place(relx=0.45, y=130, anchor='nw')
SecondaryElements.append(dropdownFont)



temp = tk.Frame(SettingsFrame, width=880, height=150, background=SecondaryColor)
temp.place(relx=0.5, y=210, anchor='n')
SecondaryElements.append(temp)
temp1 = tk.Frame(temp, width=870, height=140, background=PrimaryColor)
temp1.place(relx=0.5, y=5, anchor='n')
PrimaryElements.append(temp1)
temp = tk.Frame(temp1, width=870, height=55, background=SecondaryColor)
temp.place(relx=0.5, y=0, anchor='n')
SecondaryElements.append(temp)
ttt = tk.Label(temp, text="Output", font=(f"{Global_font} bold", 27), bg=SecondaryColor, fg=ForeGround)
ttt.place(relx=0.5, y=0, anchor='n')
SecondaryElements.append(ttt)
ttt = tk.Label(temp1, text="Output Folder:", font=(Global_font, 20), bg=PrimaryColor, fg=ForeGround)
ttt.place(relx=0.29, y=75, anchor='ne')
PrimaryElements.append(ttt)


    

oten = tk.Entry(temp1, font=(Global_font, 20),bg=SecondaryColor, fg=ForeGround, bd=0, highlightthickness=0, width=28)
oten.place(relx=0.34, y=80, anchor='nw')
SecondaryElements.append(oten)

oten.insert(tk.END, get_output())
ttt = tk.Button(temp1, text="...", font=(Global_font, 14), command=SetOutputFolder,bg=SecondaryColor, fg=ForeGround, bd=0, highlightthickness=0, activebackground=SecondaryColor, activeforeground=ForeGround)
ttt.place(x=695+31, y=80, anchor='nw')
SecondaryElements.append(ttt)
ConfirmOutputButton = tk.Button(temp1, text="✓", font=(Global_font, 14), command=ApplyOutputFolder,bg=SecondaryColor, fg=ForeGround, bd=0, highlightthickness=0, activebackground=SecondaryColor, activeforeground=ForeGround)
ConfirmOutputButton.place(x=730+30, y=80, anchor='nw')
SecondaryElements.append(ConfirmOutputButton)



temp = tk.Frame(SettingsFrame, width=880, height=380, background=SecondaryColor)
temp.place(relx=0.5, y=365, anchor='n')
SecondaryElements.append(temp)
temp1 = tk.Frame(temp, width=870, height=370, background=PrimaryColor)
temp1.place(relx=0.5, y=5, anchor='n')
PrimaryElements.append(temp1)
temp = tk.Frame(temp1, width=870, height=55, background=SecondaryColor)
temp.place(relx=0.5, y=0, anchor='n')
SecondaryElements.append(temp)
ttt = tk.Label(temp, text="License", font=(f"{Global_font} bold", 27), bg=SecondaryColor, fg=ForeGround)
ttt.place(relx=0.5, y=0, anchor='n')
SecondaryElements.append(ttt)

l = tk.Text(temp1, bd=0, highlightthickness=0, bg=SecondaryColor, fg=ForeGround, width=107, height=19, wrap='word')
SecondaryElements.append(l)
l.tag_configure('indent', lmargin1=20, lmargin2=20)
l.insert("1.0", """Apache License
Version 2.0, January 2004
http://www.apache.org/licenses/

TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION

1. Definitions.

"License" shall mean the terms and conditions for use, reproduction, and distribution as defined by Sections 1 through 9 of this document.

"Licensor" shall mean the copyright owner or entity authorized by the copyright owner that is granting the License.

"Legal Entity" shall mean the union of the acting entity and all other entities that control, are controlled by, or are under common control with that entity.

"You" (or "Your") shall mean an individual or Legal Entity exercising permissions granted by this License.

"Source" form shall mean the preferred form for making modifications, including but not limited to software source code, documentation, and configuration files.

"Object" form shall mean any form resulting from mechanical transformation or translation of a Source form, including but not limited to compiled object code, generated documentation, and conversions to other media types.

2. Grant of Copyright License.
Each Contributor grants to You a perpetual, worldwide, non-exclusive, royalty-free, irrevocable copyright license to reproduce, modify, distribute, and sublicense the Work and Derivative Works.

3. Grant of Patent License.
Each Contributor grants to You a perpetual, worldwide, non-exclusive, royalty-free, irrevocable patent license to make, use, and sell the Work.

4. Redistribution.
You may reproduce and distribute copies of the Work under the following conditions:
- Provide recipients with a copy of this License.
- State any modifications made to the original Work.
- Retain all copyright, patent, and attribution notices.

5. Trademarks.
This License does not grant permission to use the trade names, trademarks, or service marks of the Licensor.

6. Disclaimer of Warranty.
The Work is provided "AS IS", without warranties or conditions of any kind.

7. Limitation of Liability.
Contributors shall not be liable for damages arising from the use of the Work.

END OF TERMS AND CONDITIONS
""", "indent")
l.config(state="disabled")
l.place(x=6, y=60)


ttt = tk.Frame(GatherFrame, width=880, height=740, bg=PrimaryColor)
ttt.place(relx=0.5, rely=0.5, anchor="center")
PrimaryElements.append(ttt)
temp1 = tk.Frame(ttt, width=870, height=730, bg=SecondaryColor)
temp1.place(relx=0.5, rely=0.5, anchor="center")


canvas = tk.Canvas(temp1, width=870, height=730, bg=PrimaryColor)
PrimaryElements.append(canvas)



scrollbar = tk.Scrollbar(temp1, orient="vertical", command=canvas.yview)
scrollable_frame = tk.Frame(canvas, bg=PrimaryColor)
PrimaryElements.append(scrollable_frame)

scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
canvas.configure(yscrollcommand=scrollbar.set)
scrollbar.place(relx=1.0, rely=0.5, anchor="e", relheight=1.0)
canvas.place(relx=0.5,rely=0.5, anchor="center")

canvas.bind_all("<MouseWheel>", on_mouse_wheel_Gather)

yml_files = [f for f in os.listdir("Models") if f.endswith('.yml')]

filesWidget = []

for i in yml_files:
    k = FileWidget(scrollable_frame, f"Models/{i}", "Models/")
    k.pack()
    filesWidget.append(k)



update_Dataset_step(1)



ShowLiveFeed(LiveFeedFrame, Panels)

update_frame(label1=OutputWindow, width=WIDTH-200-10, height=int((WIDTH-200-10) * 9 / 16))

root.mainloop()
