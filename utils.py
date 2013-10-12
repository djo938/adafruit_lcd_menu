#Embedded file name: /Volumes/Home/development/goprodumper/utils.py
import shutil
import os
import hashlib
import glob

def parse_df():
    results = []
    lines = os.popen('df -h')
    first = True
    ColumnCount = 0
    for line in lines:
        line_items = line.split()
        if first:
            first = False
            ColumnCount = len(line_items) - 1
            lastColumn = line_items[ColumnCount - 1] + ' ' + line_items[ColumnCount]
            line_items = line_items[:-1]
            line_items[ColumnCount - 1] = lastColumn
            results.append(line_items)
            continue
        if not line_items[0].startswith('/dev/'):
            continue
        last_column = ''
        first_col = True
        for i in range(ColumnCount - 1, len(line_items)):
            if first_col:
                first_col = False
                last_column += line_items[i]
            else:
                last_column += ' ' + line_items[i]

        line_items = line_items[:ColumnCount - 1]
        line_items.append(last_column)
        results.append(line_items)

    return results


def hash_file(file_path, block_size = 512, max_block_to_hash = 2000):
    """hash the content prefix of a file"""
    m = hashlib.sha256()
    m.update(file_path)
    with open(file_path, 'rb') as fh:
        iterator = 0
        while iterator < max_block_to_hash:
            data = fh.read(512)
            if not data:
                break
            m.update(data)
            iterator += 1

    return m.hexdigest()


def getLastDirectory(destination_folder, DIRECTORY_PREFIX):
    """find the directory backup in destination_folder with the highest id"""
    dir_list = glob.glob(destination_folder + os.sep + DIRECTORY_PREFIX + '*')
    last_dir = 0
    last_path = None
    for path in dir_list:
        try:
            index = path.rfind(DIRECTORY_PREFIX)
            index += len(DIRECTORY_PREFIX)
            dir_num = int(path[index:])
            if dir_num > last_dir:
                last_dir = dir_num
                last_path = path
        except ValueError:
            continue

    return (last_path, last_dir)


def compute_files_dico(origin_folder):
    origin_folder_list = os.walk(origin_folder)
    files_dico = {}
    total_files = 0
    for folder in origin_folder_list:
        total_files += len(folder[2])
        for lfile in folder[2]:
            origin_local_path = folder[0][len(origin_folder):] + os.sep + lfile
            origin_complete_path = folder[0] + os.sep + lfile
            files_dico[origin_local_path] = (os.path.getsize(origin_complete_path),
             hash_file(origin_complete_path),
             origin_complete_path,
             lfile)

    return files_dico


def append_information_to_directory(main_id, data_array, BACKUP_METADATA_DIRECTORY, sub_id = None, data_sep = ' '):
    """Cette fonction permet d'ajouter une ligne dans un fichier sans buffering"""
    line = ''
    for d in data_array:
        line += str(d) + data_sep

    line += '\n\r'
    file_name = BACKUP_METADATA_DIRECTORY + os.sep + str(main_id)
    if sub_id != None:
        file_name += os.sep + str(sub_id)
    with open(file_name, 'a', 0) as f:
        f.write(line)
        f.flush()
        f.close()


def load_hash_file_from_directory(main_id, BACKUP_METADATA_DIRECTORY, sub_id = None, data_sep = ' '):
    """cette fonction permet de charger le contenu d'un fichier de lignes"""
    to_return = {}
    file_name = BACKUP_METADATA_DIRECTORY + os.sep + str(main_id)
    if sub_id != None:
        file_name += os.sep + str(sub_id)
    with open(file_name, 'r') as f:
        while True:
            line = f.readline()
            if line == None or line == '':
                break
            line = line.strip()
            if len(line) == 0:
                continue
            line_part = line.split(data_sep)
            filtered_data = []
            for part in line_part:
                if len(part) > 0:
                    filtered_data.append(part)

            if len(filtered_data) > 1:
                to_return[filtered_data[0]] = filtered_data[1:]

        f.close()
    return to_return


if __name__ == '__main__':
    for line in parse_df():
        print line
