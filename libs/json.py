import os
import json
import gzip
import re

class JSON(object):
    @classmethod
    def serialize(cls, obj, path, folder, filename, append=False):

        if not os.path.exists(path):
            os.mkdir(path)

        if type(folder) is list:
            for f in folder:
                path = os.path.join(path, f)
                if not os.path.exists(path):
                    os.mkdir(path)
        else:
            path = os.path.join(path, folder)
            if not os.path.exists(path):
                os.mkdir(path)

        file = os.path.join(path, filename)
        if append:
            mode = 'a'
        else:
            mode = 'w'
        if filename.endswith('.gz'):
            json_string = json.dumps(obj, separators=(',',':'), ensure_ascii=False)
            if append:
                json_string = '\n' + json_string
            json_bytes = json_string.encode('utf-8')
            mode = mode + 'b'
            with gzip.open(file, mode) as compressed_json_file:
                compressed_json_file.write(json_bytes)
        else:
            with open(file, mode, encoding='utf8') as json_file:
                json.dump(obj, json_file, indent=4, separators=(',',':'), ensure_ascii=False)
                print(file, 'was serialized!')


    @classmethod
    def deserialize(cls, path, folder, filename):
        print(path, folder, filename)
        if type(folder) is list:
            file = os.path.join(path, *folder, filename)
        else:
            file = os.path.join(path, folder, filename)

        if not os.path.isfile(file):
            return None

        if filename.endswith('.gz'):
            with gzip.open(file, 'rb') as compressed_json_file:
                string = compressed_json_file.read().decode("utf-8")
            if string.startswith('\n'):
                obj = json.loads('['+re.sub('\n', ',', string.strip())+']')
            else:
                obj = json.loads(string)
            return obj
        else:
            with open(file, encoding='utf8') as json_file:
                obj = json.load(json_file)
                print(file, 'was deserialized!')
                return obj
