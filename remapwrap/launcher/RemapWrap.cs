/* ============================================================
   RemapWrap.exe — the thing a person double-clicks
   F-Keys | www.f-keys.com
   ------------------------------------------------------------
   Running RemapWrap used to mean installing Node.js and keeping
   a terminal open. That is the entire distance between this and
   something an ordinary person can use, so it is closed here:
   node.exe is shipped inside the folder, this starts it with no
   console window, and puts an icon in the tray.

   Compiled with the C# compiler that is already in Windows, so
   building RemapWrap needs no toolchain anyone has to install.
   ============================================================ */
using System;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Threading;
using System.Windows.Forms;

static class RemapWrap {
  static Process server;
  static NotifyIcon tray;
  const string URL = "http://127.0.0.1:7331/";

  [STAThread]
  static void Main() {
    // Two copies would fight over port 7331 and the second would lose in a
    // way that looks like the program simply not starting.
    bool fresh;
    using (var only = new Mutex(true, "RemapWrap.SingleInstance", out fresh)) {
      if (!fresh) {
        Open(URL);
        return;
      }

      Application.EnableVisualStyles();
      string here = Path.GetDirectoryName(Application.ExecutablePath);

      if (!StartServer(here)) { return; }
      BuildTray(here);
      Application.ApplicationExit += delegate { StopServer(); };
      Application.Run();
    }
  }

  static bool StartServer(string here) {
    string node = Path.Combine(here, "node.exe");
    string app  = Path.Combine(here, "app", "remapwrap-server.js");

    if (!File.Exists(node) || !File.Exists(app)) {
      MessageBox.Show(
        "RemapWrap is missing part of itself.\r\n\r\nExpected:\r\n" +
        node + "\r\n" + app +
        "\r\n\r\nRe-install, or unzip the whole folder rather than one file.",
        "RemapWrap", MessageBoxButtons.OK, MessageBoxIcon.Error);
      return false;
    }

    var psi = new ProcessStartInfo(node, "\"" + app + "\"");
    psi.WorkingDirectory = Path.Combine(here, "app");
    psi.UseShellExecute = false;
    psi.CreateNoWindow = true;                 // no black box on the desktop
    psi.RedirectStandardOutput = true;
    psi.RedirectStandardError = true;

    try {
      server = Process.Start(psi);
      // Read and discard, or the pipes fill and the server blocks on its
      // own logging after a few hundred lines.
      server.OutputDataReceived += delegate { };
      server.ErrorDataReceived += delegate { };
      server.BeginOutputReadLine();
      server.BeginErrorReadLine();
      return true;
    } catch (Exception e) {
      MessageBox.Show("RemapWrap could not start:\r\n\r\n" + e.Message,
                      "RemapWrap", MessageBoxButtons.OK, MessageBoxIcon.Error);
      return false;
    }
  }

  static void StopServer() {
    try {
      if (server != null && !server.HasExited) { server.Kill(); }
    } catch { /* already gone */ }
    if (tray != null) { tray.Visible = false; }
  }

  static void BuildTray(string here) {
    tray = new NotifyIcon();
    string ico = Path.Combine(here, "app", "assets", "icon.ico");
    tray.Icon = File.Exists(ico) ? new Icon(ico) : SystemIcons.Application;
    tray.Text = "RemapWrap — your phone is the control surface";
    tray.Visible = true;

    var menu = new ContextMenuStrip();
    menu.Items.Add("Open RemapWrap", null, delegate { Open(URL); });
    menu.Items.Add("Profiles folder", null, delegate {
      Open(Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
        "RemapWrap", "profiles"));
    });
    menu.Items.Add(new ToolStripSeparator());
    menu.Items.Add("Quit RemapWrap", null, delegate {
      StopServer();
      Application.Exit();
    });
    tray.ContextMenuStrip = menu;

    // Double-click is what people try first.
    tray.DoubleClick += delegate { Open(URL); };

    // The server needs a moment to bind before a browser is any use.
    // Qualified: System.Threading is imported for the single-instance
    // mutex and also has a Timer, and the two are nothing alike.
    var t = new System.Windows.Forms.Timer();
    t.Interval = 1200;
    t.Tick += delegate { t.Stop(); Open(URL); };
    t.Start();
  }

  static void Open(string what) {
    try {
      var psi = new ProcessStartInfo(what);
      psi.UseShellExecute = true;
      Process.Start(psi);
    } catch { /* no browser, or the folder is gone */ }
  }
}
