import os
import json
import glob
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import Button, Entry, Label, messagebox, Checkbutton, BooleanVar

class ImageAnnotationApp:
    def __init__(self, root, image_paths):
        self.root = root
        self.image_paths = image_paths
        self.rects = []
        self.bboxes = []
        self.annotations = {}
        self.index_file = 'last_index.json'  # 最後のインデックスを保存するファイル
        self.current_image_index = self.load_last_index()
        self.scale_factor = 1.0  # 拡大縮小の倍率

        # ウィンドウの初期設定
        self.root.geometry("900x800")
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(1, weight=1)

        # 現在の画像パス表示
        self.image_path_label = Label(root, text="", anchor='w')
        self.image_path_label.grid(row=0, column=0, sticky='w', padx=10)

        # カテゴリ名入力フィールド
        self.label_category = Label(root, text="カテゴリ名:")
        self.label_category.grid(row=0, column=1, sticky='e', padx=10)
        self.category_tag_entry = Entry(root)
        self.category_tag_entry.grid(row=0, column=2, sticky='ew', padx=10)

        # キャンバスの設定
        self.canvas = tk.Canvas(root, cursor="cross")
        self.canvas.grid(row=1, column=0, columnspan=3, sticky='nsew')

        # ウィンドウのレイアウト設定
        button_width = 15
        self.undo_button = Button(root, text="Undo Last Box", command=self.undo_last_box, height=2, width=button_width)
        self.undo_button.grid(row=3, column=0, sticky='ew', padx=10, pady=10)

        self.delete_var = BooleanVar()
        self.delete_checkbox = Checkbutton(root, text="Delete", var=self.delete_var, height=2, width=button_width)
        self.delete_checkbox.grid(row=3, column=1, sticky='ew', padx=10)

        self.next_button = Button(root, text="Next Image", command=self.next_image, height=2, width=button_width)
        self.next_button.grid(row=3, column=2, sticky='ew', padx=10, pady=10)

        # キャンバスイベントのバインド
        self.canvas.bind("<Motion>", self.on_motion)
        self.canvas.bind("<ButtonPress-1>", self.on_click)
        self.canvas.bind("<MouseWheel>", self.on_zoom)

        self.start_x = None
        self.start_y = None
        self.mark = None

        # ウィンドウを閉じる際の処理
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.load_image(self.image_paths[self.current_image_index])

    # 画像をロードしてキャンバスに表示
    def load_image(self, image_path):
        self.canvas.delete("all")
        self.image = Image.open(image_path)
        self.resize_image_to_canvas()

    # キャンバスに合わせて画像をリサイズ
    def resize_image_to_canvas(self):
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        width_ratio = canvas_width / self.image.width
        height_ratio = canvas_height / self.image.height
        self.scale_factor = min(width_ratio, height_ratio, 1.0)

        resized_image = self.image.resize(
            (int(self.image.width * self.scale_factor), int(self.image.height * self.scale_factor)),
            Image.LANCZOS
        )
        self.tk_image = ImageTk.PhotoImage(resized_image)
        self.canvas_image = self.canvas.create_image(0, 0, anchor="nw", image=self.tk_image)
        self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))

        # 画像パスとカテゴリの初期化
        self.image_path_label.config(text=f'{self.current_image_index}枚目：{self.image_paths[self.current_image_index]}')
        self.category_tag_entry.delete(0, tk.END)
        parent_folder_name = os.path.basename(os.path.dirname(os.path.dirname(os.path.dirname(self.image_paths[self.current_image_index]))))
        self.category_tag_entry.insert(0, parent_folder_name)

    # 最後のインデックスをロード
    def load_last_index(self):
        if os.path.exists(self.index_file):
            with open(self.index_file, 'r') as f:
                return json.load(f).get('index', 0)
        return 0

    # インデックスを保存
    def save_last_index(self):
        with open(self.index_file, 'w') as f:
            json.dump({'index': self.current_image_index}, f)

    # ズームイン・アウトの処理
    def on_zoom(self, event):
        self.scale_factor *= 1.1 if event.delta > 0 else 0.9
        self.resize_image_to_canvas()

    # カーソルの位置をトラッキングし、補助線を表示
    def on_motion(self, event):
        x, y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        self.canvas.delete("crosshair")
        self.canvas.create_line(0, y, self.canvas.winfo_width(), y, fill="blue", tags="crosshair")
        self.canvas.create_line(x, 0, x, self.canvas.winfo_height(), fill="blue", tags="crosshair")

    # クリックしてバウンディングボックスを描画
    def on_click(self, event):
        raw_x, raw_y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        image_x, image_y = self.canvas.coords(self.canvas_image)
        image_width, image_height = self.tk_image.width(), self.tk_image.height()

        x = max(image_x, min(raw_x, image_x + image_width - 1))
        y = max(image_y, min(raw_y, image_y + image_height - 1))

        if self.start_x is None and self.start_y is None:
            self.start_x, self.start_y = x, y
            self.mark = self.canvas.create_oval(self.start_x-5, self.start_y-5, self.start_x+5, self.start_y+5, fill="green")
        else:
            end_x, end_y = max(image_x, min(raw_x, image_x + image_width - 1)), max(image_y, min(raw_y, image_y + image_height - 1))
            self.rect = self.canvas.create_rectangle(min(self.start_x, end_x), min(self.start_y, end_y), max(self.start_x, end_x), max(self.start_y, end_y), outline="red")
            self.rects.append(self.rect)

            folder_name = os.path.basename(os.path.dirname(self.image_paths[self.current_image_index]))
            self.bboxes.append({
                "bbox": [min(self.start_x, end_x) / self.scale_factor, min(self.start_y, end_y) / self.scale_factor, max(self.start_x, end_x) / self.scale_factor, max(self.start_y, end_y) / self.scale_factor],
                "mode": folder_name
            })

            self.canvas.delete(self.mark)
            self.start_x, self.start_y, self.mark = None, None, None

    # 最後のバウンディングボックスを取り消し
    def undo_last_box(self):
        if self.mark:
            self.canvas.delete(self.mark)
            self.start_x, self.start_y, self.mark = None, None, None
        elif self.rects:
            last_rect = self.rects.pop()
            self.canvas.delete(last_rect)
            if self.bboxes:
                self.bboxes.pop()

    # 次の画像へ移動
    def next_image(self):
        category_tag = self.category_tag_entry.get()
        if category_tag:
            self.annotations[self.image_paths[self.current_image_index]] = {
                "bboxes": self.bboxes,
                "removal": self.delete_var.get()
            }
            self.current_image_index += 1
            self.save_last_index()

            if self.current_image_index < len(self.image_paths):
                self.bboxes = []  # バウンディングボックスのリセット
                self.scale_factor = 1.0
                self.load_image(self.image_paths[self.current_image_index])
            else:
                self.root.destroy()
        else:
            messagebox.showwarning("Warning", "カテゴリ名を入力してください。")

    # アプリ終了時にインデックスとアノテーションを保存
    def on_close(self):
        self.save_last_index()
        idx = 0
        while os.path.exists(f'annotations/output_{idx}.json'):
            idx += 1
        self.save_annotations(f'annotations/output_{idx}.json')
        self.root.destroy()

    # アノテーションを保存
    def save_annotations(self, json_path):
        with open(json_path, 'w') as f:
            json.dump(self.annotations, f, indent=4)

# 画像パスのフィルタリング
ignore_folders = ['OK' ,' __templete', 'test', '後で修正', '__setting']
path_list = sorted(glob.glob('G:/共有ドライブ/お菓子データセット/snacks/cookie/*/*/*.png'))
filtered_paths = [path for path in path_list if not any(ignored in path for ignored in ignore_folders)]

# アプリケーションの起動
root = tk.Tk()
app = ImageAnnotationApp(root, filtered_paths)
root.mainloop()
