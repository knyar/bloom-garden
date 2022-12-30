#!/usr/bin/env python3

import argparse
import glob
import logging
import os
import os.path
import pathlib
import rtoml
import shutil
import subprocess
import tempfile
import time

def output_path(args):
    return os.path.join(args.out_dir, "public")

def is_empty(filename):
    with open(filename) as f:
        for line in f:
            if line.strip() != '-':
                return False
    return True

def remove_empty_md(dirname):
    for root, dirs, files in os.walk(dirname):
        for name in files:
            if not name.endswith('.md'):
                continue
            fname = os.path.join(root, name)
            if is_empty(fname):
                logging.info("Removing empty file %s", fname)
                os.unlink(fname)
                continue

def run(cmd, **kwargs):
    logging.info("Running %s", cmd)
    subprocess.run(cmd, check=True, **kwargs)

def rmtree(dirpath):
    if not os.path.isdir(dirpath):
        return
    logging.info("Cleaning up %s", dirpath)
    shutil.rmtree(dirpath)

def export_dump(args, filepath):
    logseq_dir = os.path.join(args.temp_dir, "logseq")
    rmtree(logseq_dir)

    cmd = ["clojure", "-X", "athens.export/export",
        ":athens", '"{}"'.format(filepath),
        ":logseq", '"{}"'.format(logseq_dir)]
    run(cmd, cwd=args.athens_export)

    logging.info("Removing empty files")
    remove_empty_md(logseq_dir)

    build_dir = os.path.join(args.temp_dir, "build")
    rmtree(build_dir)

    run(["rsync", "-a",
        "{}/zola/".format(args.obsidian_zola), build_dir])
    run(["rsync", "-a",
        "{}/content/".format(args.obsidian_zola),
        "{}/content/".format(build_dir)])
    os.mkdir(os.path.join(build_dir, "content", "docs"))

    obsidian_dir = os.path.join(build_dir, "__docs")
    os.mkdir(obsidian_dir)
    run(["obsidian-export", "--frontmatter=never", "--hard-linebreaks",
        "--no-recursive-embeds", logseq_dir, obsidian_dir])

    for fname in ["convert.py", "utils.py"]:
        logging.info("Copying %s", fname)
        shutil.copy(os.path.join(args.obsidian_zola, fname), args.temp_dir)

    logging.info("Reading %s", args.config_file)
    env = rtoml.load(pathlib.Path(args.config_file))["build"]["environment"]
    run(["python", "convert.py"], cwd=args.temp_dir, env=env)

    tmpprefix = "public_tmp_"
    tmpdir = tempfile.mkdtemp(prefix=tmpprefix, dir=args.out_dir)
    os.rmdir(tmpdir)  # zola expects a nonexistent directory
    run(["zola", "--root", build_dir, "build", "-o", tmpdir])
    tmplink = tmpdir + ".link"
    os.symlink(os.path.basename(tmpdir), tmplink)
    os.rename(tmplink, output_path(args))
    for d in glob.glob("{}/{}*".format(args.out_dir, tmpprefix)):
        if d != tmpdir:
            rmtree(d)


def find_dump(args, prev):
    """Finds the latest dump file and triggers export."""
    files = glob.glob("%s/*.json" % args.input_dir)
    if not files:
        logging.debug("No athens dumps found")
        return prev
    latest = max(files, key=os.path.getmtime)
    if latest == prev:
        logging.debug("Latest file has not changed (%s)", latest)
        return prev

    age = time.time() - os.path.getmtime(latest)
    if age < args.wait_sec:
        logging.debug(
            "Latest file (%s) is too fresh (%d sec)", latest, age)
        return prev

    logging.info("Exporting new dump %s (%d sec old)", latest, age)
    export_dump(args, latest)
    logging.info("Finished exporting dump %s", latest)
    return latest


def main():
    parser = argparse.ArgumentParser(
        description="Generates static website based on Athens content",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        "--input_dir", required=True,
        help="Directory with Athens database dumps")
    parser.add_argument(
        "--config_file", required=True, default="config.toml",
        help="Configuration file")
    parser.add_argument(
        "--temp_dir", required=True, help="Temporary directory")
    parser.add_argument(
        "--out_dir", required=True, help="Output directory")
    parser.add_argument(
        "--athens_export", required=True, help="Path to athens-export")
    parser.add_argument(
        "--obsidian_zola", required=True, help="Path to obsidian-zola")
    parser.add_argument(
        "--wait_sec", type=int, default=300,
        help="How long to wait for after Athen content has last been modified. "
        "(useful to avoid regenerating output based on partial changes)")
    parser.add_argument(
        "--interval_sec", type=int, default=10,
        help="Time between checking export files")
    parser.add_argument(
        "--debug", action="store_const", dest="loglevel",
        const=logging.DEBUG, default=logging.INFO, help="Enable debug logging")
    args = parser.parse_args()
    logging.basicConfig(
        format="%(asctime)-15s %(message)s", level=args.loglevel)

    o = output_path(args)
    if os.path.exists(o) and not os.path.islink(o):
        raise RuntimeError("expected %f to be a symlink")

    if not os.path.exists(args.out_dir):
        os.mkdir(args.out_dir)

    prev = None
    while True:
        prev = find_dump(args, prev)
        time.sleep(args.interval_sec)
    

if __name__ == "__main__":
    main()
