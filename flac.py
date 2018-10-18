import re


def file_is_flac(filename):
    with open(filename, 'rb') as f:
        file = f.read()
        if file[0:4].decode() != 'fLaC':
            raise Exception('file is not flac')


def parse_metadata_block_header(header):
    flag_and_type = bin(header[0])[2:].zfill(8)
    is_last = int(flag_and_type[0])
    type_of_block = int(flag_and_type[1:], 2)
    size = int.from_bytes(header[1:], byteorder='big')
    return is_last, type_of_block, size


def parse_vorbis_comment(block):
    tags = {}
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


def parse_metadata(filename):
    with open(filename, 'rb') as f:
        file = f.read()
        pos = 4
        is_last = False
        while not is_last:
            is_last, type_of_block, size = parse_metadata_block_header(
                file[pos:pos+4])
            if type_of_block == 4:
                a = parse_vorbis_comment(file[pos+4:pos+4+size])
            pos += size + 4


def main():
    filename = 'sample2.flac'
    file_is_flac(filename)
    parse_metadata(filename)


if __name__ == '__main__':
    main()
