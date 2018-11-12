import re


class AudioFile:
    def __init__(self, filename):
        self.filename = filename
        self.file_is_flac()
        self.positions = {}
        self.parse_metadata()
        self.streaminfo = {}
        self.parse_streaminfo()
        self.tags = None
        self.picture = None
        if 'vorbis comment' in self.positions:
            self.tags = self.parse_vorbis_comment()
        if 'picture' in self.positions:
            self.picture = self.parse_picture()

    def file_is_flac(self):
        with open(self.filename, 'rb') as f:
            file = f.read()
            if file[0:4].decode() != 'fLaC':
                raise Exception('file is not flac')

    @staticmethod
    def parse_metadata_block_header(header):
        flag_and_type = bin(header[0])[2:].zfill(8)
        is_last = int(flag_and_type[0])
        type_of_block = int(flag_and_type[1:], 2)
        size = int.from_bytes(header[1:], byteorder='big')
        return is_last, type_of_block, size

    def parse_vorbis_comment(self):
        tags = {}
        with open(self.filename, 'rb') as f:
            file = f.read()
            begin, end = self.positions['vorbis comment']
            block = file[begin:end]
        vendor_length = int.from_bytes(block[0:4], byteorder='little')
        vendor = block[4:4+vendor_length].decode()
        tags['vendor'] = vendor
        tags_count = int.from_bytes(block[4+vendor_length:8+vendor_length],
                                        byteorder='little')
        pos = 8 + vendor_length
        tag_regex = re.compile('(.+?)=(.+)')
        for i in range(0, tags_count):
            length = int.from_bytes(block[pos:pos+4], byteorder='little')
            tag = tag_regex.match(block[pos+4:pos+4+length].decode())
            tag_name = tag.group(1)
            tag_value = tag.group(2)
            if tag_name in tags:
                tags[tag_name].add(tag_value)
            else:
                tags[tag_name] = {tag_value}
            pos += 4 + length
        return tags

    def parse_streaminfo(self):
        with open(self.filename, 'rb') as f:
            file = f.read()
            begin, end = self.positions['streaminfo']
            block = file[begin:end]
        self.streaminfo['block_minsize'] = \
            int.from_bytes(block[0:2], byteorder='big')
        self.streaminfo['block_maxsize'] = \
            int.from_bytes(block[2:4], byteorder='big')
        self.streaminfo['frame_minsize'] = \
            int.from_bytes(block[4:7], byteorder='big')
        self.streaminfo['frame_maxsize'] = \
            int.from_bytes(block[7:10], byteorder='big')
        data = bin(int.from_bytes(block[10:18], byteorder='big'))[2:].zfill(64)
        self.streaminfo['rate'] = int(data[0:20], 2)
        self.streaminfo['channels'] = int(data[20:23], 2) + 1
        self.streaminfo['bits per sample'] = int(data[23:28], 2) + 1
        self.streaminfo['samples in flow'] = int(data[28:64], 2)

    def parse_picture(self):
        with open(self.filename, 'rb') as f:
            file = f.read()
            begin, end = self.positions['picture'][0]
            block = file[begin:end]
        ext_regex = re.compile('.+?/(.+)')
        ext_len = int.from_bytes(block[4:8], byteorder='big')
        ext = ext_regex.match(block[8:8+ext_len].decode()).group(1)
        descr_len = int.from_bytes(block[8+ext_len:8+ext_len+4], byteorder='big')
        descr = block[8+ext_len+4:8+ext_len+4+descr_len].decode()
        pic_len = int.from_bytes(block[8+ext_len+4+descr_len+16:8+ext_len+4+descr_len+20], byteorder='big')
        pic = block[8+ext_len+4+descr_len+20:8+ext_len+4+descr_len+pic_len]
        return pic, ext

    def parse_metadata(self):
        with open(self.filename, 'rb') as f:
            file = f.read()
            pos = 4
            is_last = False
            while not is_last:
                is_last, type_of_block, size = \
                    self.parse_metadata_block_header(file[pos:pos+4])
                positions = (pos+4, pos+4+size)
                if type_of_block == 0:
                    self.positions['streaminfo'] = positions
                if type_of_block == 4:
                    self.positions['vorbis comment'] = positions
                if type_of_block == 6:
                    if 'picture' not in self.positions:
                        self.positions['picture'] = [positions]
                    else:
                        self.positions['picture'].append(positions)
                pos += size + 4

    def save_picture(self):
        with open('pic.{}'.format(self.picture[1]), 'wb') as f:
            f.write(self.picture[0])

    def make_text(self):
        text = '''                      minimum block size: {0} samples
                                  maximum block size: {1} samples
                                  minimum frame size: {2} bytes
                                  maximum frame size: {3} bytes
                                  sample rate: {4} Hz
                                  number of channels: {5}
                                  bits per sample: {6}
                                  samples in stream: {7}'''.format(self.streaminfo['block_minsize'],
                                                                   self.streaminfo['block_maxsize'],
                                                                   self.streaminfo['frame_minsize'],
                                                                   self.streaminfo['frame_maxsize'],
                                                                   self.streaminfo['rate'],
                                                                   self.streaminfo['channels'],
                                                                   self.streaminfo['bits per sample'],
                                                                   self.streaminfo['samples in flow'])
        if self.tags:
            tags = ''
            for tag in self.tags:
                if tag is 'vendor': continue
                i = 0
                tags += '\n                      {0}: '.format(tag)
                for tag_value in self.tags[tag]:
                    tags += tag_value
                    if i != len(self.tags[tag]) - 1:
                        tags += ', '
                    i += 1
            text += tags

        return text
