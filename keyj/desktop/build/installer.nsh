; ============================================================
; installer.nsh — refuse a silent install over a running Key-J
; F-Keys | www.f-keys.com
; ------------------------------------------------------------
; WHY THIS EXISTS, MEASURED
;
; Installing 1.4.1 over a running 1.4.0 with /S exited 0 and produced a
; mixed install. Windows held Key-J.exe and resources\app.asar open, NSIS
; skipped both, replaced every unlocked file, and reported success. The
; result on disk was a 1.4.0 executable and a 1.4.0 renderer sitting
; beside 1.4.1's Electron runtime, with the registry claiming 1.4.1.
;
; That matters because winget installs silently by default, so the
; upgrade path most users take is exactly the one that produces it. A
; user would then report behaviour that exists in neither version.
;
; electron-builder's own running-app handling asks the user to close the
; app, which a silent install has no way to do. So a silent install now
; stops instead, with an exit code the package manager can report.
;
; It stops rather than killing the app on purpose: Key-J holds an unsaved
; session - the sequence you just built from a tab is in memory - and no
; installer should throw that away to save someone a click.
; ============================================================

!macro customInit
  ${If} ${Silent}
    ; tasklist rather than a mutex: no plugin, and it is the same check a
    ; person would run to answer the same question.
    nsExec::Exec `cmd /c tasklist /NH /FI "IMAGENAME eq ${APP_EXECUTABLE_FILENAME}" | find /I "${APP_EXECUTABLE_FILENAME}"`
    Pop $0
    ${If} $0 == 0
      ; 1618 is ERROR_INSTALL_ALREADY_RUNNING. Package managers surface it
      ; as "try again shortly" rather than a generic failure.
      SetErrorLevel 1618
      DetailPrint "${PRODUCT_NAME} is running. Close it and install again."
      Abort
    ${EndIf}
  ${EndIf}
!macroend
