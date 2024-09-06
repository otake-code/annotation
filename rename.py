import os

# フォルダのルートパス
root_dir = r"G:/共有ドライブ/お菓子データセット/snacks"

# フォルダの探索と名前変更
for dirpath, dirnames, filenames in os.walk(root_dir):
    for dirname in dirnames:
        # 欠陥名フォルダにある "cut" を "scratch" に変更
        if dirname == "cut":
            old_path = os.path.join(dirpath, dirname)
            new_path = os.path.join(dirpath, "scratch")
            os.rename(old_path, new_path)
            print(f"Renamed: {old_path} -> {new_path}")

print("フォルダ名の変更が完了しました。")
