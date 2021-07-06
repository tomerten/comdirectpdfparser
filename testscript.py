from comdirectpdfparser import ComDirectParser, log
from comdirectpdfparser.utils import readRaw

import pandas as pd
if __name__ == '__main__':
    etr_folder = "/Users/tommertens/home/ComDirectDokumente/Ertragsgutschrift"
    tax_folder = "/Users/tommertens/home/ComDirectDokumente/Steuermitteilung"
    log.setup()
    cdp = ComDirectParser(inputlist=[etr_folder, tax_folder])

    parsed = cdp.parse()
    divdf = pd.DataFrame(parsed[0]) 
    taxdf = pd.DataFrame(parsed[2])
    #print(divdf)
    #print(divdf.Brutto.sum())
    #print(taxdf)
    #print(taxdf['After Tax'].sum())

    dfm = pd.merge(divdf, taxdf.drop('Type',axis=1), on='Tax Reference Number', how='inner')
    print(dfm.T)


