# -*- coding: utf-8 -*-
"""
Created on Wed Mar 24 15:17:30 2021

@author: hurui2
"""



import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from statsmodels.tsa.arima_model import ARIMA
import statsmodels.api as sm
import warnings
from itertools import product
from datetime import datetime, timedelta
import calendar

train=pd.read_csv('./train.csv')
#转换为pandas中的日期格式
train['Datetime']=pd.to_datetime(train['Datetime'])
#将datetime作为index
train.index=train['Datetime']
train.drop(['ID','Datetime'],axis=1,inplace=True)
#print(train)
#按天采样
daily_train=train.resample('D').sum()
daily_train['ds']=daily_train.index
daily_train['y']=daily_train['Count']
daily_train.drop(['Count'],axis=1,inplace=True)
print(daily_train)

"""from fbprophet import Prophet
#创建模型
m = Prophet(yearly_seasonality=True, seasonality_prior_scale=0.1)
m.fit(daily_train)
#预测未来7个月，213天
future=m.make_future_dataframe(periods=213)
forecast=m.predict(future)

m.plot(forecast)"""

# 设置参数范围
ps = range(0, 10)
qs = range(0, 10)
ds = range(1, 5)
#product迪卡尔积，相乘
parameters = product(ps, ds, qs)
parameters_list = list(parameters)
# 寻找最优ARMA模型参数，即best_aic最小
results = []
best_aic = float("inf") # 正无穷
for param in parameters_list:
    try:
        #model = ARIMA(df_month.Price,order=(param[0], param[1], param[2])).fit()
        # SARIMAX 包含季节趋势因素的ARIMA模型
        model = sm.tsa.statespace.SARIMAX(daily_train.y,
                                order=(param[0], param[1], param[2]),
                                #seasonal_order=(4, 1, 2, 12),
                                enforce_stationarity=False,
                                enforce_invertibility=False).fit()

    except ValueError:
        print('参数错误:', param)
        continue
    aic = model.aic
    #打擂法
    if aic < best_aic:
        best_model = model
        best_aic = aic
        best_param = param
    results.append([param, model.aic])
# 输出最优模型
print('最优模型: ', best_model.summary())

# 设置future_month，需要预测的时间date_list
daily_train2 = daily_train[['y']]
future_month = 7
last_month = pd.to_datetime(daily_train2.index[len(daily_train2)-1])
date_list = []
for i in range(future_month):
    # 计算下个月有多少天
    year = last_month.year
    month = last_month.month
    if month == 12:
        month = 1
        year = year+1
    else:
        month = month + 1
    next_month_days = calendar.monthrange(year, month)[1]
    #print(next_month_days)
    last_month = last_month + timedelta(days=next_month_days)
    date_list.append(last_month)
print('date_list=', date_list)

# 添加未来要预测的7个月
future = pd.DataFrame(index=date_list, columns= daily_train.columns)
daily_train2 = pd.concat([daily_train2, future])

# get_prediction得到的是区间，使用predicted_mean
daily_train2['forecast'] = best_model.get_prediction(start=0, end=len(daily_train2)).predicted_mean

# 预测结果显示
plt.figure(figsize=(30,7))
daily_train2.y.plot(label='实际交通流量')
daily_train2.forecast.plot(color='r', ls='--', label='预测交通流量')
plt.legend()
plt.title('交通流量')
plt.xlabel('时间')
plt.ylabel('乘客人数')
plt.show()
