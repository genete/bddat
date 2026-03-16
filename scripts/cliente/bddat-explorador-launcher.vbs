Dim uri, cmd, handlerPath
handlerPath = CreateObject("WScript.Shell").ExpandEnvironmentStrings( _
              "%LOCALAPPDATA%\bddat-tools\bddat-explorador-handler.ps1")
uri = WScript.Arguments(0)
cmd = "powershell.exe -ExecutionPolicy Bypass -NonInteractive -WindowStyle Hidden" & _
      " -File """ & handlerPath & """ """ & uri & """"
CreateObject("WScript.Shell").Run cmd, 0, False
