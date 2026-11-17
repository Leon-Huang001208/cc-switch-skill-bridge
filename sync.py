"""Render the two official Skill releases for CC Switch, without running upstream code."""
import argparse
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen
from zipfile import ZipFile

GRAPHIFY = "https://github.com/Graphify-Labs/graphify"
CLAW = "https://clawhub.ai"
SLUG = "skill-vetter-bak"
LIMIT = 24 * 1024 * 1024

def fetch(url, limit=LIMIT):
    req = Request(url, headers={"User-Agent": "cc-switch-skill-source-bridge"})
    with urlopen(req, timeout=35) as response:
        parsed = urlsplit(response.geturl())
        if parsed.scheme != "https" or parsed.hostname not in {
            "api.github.com", "github.com", "release-assets.githubusercontent.com",
            "objects.githubusercontent.com", "clawhub.ai", "www.clawhub.ai",
        }:
            raise ValueError("Unexpected upstream download location")
        data = response.read(limit + 1)
    if len(data)>limit:
        raise ValueError("Upstream response exceeds size limit")
    return data

def version(value):
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", value):
        raise ValueError("Unsupported release version")
    return value

def read_member(archive, member):
    name = PurePosixPath(member.filename)
    if name.is_absolute() or ".." in name.parts or "\\" in member.filename:
        raise ValueError("Unsafe archive member")
    mode=member.external_attr >> 16
    if stat.S_IFMT(mode) not in (0, stat.S_IFREG) or member.file_size>2*1024*1024:
        raise ValueError("Unexpected archive file type or size")
    return archive.read(member)

def skill_head(data, name):
    text=data.decode("utf-8")
    header=text.split("---",2)
    if len(header)<3 or header[0].strip() or not re.search(r'^name:\s*["\']?'+name+r'["\']?\s*$',header[1],re.M):
        raise ValueError(f"Unexpected Skill manifest for {name}")

def graphify_files(data, release):
    prefix="graphify/skills/codex/references/"
    license_prefix=f"graphifyy-{release}.dist-info/licenses/"
    selected={}
    with ZipFile(io.BytesIO(data)) as archive:
        for member in archive.infolist():
            n=member.filename
            if n=="graphify/skill-codex.md":
                target="SKILL.md"
            elif n.startswith(prefix) and re.fullmatch(r"[A-Za-z0-9_-]+\.md",n[len(prefix):]):
                target="references/"+n[len(prefix):]
            elif n.startswith(license_prefix) and n[len(license_prefix):] in {"LICENSE","LICENSE-MIT","NOTICE"}:
                target=n[len(license_prefix):]
            else:
                continue
            if target in selected:raise ValueError("Duplicate selected file")
            selected[target]=read_member(archive,member)
    if "SKILL.md" not in selected or "LICENSE" not in selected or not any(k.startswith("references/") for k in selected):
        raise ValueError("Graphify release layout changed")
    skill_head(selected["SKILL.md"],"graphify")
    return selected

def vetter_files(data, canonical, release):
    selected={}
    with ZipFile(io.BytesIO(data)) as archive:
        for member in archive.infolist():
            n=member.filename
            if n not in {"SKILL.md","skill-card.md","_meta.json"} or n in selected:
                raise ValueError("Unexpected file in approved skill-vetter release")
            selected[n]=read_member(archive,member)
    if selected.get("SKILL.md")!=canonical:
        raise ValueError("ClawHub ZIP differs from its versioned canonical file")
    if "_meta.json" in selected:
        if json.loads(selected.pop("_meta.json"))["version"] != release:
            raise ValueError("Unexpected ClawHub archive version")
    skill_head(canonical,"skill-vetter")
    return selected

def online():
    release=json.loads(fetch("https://api.github.com/repos/Graphify-Labs/graphify/releases/latest",1048576))
    g=version(release["tag_name"].removeprefix("v"))
    asset_name=f"graphifyy-{g}-py3-none-any.whl"
    assets=[a for a in release["assets"] if a["name"]==asset_name]
    if len(assets)!=1:raise ValueError("Expected one official Graphify wheel")
    asset=assets[0]
    url=f"{GRAPHIFY}/releases/download/v{g}/{asset_name}"
    if asset["browser_download_url"] != url or not re.fullmatch(r"sha256:[0-9a-f]{64}",asset.get("digest","")):
        raise ValueError("Unexpected Graphify release identity")
    wheel=fetch(url)
    if "sha256:"+hashlib.sha256(wheel).hexdigest()!=asset["digest"]:
        raise ValueError("Graphify release digest mismatch")

    meta=json.loads(fetch(f"{CLAW}/api/v1/skills/{SLUG}",1048576))
    if meta["skill"]["slug"]!=SLUG or meta["owner"]["handle"]!="aysun168":
        raise ValueError("ClawHub publisher or slug changed")
    s=version(meta["latestVersion"]["version"])
    bundle=fetch(f"{CLAW}/api/v1/download?"+urlencode({"slug":SLUG,"version":s}),2097152)
    body=fetch(f"{CLAW}/api/v1/skills/{SLUG}/file?"+urlencode({"path":"SKILL.md","version":s}),2097152)
    return (g,wheel,s,bundle,body)

def write(root,name,files,provenance):
    destination=root/"skills"/name
    parents=(root,root/"skills",destination)
    if any(p.is_symlink() for p in parents):
        raise ValueError("Unexpected output symlink")
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True)
    for relative,data in files.items():
        path=destination/relative
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(data)
    (destination/"UPSTREAM.json").write_text(json.dumps(provenance,sort_keys=True,indent=2)+"\n")

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--fixture",type=Path,help="use verified local packages instead of downloading latest")
    args=parser.parse_args()
    if args.fixture:
        g,s="0.9.111","1.0.0"
        p=args.fixture
        wheel=(p/f"graphifyy-{g}-py3-none-any.whl").read_bytes()
        bundle=(p/f"skill-vetter-{s}.zip").read_bytes()
        body=(p/"skill-vetter-canonical.md").read_bytes()
        if hashlib.sha256(wheel).hexdigest()!="1357a12b0f18b64ce0ab2ace16bdd5ae9c20282e192bc77f41fd6aec1ca2d006":
            raise ValueError("Graphify fixture digest mismatch")
    else:
        g,wheel,s,bundle,body=online()
    graph=graphify_files(wheel,g)
    vetter=vetter_files(bundle,body,s)
    root=Path(__file__).resolve().parent
    write(root,"graphify",graph,{"version":g,"release":f"{GRAPHIFY}/releases/tag/v{g}","artifact_sha256":hashlib.sha256(wheel).hexdigest(),"source_file":"graphify/skill-codex.md","scope":"Skill files only; graphifyy CLI is managed separately"})
    write(root,"skill-vetter",vetter,{"version":s,"release":f"{CLAW}/aysun168/skills/{SLUG}","artifact_sha256":hashlib.sha256(bundle).hexdigest(),"license":"MIT-0"})
    print(f"Verified Graphify {g} and skill-vetter {s}")

if __name__=="__main__":
    main()
