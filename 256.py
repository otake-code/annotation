from PIL import Image
import os

# フォルダのパスを指定
input_folder = 'input_images'
output_folder = 'output_images'


# 出力フォルダが存在しない場合、作成
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# 入力フォルダ内のすべての画像を処理
for filename in os.listdir(input_folder):
    if filename.endswith('.jpg') or filename.endswith('.png'):
        # 画像を開く
        image_path = os.path.join(input_folder, filename)
        image = Image.open(image_path)

        # 画像をリサイズ（256x256）
        resized_image = image.resize((256, 256))

        # リサイズ後の画像を保存
        resized_image_path = os.path.join(output_folder, filename)
        resized_image.save(resized_image_path)

        print(f"{filename} を256x256にリサイズし、保存しました。")
