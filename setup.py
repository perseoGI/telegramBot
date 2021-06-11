import os
import subprocess


def create_mo_files():
    data_files = []
    localedir = "locale"
    po_dirs = [
        localedir + "/" + l + "/LC_MESSAGES/" for l in next(os.walk(localedir))[1]
    ]

    for d in po_dirs:
        mo_files = []
        po_files = [f for f in next(os.walk(d))[2] if os.path.splitext(f)[1] == ".po"]
        for po_file in po_files:
            filename, extension = os.path.splitext(po_file)
            mo_file = filename + ".mo"
            msgfmt_cmd = "msgfmt {} -o {}".format(d + po_file, d + mo_file)
            print("Executing: ", msgfmt_cmd, "...")
            subprocess.call(msgfmt_cmd, shell=True)
            mo_files.append(d + mo_file)
        data_files.append((d, mo_files))
    return data_files


if __name__ == "__main__":
    mo_files = create_mo_files()
    print("Created following .mo files:")
    for _, mo_file in mo_files:
        print(mo_file)
