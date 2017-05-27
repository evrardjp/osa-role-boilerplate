#!/usr/bin/env python

import argparse
import errno
import logging
import os
import re
import shutil
import sys
# import yaml


def build_parser():
    parser = argparse.ArgumentParser(description='Build an OSA role.')
    # Mandatory args
    parser.add_argument(
        "-in", "--master",
        help="The folder where your master repo is located"
    )
    parser.add_argument(
        "-out", "--builder",
        default="generated_role",
        help="The folder where your generated repo will be stored"
    )
    parser.add_argument(
        "--rolename",
        default="neutron",
        help="This will be replaced by {{ role_name }}"
    )
#    parser.add_argument(
#        "--seds",
#        default="seds",
#        help="Contents of this folder will be applied."
#    )
    parser.add_argument(
        "--prevent_delete",
        help="Prevents the deletion of existing folder",
        action="store_true"
    )
    return parser


def validate_args(args):
    # Validate IN
    if not os.path.isdir(args.master):
        raise SystemExit("The master folder isn't given")
    # Validate out
    try:
        os.mkdir(args.builder)
    except FileExistsError:
        logging.warning("The path already exists")
        if args.prevent_delete:
            raise SystemExit(
                "Prevent delete is on, and output folder exists."
            )
        else:
            logging.warning("Deleting {}".format(args.builder))
            shutil.rmtree(args.builder)
    return (args.master, args.builder)


def filterfiles(folder):
    filtered = []
    # Single line string pattern
    pattern = (".*/("
               "\.git|"
               "library|releasenotes/notes/|"
               "doc/source/!(conf.py|index.rst)"
               ")")
    for (root, dirs, files) in os.walk(folder):
        # dirs[:] = [d for d in dirs if d not in exclude]
        # This needs topdown=True in the os walk
        # and is far less readable
        for filename in files:
            fullname = os.path.join(root, filename)
            if not re.match(pattern, fullname):
                filtered.append(fullname)
    return filtered


def create_folders(filenames, src_folder, dest_folder):
    folders = set()
    for f in filenames:
        folders.add(os.path.dirname(f).replace(src_folder, dest_folder))
    for f in folders:
        mkdir_p(f)


def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def write_file(filename, src_folder, dest_folder, oldrolename):
    with open(filename, 'r') as f:
        content = f.read()
    content = template_content(content, oldrolename)

    destination_file = filename.replace(src_folder, dest_folder)
    with open(destination_file + '.j2', 'w') as wf:
        wf.write(content)


def template_content(content, oldrolename):
    replacer = []
    replacer.append(['{% ', '{% raw %}{% {% endraw %}'])
    replacer.append([' %}', '{% raw %} %}{% endraw %}'])
    replacer.append(['{{ ', '{% raw %}{{ {% endraw %}'])
    replacer.append([' }}', '{% raw %} }}{% endraw %}'])
    replacer.append(['os_' + oldrolename, '{{ role_name }}'])
    replacer.append([oldrolename, '{{ role_name }}'])
    replacer.append([oldrolename.capitalize(), '{{ role_name }}'])
    for undesired, desired in replacer:
        content = content.replace(undesired, desired)
    return content


# def extra_seds(seds_folder, dest_folder):
#     sedfiles = []
#     try:
#         for (root, dirs, files) in os.walk(seds_folder):
#             for filename in files:
#                 sedfiles.append(os.path.join(root, filename))
#     except OSError as exc:  # Python >2.5
#         if not os.path.isdir(seds_folder):
#             pass
#         else:
#             raise
#     #for sf in sed_files:
#     #    with open(sf, 'r') as sfd:
#     #        sedfile_lines = sfd.readlines()
#     #    file_to_modify = sf.replace(seds_folder, destfolder)+'.j2'
#     #    with open(file_to_modify, "r") as ftm_fd:
#     #        ftm_lines = ftm_fd.readlines()
#     #        ftm_fd.close()
#     #    with open(file_to_modify, "w") as ftm_fd:
#     #         ftm_fd.writelines(exclude())
#     #        to_modify_file_lines = to_modify_fd.readlines()


def main():
    logging.getLogger().setLevel(logging.INFO)
    parser = build_parser()
    cli_args = parser.parse_args()
    source, dest = validate_args(cli_args)
    source_list = filterfiles(source)
    create_folders(source_list, source, dest)
    for f in source_list:
        write_file(f, source, dest, cli_args.rolename)


if __name__ == "__main__":
    sys.exit(main())
