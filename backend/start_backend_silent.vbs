Set WshShell = CreateObject("WScript.Shell")
backendPath = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
pythonPath = backendPath & "\venv\Scripts\python.exe"
cmd = "cmd /c cd /d " & Chr(34) & backendPath & Chr(34) & " && " & Chr(34) & pythonPath & Chr(34) & " " & Chr(34) & backendPath & "\run_backend.py" & Chr(34)
WshShell.Run cmd, 0, False
