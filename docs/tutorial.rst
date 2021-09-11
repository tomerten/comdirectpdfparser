**********
Tutorial
**********

Reading and parsing
===================

.. code-block:: python

    from comdirectparser import ComDirectParser
    from pymongo import MongoClient
    from matplotlib import pyplot as plt 

    div_folder = "YOUR-PATH-TO-DIV-FOLDER"
    div_ert_folder = "YOUR-PATH-TO-DIVERT-FOLDER"
    tax_folder = "YOUR-PATH-TO-STEUER-FOLDER"
    buy_sell_folder = "YOUR-PATH-TO-KAUF/VERKAUF-FOLDER"
    fin_folder = "YOUR-PATH-TO-FINANZREPORT-FOLDER"

    client = MongoClient("mongodb://localhost:27017")
    cdp = ComDirectParser(inputlist = 
            [
                div_folder, 
                div_ert_folder, 
                tax_folder, 
                fin_folder,
                buy_sell_folder
            ])
    parsed = cdp.parse()
    

Saving
======

.. code-block:: python

    cdp.save()


Closer look at the data
=======================

Dividends and taxes
-------------------

.. code-block:: python

    import pandas as pd
    divdf = pd.DataFrame(parsed[0])
    taxdf = pd.DataFrame(parsed[2])

    # taxes have a unique ID that allows to combine 
    # the above dataframes

    dfm = pd.merge(divdf, taxdf.drop('Type', axis=1), on='Tax Reference Number', how='inner')

    # some cleaning and grouping
    divdf['Date'] = pd.to_datetime(divdf['Date'],dayfirst=True)
    divdf.set_index('Date').groupby(pd.Grouper(freq='M')).sum()['Net Before Tax'].plot(kind='bar', grid=True) 

    # bar plot with values
    ax = dfdiv.set_index('Date').drop_duplicates().groupby(pd.Grouper(freq='M')).sum()['Net Before Tax'].plot(kind='bar',grid=True, figsize=(14,8))
    x_offset = -0.2
    y_offset = 25
    for p in ax.patches:
        b = p.get_bbox()
        val = "{:+.2f}".format(b.y1 + b.y0)        
        ax.annotate(val, ((b.x0 + b.x1)/2 + x_offset, b.y1 + y_offset), rotation=90)


Finanzreport 
------------

.. code-block:: python

    # giro saldo and depot value from report
    dfo = parsed[3]
    ax  = dfo.loc[dfo['name'].str.contains("Giro")].sort_values(by='date').plot(x='date',y='saldo', label='saldo')
    dfo.loc[dfo['name'].str.contains("Depot")].sort_values(by='date').plot(x='date',y='saldo',ax=ax,label='depot')
    plt.grid()

    # dividend payments on girokonto (transactions)
    dft = pd.DataFrame(parsed[4])
    dft.loc[dft['type'].str.contains('Kupon')].sort_values(by='date').set_index('date')['value'].cumsum().plot()
    plt.grid()

    # total expenses
    dft.loc[(dft['type'].str.contains('Über')) & (dft['value']<0)].sort_values(by='date').sum()['value']

    # stats on monthly expenses
    g = dft.loc[(dft['type'].str.contains('Über')) & (dft['value']<0)].sort_values(by='date').set_index('date').groupby(pd.Grouper(freq="M"))
    g.sum().describe()

    # plot expenses/income per month
    g = dft.loc[(dft['type'].str.contains('Über')) ].sort_values(by='date').set_index('date').groupby(pd.Grouper(freq="M"))
    g.sum().plot(kind='bar')
