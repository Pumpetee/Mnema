; Mnema installer (Inno Setup 6). Built by tools/package.py:  ISCC /DAppVersion=0.5.0 packaging\mnema.iss
;
; - Installs for the current user, no administrator rights: %LOCALAPPDATA%\Programs\Mnema.
; - Before copying: remembers where Mnema was running from and closes it (old portable builds included).
; - After copying: mnema-cli upgrade — finds older versions (the first builds were an unpacked archive), closes and
;   deletes them, moves autostart to the new program, puts the first build's settings aside for a clean start.
;   The memory and the downloaded models are never deleted. What was found is shown on the last page.
; - Uninstall removes the program and its autostart, not the memory.

#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif

[Setup]
AppId={{6F1D2C83-4B7A-4E39-9A51-3C8E2D7B5A10}
AppName=Mnema
AppVersion={#AppVersion}
AppVerName=Mnema {#AppVersion}
AppPublisher=Mnema
VersionInfoVersion={#AppVersion}
VersionInfoProductName=Mnema
VersionInfoProductVersion={#AppVersion}
DefaultDirName={localappdata}\Programs\Mnema
DefaultGroupName=Mnema
DisableProgramGroupPage=yes
DisableDirPage=auto
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
OutputDir=..\dist
OutputBaseFilename=Mnema-Setup-{#AppVersion}
SetupIconFile=mnema.ico
UninstallDisplayIcon={app}\Mnema.exe
UninstallDisplayName=Mnema
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
CloseApplications=no
RestartApplications=no

[Languages]
Name: "ru"; MessagesFile: "compiler:Languages\Russian.isl"
Name: "en"; MessagesFile: "compiler:Default.isl"

[CustomMessages]
ru.Looking=Ищу прежние версии Mnema…
en.Looking=Looking for previous versions of Mnema…
ru.Launch=Открыть Mnema
en.Launch=Open Mnema
ru.Found=Что сделано с прежними версиями:
en.Found=Previous versions:

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "..\dist\Mnema\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[InstallDelete]
; files of the previous install in the same folder: the new set replaces them completely
Type: filesandordirs; Name: "{app}\_internal"

[Icons]
Name: "{userprograms}\Mnema"; Filename: "{app}\Mnema.exe"
Name: "{userdesktop}\Mnema"; Filename: "{app}\Mnema.exe"; Tasks: desktopicon

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: none; ValueName: "Mnema"; Flags: uninsdeletevalue dontcreatekey

[Run]
Filename: "{app}\Mnema.exe"; Description: "{cm:Launch}"; Flags: nowait postinstall skipifsilent

[UninstallRun]
Filename: "{sys}\taskkill.exe"; Parameters: "/F /T /IM Mnema.exe"; Flags: runhidden; RunOnceId: "KillMnema"
Filename: "{sys}\taskkill.exe"; Parameters: "/F /IM llama-server.exe"; Flags: runhidden; RunOnceId: "KillLlama"

[Code]
var
  Report: String;
  ReportLabel: TNewStaticText;

procedure InitializeWizard;
begin
  ReportLabel := TNewStaticText.Create(WizardForm);
  ReportLabel.Parent := WizardForm.FinishedPage;
  ReportLabel.Left := WizardForm.FinishedLabel.Left;
  ReportLabel.Width := WizardForm.FinishedLabel.Width;
  ReportLabel.WordWrap := True;
  ReportLabel.AutoSize := True;
  ReportLabel.Caption := '';
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
var
  Code: Integer;
begin
  { where Mnema runs from, before it is closed — the first builds are found this way too }
  Exec(ExpandConstant('{sys}\WindowsPowerShell\v1.0\powershell.exe'),
       '-NoProfile -ExecutionPolicy Bypass -Command "Get-Process Mnema -ErrorAction SilentlyContinue | ForEach-Object { $_.Path } | Out-File -Encoding utf8 ''' + ExpandConstant('{tmp}\running.txt') + '''"',
       '', SW_HIDE, ewWaitUntilTerminated, Code);
  Exec(ExpandConstant('{sys}\taskkill.exe'), '/F /T /IM Mnema.exe', '', SW_HIDE, ewWaitUntilTerminated, Code);
  Exec(ExpandConstant('{sys}\taskkill.exe'), '/F /IM llama-server.exe', '', SW_HIDE, ewWaitUntilTerminated, Code);
  Sleep(800);
  Result := '';
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  Code: Integer;
  S: AnsiString;
begin
  if CurStep = ssPostInstall then
  begin
    WizardForm.StatusLabel.Caption := CustomMessage('Looking');
    Exec(ExpandConstant('{app}\mnema-cli.exe'),
         'upgrade --app-dir "' + ExpandConstant('{app}') + '" --running "' + ExpandConstant('{tmp}\running.txt') +
         '" --report "' + ExpandConstant('{tmp}\upgrade.txt') + '" --lang ' + ActiveLanguage,
         ExpandConstant('{app}'), SW_HIDE, ewWaitUntilTerminated, Code);
    Log('upgrade helper exit code: ' + IntToStr(Code));
    if LoadStringFromFile(ExpandConstant('{tmp}\upgrade.txt'), S) then
      Report := UTF8Decode(S);
    Log('upgrade report: ' + Report);
  end;
end;

procedure CurPageChanged(CurPageID: Integer);
begin
  if (CurPageID = wpFinished) and (Report <> '') then
  begin
    ReportLabel.Top := WizardForm.FinishedLabel.Top + WizardForm.FinishedLabel.Height + ScaleY(12);
    ReportLabel.Caption := CustomMessage('Found') + #13#10 + Report;
    WizardForm.RunList.Top := ReportLabel.Top + ReportLabel.Height + ScaleY(12);
  end;
end;
