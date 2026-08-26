/* ============================================================
   RemapWrap-Setup.exe — the thing a stranger downloads
   F-Keys | www.f-keys.com
   ------------------------------------------------------------
   A single file. Double-click, Install, done.

   Compiled with the C# compiler that is already inside Windows,
   with the whole application carried as an embedded resource,
   so building an installer needs no installer-building tool.
   installer.iss is still in this repository for the day Inno
   Setup is on the build machine; this exists so that day is not
   a blocker.

   PER USER, ON PURPOSE

   It installs to %LOCALAPPDATA%\Programs and needs no
   administrator. RemapWrap does not need one, and asking for
   one on a school, work or library machine is the point at
   which most people stop installing - which is the opposite of
   what assistive software should do.

   WHAT IT WILL NOT DO

   Uninstalling removes the program and leaves
   %APPDATA%\RemapWrap alone. The boards in there are the
   user's, somebody reinstalling should find them where they
   left them, and for a person whose communication board lives
   in that folder, deleting it would be taking their words away.
   ============================================================ */
using System;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.IO.Compression;
using System.Reflection;
using System.Threading;
using System.Windows.Forms;
using Microsoft.Win32;

static class Setup {
  const string APP = "RemapWrap";
  const string VERSION = "0.1.0";
  const string PUBLISHER = "F-Keys Creative LLC";
  const string URL = "https://f-keys.com/remapwrap/";
  const string KEY = @"Software\Microsoft\Windows\CurrentVersion\Uninstall\RemapWrap";

  static string Target() {
    return Path.Combine(
      Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
      "Programs", APP);
  }

  [STAThread]
  static void Main(string[] args) {
    bool silent = false, uninstall = false;
    foreach (string a in args) {
      string f = a.ToLowerInvariant().TrimStart('/', '-');
      if (f == "silent" || f == "s" || f == "quiet") { silent = true; }
      if (f == "uninstall" || f == "u") { uninstall = true; }
    }

    // Both paths leave a trail and neither may raise a dialog when running
    // silently: an unhandled exception with no console attached puts up a
    // window nobody can see and the process waits on it forever. That was
    // fixed for installing and not for removing, and removing then hung in
    // exactly the same way.
    string trail = Path.Combine(Path.GetTempPath(), "remapwrap-setup.log");
    Action<string> note = delegate(string m) {
      try { File.AppendAllText(trail, DateTime.Now.ToString("HH:mm:ss")
        + "  " + m + Environment.NewLine); }
      catch { }
    };

    if (uninstall) {
      try {
        note("uninstall: start");
        Uninstall(silent, note);
        note("uninstall: done");
        if (silent) { Environment.Exit(0); }
      } catch (Exception ex) {
        note("uninstall failed: " + ex.Message);
        if (!silent) {
          MessageBox.Show("RemapWrap could not be removed." +
                          Environment.NewLine + Environment.NewLine + ex.Message,
                          "RemapWrap", MessageBoxButtons.OK, MessageBoxIcon.Error);
        }
        Environment.Exit(1);
      }
      return;
    }
    if (silent) {
      // Nothing may open a window here. An unhandled exception in silent
      // mode raises a dialog nobody can see and the installer waits on it
      // forever, which is exactly how a ten minute "install" happened.
      try {
        // A silent install that hangs gives nobody anything to look at, so
        // it leaves a trail. This is how the ten minute hang was found.
        note("install: start");
        Install(true, true, false, note);
        note("finished");
        Environment.Exit(0);
      } catch (Exception ex) {
        try {
          Console.Error.WriteLine("RemapWrap install failed: " + ex.Message);
        } catch { }
        Environment.Exit(1);
      }
      return;
    }

    Application.EnableVisualStyles();
    Application.Run(new Wizard());
  }

  // ── installing ──────────────────────────────────────────────
  public static void Install(bool desktop, bool startMenu, bool atSignIn,
                             Action<string> say) {
    string dir = Target();
    if (say != null) { say("Closing any copy already running…"); }
    StopRunning();

    if (say != null) { say("stopped what was running"); }
    // The whole application, carried inside this file.
    using (Stream src = Assembly.GetExecutingAssembly()
             .GetManifestResourceStream("payload.zip")) {
      if (src == null) {
        throw new Exception("This installer is missing the application it " +
                            "was supposed to carry. Download it again.");
      }
      string temp = Path.Combine(Path.GetTempPath(), "RemapWrap-" + Guid.NewGuid().ToString("N") + ".zip");
      try {
        using (FileStream f = File.Create(temp)) { src.CopyTo(f); }
        if (say != null) { say("payload written to temp"); }
        // Replacing rather than merging: files left behind by an older
        // version are how an application starts loading something it no
        // longer ships. But a locked file must not stop the install - the
        // first attempt at this deleted what it could, then extracted into
        // what was left and threw on the first file already there.
        if (Directory.Exists(dir)) {
          try { Directory.Delete(dir, true); } catch { }
        }
        if (say != null) { say("old copy cleared"); }
        Directory.CreateDirectory(dir);
        Extract(temp, dir);
        if (say != null) { say("extracted"); }
      } finally {
        try { File.Delete(temp); } catch { }
      }
    }

    string exe = Path.Combine(dir, "RemapWrap.exe");
    if (!File.Exists(exe)) {
      throw new Exception("Unpacking finished but RemapWrap.exe is not there. " +
                          "The download is probably damaged.");
    }

    if (say != null) { say("Making shortcuts…"); }
    if (startMenu) {
      Shortcut(Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.Programs),
        APP + ".lnk"), exe);
    }
    if (desktop) {
      Shortcut(Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.DesktopDirectory),
        APP + ".lnk"), exe);
    }
    if (atSignIn) {
      Shortcut(Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.Startup),
        APP + ".lnk"), exe);
    }

    if (say != null) { say("Registering…"); }
    // A copy of this installer stays behind so Windows has something real
    // to point Add or remove programs at.
    string mine = Path.Combine(dir, "uninstall.exe");
    try { File.Copy(Application.ExecutablePath, mine, true); } catch { mine = null; }

    using (RegistryKey k = Registry.CurrentUser.CreateSubKey(KEY)) {
      k.SetValue("DisplayName", APP);
      k.SetValue("DisplayVersion", VERSION);
      k.SetValue("Publisher", PUBLISHER);
      k.SetValue("URLInfoAbout", URL);
      k.SetValue("InstallLocation", dir);
      k.SetValue("DisplayIcon", exe);
      k.SetValue("NoModify", 1, RegistryValueKind.DWord);
      k.SetValue("NoRepair", 1, RegistryValueKind.DWord);
      if (mine != null) {
        k.SetValue("UninstallString", "\"" + mine + "\" /uninstall");
        k.SetValue("QuietUninstallString", "\"" + mine + "\" /uninstall /silent");
      }
      try {
        long bytes = 0;
        foreach (string f in Directory.GetFiles(dir, "*", SearchOption.AllDirectories)) {
          bytes += new FileInfo(f).Length;
        }
        k.SetValue("EstimatedSize", (int)(bytes / 1024), RegistryValueKind.DWord);
      } catch { }
    }
  }

  // ExtractToDirectory refuses to overwrite and gives up on the first file
  // that already exists. Doing it entry by entry means a directory that
  // could not be fully cleared is written over rather than fatal.
  static void Extract(string zipPath, string dir) {
    using (ZipArchive zip = ZipFile.OpenRead(zipPath)) {
      foreach (ZipArchiveEntry entry in zip.Entries) {
        string full = Path.GetFullPath(Path.Combine(dir, entry.FullName));
        // A zip is a file somebody downloaded. An entry naming its way out
        // of the folder is not a file, it is an attack.
        if (!full.StartsWith(Path.GetFullPath(dir), StringComparison.OrdinalIgnoreCase)) {
          continue;
        }
        if (entry.Name.Length == 0) {
          Directory.CreateDirectory(full);
          continue;
        }
        Directory.CreateDirectory(Path.GetDirectoryName(full));
        entry.ExtractToFile(full, true);
      }
    }
  }

  // ── removing ────────────────────────────────────────────────
  static void Uninstall(bool silent, Action<string> note) {
    if (!silent) {
      DialogResult r = MessageBox.Show(
        "Remove RemapWrap from this computer?\r\n\r\n" +
        "Your boards and your licence key are kept. They live in your own " +
        "AppData folder, and reinstalling will find them exactly where you " +
        "left them.",
        "Uninstall RemapWrap", MessageBoxButtons.YesNo, MessageBoxIcon.Question);
      if (r != DialogResult.Yes) { return; }
    }

    note("stopping what is running");
    StopRunning();
    note("removing shortcuts");
    foreach (string where in new string[] {
        Environment.GetFolderPath(Environment.SpecialFolder.Programs),
        Environment.GetFolderPath(Environment.SpecialFolder.DesktopDirectory),
        Environment.GetFolderPath(Environment.SpecialFolder.Startup) }) {
      try { File.Delete(Path.Combine(where, APP + ".lnk")); } catch { }
    }
    note("removing the registry entry");
    try { Registry.CurrentUser.DeleteSubKeyTree(KEY, false); } catch { }

    string dir = Target();
    // This program is running from inside the folder it has to delete, so
    // it asks the shell to do it a moment after this process ends.
    note("scheduling the folder removal");
    string bat = Path.Combine(Path.GetTempPath(), "rw-remove.cmd");
    try {
      File.WriteAllText(bat,
        "@echo off\r\n" +
        "ping 127.0.0.1 -n 3 >nul\r\n" +
        "rmdir /s /q \"" + dir + "\"\r\n" +
        "del \"%~f0\"\r\n");
      ProcessStartInfo psi = new ProcessStartInfo("cmd.exe", "/c \"" + bat + "\"");
      psi.WindowStyle = ProcessWindowStyle.Hidden;
      psi.CreateNoWindow = true;
      psi.UseShellExecute = false;
      Process.Start(psi);
    } catch { }

    if (!silent) {
      MessageBox.Show("RemapWrap has been removed.\r\n\r\n" +
                      "Your boards are still in your AppData folder.",
                      APP, MessageBoxButtons.OK, MessageBoxIcon.Information);
    }
  }

  static void StopRunning() {
    // Bounded. Reading another process's MainModule can block, and cleanup
    // that cannot finish must not stop the thing it was cleaning up for.
    Thread t = new Thread(new ThreadStart(StopRunningInner));
    t.IsBackground = true;
    t.Start();
    t.Join(6000);
    Thread.Sleep(200);
  }

  static void StopRunningInner() {
    foreach (Process p in Process.GetProcessesByName("RemapWrap")) {
      try { p.Kill(); p.WaitForExit(4000); } catch { }
    }
    // The bundled node runs the server and would keep the port and the
    // files open. Only the one inside the install folder is touched;
    // somebody's own Node projects are none of our business.
    string dir = Target().ToLowerInvariant();
    foreach (Process p in Process.GetProcessesByName("node")) {
      try {
        if (p.MainModule != null &&
            p.MainModule.FileName.ToLowerInvariant().StartsWith(dir)) {
          p.Kill(); p.WaitForExit(4000);
        }
      } catch { /* not ours to look at */ }
    }
    Thread.Sleep(300);
  }

  static void Shortcut(string linkPath, string target) {
    try {
      Type t = Type.GetTypeFromProgID("WScript.Shell");
      if (t == null) { return; }
      object shell = Activator.CreateInstance(t);
      object link = t.InvokeMember("CreateShortcut", BindingFlags.InvokeMethod,
                                   null, shell, new object[] { linkPath });
      Type lt = link.GetType();
      lt.InvokeMember("TargetPath", BindingFlags.SetProperty, null, link,
                      new object[] { target });
      lt.InvokeMember("WorkingDirectory", BindingFlags.SetProperty, null, link,
                      new object[] { Path.GetDirectoryName(target) });
      lt.InvokeMember("Description", BindingFlags.SetProperty, null, link,
                      new object[] { "RemapWrap — your phone is the control surface" });
      lt.InvokeMember("Save", BindingFlags.InvokeMethod, null, link, null);
    } catch { /* a shortcut is a convenience, not the install */ }
  }
}

// ── the window ────────────────────────────────────────────────
// Deliberately one screen. Every extra page is a place somebody stops.
class Wizard : Form {
  CheckBox cbDesktop, cbStartup;
  Button go;
  Label status;

  public Wizard() {
    Text = "Install RemapWrap";
    FormBorderStyle = FormBorderStyle.FixedDialog;
    MaximizeBox = false; MinimizeBox = false;
    StartPosition = FormStartPosition.CenterScreen;
    ClientSize = new Size(460, 300);
    Font = new Font("Segoe UI", 10f);          // 10pt at 96dpi is 13px

    try {
      string ico = Path.Combine(Path.GetDirectoryName(Application.ExecutablePath),
                                "icon.ico");
      if (File.Exists(ico)) { Icon = new Icon(ico); }
    } catch { }

    Label title = new Label();
    title.Text = "RemapWrap";
    title.Font = new Font("Segoe UI", 20f, FontStyle.Bold);
    title.SetBounds(24, 20, 400, 40);
    Controls.Add(title);

    Label blurb = new Label();
    blurb.Text = "Your phone becomes a control surface for this computer.\r\n\r\n" +
                 "It installs for you only and needs no administrator. Nothing " +
                 "is sent anywhere: your phone talks to this computer directly.";
    blurb.SetBounds(24, 64, 412, 84);
    Controls.Add(blurb);

    cbDesktop = new CheckBox();
    cbDesktop.Text = "Put a shortcut on my desktop";
    cbDesktop.Checked = true;
    cbDesktop.SetBounds(24, 156, 412, 26);
    Controls.Add(cbDesktop);

    cbStartup = new CheckBox();
    cbStartup.Text = "Start RemapWrap when I sign in";
    cbStartup.SetBounds(24, 184, 412, 26);
    Controls.Add(cbStartup);

    status = new Label();
    status.SetBounds(24, 216, 412, 22);
    status.ForeColor = SystemColors.GrayText;
    Controls.Add(status);

    go = new Button();
    go.Text = "Install";
    go.SetBounds(320, 246, 116, 34);
    go.Click += Run;
    Controls.Add(go);
    AcceptButton = go;
  }

  void Say(string s) {
    if (InvokeRequired) { Invoke(new Action<string>(Say), s); return; }
    status.Text = s;
    Refresh();
  }

  void Run(object sender, EventArgs e) {
    go.Enabled = false;
    cbDesktop.Enabled = cbStartup.Enabled = false;
    try {
      Setup.Install(cbDesktop.Checked, true, cbStartup.Checked, Say);
      Say("Done.");
      string exe = Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
        "Programs", "RemapWrap", "RemapWrap.exe");
      if (MessageBox.Show("RemapWrap is installed.\r\n\r\nStart it now?",
                          "RemapWrap", MessageBoxButtons.YesNo,
                          MessageBoxIcon.Information) == DialogResult.Yes) {
        ProcessStartInfo psi = new ProcessStartInfo(exe);
        psi.UseShellExecute = true;
        Process.Start(psi);
      }
      Close();
    } catch (Exception ex) {
      Say("");
      MessageBox.Show("RemapWrap could not be installed.\r\n\r\n" + ex.Message,
                      "RemapWrap", MessageBoxButtons.OK, MessageBoxIcon.Error);
      go.Enabled = true;
      cbDesktop.Enabled = cbStartup.Enabled = true;
    }
  }
}
