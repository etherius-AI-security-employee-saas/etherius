#define MyAppName "Etherius Security Suite"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Etherius"
#define MyAppExeName "EtheriusSuite.exe"

[Setup]
AppId={{ACCB63E3-0D7E-4FCB-A934-DB26ABAF0AA1}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\Etherius
DefaultGroupName=Etherius
DisableProgramGroupPage=yes
OutputDir=..\release\installer
OutputBaseFilename=Etherius-Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
SetupIconFile=..\suite\assets\etherius-suite.ico
UninstallDisplayIcon={app}\EtheriusSuite.exe

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create desktop icon"; GroupDescription: "Additional icons:"

[Files]
Source: "..\release\bin\EtheriusSuite.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\release\bin\EtheriusShield.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\release\bin\EtheriusBackendService.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Etherius Control Center"; Filename: "{app}\EtheriusSuite.exe"; IconFilename: "{app}\EtheriusSuite.exe"
Name: "{group}\Etherius Employee Shield"; Filename: "{app}\EtheriusShield.exe"; IconFilename: "{app}\EtheriusShield.exe"
Name: "{group}\Uninstall Etherius"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Etherius Control Center"; Filename: "{app}\EtheriusSuite.exe"; IconFilename: "{app}\EtheriusSuite.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\EtheriusBackendService.exe"; Description: "Start Etherius backend service now"; Flags: postinstall nowait skipifsilent
Filename: "{app}\EtheriusSuite.exe"; Description: "Launch Etherius Control Center"; Flags: postinstall nowait skipifsilent
