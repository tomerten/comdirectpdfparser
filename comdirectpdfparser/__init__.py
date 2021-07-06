# -*- coding: utf-8 -*-

"""
Package comdirectpdfparser
=======================================

Top-level package for comdirectpdfparser.
"""

__version__ = "0.0.0"

from .utils import readRaw, stringToNumber
import os
import re
from . import log
import numpy as np

regexdecimal = "(\d+(?:\.\d+)?,\d+)"
    
class ComDirectParser:
    """
    Class to parse comdirect pdf files.

    Currently implemented are:
        - dividendgutschrift
        - kauf/verkauf wertpapier
        - steuermitteilung dividends
    """

    # CONSTANTS
    # currencies
    CUR = (
        "(AED|ARS|AUD|BDT|BGN|BRL|CAD|CHF|CNY|COP|CZK|DKK|EGP|"
        "EUR|GBP|GEL|GHS|HKDHUF|IDR|ILS|INR|JMD|JPY|KRW|KWD|KZTMAD|MXN|"
        "MYR|NGN|NOK|NZD|OMR|PEN|PHP|PKR|PLN|RON|RUB|SAR|SEK|SGD|THB|TRY|"
        "TWD|UAH|USD|VND|ZAR)"
    )

    # docutypes that can be parsed
    docuDict = {
        "Ertragsgutschrift" : "divertrags",
        "Dividendengutschrift": "div",
        "Wertpapierkauf": "buy",
        "Wertpapierverkauf": "sell",
        "Steuerliche Behandlung": "tax",
    }

    def __init__(self, inputlist: list) -> None:
        # log.setup()
        self.folders = []
        self.files = []
        self.filelist = []
        self.divparsed = []
        self.buysellparsed = []
        self.taxparsed = []
        # if inputlist is single file make a list out of it
        if isinstance(inputlist, list):
            pass
        else:
            inputlist = [inputlist]

        # check if entries in inputlist
        # have existing folders and files
        # select only the ones that do.
        for entry in inputlist:
            if os.path.isdir(entry):
                self.folders.append(entry)
            elif os.path.isfile(entry):
                self.files.append(entry)

        self.filelist = self.files.copy()
        for folder in self.folders:
            for file in os.listdir(folder):
                # ignore the files starting with dots
                if not file.startswith("."):
                    self.filelist.append(os.path.join(folder, file))

    def parse(self):
        """
            General parser that will go through all given
            files (also in given folders) and try to parse them.
            
            """
        for _file in self.filelist:
            log.info(_file)
            # return dict
            parsed = {'filename': _file.split("/")[-1]}

            # load pdf data
            raw = readRaw(_file)
            rawText = raw["content"]

            docutypere = "(" + ("|").join(self.docuDict.keys()) + ")"
            docutype = re.findall(f"{docutypere}", rawText)
            log.info(docutype[0])


            if docutype:
                _doctype = self.docuDict[docutype[0]]
                parsed = {**parsed, **{"Type": self.docuDict[docutype[0]]}}
            else:
                print(_file)
                continue
            log.info(parsed)

            accountDict = self.parse_account(rawText, _doctype)
            parsed = {**parsed, **accountDict}
            log.info(parsed)

            if _doctype == "div":
                parsed = {**parsed, **self.parse_div(rawText, accountDict)}
                self.divparsed.append(parsed)

            elif _doctype == 'divertrags':
                parsed = {**parsed, **self.parse_divertrags(rawText, accountDict)}
                self.divparsed.append(parsed)

            elif _doctype == "tax":
                parsed = {**parsed, **self.parse_tax(rawText)}
                self.taxparsed.append(parsed)

            elif _doctype in ["buy", "sell"]:
                parsed = {**parsed, **self.parse_buysell(rawText, _doctype)}
                self.buysellparsed.append(parsed)

        return self.divparsed, self.buysellparsed, self.taxparsed

    def parse_account(self, rawText, _doctype):
        """
        Extract account and account currency data,
        date of transaction and total amount.
        
        Total amount is stored with different key for
        kauf/verkauf or div as they have a different 
        meaning.
        """
        acc = {}

        # account info, date and total cost
        accountre = rf"([A-Z]{{2}}[0-9]{{2}}(?:[ ]?[0-9]{{4}}){{4}}(?:[ ]?[0-9]{{1,2}})) \s+ {self.CUR} \s+"
        datere = r"([0-9]+\.[0-9]+\.[0-9]+) \s+"
        totalcostre = rf" {self.CUR} \s+([0-9]*[.]*[0-9]*[,][0-9]*)"

        accountDateCost = re.findall(accountre + datere + totalcostre, rawText)

        if accountDateCost:
            if _doctype == "div":
                _accountDateCostKeys = [
                    "Account",
                    "Account curr",
                    "Date",
                    "Netto curr",
                    "Net Before Tax",
                ]
            elif _doctype == 'divertrags':
                _accountDateCostKeys = [
                   "Account",
                    "Account curr",
                    "Date",
                    "Netto curr",
                    "Net Before Tax", 
                ]
            else:
                _accountDateCostKeys = [
                    "Account",
                    "Account curr",
                    "Date",
                    "Total Cost curr",
                    "Total Cost",
                ]

            account, accountCurr, date, totalCostCurr, totalCost = accountDateCost[0]

            date = date.replace(".", "-")
            totalCost = stringToNumber(totalCost)

            _accountDateCostValues = [account, accountCurr, date, totalCostCurr, totalCost]

            acc = {**acc, **dict(zip(_accountDateCostKeys, _accountDateCostValues))}

        return acc

    def parse_divertrags(self, rawText, accountDict):
        """
        Ertragsgutschrift parser.
        """
        divparsed = {}
        accountCurr = accountDict.get("Account curr", None)
        totalCost = accountDict.get("Net Before Tax", None)

        # get isin, wkn and stock name
        isinliteralre = r"WKN/ISIN\s+\S+(?:\s[\w\.]*)+?(?=[ ]{2,})\s+"
        wknre = r"(\S+)\s+(\S+\s+\S+(?:\s[\w\.]*)+?)(?=[ ]{2,})\s+\S+"
        stocknamere = r"(?:\s[\w\.]*)+?(?=[ ]{2,})\s+"
        sharesre = r"(\S+)"
        isinre = r"\s+(\S+)"
        wknNameIsin = re.findall(isinliteralre + wknre + stocknamere + sharesre + isinre, rawText)

        if wknNameIsin:
            _wknNameIsinKeys = ["wkn", "Stock", "Shares", "isin"]
            wkn, stockname, shares, isin = wknNameIsin[0]

            shares = stringToNumber(shares)
            _wknNameIsinValues = [wkn, stockname, shares, isin]
            
            divparsed = {**divparsed, **dict(zip(_wknNameIsinKeys, _wknNameIsinValues))}
        
        # get dividend per stock and dividend currency
        dividendperstockAndCurr = re.findall(
            rf"{self.CUR}\s*(\d+(?:\.\d+)?,\d+).*Stück", rawText
            # rf"{self.CUR}\s([0-9]*[.]*[0-9]*[,][0-9]*)\s+Stück", rawText
        )
        divCurr, divperstock = dividendperstockAndCurr[0]

        _, brutto = re.findall(rf"Bruttobetrag:\s+{self.CUR}\s+(\S+)", rawText)[0]

        # convert string numbers to float
        divperstock = stringToNumber(divperstock)
        brutto = stringToNumber(brutto)

        # source tax
        sourcetax = re.findall(rf"(\d+(?:\.\d+)?,\d+) % Quellensteuer\s+{self.CUR}\s+{regexdecimal}", rawText)
        tax_percentage, tax_curr, tax = sourcetax[0]
        
        tax_percentage = stringToNumber(tax_percentage)
        tax = stringToNumber(tax)

        log.warning(tax)
        # if dividend currency is not equal to account currency
        if divCurr != accountCurr:
            forexrate = stringToNumber(
                re.findall(r"Devisenkurs:\s+\S+\s+([0-9]*[.]*[0-9]*,[0-9]*)", rawText)[0]
            )
        else:
            forexrate = 1.0
        
        div = np.round(divperstock / forexrate, 2)
        brutto = np.round(brutto / forexrate, 2)
        tax = np.round(tax / forexrate,2)
        cost = np.round(brutto - totalCost, 2)

        _costKeys = ["Dividend (per share)", "Brutto", "Fees"]
        _costValues = [div, brutto, cost]

        divparsed = {**divparsed, **dict(zip(_costKeys, _costValues))}

        # get reference number to match with Tax document
        refnr = re.findall(rf"Referenz\S+\s+(\S+)\)", rawText)[0]

        divparsed = {**divparsed, **{"Tax Reference Number": refnr}}

        return divparsed

    def parse_div(self, rawText, accountDict):
        """
        Dividendgutschrift parser.
        """
        divparsed = {}

        accountCurr = accountDict.get("Account curr", None)
        totalCost = accountDict.get("Net Before Tax", None)

        # get isin, wkn and stock name
        isinliteralre = r"WKN/ISIN\s+\S+(?:\s[\w\.]*)+?(?=[ ]{2,})\s+"
        wknre = r"(\S+)\s+(\S+\s+\S+(?:\s[\w\.]*)+?)(?=[ ]{2,})\s+\S+"
        stocknamere = r"(?:\s[\w\.]*)+?(?=[ ]{2,})\s+"
        sharesre = r"(\S+)"
        isinre = r"\s+(\S+)"
        wknNameIsin = re.findall(isinliteralre + wknre + stocknamere + sharesre + isinre, rawText)

        if wknNameIsin:
            _wknNameIsinKeys = ["wkn", "Stock", "Shares", "isin"]
            wkn, stockname, shares, isin = wknNameIsin[0]

            shares = stringToNumber(shares)
            _wknNameIsinValues = [wkn, stockname, shares, isin]

            divparsed = {**divparsed, **dict(zip(_wknNameIsinKeys, _wknNameIsinValues))}

        # get dividend and dividend currency
        dividendAndCurr = re.findall(
            rf"{self.CUR}\s([0-9]*[.]*[0-9]*[,][0-9]*)\s+Dividende pro Stück", rawText
        )
        divCurr, div = dividendAndCurr[0]
        _, brutto = re.findall(rf"Bruttobetrag:\s+{self.CUR}\s+(\S+)", rawText)[0]

        # convert string numbers to float
        div = stringToNumber(div)
        brutto = stringToNumber(brutto)

        # if dividend currency is not equal to account currency
        if divCurr != accountCurr:
            forexrate = stringToNumber(
                re.findall(r"Devisenkurs:\s+\S+\s+([0-9]*[.]*[0-9]*,[0-9]*)", rawText)[0]
            )
        else:
            forexrate = 1.0

        div = np.round(div / forexrate, 2)
        brutto = np.round(brutto / forexrate, 2)
        cost = np.round(brutto - totalCost, 2)

        _costKeys = ["Dividend (per share)", "Brutto", "Fees"]
        _costValues = [div, brutto, cost]

        divparsed = {**divparsed, **dict(zip(_costKeys, _costValues))}

        # get reference number to match with Tax document
        refnr = re.findall(rf"Referenz\S+\s+(\S+)\)", rawText)[0]

        divparsed = {**divparsed, **{"Tax Reference Number": refnr}}

        return divparsed

    def parse_buysell(self, rawText, doctype):
        """
        Kauf/Verkauf parser
        """
        parsed = {}

        # get isin, wkn and stock name
        # match ISIN literal
        isinliteralre = r"WPKNR/ISIN\s+\n"
        stocknamewknre = r"(\S+(?:\s[a-zA-Z0-9äöüÄÖÜß\.\-\&]+)+?)(?=[ ]{2,})\s+(\S+)\s+\n"
        stocktypeisinre = r"(\S+(?:\s[\w\.\-\,]*)+?)(?=[ ]{2,})\s+(\S+)"
        nameWknTypeIsin = re.findall(isinliteralre + stocknamewknre + stocktypeisinre, rawText)

        if nameWknTypeIsin:
            _stockWknTypeIsinKeys = ["Stock", "wkn", "stock Type", "isin"]
            stockname, wkn, stocktype, isin = nameWknTypeIsin[0]
            _stockWknTypeIsinValues = [stockname, wkn, stocktype, isin]

            parsed = {**parsed, **dict(zip(_stockWknTypeIsinKeys, _stockWknTypeIsinValues))}

        stk, pricecurr, pricepershare = re.findall(
            rf"[St\.|Stk]\s+(\S+) \s+ {self.CUR}\s* ([0-9]*[.]*[0-9]*[,][0-9]*)", rawText
        )[0]

        stk = stringToNumber(stk)
        pricepershare = stringToNumber(pricepershare)

        try:
            _, _, provision = re.findall(
                rf"\n[ ]*(Provision(?:\s[\S+\.]*)+?)[ ]:[ ]{self.CUR}[ ]*([0-9]*[.]*[0-9]*[,][0-9]*)",
                rawText,
            )[0]
        except:
            provision = np.nan

        try:
            _, _, entgelt = re.findall(
                rf"\n[ ]*(Summe Entgelte(?:\s[\S+\.]*)+?)[ ]:[ ]{self.CUR}[ ]*([0-9]*[.]*[0-9]*[,][0-9]*)",
                rawText,
            )[0]
        except:
            entgelt = np.nan

        try:
            _, _, maklercourtage = re.findall(
                rf"\n[ ]*(Maklercourtage(?:\s[\S+\.]*)+?)[ ]:[ ]{self.CUR}[ ]*([0-9]*[.]*[0-9]*[,][0-9]*)",
                rawText,
            )[0]
        except:
            maklercourtage = np.nan

        try:
            _, _, umschreibe = re.findall(
                rf"\n[ ]*(Umschreibeentgelt(?:\s[\S+\.]*)+?)[ ]:[ ]{self.CUR}[ ]*([0-9]*[.]*[0-9]*[,][0-9]*)",
                rawText,
            )[0]
        except:
            umschreibe = np.nan

        try:
            _, _, varexchange = re.findall(
                rf"\n[ ]*(Variable Börsenspesen(?:\s[\S+\.]*)+?)[ ]:[ ]{self.CUR}[ ]*([0-9]*[.]*[0-9]*[,][0-9]*)",
                rawText,
            )[0]
        except:
            varexchange = np.nan

        try:
            _, _, netto, = re.findall(
                rf"\n[ ]*(Zu Ihren Gunsten nach Steuern:)[ ]*{self.CUR}[ ]*([0-9]*[.]*[0-9]*[,][0-9]*)",
                rawText,
            )[0]
        except:
            netto = np.nan

        _priceKeys = [
            "Shares",
            "Cost Curr",
            "Price (per share)",
            "Cost (Provision)",
            "Cost (Entgelt Summe)",
            "Cost (Makler)",
            "Cost (Umschreibe Entgelt)",
            "Cost (Var Boerse)",
            "Netto (Verkauf)",
        ]
        _priceVals = [
            stk,
            pricecurr,
            pricepershare,
            provision,
            entgelt,
            maklercourtage,
            umschreibe,
            varexchange,
            netto,
        ]
        parsed = {**parsed, **dict(zip(_priceKeys, _priceVals))}

        # get Exchange name
        boerse = re.findall(f"Ausführungsplatz\s+:\s+(.*)", rawText)[0]
        parsed = {**parsed, **{"Exchange": boerse.strip()}}

        return parsed

    def parse_tax(self, rawText):
        parsed = {}
        # Get Tax Type
        taxtype = re.findall(f"\nSteuerliche Behandlung:\s+(.*)", rawText)[0]

        if "Dividende" in taxtype:
            taxtype = "div"
        elif "verkauf" in taxtype.lower():
            taxtype = "sell"
        else:
            taxtype = "unknown"

        # get reference number to match with Tax document
        refnr = re.findall(rf"Referenz\S+\s+(\S+)", rawText)[0]
        values = re.findall(
            rf"\nZu Ihren \w+\s+\S+\s+\S+\s+{self.CUR}\s* ([-]?[0-9]*[.]*[0-9]*[,][0-9]*)", rawText
        )
        tax_currency = values[0][0]

        parsed["Before Tax"] = stringToNumber(values[0][1])
        parsed["After Tax"] = stringToNumber(values[1][1])
        parsed["Total Tax"] = parsed["Before Tax"] - parsed["After Tax"]
        parsed["Tax Type"] = taxtype
        parsed["Tax Currency"] = tax_currency

        return {**parsed, **{"Tax Reference Number": refnr}}