' SENTIA launcher — avvia il ponte invisibile e apre la dashboard
Set fso = CreateObject("Scripting.FileSystemObject")
Set sh  = CreateObject("WScript.Shell")
dir = fso.GetParentFolderName(WScript.ScriptFullName)
sh.CurrentDirectory = dir

' ponte di sistema nascosto (pythonw = senza finestra console)
On Error Resume Next
sh.Run "pythonw """ & dir & "\server.py""", 0, False
If Err.Number <> 0 Then
    Err.Clear
    sh.Run "python """ & dir & "\server.py""", 0, False
End If
On Error GoTo 0

WScript.Sleep 2500
sh.Run "http://localhost:7107/", 1, False
