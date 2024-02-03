import os
import yaml
import json
import glob
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import Button, Entry, Label, messagebox, Toplevel, Checkbutton, BooleanVar

class ImageAnnotationApp:
    def __init__(self, root, image_paths, anomaly_mode_path='anomalies.yaml'):
        self.root = root
        self.image_paths = image_paths
        self.anomaly_mode_path = anomaly_mode_path
        self.rects = []
        # HACK 途中再開の場合は以下の値を変更，前回のshellに表示された最後の値を与えればよい
        self.current_image_index = 1222
        self.annotations = {}

        # レイアウト
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(1, weight=1)

        # 現在の画像パス
        self.image_path_label = Label(root, text="", width=65)
        self.image_path_label.grid(row=0, column=0, sticky='w')

        # 区切り線を表示するラベル
        self.separator_label = Label(root, text="------------------------")
        self.separator_label.grid(row=1, column=0, sticky='w')

        # カテゴリ
        self.label_category = Label(root, text="カテゴリ名（必要があれば手打ちで修正）")
        self.label_category.grid(row=2, column=0, sticky='w')
        self.category_tag_entry = Entry(root)
        self.category_tag_entry.grid(row=3, column=0, sticky='ew')

        # 画像
        self.canvas = tk.Canvas(root, cursor="cross")
        self.canvas.grid(row=4, column=0, columnspan=2, ipady=15, sticky='nsew')

        # BBoxの補助線
        self.horizontal_line = self.canvas.create_line(0, 0, self.canvas.winfo_reqwidth(), 0, fill="blue")
        self.vertical_line = self.canvas.create_line(0, 0, 0, self.canvas.winfo_reqheight(), fill="blue")

        # 取り消し
        self.undo_button = Button(root, text="Undo Last Box", command=self.undo_last_box, height=2, width=20)
        self.undo_button.grid(row=5, column=0, sticky='w')

        # チェックボックス
        self.delete_var = BooleanVar()
        self.delete_checkbox = Checkbutton(root, text="Delete", var=self.delete_var)
        self.delete_checkbox.grid(row=5, column=0)

        # 画像遷移
        self.next_button = Button(root, text="Next Image", command=self.next_image, height=2, width=20)
        self.next_button.grid(row=5, column=0, sticky='e')

        self.canvas.bind("<Motion>", self.on_motion)
        self.canvas.bind("<ButtonPress-1>", self.on_click)
        self.start_x = None
        self.start_y = None
        self.mark = None
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.load_image(self.image_paths[self.current_image_index])

    # 画像のロードと初期化
    def load_image(self, image_path):
        self.canvas.delete(self.horizontal_line)
        self.canvas.delete(self.vertical_line)
        self.image = Image.open(image_path)
        # self.image = self.image.resize((224, 224), Image.ANTIALIAS)
        self.tk_image = ImageTk.PhotoImage(self.image)
        self.canvas_image = self.canvas.create_image(100, 20, anchor="nw", image=self.tk_image)
        self.canvas.bind("<ButtonPress-1>", self.on_click)
        self.anomaly_mode = None
        self.scope = None
        self.anomaly_location = None
        self.delete_var.set(False)
        self.bboxes = []
        for rect in self.rects:
            self.canvas.delete(rect)
        self.rects = []
        self.image_path_label.config(text=f'{self.current_image_index}枚目：{image_path}')
        print(self.current_image_index)
        self.category_tag_entry.delete(0, tk.END)
        # カテゴリ名はふり直さない場合が多いので，元のカテゴリをデフォで入力しておく．変更が必要な場合のみ手打ち（HACK Linuxの場合は\\を/に直す）
        self.category_tag_entry.insert(0, image_path.split('\\')[1])
        self.horizontal_line = self.canvas.create_line(0, 0, self.canvas.winfo_reqwidth(), 0, fill="blue")
        self.vertical_line = self.canvas.create_line(0, 0, 0, self.canvas.winfo_reqheight(), fill="blue")

    # カーソルをトラッキング，補助線を描画
    def on_motion(self, event):
        x, y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        self.canvas.coords(self.horizontal_line, 0, y, self.canvas.winfo_width(), y)
        self.canvas.coords(self.vertical_line, x, 0, x, self.canvas.winfo_height())

    # クリックでBBoxの描画範囲選択
    def on_click(self, event):
        # キャンバス上でのクリックされた座標を取得
        raw_x, raw_y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)

        # 画像の位置とサイズを取得（load_imageで設定したものを使用）
        image_x, image_y = self.canvas.coords(self.canvas_image)  # 画像の左上の座標
        image_width = self.tk_image.width()
        image_height = self.tk_image.height()

        # 座標を補正
        x = max(image_x, min(raw_x, image_x + image_width - 1))
        y = max(image_y, min(raw_y, image_y + image_height - 1))

        # 1回目のクリック位置を記録，マーカーを描画
        if self.start_x is None and self.start_y is None:
            self.start_x, self.start_y = x, y
            self.mark = self.canvas.create_oval(self.start_x-5, self.start_y-5, self.start_x+5, self.start_y+5, fill="green")
        # 2回目のクリックでBBoxを描画
        else:
            # 座標を補正
            end_x = max(image_x, min(raw_x, image_x + image_width - 1))
            end_y = max(image_y, min(raw_y, image_y + image_height - 1))

            # BBoxを描画
            self.rect = self.canvas.create_rectangle(min(self.start_x, end_x), 
                                                    min(self.start_y, end_y), 
                                                    max(self.start_x, end_x), 
                                                    max(self.start_y, end_y), 
                                                    outline="red")
            self.rects.append(self.rect)

            # タグ入力 -> 別ウィンドウ
            self.select_anomaly_category(self.anomaly_mode_path)
            if self.anomaly_mode and self.scope and self.anomaly_location:
                # タグが入力されるとBBoxの情報とタグを保存，224*224pixel用の値も保存
                self.bboxes.append({"bbox": [min(self.start_x, end_x)-100, min(self.start_y, end_y)-20, max(self.start_x, end_x)-100, max(self.start_y, end_y)-20], "mode": self.anomaly_mode, "scope": self.scope, "location": self.anomaly_location})
                # self.bboxes_corrected.append({"bbox": [float(round((min(self.start_x, end_x)-100)/256*224)), float(round((min(self.start_y, end_y)-20)/256*224)), float(round((max(self.start_x, end_x)-100)/256*224)), float(round((max(self.start_y, end_y)-20)/256*224))], "mode": self.anomaly_mode, "scope": self.scope, "location": self.anomaly_location})
            else:
                # タグ入力がキャンセルされた場合、BBoxを削除
                self.canvas.delete(self.rect)
                self.rects.pop()

            # 座標と印をリセット
            self.start_x = None
            self.start_y = None
            self.canvas.delete(self.mark)
    
    # BBoxの取り消し
    def undo_last_box(self):
        if self.mark:
            # マーク（最初のクリックの位置）を取り消す
            self.canvas.delete(self.mark)
            self.start_x = None
            self.start_y = None
            self.mark = None
        elif self.rects:
            # マークがなく，かつBBoxがあれば最後のBBoxを取り消す
            last_rect = self.rects.pop()
            self.canvas.delete(last_rect)
            if self.bboxes:
                self.bboxes.pop()

    # 次の画像へ
    def next_image(self):
        # カテゴリ名が入力されていれば次の画像へ進む
        category_tag = self.category_tag_entry.get()
        if category_tag:
            # jsonに格納する情報を保存
            self.annotations[self.image_paths[self.current_image_index]] = {
                "bboxes": self.bboxes,
                "category": category_tag,
                "removal": self.delete_var.get()
            }
            self.current_image_index += 1
            # 次の画像があれば表示，なければjsonに出力して終了
            if self.current_image_index < len(self.image_paths):
                os.makedirs('annotations', exist_ok=True)
                self.save_annotations('annotations/output_temp.json')
                self.load_image(self.image_paths[self.current_image_index])
            else:
                os.makedirs('annotations', exist_ok=True)
                self.save_annotations('annotations/output_last.json')
                self.root.destroy()
        else:
            messagebox.showwarning("Warning", "Please enter both category and anomaly tags before proceeding.")

    # ウィンドウが途中で閉じた場合，それまでの情報を新しいjsonに保存
    def on_close(self):
        idx = 0
        os.makedirs('annotations', exist_ok=True)
        while os.path.exists(f'annotations/output_{idx}.json'):
            idx += 1
        self.save_annotations(f'annotations/output_{idx}.json')
        self.root.destroy()

    # 別ウィンドウでBBoxのタグ選択
    def select_anomaly_category(self, yaml_file_path):
        new_window = Toplevel()
        new_window.title("Anomaly Tag Selector")

        # YAMLファイルからタグリストを読み込む
        def load_tags(yaml_file_path):
            with open(yaml_file_path, 'r') as file:
                anomalies_data = yaml.safe_load(file)
            return anomalies_data.get('anomalies', [])

        # ボタンが押された時
        def on_button_press():
            # テキストボックスの文字列を取得
            entered_text = text_entry.get().strip()
            entered_text.replace('product', '{product}')
            scope_text = scope_entry.get().strip()
            scope_text.replace('product', '{product}')
            loc_text = loc_entry.get().strip()
            loc_text.replace('product', '{product}')

            # 両方のリストボックスから何かが選択されている場合のみ処理を続ける
            if (entered_text or tag_listbox.curselection()) and (scope_text or scope_listbox.curselection()) and (loc_text or fixed_tag_listbox.curselection()):
                # テキストボックス優先
                if entered_text:
                    if entered_text not in tags:
                        tags.append(entered_text)
                        tag_listbox.insert(tk.END, entered_text)
                        update_yaml_file(yaml_file_path, tags)
                    self.anomaly_mode = entered_text
                else:
                    self.anomaly_mode = tag_listbox.get(tag_listbox.curselection())

                if scope_text:
                    self.scope = scope_text
                else:
                    if not scope_listbox.get(scope_listbox.curselection())=='This':
                        if scope_listbox.get(scope_listbox.curselection())=='center':
                            self.scope = 'The {product} in the ' + scope_listbox.get(scope_listbox.curselection())
                        self.scope = 'The {product} on the ' + scope_listbox.get(scope_listbox.curselection())
                    else:
                        self.scope = 'This {product}'

                if loc_text:
                    self.anomaly_location = loc_text
                else:
                    self.anomaly_location = fixed_tag_listbox.get(fixed_tag_listbox.curselection())

                print(f'scope: {self.scope}')
                print(f'location: {self.anomaly_location} of the ...')
                new_window.destroy()
            else:
                pass  # 両方のリストボックスからの選択がない場合、何もしない

        # YAMLファイルを更新
        def update_yaml_file(yaml_file_path, tags):
            anomalies_data = {'anomalies': tags}
            with open(yaml_file_path, 'w') as file:
                yaml.dump(anomalies_data, file)


        # 異常タグ用のリストボックス
        label_anomaly_mode = tk.Label(new_window, text="欠陥モード")
        label_anomaly_mode.grid(row=0, column=0, padx=10, pady=5)
        tag_listbox = tk.Listbox(new_window, exportselection=0)
        tag_listbox.grid(row=1, column=0, padx=10, pady=5)
        tag_listbox_scrollbar = tk.Scrollbar(new_window, orient="vertical", command=tag_listbox.yview)
        tag_listbox_scrollbar.grid(row=1, column=1, sticky='nsew', padx=(0, 10))
        tag_listbox['yscrollcommand'] = tag_listbox_scrollbar.set
        # 異常タグ用のテキストボックスの作成
        text_entry = tk.Entry(new_window, exportselection=0)
        text_entry.grid(row=2, column=0, padx=10, pady=5)

        # YAMLファイルからタグを読み込んでリストボックスに追加
        tags = load_tags(yaml_file_path)
        for tag in tags:
            tag_listbox.insert(tk.END, tag)


        # 対象物体選択用のリストボックス
        #  json作成時は The {product} on/in the {scope}を想定 -> The {product} on the right
        object_scope = tk.Label(new_window, text="画像中のどの位置にある製品か\n（単体の場合はThis）")
        object_scope.grid(row=0, column=2, padx=10, pady=5)
        scope_listbox = tk.Listbox(new_window, exportselection=0)
        scope_listbox.grid(row=1, column=2, padx=10, pady=5)
        for scopens in ['This', 'left', 'right', 'top', 'bottom', 'center', 'upper left', 'upper center', 'upper right', 'middle left', 'center', 'midle right', 'lower left', 'lower center', 'lower right', 'foreground', 'background']:
            scope_listbox.insert(tk.END, scopens)
        scope_listbox_scrollbar = tk.Scrollbar(new_window, orient="vertical", command=tag_listbox.yview)
        scope_listbox_scrollbar.grid(row=1, column=3, sticky='nsew', padx=(0, 10))
        scope_listbox['yscrollcommand'] = scope_listbox_scrollbar.set
        # 対象物体選択用のテキストボックスの作成
        scope_notice = tk.Label(new_window, text="手打ち：the product を用いて\n(例：The product in the center)")
        scope_notice.grid(row=2, column=2, padx=10, pady=5)
        scope_entry = tk.Entry(new_window, exportselection=0)
        scope_entry.grid(row=3, column=2, padx=10, pady=5)

        # 欠陥位置用のリストボックス
        # json作成時は The {loc} of the {product} を想定 -> The whole of the product
        label_anomaly_location = tk.Label(new_window, text="製品のどこに欠陥があるか")
        label_anomaly_location.grid(row=0, column=4, padx=10, pady=5)
        fixed_tag_listbox = tk.Listbox(new_window)
        fixed_tag_listbox.grid(row=1, column=4, padx=10, pady=5)
        for fixed_tag in ['whole', 'left side', 'right side', 'top part', 'bottom part', 'center part', 'upper left', 'upper center', 'upper right', 'middle left', 'center', 'midle right', 'lower left', 'lower center', 'lower right']:
            fixed_tag_listbox.insert(tk.END, fixed_tag)
        fixed_tag_listbox_scrollbar = tk.Scrollbar(new_window, orient="vertical", command=fixed_tag_listbox.yview)
        fixed_tag_listbox_scrollbar.grid(row=1, column=5, sticky='nsew', padx=(0, 10))
        fixed_tag_listbox['yscrollcommand'] = fixed_tag_listbox_scrollbar.set
        # 対象物体選択用のテキストボックスの作成
        loc_notice = tk.Label(new_window, text="手打ち：of the product の前を入力\n(例：ternimal)")
        loc_notice.grid(row=2, column=4, padx=10, pady=5)
        loc_entry = tk.Entry(new_window, exportselection=0)
        loc_entry.grid(row=3, column=4, padx=10, pady=5)

        # 決定ボタンの作成
        select_button = tk.Button(new_window, text="Select Tag", command=on_button_press)
        select_button.grid(row=4, column=0, columnspan=6, padx=10, pady=5)
        # 元のウィンドウと同期
        new_window.wait_window()

    # jsonに出力
    def save_annotations(self, json_path):
        with open(json_path, 'w') as f:
            json.dump(self.annotations, f, indent=4)
            
# HACK パスは環境に合わせて治す
path_list = sorted(glob.glob('./rename_ViEW/*/*/*'))
anomaly_mode_path = 'anomalies.yaml'
root = tk.Tk()
app = ImageAnnotationApp(root, path_list, anomaly_mode_path)
root.mainloop()
