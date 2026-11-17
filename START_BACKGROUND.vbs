Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "cmd.exe /c ""D:\task3\START_SERVER.bat""", 0, False
Set WshShell = Nothing
