# Embeds System.AppUserModel.ID into a .lnk file via IPropertyStore.
# Usage: .\set_lnk_appid.ps1 -LnkPath 'C:\path\to\file.lnk' -AppId 'My.App.Id'

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)] [string] $LnkPath,
    [Parameter(Mandatory=$true)] [string] $AppId
)

$ErrorActionPreference = 'Stop'

if (-not (Test-Path -LiteralPath $LnkPath)) {
    throw "File not found: $LnkPath"
}
if ([System.IO.Path]::GetExtension($LnkPath).ToLowerInvariant() -ne '.lnk') {
    throw "Refusing to operate on non-.lnk file: $LnkPath"
}
$resolved = (Resolve-Path -LiteralPath $LnkPath).Path
if ($resolved -match '^::') {
    throw "Refusing shell namespace path: $resolved"
}

Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;

[StructLayout(LayoutKind.Sequential, Pack = 4)]
public struct PROPERTYKEY
{
    public Guid fmtid;
    public uint pid;
}

[StructLayout(LayoutKind.Sequential)]
public struct PROPVARIANT
{
    public ushort vt;
    public ushort r1;
    public ushort r2;
    public ushort r3;
    public IntPtr p;
    public IntPtr p2;
}

[ComImport]
[Guid("886D8EEB-8CF2-4446-8D02-CDBA1DBDCF99")]
[InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
public interface IPropertyStore
{
    [PreserveSig] int GetCount(out uint count);
    [PreserveSig] int GetAt(uint i, out PROPERTYKEY key);
    [PreserveSig] int GetValue(ref PROPERTYKEY key, out PROPVARIANT pv);
    [PreserveSig] int SetValue(ref PROPERTYKEY key, ref PROPVARIANT pv);
    [PreserveSig] int Commit();
}

public static class LnkAppId
{
    [DllImport("shell32.dll", CharSet = CharSet.Unicode, PreserveSig = false)]
    private static extern void SHGetPropertyStoreFromParsingName(
        [MarshalAs(UnmanagedType.LPWStr)] string pszPath,
        IntPtr zeroWorks,
        int flags,
        ref Guid riid,
        [MarshalAs(UnmanagedType.Interface)] out IPropertyStore propertyStore);

    [DllImport("ole32.dll", PreserveSig = false)]
    private static extern void PropVariantClear(ref PROPVARIANT pv);

    private static readonly Guid IID_IPropertyStore = new Guid("886D8EEB-8CF2-4446-8D02-CDBA1DBDCF99");
    private const int GPS_READWRITE = 0x2;
    private const ushort VT_LPWSTR = 31;

    public static void Set(string lnkPath, string appId)
    {
        IPropertyStore store;
        Guid iid = IID_IPropertyStore;
        SHGetPropertyStoreFromParsingName(lnkPath, IntPtr.Zero, GPS_READWRITE, ref iid, out store);
        try
        {
            PROPERTYKEY key = new PROPERTYKEY {
                fmtid = new Guid("9F4C2855-9F79-4B39-A8D0-E1D42DE1D5F3"),
                pid = 5
            };
            PROPVARIANT pv = new PROPVARIANT();
            pv.vt = VT_LPWSTR;
            pv.p = Marshal.StringToCoTaskMemUni(appId);
            try
            {
                int hr = store.SetValue(ref key, ref pv);
                if (hr < 0) throw new InvalidOperationException("SetValue HR=0x" + hr.ToString("X8"));
                hr = store.Commit();
                if (hr < 0) throw new InvalidOperationException("Commit HR=0x" + hr.ToString("X8"));
            }
            finally { PropVariantClear(ref pv); }
        }
        finally { Marshal.ReleaseComObject(store); }
    }

    public static string Get(string lnkPath)
    {
        IPropertyStore store;
        Guid iid = IID_IPropertyStore;
        SHGetPropertyStoreFromParsingName(lnkPath, IntPtr.Zero, 0, ref iid, out store);
        try
        {
            PROPERTYKEY key = new PROPERTYKEY {
                fmtid = new Guid("9F4C2855-9F79-4B39-A8D0-E1D42DE1D5F3"),
                pid = 5
            };
            PROPVARIANT pv;
            int hr = store.GetValue(ref key, out pv);
            try
            {
                if (hr != 0) return "<HR=0x" + hr.ToString("X8") + ">";
                if (pv.vt == VT_LPWSTR) return Marshal.PtrToStringUni(pv.p);
                return "<vt=" + pv.vt + ">";
            }
            finally { PropVariantClear(ref pv); }
        }
        finally { Marshal.ReleaseComObject(store); }
    }
}
"@ -ErrorAction Stop

[LnkAppId]::Set($resolved, $AppId)
$verify = [LnkAppId]::Get($resolved)
Write-Host "AppUserModel.ID on $resolved => $verify"
