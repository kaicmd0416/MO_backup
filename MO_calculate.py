import numpy as np
import pandas as pd
import sys
import os
import datetime

from matplotlib import pyplot as plt

path = os.getenv('GLOBAL_TOOLSFUNC_new')
sys.path.append(path)
import global_tools as gt

def input_construction(target_date,year_month,strik_price_list,proportion_list,is_signal):
    future_code='IM'+str(year_month)
    option_code_list=['MO'+str(year_month)+'-C-'+str(i) for i in strik_price_list]
    df_future=pd.DataFrame()
    df_future['code']=[future_code]
    df_future['type']='Future'
    if is_signal==True:
       df_future['quantity']=1
    else:
        df_future['quantity']=0
    df_future['valuation_date']=target_date
    df_option = pd.DataFrame()
    df_option['code'] = option_code_list
    if is_signal==True:
       df_option['quantity'] = proportion_list
    else:
        df_option['quantity']=0
    df_option['valuation_date'] = target_date
    df_option['type'] = 'Option'
    df_holding=pd.concat([df_future,df_option])
    return df_holding
def FOData_withdraw(start_date,end_date,realtime):
    if realtime==True:
        today=datetime.datetime.today()
        today=gt.strdate_transfer(today)
        start_date=today
        end_date=today
    else:
        start_date=gt.last_workday_calculate(start_date)
        end_date=gt.last_workday_calculate(end_date)
    df_future=gt.futureData_withdraw(start_date,end_date,[],realtime)
    df_future=df_future[['valuation_date','code','close','multiplier']]
    df_option=gt.optionData_withdraw(start_date,end_date,[],realtime)
    df_option = df_option[['valuation_date','code', 'close', 'delta']]
    df_option['multiplier']=100
    df_future['delta']=1
    df_fo=pd.concat([df_option,df_future])
    return df_fo
def indexData_withdraw(start_date,end_date,realtime):
    if realtime == True:
        today = datetime.datetime.today()
        today = gt.strdate_transfer(today)
        start_date = today
        end_date = today
    else:
        start_date = gt.last_workday_calculate(start_date)
        end_date = gt.last_workday_calculate(end_date)
    df_index = gt.indexData_withdraw('中证1000', start_date, end_date, ['close'], realtime)
    return df_index
def year_month_generator(date):
    date=pd.to_datetime(date)
    def third_friday(y, m):
        first_day = datetime.date(y, m, 1)
        # 周一=0 ... 周日=6，周五=4
        first_friday = 1 + ((4 - first_day.weekday()) % 7)
        return datetime.date(y, m, first_friday + 14)

    def add_one_month(y, m):
        if m == 12:
            return y + 1, 1
        return y, m + 1

    def ym_to_str(y, m):
        return f"{y % 100:02d}{m:02d}"

    tf = third_friday(date.year, date.month)
    base_year, base_month = (date.year, date.month)
    if date.date() > tf:
        base_year, base_month = add_one_month(base_year, base_month)
    this_year_month = ym_to_str(base_year, base_month)
    next_year, next_month = add_one_month(base_year, base_month)
    year_month = ym_to_str(next_year, next_month)
    return year_month
def strikePrice_Quantity_generator(index_price):
    remainder = int(index_price) % 100
    base_lower = int(index_price) - remainder
    base_upper = base_lower + 100
    if remainder < 35:
        strike_price_list = [str(base_lower)]
        proportion_list = [-4]
    elif remainder >= 35 and remainder <= 70:
        strike_price_list = [str(base_lower), str(base_upper)]
        proportion_list = [-2, -2]
    elif remainder > 70:
        strike_price_list = [str(base_upper)]
        proportion_list = [-4]
    else:
        raise ValueError('index_price 的末两位不在 0-99 范围内')
    return strike_price_list,proportion_list
def signal_generator(target_date):
    available_date=gt.last_workday_calculate(target_date)
    df_index = gt.indexData_withdraw('中证1000', '2024-01-01', available_date, ['close'], realtime)
    mean=np.mean(df_index['close'].tolist()[-20:])
    last_index=df_index['close'].tolist()[-1]
    if mean<=last_index:
        return True
    else:
        return False
def portfolio_construction(start_date,end_date,realtime):
    working_days_list=gt.working_days_list(start_date,end_date)
    df_index_base=indexData_withdraw(start_date,end_date,realtime)
    df_holding=pd.DataFrame()
    for target_date in working_days_list:
        if realtime==False:
            available_date=gt.last_workday_calculate(target_date)
        else:
            available_date=target_date
        signal=signal_generator(target_date)
        df_index=df_index_base[df_index_base['valuation_date']==available_date]
        index_price=df_index['close'].tolist()[0]
        year_month=year_month_generator(target_date)
        strike_price_list,proportion_list=strikePrice_Quantity_generator(index_price)
        df_holding_daily = input_construction(target_date,year_month, strike_price_list, proportion_list,signal)
        df_holding=pd.concat([df_holding,df_holding_daily])
    return df_holding
def report_generator(df_holding,realtime):
    date_list = df_holding['valuation_date'].unique().tolist()
    date_list.sort()
    start_date = date_list[0]
    end_date = date_list[-1]
    if realtime==False:
        df_holding['valuation_date']=df_holding['valuation_date'].apply(lambda x: gt.last_workday_calculate(x))
    df_fo=FOData_withdraw(start_date,end_date,realtime)
    df_index_base = indexData_withdraw(start_date, end_date, realtime)
    df_holding=df_holding.merge(df_fo,on=['valuation_date','code'],how='left')
    date_list2=df_holding['valuation_date'].unique().tolist()
    for date in date_list2:

        if realtime==False:
            target_date=gt.next_workday_calculate(date)
        else:
            target_date=date
        df_daily=df_holding[df_holding['valuation_date']==date]
        df_index=df_index_base[df_index_base['valuation_date']==date]
        index_price = df_index['close'].tolist()[0]
        future_price =df_daily[df_daily['type']=='Future']['close'].tolist()[0]
        multiplier = df_daily[df_daily['type']=='Future']['multiplier'].tolist()[0]
        mkt_value = future_price * multiplier
        jicha = index_price - future_price
        df_option_holding=df_daily[df_daily['type']=='Option']
        df_option_holding['proportion'] = df_option_holding['delta'] * df_option_holding['quantity'] / 2
        df_option_holding['money'] = df_option_holding['close'] * df_option_holding['quantity'] / 2
        proportion = df_option_holding['proportion'].sum()
        money = df_option_holding['money'].sum()
        protection_money = jicha - money
        loss_line = index_price - protection_money
        net_delta = 1 + proportion
        df_daily['valuation_date']=target_date
        print('----------------------------------------------------------------------------')
        print(f"对于组合在'{target_date}':")
        print(df_daily[['valuation_date','code','quantity','close','delta']])
        print('当前基差为:' + str(round(jicha, 2)))
        print('组合保护为:' + str(round(protection_money, 2)))
        print('盈亏线为:' + str(round(loss_line, 2)))
        print('敞口(delta)为:' + str(round(net_delta, 2)))
        print('敞口(市值)为:' + str(round(net_delta * mkt_value, 2)))
        print('----------------------------------------------------------------------------')
if __name__ == '__main__':
    start_date='2025-01-01'
    end_date='2025-10-29'
    realtime=False
    df_holding=portfolio_construction(start_date,end_date,realtime)
    df_holding=df_holding[['valuation_date','code','quantity']]
    print(df_holding)
    df_info,df_detail=gt.portfolio_analyse(df_holding,cost_option=0.001)
    print(df_info)
    df_info=df_info[['valuation_date','portfolio_profit']]
    df_info['portfolio_profit']=df_info['portfolio_profit'].cumsum()
    df_info.set_index('valuation_date',inplace=True,drop=True)
    df_info.plot()
    plt.show()
    #report_generator(df_holding, realtime)
    # year_month='2512'
    # strik_price=['7300']
    # proportion_list=[-2]
    # calculation_main(year_month, strik_price, proportion_list)