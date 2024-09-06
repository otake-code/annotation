import os

# snacksフォルダのパスを指定
folder_path = r'G:\共有ドライブ\お菓子データセット\snacks'

# 除外するフォルダ名リスト
exclude_folders = {'__templete', 'test', '後で修正', '__setting'}

# snacksフォルダ内のディレクトリ数をカウント（除外リストに含まれるフォルダを除外）
subfolders = [name for name in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, name)) and name not in exclude_folders]
folder_count = len(subfolders)
print(f"snacksのカテゴリ数: {folder_count}")

# 各サブフォルダ内のフォルダ数をカウントし、合計を計算
total_inner_folders = 0
for subfolder in subfolders:
    subfolder_path = os.path.join(folder_path, subfolder)
    # 子フォルダ内に__templateが含まれている場合、その子フォルダを除外
    inner_folders = [
        name for name in os.listdir(subfolder_path)
        if os.path.isdir(os.path.join(subfolder_path, name)) and name not in exclude_folders
    ]
    inner_folder_count = len(inner_folders)
    total_inner_folders += inner_folder_count
    print(f"{subfolder}: {inner_folder_count}")

# サブフォルダ内のフォルダの合計数を表示
print(f"お菓子の合計数: {total_inner_folders}")
