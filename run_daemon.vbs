Set WshShell = CreateObject("WScript.Shell")
' 0 代表隐藏窗口运行，True/False 代表是否等待执行结束
WshShell.Run "cmd /c venv\Scripts\python.exe agent\main.py", 0, False
Set WshShell = Nothing