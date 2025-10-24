; -- Finao_setup.iss --
; Ce script est adapté pour installer votre application Finao.exe
; Assurez-vous que votre application (Main.exe) est bien une application 64-bit
; pour que les paramètres ArchitecturesAllowed et ArchitecturesInstallIn64BitMode soient corrects.

; Pour exécuter cette installation et le programme qu'elle installe,
; vous devez avoir une édition "x64" de Windows ou Windows 11 on Arm.

[Setup]
AppName=Finao
AppVersion=1.0.0.0
WizardStyle=modern
DefaultDirName={autopf}\Finao
DefaultGroupName=Finao
; Attention: Un programme de désinstallation affiche le fichier principal de l'app.
; Si votre app principale est 'Main.exe', c'est ce qu'il faut indiquer ici.
UninstallDisplayIcon={app}\Main.exe
Compression=lzma2
SolidCompression=yes
OutputDir=userdocs:Inno Setup Output
; Le nom de votre fichier d'installation final (ex: Setup_Finao.exe)
OutputBaseFilename=Setup_Finao
; Votre icône personnalisée pour le programme d'installation
; Le fichier assets/icons/Finao.ico doit être dans le même dossier que Finao_setup.iss
SetupIconFile="assets/icons/Finao.ico"
; "ArchitecturesAllowed=x64compatible" spécifie que le programme d'installation ne peut s'exécuter
; que sur les systèmes 64-bit (x64 ou Windows 11 on Arm).
ArchitecturesAllowed=x64compatible
; "ArchitecturesInstallIn64BitMode=x64compatible" demande que l'installation soit faite en "mode 64-bit"
; sur les systèmes 64-bit, ce qui signifie qu'elle utilisera le répertoire natif
; "Program Files" 64-bit et la vue 64-bit du registre.
ArchitecturesInstallIn64BitMode=x64compatible

; --------------- Informations sur l'Éditeur / l'Application ---------------
AppPublisher=Langello Antoine
; AppPublisherURL=https://www.votresite.com
; AppSupportURL=https://www.votresite.com/support
; AppUpdatesURL=https://www.votresite.com/updates
VersionInfoVersion=1.0.0.0
VersionInfoCompany=Finao
VersionInfoDescription=Logiciel de gestion de budget personnel
VersionInfoCopyright=Copyright (c) 2025 Langello&BOUCHUT Corp. Tous droits réservés.
; --------------------------------------------------------------------------

[Tasks]
; Cette section définit les tâches que l'utilisateur peut choisir.
; La tâche "desktopicon" permet la création d'un raccourci sur le bureau.
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
; Votre programme principal Finao.exe
; Le fichier MaFinaoin.exe doit être dans le même dossier que Finao_setup.iss
Source: "Finao.exe"; DestDir: "{app}"
Source: "assets\icons\Finao.ico"; DestDir: "{app}\assets\icons"
Source: "assets\sounds\*"; DestDir:"{app}\assets\sounds"
; Si vous avez d'autres fichiers (comme MyProg.chm ou Readme.txt dans l'exemple original),
; assurez-vous de les inclure ici.
; Par exemple, si vous avez un fichier Readme.txt :
; Source: "Readme.txt"; DestDir: "{app}"; Flags: isreadme
; Si vous avez d'autres fichiers ou des dossiers entiers à inclure :
; Source: "mon_dossier_de_ressources\*"; DestDir: "{app}\resources"; Flags: recursesubdirs createallsubdirs
; (Ceci inclurait tout le contenu d'un dossier 'mon_dossier_de_ressources' dans un sous-dossier 'resources' de l'app)

[Icons]
; Raccourci dans le menu Démarrer
Name: "{group}\Finao"; Filename: "{app}\Finao.exe"; IconFilename: "{app}\Finao.exe"
; Raccourci sur le bureau (maintenant que la tâche "desktopicon" est définie)
Name: "{autodesktop}\Finao"; Filename: "{app}\Finao.exe"; Tasks: desktopicon; IconFilename: "{app}\Finao.exe"