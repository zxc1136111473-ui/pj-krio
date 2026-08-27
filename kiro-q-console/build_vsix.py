#!/usr/bin/env python3
"""把 kiro-q-console/ 打成标准 VSIX（无需 node/vsce）。输出到仓库根 kiro-q-console.vsix。"""
import json
import pathlib
import sys
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent
OUT = ROOT.parent / "kiro-q-console.vsix"

FILES = [
    "package.json",
    "extension.js",
    "README.md",
    "CHANGELOG.md",
    "media/style.css",
    "media/panel.js",
]

pkg = json.loads((ROOT / "package.json").read_text())
ext_id = f"{pkg['publisher']}.{pkg['name']}"
version = pkg["version"]

manifest = f"""<?xml version="1.0" encoding="utf-8"?>
<PackageManifest Version="2.0.0" xmlns="http://schemas.microsoft.com/developer/vsx-schema/2011" xmlns:d="http://schemas.microsoft.com/developer/vsx-schema-design/2011">
  <Metadata>
    <Identity Language="en-US" Id="{ext_id}" Version="{version}" Publisher="{pkg['publisher']}" />
    <DisplayName>{pkg['displayName']}</DisplayName>
    <Description xml:space="preserve">{pkg['description']}</Description>
    <Tags>kiro,q-console,amazon-q</Tags>
    <Categories>Other</Categories>
  </Metadata>
  <Installation>
    <InstallationTarget Id="Microsoft.VisualStudio.Code" />
  </Installation>
  <Dependencies />
  <Assets>
    <Asset Type="Microsoft.VisualStudio.Code.Manifest" Path="extension/package.json" />
    <Asset Type="Microsoft.VisualStudio.Services.Content.Details" Path="extension/README.md" />
    <Asset Type="Microsoft.VisualStudio.Services.Content.Changelog" Path="extension/CHANGELOG.md" />
  </Assets>
</PackageManifest>
"""

content_types = """<?xml version="1.0" encoding="utf-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="vsixmanifest" ContentType="text/xml" />
  <Default Extension="json" ContentType="application/json" />
  <Default Extension="js" ContentType="application/javascript" />
  <Default Extension="css" ContentType="text/css" />
  <Default Extension="md" ContentType="text/markdown" />
</Types>
"""

missing = [f for f in FILES if not (ROOT / f).exists()]
if missing:
    print("缺少文件:", missing, file=sys.stderr)
    sys.exit(1)

with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
    z.writestr("[Content_Types].xml", content_types)
    z.writestr("extension.vsixmanifest", manifest)
    for f in FILES:
        z.write(ROOT / f, f"extension/{f}")

print(f"OK -> {OUT} ({OUT.stat().st_size} bytes, {ext_id}@{version})")
