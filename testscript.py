from comdirectpdfparser import ComDirectParser, log

if __name__ == '__main__':
    _file = "/Users/tommertens/home/ComDirectDokumente/Ertragsgutschrift"
    log.setup()
    cdp = ComDirectParser(inputlist=_file)

    print(cdp.parse())