# ============================================================
# RemapWrap - audio host
# F-Keys Creative LLC | www.f-keys.com
# ------------------------------------------------------------
# WHY THIS EXISTS
#
# A dial reports a value many times a second. Starting a process
# per value would cost a few hundred milliseconds each time, so
# this starts once, compiles its helper once, and then reads one
# command per line from standard input for as long as RemapWrap
# is running.
#
# WHY NOT A LIBRARY
#
# Windows already exposes all of this through Core Audio, and
# PowerShell can compile against it with nothing installed. The
# alternative was a native npm module, which would mean a
# compiler on the machine of anybody who wants to run this. The
# product is meant to work in fifteen seconds.
#
# PROTOCOL   one JSON object per line, in and out
#
#   {"id":1,"cmd":"master.get"}
#   {"id":2,"cmd":"master.set","value":40}
#   {"id":3,"cmd":"mic.mute","value":true}
#   {"id":4,"cmd":"mic.gain","value":75}
#   {"id":5,"cmd":"sessions"}
#   {"id":6,"cmd":"session.set","name":"chrome","value":20}
#   {"id":7,"cmd":"sound.play","path":"C:\...\airhorn.wav"}
#
# Values are 0-100. Every reply carries the id it answers and
# either "ok" or "error", so a caller never has to guess which
# request a line belongs to.
# ============================================================

$ErrorActionPreference = 'Stop'

$source = @'
using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;

[Guid("5CDF2C82-841E-4546-9722-0CF74078229A"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IAudioEndpointVolume {
  int RegisterControlChangeNotify(IntPtr n);
  int UnregisterControlChangeNotify(IntPtr n);
  int GetChannelCount(out uint c);
  int SetMasterVolumeLevel(float db, ref Guid ctx);
  int SetMasterVolumeLevelScalar(float level, ref Guid ctx);
  int GetMasterVolumeLevel(out float db);
  int GetMasterVolumeLevelScalar(out float level);
  int SetChannelVolumeLevel(uint ch, float db, ref Guid ctx);
  int SetChannelVolumeLevelScalar(uint ch, float level, ref Guid ctx);
  int GetChannelVolumeLevel(uint ch, out float db);
  int GetChannelVolumeLevelScalar(uint ch, out float level);
  int SetMute([MarshalAs(UnmanagedType.Bool)] bool mute, ref Guid ctx);
  int GetMute([MarshalAs(UnmanagedType.Bool)] out bool mute);
}

[Guid("87CE5498-68D6-44E5-9215-6DA47EF883D8"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface ISimpleAudioVolume {
  int SetMasterVolume(float level, ref Guid ctx);
  int GetMasterVolume(out float level);
  int SetMute([MarshalAs(UnmanagedType.Bool)] bool mute, ref Guid ctx);
  int GetMute([MarshalAs(UnmanagedType.Bool)] out bool mute);
}

[Guid("BFB7FF88-7239-4FC9-8FA2-07C950BE9C6D"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IAudioSessionControl2 {
  // IAudioSessionControl has NINE methods and the count has to be exact.
  // Declaring ten put GetProcessId on IsSystemSoundsSession, which returns
  // a status rather than a process id, so every session reported pid 0 and
  // the whole list came back empty. COM does not complain about this; it
  // just answers the wrong question.
  int GetState(out int state);
  int GetDisplayName(out IntPtr name); int SetDisplayName(string v, ref Guid ctx);
  int GetIconPath(out IntPtr p);       int SetIconPath(string v, ref Guid ctx);
  int GetGroupingParam(out Guid g);    int SetGroupingParam(ref Guid g, ref Guid ctx);
  int RegisterAudioSessionNotification(IntPtr n);
  int UnregisterAudioSessionNotification(IntPtr n);
  // IAudioSessionControl2 starts here
  int GetSessionIdentifier(out IntPtr id);
  int GetSessionInstanceIdentifier(out IntPtr id);
  int GetProcessId(out uint pid);
  int IsSystemSoundsSession();
  int SetDuckingPreference(bool opt);
}

[Guid("E2F5BB11-0570-40CA-ACDD-3AA01277DEE8"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IAudioSessionEnumerator {
  int GetCount(out int count);
  int GetSession(int index, out IAudioSessionControl2 session);
}

[Guid("77AA99A0-1BD6-484F-8BC7-2C654C9A9B6F"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IAudioSessionManager2 {
  int NotImpl0(); int NotImpl1();
  int GetSessionEnumerator(out IAudioSessionEnumerator e);
}

[Guid("D666063F-1587-4E43-81F1-B948E807363F"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IMMDevice {
  int Activate(ref Guid id, int ctx, IntPtr p,
               [MarshalAs(UnmanagedType.IUnknown)] out object o);
}

[Guid("A95664D2-9614-4F35-A746-DE8DB63617E6"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IMMDeviceEnumerator {
  int EnumAudioEndpoints(int f, int s, out IntPtr c);
  int GetDefaultAudioEndpoint(int dataFlow, int role, out IMMDevice endpoint);
}

[ComImport, Guid("BCDE0395-E52F-467C-8E3D-C4579291692E")]
class MMDeviceEnumeratorComObject { }

public class RwWindow {
  [DllImport("user32.dll")] static extern IntPtr GetForegroundWindow();
  [DllImport("user32.dll")] static extern int GetWindowThreadProcessId(IntPtr h, out int pid);
  [DllImport("user32.dll", CharSet=CharSet.Unicode)]
  static extern int GetWindowTextW(IntPtr h, System.Text.StringBuilder s, int n);

  // Which program the person is actually looking at. Returned as a pair so
  // a profile can match on either the executable or what the title bar
  // says, because "chrome.exe" and "Photoshop" are both how people think
  // about the same question.
  public static string Foreground() {
    IntPtr h = GetForegroundWindow();
    if (h == IntPtr.Zero) return "|";
    int pid = 0;
    GetWindowThreadProcessId(h, out pid);
    string exe = "";
    try { exe = System.Diagnostics.Process.GetProcessById(pid).ProcessName; }
    catch { exe = ""; }
    var sb = new System.Text.StringBuilder(512);
    GetWindowTextW(h, sb, sb.Capacity);
    return exe + "|" + sb.ToString();
  }
}

public class RwAudio {
  static Guid ctx = Guid.Empty;

  // 0 = playback, 1 = capture. Role 1 is the multimedia default, which is
  // the one a person means by "my speakers".
  static IMMDevice Device(int flow) {
    var e = (IMMDeviceEnumerator)(new MMDeviceEnumeratorComObject());
    IMMDevice dev;
    Marshal.ThrowExceptionForHR(e.GetDefaultAudioEndpoint(flow, 1, out dev));
    return dev;
  }

  static IAudioEndpointVolume Endpoint(int flow) {
    var iid = typeof(IAudioEndpointVolume).GUID; object o;
    Marshal.ThrowExceptionForHR(Device(flow).Activate(ref iid, 23, IntPtr.Zero, out o));
    return (IAudioEndpointVolume)o;
  }

  public static float Get(int flow) {
    float v; Marshal.ThrowExceptionForHR(Endpoint(flow).GetMasterVolumeLevelScalar(out v));
    return v * 100f;
  }
  public static void Set(int flow, float pct) {
    var v = Math.Max(0f, Math.Min(1f, pct / 100f));
    Marshal.ThrowExceptionForHR(Endpoint(flow).SetMasterVolumeLevelScalar(v, ref ctx));
  }
  public static bool GetMute(int flow) {
    bool m; Marshal.ThrowExceptionForHR(Endpoint(flow).GetMute(out m));
    return m;
  }
  public static void SetMute(int flow, bool mute) {
    Marshal.ThrowExceptionForHR(Endpoint(flow).SetMute(mute, ref ctx));
  }

  // Per-application volume. This is the reason for talking to Core Audio
  // rather than sending the media keys: "turn the game down but leave the
  // voice chat" is not something a keyboard can express.
  static IAudioSessionEnumerator Sessions() {
    var iid = typeof(IAudioSessionManager2).GUID; object o;
    Marshal.ThrowExceptionForHR(Device(0).Activate(ref iid, 23, IntPtr.Zero, out o));
    IAudioSessionEnumerator e;
    Marshal.ThrowExceptionForHR(((IAudioSessionManager2)o).GetSessionEnumerator(out e));
    return e;
  }

  // An application can hold several sessions - one playing and others
  // idle - so the active one is reported. Taking the first found reported
  // Discord at 0% while it was actually sitting at 53%.
  public static string[] List() {
    var e = Sessions();
    int n; e.GetCount(out n);
    var best = new Dictionary<string, string>();
    var active = new Dictionary<string, bool>();
    for (int i = 0; i < n; i++) {
      IAudioSessionControl2 s;
      if (e.GetSession(i, out s) != 0) { continue; }
      uint pid;
      if (s.GetProcessId(out pid) != 0 || pid == 0) { continue; }
      try {
        var p = System.Diagnostics.Process.GetProcessById((int)pid);
        int state; s.GetState(out state);          // 1 = rendering audio
        float v; ((ISimpleAudioVolume)s).GetMasterVolume(out v);
        var name = p.ProcessName;
        var playing = (state == 1);
        if (!best.ContainsKey(name) || (playing && !active[name])) {
          best[name] = name + "\t" + (int)Math.Round(v * 100) +
                       "\t" + (playing ? "playing" : "idle");
          active[name] = playing;
        }
      } catch { }
    }
    var outp = new List<string>(best.Values);
    return outp.ToArray();
  }

  public static bool SetSession(string name, float pct) {
    var e = Sessions();
    int n; e.GetCount(out n);
    bool hit = false;
    var v = Math.Max(0f, Math.Min(1f, pct / 100f));
    for (int i = 0; i < n; i++) {
      IAudioSessionControl2 s;
      if (e.GetSession(i, out s) != 0) { continue; }
      uint pid;
      if (s.GetProcessId(out pid) != 0 || pid == 0) { continue; }
      try {
        var p = System.Diagnostics.Process.GetProcessById((int)pid);
        if (String.Equals(p.ProcessName, name, StringComparison.OrdinalIgnoreCase)) {
          ((ISimpleAudioVolume)s).SetMasterVolume(v, ref ctx);
          hit = true;
        }
      } catch { }
    }
    return hit;
  }
}
'@

Add-Type -TypeDefinition $source -Language CSharp
Add-Type -AssemblyName presentationCore
# Speech is what turns a board of keys into a way of talking. Loaded with
# everything else so the cost is paid once, at start, rather than the first
# time somebody needs to say something.
Add-Type -AssemblyName System.Speech
$script:voice = New-Object System.Speech.Synthesis.SpeechSynthesizer

# Sounds are kept so a pad can retrigger one without reloading it, and so
# "stop all" has something to stop.
$script:players = @{}

function Reply($id, $ok, $body) {
  $o = @{ id = $id; ok = $ok }
  if ($null -ne $body) { $o.result = $body }
  [Console]::Out.WriteLine(($o | ConvertTo-Json -Compress -Depth 4))
  [Console]::Out.Flush()
}

Reply 0 $true "ready"

while ($true) {
  $line = [Console]::In.ReadLine()
  if ($null -eq $line) { break }
  if ($line.Trim() -eq '') { continue }

  $id = 0
  try {
    $m = $line | ConvertFrom-Json
    $id = $m.id
    switch ($m.cmd) {
      'master.get'   { Reply $id $true ([math]::Round([RwAudio]::Get(0))) }
      'master.set'   { [RwAudio]::Set(0, [float]$m.value); Reply $id $true $null }
      'master.mute'  { [RwAudio]::SetMute(0, [bool]$m.value); Reply $id $true $null }
      'master.muted' { Reply $id $true ([RwAudio]::GetMute(0)) }
      'mic.get'      { Reply $id $true ([math]::Round([RwAudio]::Get(1))) }
      'mic.gain'     { [RwAudio]::Set(1, [float]$m.value); Reply $id $true $null }
      'mic.mute'     { [RwAudio]::SetMute(1, [bool]$m.value); Reply $id $true $null }
      'mic.muted'    { Reply $id $true ([RwAudio]::GetMute(1)) }
      'sessions'     { Reply $id $true ([RwAudio]::List()) }
      'session.set'  { Reply $id $true ([RwAudio]::SetSession($m.name, [float]$m.value)) }
      'sound.play'   {
        if (-not (Test-Path $m.path)) { throw "no such file: $($m.path)" }
        $key = $m.path
        if (-not $script:players.ContainsKey($key)) {
          $p = New-Object System.Windows.Media.MediaPlayer
          $p.Open([uri]$m.path)
          $script:players[$key] = $p
        }
        $script:players[$key].Position = [TimeSpan]::Zero
        $script:players[$key].Play()
        Reply $id $true $null
      }
      'sound.stop'   {
        foreach ($p in $script:players.Values) { $p.Stop() }
        Reply $id $true $null
      }
      'foreground'   { Reply $id $true ([RwWindow]::Foreground()) }
      'speak' {
        # Asynchronous on purpose. A long sentence must not freeze every
        # other key on the board while it is being said, and somebody who
        # presses a second key means "say that instead".
        $script:voice.SpeakAsyncCancelAll()
        if ($m.rate -ne $null) { $script:voice.Rate = [int]$m.rate }
        if ($m.volume -ne $null) { $script:voice.Volume = [int]$m.volume }
        if ($m.voice) {
          try { $script:voice.SelectVoice([string]$m.voice) } catch { }
        }
        $script:voice.SpeakAsync([string]$m.text) | Out-Null
        Reply $id $true $null
      }
      'speak.stop'   { $script:voice.SpeakAsyncCancelAll(); Reply $id $true $null }
      'voices'       {
        Reply $id $true (@($script:voice.GetInstalledVoices() |
          ForEach-Object { $_.VoiceInfo.Name }))
      }
      'state' {
        # Everything the phone needs, in one reply. Asking four times
        # twice a second put twenty four round trips a second through a
        # host that answers them one at a time, and anything else -
        # such as the foreground check - queued behind all of it.
        Reply $id $true @{
          master  = [math]::Round([RwAudio]::Get(0))
          mmuted  = [RwAudio]::GetMute(0)
          mic     = [math]::Round([RwAudio]::Get(1))
          micmuted= [RwAudio]::GetMute(1)
          fore    = [RwWindow]::Foreground()
        }
      }
      'ping'         { Reply $id $true "pong" }
      default        { Reply $id $false "unknown command: $($m.cmd)" }
    }
  } catch {
    Reply $id $false $_.Exception.Message
  }
}
