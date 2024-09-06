import subprocess

# スクリプトファイルのパスを指定
today_count_script = r'todayCount.py'
folder_count_script = r'foldaCount.py'

# subprocessモジュールを使用してスクリプトを同時に実行
process1 = subprocess.Popen(['python', today_count_script], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
process2 = subprocess.Popen(['python', folder_count_script], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

# 各スクリプトの出力を表示
output1, error1 = process1.communicate()
output2, error2 = process2.communicate()

# 結果を表示
#print("todayCount.pyの出力:")
print(output1.decode('cp932', errors='ignore'))  # cp932でデコード、エラーは無視
if error1:
    print("todayCount.pyのエラー:")
    print(error1.decode('cp932', errors='ignore'))
print("--------------------")

#print("foldaCount.pyの出力:")
print(output2.decode('cp932', errors='ignore'))  # cp932でデコード、エラーは無視
if error2:
    print("foldaCount.pyのエラー:")
    print(error2.decode('cp932', errors='ignore'))
