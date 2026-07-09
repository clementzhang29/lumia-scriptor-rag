#define AppName "ZCLUM Prism OCR"
#define AppVersion "0.1.0"

[Setup]
AppId={{8A1C5B5B-0D2A-4D7E-9F61-1C8A94B6C911}}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=ZCLUM
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
OutputDir={#InstallerOutput}
OutputBaseFilename=ZCLUM-Prism-OCR-Setup
SetupIconFile=
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
DisableProgramGroupPage=yes
UsePreviousAppDir=no
DiskSpanning=yes
DiskSliceSize=2000000000

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop icon"; GroupDescription: "Additional icons:"; Flags: unchecked

[Files]
Source: "{#AppSource}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#ModelSource}\*"; DestDir: "{localappdata}\datalab\datalab\Cache\models"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\ZCLUM Prism OCR.exe"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\ZCLUM Prism OCR.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\ZCLUM Prism OCR.exe"; Description: "Launch {#AppName}"; Flags: nowait postinstall skipifsilent
