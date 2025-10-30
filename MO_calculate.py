import pandas as pd
import sys
import os
import datetime
path = os.getenv('GLOBAL_TOOLSFUNC_new')
sys.path.append(path)
import global_tools as gt

date = datetime.datetime.today()
date = gt.strdate_transfer(date)
def input_construction(year_month,strik_price_list,proportion_list):
    future_code='IM'+str(year_month)
    option_code_list=['MO'+str(year_month)+'-C-'+str(i) for i in strik_price_list]
    df_future=pd.DataFrame()
    df_future['code']=[future_code]
    df_future['quantity']=1
    df_future['valuation_date']=date
    df_option = pd.DataFrame()
    df_option['code'] = option_code_list
    df_option['quantity'] = proportion_list
    df_option['valuation_date'] = date
    return df_future,df_option
def mktData_withdraw():
    df_index=gt.indexData_withdraw('中证1000',date,date,['close'],True)
    df_future=gt.futureData_withdraw(date,date,[],True)
    df_future=df_future[['code','close','multiplier','delta']]
    df_option=gt.optionData_withdraw(date,date,[],True)
    df_option = df_option[['code', 'close', 'multiplier', 'delta']]
    df_option['multiplier']=100
    df_future['delta']=1
    return df_index,df_future,df_option
def calculation_main(year_month,strik_price,proportion_list):
    df_future_holding,df_option_holding=input_construction(year_month,strik_price,proportion_list)
    df_holding=pd.concat([df_future_holding,df_option_holding])
    df_index, df_future,df_option=mktData_withdraw()
    df_fo=pd.concat([df_future,df_option])
    df_holding=df_holding.merge(df_fo,on='code',how='left')
    df_future=df_future_holding.merge(df_future,on='code',how='left')
    future_price=df_future['close'].tolist()[0]
    multiplier=df_future['multiplier'].tolist()[0]
    mkt_value=future_price*multiplier
    index_price=df_index['close'].tolist()[0]
    jicha=index_price-future_price
    df_option_holding=df_option_holding.merge(df_option,on='code',how='left')
    df_option_holding['proportion']=df_option_holding['delta']*df_option_holding['quantity']/2
    df_option_holding['money']=df_option_holding['close']*df_option_holding['quantity']/2
    proportion=df_option_holding['proportion'].sum()
    money=df_option_holding['money'].sum()
    protection_money=jicha-money
    loss_line=index_price-protection_money
    net_delta=1+proportion
    print('对于组合:')
    print(df_holding)
    print('当前基差为:'+str(round(jicha,2)))
    print('组合保护为:' + str(round(protection_money,2)))
    print('盈亏线为:' + str(round(loss_line,2)))
    print('敞口(delta)为:' + str(round(net_delta,2)))
    print('敞口(市值)为:' + str(round(net_delta*mkt_value,2)))




if __name__ == '__main__':
    year_month='2512'
    strik_price=['7300']
    proportion_list=[-2]
    calculation_main(year_month, strik_price, proportion_list)