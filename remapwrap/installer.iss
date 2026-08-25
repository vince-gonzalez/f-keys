; ============================================================
;  RemapWrap installer
;  F-Keys | www.f-keys.com
; ------------------------------------------------------------
;  Build dist\RemapWrap\ first:   node build.js
;  Then compile this with Inno Setup 6 (ISCC.exe installer.iss).
;
;  Deliberately per-user. RemapWrap needs no administrator, and
;  asking for one on a shared or school machine is the point at
;  which most people stop installing.
; ============================================================

#define AppName    "RemapWrap"
#define AppVersion "0.1.0"
#define AppPublisher "F-Keys Creative LLC"
#define AppURL     "https://f-keys.com/remapwrap/"

[Setup]
AppId={{7C4C1C4E-2B1F-4C63-9C3E-5A6E1F0B8A21}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
OutputBaseFilename=RemapWrap-{#AppVersion}-setup
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
; No administrator. See the note at the top.
PrivilegesRequired=lowest
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\RemapWrap.exe
SetupIconFile=assets\icon.ico

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; \
  GroupDescription: "Shortcuts:"
Name: "startup"; Description: "Start RemapWrap when I sign in"; \
  GroupDescription: "Startup:"; Flags: unchecked

[Files]
Source: "dist\RemapWrap\*"; DestDir: "{app}"; \
  Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\RemapWrap.exe"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\RemapWrap.exe"; \
  Tasks: desktopicon
Name: "{userstartup}\{#AppName}"; Filename: "{app}\RemapWrap.exe"; \
  Tasks: startup

[Run]
Filename: "{app}\RemapWrap.exe"; \
  Description: "Start RemapWrap"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Profiles and the pairing secret live in AppData and are the user's,
; not ours. They are left alone on uninstall: somebody reinstalling
; should find their boards where they left them.
Type: filesandordirs; Name: "{app}"
