import re


class AudioFile:
    def __init__(self, filename, parse_frames=True):
        self.filename = filename
        self.file_is_flac()
        self.frames = []
        self.positions = {}
        self.first_frame = self.parse_metadata()
        self.streaminfo = {}
        self.parse_streaminfo()
        self.blocking_strategy = self.streaminfo['block_minsize'] == self.streaminfo['block_maxsize']
        if parse_frames:
            self.parse_frames()
        self.tags = None
        self.picture = []
        if 'vorbis comment' in self.positions:
            self.tags = self.parse_vorbis_comment()
        if 'picture' in self.positions:
            for i in range(0, len(self.positions['picture'])):
                self.picture.append(self.parse_picture(i))

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

    def parse_picture(self, i):
        with open(self.filename, 'rb') as f:
            file = f.read()
            begin, end = self.positions['picture'][i]
            block = file[begin:end]
        pic_type = int.from_bytes(block[0:4], byteorder='big')
        if pic_type == 0:
            pic_type = 'other'
        if pic_type == 1:
            pic_type = '32x32 pixels file icon'
        if pic_type == 2:
            pic_type = 'Other file icon'
        if pic_type == 3:
            pic_type = 'Cover (front)'
        if pic_type == 4:
            pic_type = 'Cover (back)'
        if pic_type == 5:
            pic_type = 'Leaflet page'
        if pic_type == 6:
            pic_type = 'Media'
        if pic_type == 7:
            pic_type = 'Lead artist/lead performer/soloist'
        if pic_type == 8:
            pic_type = 'Artist/performer'
        if pic_type == 9:
            pic_type = 'Conductor'
        if pic_type == 10:
            pic_type = 'Band/Orchestra'
        if pic_type == 11:
            pic_type = 'Composer'
        if pic_type == 12:
            pic_type = 'Lyricist/text writer'
        if pic_type == 13:
            pic_type = 'Recording Location'
        if pic_type == 14:
            pic_type = 'During recording'
        if pic_type == 15:
            pic_type = 'During performance'
        if pic_type == 16:
            pic_type = 'Movie/video screen capture'
        if pic_type == 17:
            pic_type = 'A bright coloured fish'
        if pic_type == 18:
            pic_type = 'Illustration'
        if pic_type == 19:
            pic_type = 'Band/artist logotype'
        if pic_type == 20:
            pic_type = 'Publisher/Studio logotype'


        ext_regex = re.compile('.+?/(.+)')
        ext_len = int.from_bytes(block[4:8], byteorder='big')
        mime_type = block[8:8+ext_len].decode()
        ext = ext_regex.match(block[8:8+ext_len].decode()).group(1)
        descr_len = int.from_bytes(block[8+ext_len:8+ext_len+4], byteorder='big')
        descr = block[8+ext_len+4:8+ext_len+4+descr_len].decode()
        width = int.from_bytes(block[12+ext_len+descr_len: 16+ext_len+descr_len], byteorder='big')
        height = int.from_bytes(block[16+ext_len+descr_len: 20+ext_len+descr_len], byteorder='big')
        color_depth = int.from_bytes(block[20+ext_len+descr_len:24+ext_len+descr_len], byteorder='big')
        number_of_color = int.from_bytes(block[24+ext_len+descr_len:28+ext_len+descr_len], byteorder='big')
        pic_len = int.from_bytes(block[8+ext_len+4+descr_len+16:8+ext_len+4+descr_len+20], byteorder='big')
        pic = block[8+ext_len+4+descr_len+20:8+ext_len+4+descr_len+pic_len]
        # return pic, ext
        return {'picture type': pic_type, 'mime type': mime_type, 'extension': ext, 'description': descr, 'width': width,
                'height': height, 'color depth': color_depth, 'number of colors': number_of_color, 'pic': pic}

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
        return pos

    def parse_frames(self):
        with open(self.filename, 'rb') as f:
            file = f.read()
            pos = self.first_frame
            counter = -1
            while pos < len(file):
                a = bin(int.from_bytes(file[pos:pos+2], byteorder='big'))[2:16]
                if bin(int.from_bytes(file[pos:pos+2], byteorder='big'))[2:16] != '11111111111110':
                    pos += 1
                else:
                    counter += 1
                    data = bin(file[pos+2])[2:].zfill(8)
                    block_size = int(data[:4], 2)
                    if block_size == 0:
                        block_size = self.streaminfo['block_maxsize']
                    if block_size == 1:
                        block_size = 192
                    if 2 <= block_size <= 5:
                        block_size = 576*2**(block_size-2)
                    if 8 <= block_size <= 15:
                        block_size = 256*2**(block_size-8)
                    if block_size == 6 or block_size == 7:
                        block_size = None
                    sample_rate = int(data[4:], 2)
                    if sample_rate == 0:
                        sample_rate = self.streaminfo['rate']
                    if sample_rate == 1:
                        sample_rate == 88,2
                    if sample_rate == 2:
                        sample_rate = 176.4
                    if sample_rate == 3:
                        sample_rate = 192
                    if sample_rate == 4:
                        sample_rate = 8
                    if sample_rate == 5:
                        sample_rate = 16
                    if sample_rate == 6:
                        sample_rate = 22.05
                    if sample_rate == 7:
                        sample_rate = 24
                    if sample_rate == 8:
                        sample_rate = 32
                    if sample_rate == 9:
                        sample_rate = 44.1
                    if sample_rate == 10:
                        sample_rate = 48
                    if sample_rate == 11:
                        sample_rate = 96
                    if 12 <= sample_rate <= 14:
                        sample_rate = None
                    data = bin(file[pos + 3])[2:].zfill(8)
                    channels = int(data[:4], 2)
                    if 0 <= channels <= 8:
                        channels += 1
                    if channels == 16:
                        channels = 'left/side stereo'
                    if channels == 17:
                        channels = 'right/side stereo'
                    if channels == 18:
                        channels == 'mid/side stereo'
                    sample_size = int(data[4:7], 2)
                    if sample_size == 0:
                        sample_size = self.streaminfo['bits per sample']
                    if sample_size == 1:
                        sample_size = 8
                    if sample_size == 2:
                        sample_size == 12
                    if sample_size == 4:
                        sample_size = 16
                    if sample_size == 5:
                        sample_size = 20
                    if sample_size == 6:
                        sample_size = 24
                    pos += self.streaminfo['frame_minsize']
                    self.frames.append({})
                    self.frames[counter]['block size'] = block_size
                    self.frames[counter]['sample rate'] = sample_rate
                    self.frames[counter]['channels'] = channels
                    self.frames[counter]['sample size'] = sample_size

    def save_picture(self):
        with open('pic.{}'.format(self.picture[0]['extension']), 'wb') as f:
            f.write(self.picture[0]['pic'])

    def make_text(self):
        text = '''STREAMINFO:
        minimum block size: {0} samples
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
            tags = '\nVORBIS COMMENT:'
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

        if self.picture:
            pictures = '\nPICTURES:'
            for i in range(0, len(self.picture)):
                pictures += '''{0}. Type of picture:{1}
                Format of picture: {2}
                Description: {3}
                Width: {4}
                Height: {5}
                Color depth: {6}
                Number of colors: {7}\n'''.format(str(i+1), self.picture[i]['picture type'],
                                                self.picture[i]['mime type'],
                                                self.picture[i]['description'],
                                                self.picture[i]['width'],
                                                self.picture[i]['height'],
                                                self.picture[i]['color depth'],
                                                self.picture[i]['number of colors'])
            text += pictures

        return text

if __name__ == '__main__':
    a = AudioFile('sample2.flac')
    print(len(a.frames))
