import os
import yaml
import json
import glob
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import Button, Entry, Label, messagebox, Checkbutton, BooleanVar, Scrollbar

class ImageAnnotationApp:
    def __init__(self, root, image_paths):
        self.root = root
        self.image_paths = image_paths
        self.rects = []
        self.bboxes = []
        self.annotations = {}

        # 最後のインデックスを保存するファイル
        self.index_file = 'last_index_2.json'

        # インデックスを読み込む
        self.current_image_index = self.load_last_index()

        # 拡大縮小の倍率
        self.scale_factor = 1.0

        # ウィンドウの初期サイズを設定 (幅 x 高さ)
        self.root.geometry("900x800")  # 例: 1200x800ピクセル

        # レイアウト設定
        self.root.grid_rowconfigure(1, weight=1)  # 画像表示部分の行（可変）
        self.root.grid_columnconfigure(1, weight=1)  # ウィンドウ全体の幅に合わせる

        # 現在の画像パス
        self.image_path_label = Label(root, text="", anchor='w')
        self.image_path_label.grid(row=0, column=0, sticky='w', padx=10)

        # カテゴリ名
        self.label_category = Label(root, text="カテゴリ名:")
        self.label_category.grid(row=0, column=1, sticky='e', padx=10)
        self.category_tag_entry = Entry(root)
        self.category_tag_entry.grid(row=0, column=2, sticky='ew', padx=10)

        # キャンバスの設定（スクロールバーは設定しない）
        self.canvas = tk.Canvas(root, cursor="cross")
        self.canvas.grid(row=1, column=0, columnspan=3, sticky='nsew')

        # ウィンドウ全体の列比率を設定
        self.root.grid_columnconfigure(0, weight=1)  # 取り消しボタン
        self.root.grid_columnconfigure(1, weight=1)  # チェックボックス
        self.root.grid_columnconfigure(2, weight=3)  # 画像遷移ボタン

        button_width = 15  # ここでボタンの幅を指定

        # 取り消しボタン
        self.undo_button = Button(root, text="Undo Last Box", command=self.undo_last_box, height=2, width=button_width)
        self.undo_button.grid(row=3, column=0, sticky='ew', padx=10, pady=10)

        # チェックボックス
        self.delete_var = BooleanVar()
        self.delete_checkbox = Checkbutton(root, text="Delete", var=self.delete_var, height=2, width=button_width)
        self.delete_checkbox.grid(row=3, column=1, sticky='ew', padx=10)

        # 画像遷移ボタン
        self.next_button = Button(root, text="Next Image", command=self.next_image, height=2, width=button_width)
        self.next_button.grid(row=3, column=2, sticky='ew', padx=10, pady=10)





        self.canvas.bind("<Motion>", self.on_motion)
        self.canvas.bind("<ButtonPress-1>", self.on_click)
        self.canvas.bind("<MouseWheel>", self.on_zoom)  # マウスホイールで拡大縮小
        self.start_x = None
        self.start_y = None
        self.mark = None
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.load_image(self.image_paths[self.current_image_index])

    # 画像のロードと初期化
    def load_image(self, image_path):
        self.canvas.delete("all")
        self.image = Image.open(image_path)
        self.resize_image_to_canvas()

    # 画像をキャンバスに合わせてリサイズ
    def resize_image_to_canvas(self):
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        # キャンバスに収まるように縮小するためのスケール計算
        width_ratio = canvas_width / self.image.width
        height_ratio = canvas_height / self.image.height
        self.scale_factor = min(width_ratio, height_ratio, 1.0)  # 1.0は拡大を防ぐため

        resized_image = self.image.resize(
            (int(self.image.width * self.scale_factor), int(self.image.height * self.scale_factor)),
            Image.LANCZOS
        )
        self.tk_image = ImageTk.PhotoImage(resized_image)

        # 画像の表示とスクロール領域の設定
        self.canvas_image = self.canvas.create_image(0, 0, anchor="nw", image=self.tk_image)
        self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))

        # カテゴリ情報を表示
        self.image_path_label.config(text=f'{self.current_image_index}枚目：{self.image_paths[self.current_image_index]}')
        self.category_tag_entry.delete(0, tk.END)
        # 画像の3個上のフォルダ名を取得
        parent_folder_name = os.path.basename(os.path.dirname(os.path.dirname(os.path.dirname(self.image_paths[self.current_image_index]))))
        self.category_tag_entry.insert(0, parent_folder_name)


    # 最後のインデックスを読み込む
    def load_last_index(self):
        if os.path.exists(self.index_file):
            with open(self.index_file, 'r') as f:
                return json.load(f).get('index', 0)
        return 0

    # 最後のインデックスを保存する
    def save_last_index(self):
        with open(self.index_file, 'w') as f:
            json.dump({'index': self.current_image_index}, f)

    # 拡大縮小の処理
    def on_zoom(self, event):
        if event.delta > 0:  # ズームイン
            self.scale_factor *= 1.1
        else:  # ズームアウト
            self.scale_factor *= 0.9
        self.resize_image_to_canvas()

    # カーソルをトラッキング，補助線を描画
    def on_motion(self, event):
        x, y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        self.canvas.delete("crosshair")
        self.canvas.create_line(0, y, self.canvas.winfo_width(), y, fill="blue", tags="crosshair")
        self.canvas.create_line(x, 0, x, self.canvas.winfo_height(), fill="blue", tags="crosshair")

    # クリックでBBoxの描画範囲選択
    def on_click(self, event):
        raw_x, raw_y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        image_x, image_y = self.canvas.coords(self.canvas_image)
        image_width = self.tk_image.width()
        image_height = self.tk_image.height()

        x = max(image_x, min(raw_x, image_x + image_width - 1))
        y = max(image_y, min(raw_y, image_y + image_height - 1))

        if self.start_x is None and self.start_y is None:
            self.start_x, self.start_y = x, y
            self.mark = self.canvas.create_oval(self.start_x-5, self.start_y-5, self.start_x+5, self.start_y+5, fill="green")
        else:
            end_x = max(image_x, min(raw_x, image_x + image_width - 1))
            end_y = max(image_y, min(raw_y, image_y + image_height - 1))

            self.rect = self.canvas.create_rectangle(min(self.start_x, end_x),
                                                     min(self.start_y, end_y),
                                                     max(self.start_x, end_x),
                                                     max(self.start_y, end_y),
                                                     outline="red")
            self.rects.append(self.rect)

            # 画像が存在するフォルダ名をmodeに設定
            folder_name = os.path.basename(os.path.dirname(self.image_paths[self.current_image_index]))

            # BBoxを保存
            self.bboxes.append({
                "bbox": [min(self.start_x, end_x) / self.scale_factor,
                         min(self.start_y, end_y) / self.scale_factor,
                         max(self.start_x, end_x) / self.scale_factor,
                         max(self.start_y, end_y) / self.scale_factor],
                "mode": folder_name
            })

            self.canvas.delete(self.mark)
            self.start_x = None
            self.start_y = None
            self.mark = None

    # BBoxの取り消し
    def undo_last_box(self):
        if self.mark:
            self.canvas.delete(self.mark)
            self.start_x = None
            self.start_y = None
            self.mark = None
        elif self.rects:
            last_rect = self.rects.pop()
            self.canvas.delete(last_rect)
            if self.bboxes:
                self.bboxes.pop()

    # 次の画像へ
    def next_image(self):
        category_tag = self.category_tag_entry.get()
        if category_tag:
            self.annotations[self.image_paths[self.current_image_index]] = {
                "bboxes": self.bboxes,
                #"category": category_tag,
                "removal": self.delete_var.get()
            }
            self.current_image_index += 1
            self.save_last_index()  # インデックスを保存
            if self.current_image_index < len(self.image_paths):
                os.makedirs('annotations', exist_ok=True)
                self.save_annotations('annotations/output_temp.json')
                self.scale_factor = 1.0  # 次の画像に進むときに拡大縮小をリセット
                self.load_image(self.image_paths[self.current_image_index])
            else:
                os.makedirs('annotations', exist_ok=True)
                self.save_annotations('annotations/output_last.json')
                self.root.destroy()
        else:
            messagebox.showwarning("Warning", "Please enter both category and anomaly tags before proceeding.")

    def on_close(self):
        self.save_last_index()  # インデックスを保存
        idx = 0
        os.makedirs('annotations', exist_ok=True)
        while os.path.exists(f'annotations/output_{idx}.json'):
            idx += 1
        self.save_annotations(f'annotations/output_{idx}.json')
        self.root.destroy()

    def save_annotations(self, json_path):
        with open(json_path, 'w') as f:
            json.dump(self.annotations, f, indent=4)

# HACK パスは環境に合わせて治す
# 無視するフォルダ名のリスト
ignore_folders = ['__template', 'ok', '__setting', '後で修正', 'test']
#G:/共有ドライブ/お菓子データセット/snacks/*/*/*/*.png 気になる写真をおく
path_list = sorted(glob.glob('G:/共有ドライブ/お菓子データセット/snacks/rice_crackers/tamagorakkasesnbei/crack/Image__2024-08-29__16-10-08.png'))
filtered_paths = [path for path in path_list if not any(ignored in path for ignored in ignore_folders)]
root = tk.Tk()
app = ImageAnnotationApp(root, filtered_paths)
root.mainloop()

