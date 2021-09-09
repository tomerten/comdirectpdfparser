from comdirectpdfparser import ComDirectParser, log
from comdirectpdfparser.utils import readRaw
from matplotlib import pyplot as plt
from pymongo import MongoClient

import pandas as pd
if __name__ == '__main__':
    etr_folder = "/Users/tommertens/home/ComDirectDokumente/Ertragsgutschrift"
    tax_folder = "/Users/tommertens/home/ComDirectDokumente/Steuermitteilung"
    div_folder = "/Users/tommertens/home/ComDirectDokumente/Dividendengutschrift" 
    log.setup()
    client = MongoClient("mongodb://localhost:27017")
    client.drop_database('ComDirect')
    cdp = ComDirectParser(inputlist=[etr_folder, tax_folder, div_folder], client=client)

    parsed = cdp.parse()
    cdp.save()
    divdf = pd.DataFrame(parsed[0]) 
    taxdf = pd.DataFrame(parsed[2])
    #print(divdf)
    #print(divdf.Brutto.sum())
    #print(taxdf)
    #print(taxdf['After Tax'].sum())

    dfm = pd.merge(divdf, taxdf.drop('Type',axis=1), on='Tax Reference Number', how='inner')
 
    print(dfm)
    print(dfm['After Tax'].sum())
    divdf['Date'] = pd.to_datetime(divdf['Date'],dayfirst=True)
    divdf.set_index('Date').groupby(pd.Grouper(freq='M')).sum()['Net Before Tax'].plot(kind='bar',grid=True)
    plt.tight_layout()
    plt.show()