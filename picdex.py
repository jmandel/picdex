import os.path
import json
import time
import subprocess
import copy
from datetime import datetime, timedelta

CHUNK_SIZE_NFILES = 200

class Processor(object):
    def __init__(self, config_file):
        self.config_file = config_file
        self.config_dir = os.path.dirname(self.config_file)
        self.db = config_load(self.config_file)
    def update_db(self):
        update_db(self.db, self.config_dir)
    def save(self):
        config_save(self.db, self.config_file)

def to_epoch(dt):
    return int(time.mktime(dt.timetuple()))

def merge_dicts(*dict_args):
    result = {}
    for dictionary in dict_args:
        result.update(dictionary)
    return result

def config_load(f):
    if os.path.exists(f):
        with open(f, "r") as fp:
            try: return json.load(fp)
            except: pass
    print("Building new catalog")
    return {
        'last_run_at': to_epoch(datetime(1900, 1, 1)),
        'images': {}
    }

def config_save(c, f):
    with open(f, "w") as fp:
        json.dump(c, fp, indent=2)

def files_since(when, dir_to_scan):
    ret = []
    for root, dirs, files in os.walk(dir_to_scan, topdown=False):
        for fpath in [os.path.join(root, p) for p in files]:
            fpath_name, fpath_ext = os.path.splitext(fpath)
            if fpath_ext.lower() not in ['.jpg', '.png', '.gif']:
                continue
            if os.stat(fpath).st_ctime < when:
                continue
            ret.append(fpath)

    return ret

def time_of(tstring):
    d = datetime.strptime(tstring[:19], "%Y:%m:%d %H:%M:%S")
    return to_epoch(d)

def chunks(l, n):
    for i in range(0, len(l), n):
        yield l[i:i+n]

def get_exif_in_chunks(files, dir_to_scan):
    ret = {}
    for filechunk in chunks(files, CHUNK_SIZE_NFILES):
        ret.update(get_exif(filechunk, dir_to_scan))
    return ret

def get_exif(files, dir_to_scan):

    ret = {}
    if len(files) == 0:
        return ret

    cmd = ["exiftool", "-json"] + files

    exif_json = subprocess.check_output(cmd)
    exif = json.loads(exif_json.decode("utf-8"))

    for scanned in exif:
        fpath = os.path.relpath(scanned['SourceFile'], dir_to_scan)
        scanned['SourceFile'] = fpath
        ret[fpath] = {
            'file': scanned['SourceFile'],
            'cam': scanned['Model'] if 'Model' in scanned else None,
            'lens': scanned['LensType'] if 'LensType' in scanned else None,
            'rating': scanned['Rating'] if 'Rating' in scanned else None,
            't': time_of(scanned['CreateDate']) if 'CreateDate' in scanned else None,
            'f': scanned['ExposureTime'] if 'ExposureTime' in scanned else None,
            'a': scanned['Aperture'] if 'Aperture' in scanned else None,
            'w': scanned['ImageWidth'] if 'ImageWidth' in scanned else None,
            'l': scanned['FocalLength'] if 'FocalLength' in scanned else None,
            'h': scanned['ImageHeight'] if 'ImageHeight' in scanned else None,
            'i': scanned['ISO'] if 'ISO' in scanned else None
        }
    return ret

def update_db(config, config_dir):
    this_run_at = to_epoch(datetime.now())
    new_images = files_since(config['last_run_at'], config_dir)
    print("getting exif for", len(new_images), "images")
    new_db_entries = get_exif_in_chunks(new_images, config_dir)
    config['images'].update(new_db_entries)
    config['last_run_at'] = this_run_at
    return config

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("dir", help="Directory to process")
    args = parser.parse_args()

    where = os.path.join(os.getcwd(), args.dir, "catalog.json")
    p = Processor(where)
    p.update_db()
    p.save()
