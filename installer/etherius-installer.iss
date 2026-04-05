#define MyAppName "Etherius Security Suite"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Etherius"
#define MyAppExeName "EtheriusSuite.exe"
#define MyAppURL "https://etherius-security-site.vercel.app"

[Setup]
AppId={{ACCB63E3-0D7E-4FCB-A934-DB26ABAF0AA1}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription=Enterprise Endpoint Security Installer
VersionInfoVersion={#MyAppVersion}
VersionInfoProductName={#MyAppName}
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
Source: "..\release\bin\EtheriusSuite\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Etherius Security"; Filename: "{app}\EtheriusSuite.exe"; IconFilename: "{app}\EtheriusSuite.exe"
Name: "{group}\Uninstall Etherius"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Etherius Security"; Filename: "{app}\EtheriusSuite.exe"; IconFilename: "{app}\EtheriusSuite.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\EtheriusSuite.exe"; Description: "Launch Etherius Security"; Flags: postinstall nowait skipifsilent
