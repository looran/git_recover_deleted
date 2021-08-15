#!/usr/bin/env python

import re
import sys
import pathlib
import argparse
import subprocess

EPILOG = "go through git history and copy each deleted files to <output_dir>/<filenum>_<commitnum>_<path>"

VERBOSE = 0

def verb(msg):
    global VERBOSE
    if VERBOSE > 0:
        print(msg)

def err(msg):
    print("error: %s" % msg)
    sys.exit(1)

def parse_commits(stdout):
    commits = list()
    files_deleted = list()
    last_file = None
    for l in stdout:
        verb("line: %s" % l)
        l = l.decode(errors='ignore').strip()
        g = re.match(r"^commit (?P<commitnum>[a-f0-9]+)", l)
        if g:
            d = { 'commit': g.group('commitnum'), 'files_deleted': files_deleted, }
            commits.append(d)
            files_deleted = list()
            verb("C")
            continue
        g = re.match(r"^diff --git (?P<src>[^ ]+) (?P<dst>[^ ]+)", l)
        if g:
            verb("G %s %s" % (g.group('src'), g.group('dst')))
            last_file = g.group('src')[2:]
            continue
        g = re.match(r"^deleted .*", l)
        if g:
            files_deleted.append(last_file)
            verb("D %s" % last_file)
            continue
    return commits

def main():
    global VERBOSE

    parser = argparse.ArgumentParser(epilog=EPILOG)
    parser.add_argument('output_dir', help="Output directory")
    parser.add_argument('filter', nargs='?', help="Filter changes to files name (eg. *.png)")
    parser.add_argument('-p', '--pretend', action="store_true", help="do not actually copy files")
    parser.add_argument('-v', '--verbose', action="store_true", help="print verbose")
    args = parser.parse_args()

    if args.verbose:
        VERBOSE = True

    path_git = pathlib.Path('.')
    path_out = pathlib.Path(args.output_dir)
    if not path_out.is_dir():
        err("%s is not a directory" % path_out)
    if path_out.is_relative_to(path_git):
        err("output_dir %s must not be in git %s" % (path_out, path_git.resolve()))

    #"git remote show $(git remote) |sed -n '/HEAD branch/s/.*: //p'")
    branch = subprocess.Popen(['git', 'branch', '--show-current'], stdout=subprocess.PIPE)
    branch_out = branch.stdout.readlines()
    if len(branch_out) != 1:
        err("error getting current branch")
    git_start_branch = branch_out[0].strip()
    print("git current branch : %s" % git_start_branch)

    cmd_git_log = ['git', 'log', '-u']
    if args.filter:
        cmd_git_log.append(args.filter)

    git_log = subprocess.Popen(cmd_git_log, stdout=subprocess.PIPE)
    files_count = 0
    for commit in parse_commits(git_log.stdout.readlines()):
       if len(commit['files_deleted']) > 0:
            print("[+] checkout %s" % commit['commit'])
            checkout = subprocess.Popen(['git', 'checkout', commit['commit']], stdout=subprocess.PIPE)
            if checkout.wait() != 0:
                err("checkout %s failed")
            for deleted in commit['files_deleted']:
                files_count += 1
                orig = deleted
                dest_file = "%s_%s_%s" % (files_count, commit['commit'], deleted.replace('/', '_'))
                dest = path_out / dest_file
                verb("copying %s to %s" % (orig, dest))
                if args.pretend is False:
                    copy = subprocess.Popen(['cp', orig, dest], stdout=subprocess.PIPE)
                    if copy.wait() != 0:
                        err("failed copy from %s to %s" % (orig, dest))

    print("[+] restoring start branch : %s" % git_start_branch)
    checkout = subprocess.Popen(['git', 'checkout', git_start_branch], stdout=subprocess.PIPE)
    if checkout.wait() != 0:
        err("error restoring branch")

    print("[*] DONE, copied %d files to %s" % (files_count, path_out))

main()
