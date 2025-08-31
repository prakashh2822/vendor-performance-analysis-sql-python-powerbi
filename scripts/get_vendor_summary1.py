import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import time
from sqlalchemy import create_engine
import logging
from  ingestion_db import ingest_db
import sqlite3

os.makedirs("logs", exist_ok=True)

# Clear old logging handlers
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)
# Configure logging
logging.basicConfig(
    filename="logs/get_vendor_summary.log",
    level=logging.DEBUG,
    format="%(asctime)s-%(levelname)s-%(message)s",
    filemode="a"
)
def create_vendor_summary1(conn):
    ''' this function merge the tables and create the overall vendor summary table and adding new columns to the relundant data '''
    vendor_sales_summary1= pd.read_sql_query(""" with frieghtsummary as (
                                            select VendorNumber, sum(Freight) as freightcost from vendor_invoice group by VendorNumber),
                                            
                                             purchasesummary as (
                                            select p.VendorNumber,p.PurchasePrice,p.VendorName,p.Brand,p.Description
    ,sum(p.Quantity) as totalpurchasequantity,sum(p.Dollars) as totaldollars,
    pp.Price as actualprice,pp.Volume from purchases as p join purchase_prices as pp on p.Brand=pp.Brand
    where p.purchaseprice>0
    group by p.VendorNumber, p.VendorName,p.Brand,p.Description,pp.Volume,pp.price
    ),
    
     salessummary as (
    select
                        VendorNo,Brand,
                        sum(SalesQuantity) as totalsalesquantity,
                        sum(SalesDollars) as totalsalesdollars,
                        sum(SalesPrice) as totalsalesprice,
                        sum(ExciseTax) as totalexcisetax
                        from sales
                        group by VendorNo,Brand
                        )
    
    select ps.VendorName,ps.VendorNumber,ps.Brand,ps.Description,ps.actualprice,ps.volume,ps.PurchasePrice,
            ps.totalpurchasequantity,ps.totaldollars,
            ss.totalsalesquantity, ss.totalsalesdollars,ss.totalsalesprice,ss.totalexcisetax,
            fs.freightcost
            from  purchasesummary as ps
            left join
            salessummary as ss on ps.VendorNumber=ss.VendorNo and ps.Brand=ss.Brand
            left join frieghtsummary as fs on ps.VendorNumber=fs.VendorNumber
            order by totaldollars desc""",conn)
    return vendor_sales_summary1

def clean_data(vendor_sales_summary1):
    ''' this function will clean the data '''
    # comvert data type
    vendor_sales_summary1['Volume']=vendor_sales_summary1['Volume'].astype('float64')
    #filling na values
    vendor_sales_summary1.fillna(0,inplace=True)
    # removing extra spaces for the columns
    vendor_sales_summary1['VendorName']=vendor_sales_summary1['VendorName'].str.strip()
    vendor_sales_summary1['Description']=vendor_sales_summary1['Description'].str.strip()
    # adding new columns for the better analysis
    vendor_sales_summary1['Grossprofit']=vendor_sales_summary1['totalsalesdollars'] - vendor_sales_summary1['totaldollars']
    vendor_sales_summary1['profitmargin']=vendor_sales_summary1['Grossprofit']/vendor_sales_summary1['totalsalesdollars'] * 100

    vendor_sales_summary1['stockturnover']=vendor_sales_summary1['totalsalesquantity']/vendor_sales_summary1['totalpurchasequantity']
    vendor_sales_summary1['salestopurchaseratio']=vendor_sales_summary1['totalsalesdollars'] / vendor_sales_summary1['totaldollars']
    return vendor_sales_summary1

if __name__=="__main__":
    # creating database connection
    conn=sqlite3.connect('inventory.db')
    start=time.time()
    logging.info('creating vendor summary table...')
    summary_df=create_vendor_summary1(conn)
    end=time.time()
    
    logging.info(summary_df.head())

    start=time.time()
    logging.info('cleaning data.....')
    clean_df=clean_data(summary_df)
    end=time.time()
    
    logging.info(clean_df.head())

    start=time.time()
    logging.info('ingesting data...')
    ingest_db(clean_df,'vendor_sales_summary1',conn)
    end=time.time()
    
    logging.info('completed')
    
    
                                       
                                        
                                            
                                        