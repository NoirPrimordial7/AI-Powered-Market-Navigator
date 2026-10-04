"""Reproducible rolling evaluation of the preserved model's APP inference pipeline.

The original training dates/scaler are unknown. These are diagnostic results,
not independently verified holdout or original training scores.
"""
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
from market import get_data,predict,snapshot_symbols

ROOT=Path(__file__).resolve().parent

def scores(actual,predicted,previous):
    actual=np.asarray(actual,dtype=float);predicted=np.asarray(predicted,dtype=float);previous=np.asarray(previous,dtype=float)
    if not(len(actual)==len(predicted)==len(previous)) or not len(actual):raise ValueError('Equal nonempty arrays required.')
    if not np.isfinite([actual,predicted,previous]).all() or (actual<=0).any():raise ValueError('Finite values and positive targets required.')
    error=predicted-actual
    moving=actual!=previous
    denominator=np.sum((actual-actual.mean())**2)
    return dict(n=len(actual),mae=float(np.abs(error).mean()),rmse=float(np.sqrt((error**2).mean())),mape_percent=float((np.abs(error)/actual).mean()*100),within_1_percent=float((np.abs(error)/actual<=.01).mean()*100),within_5_percent=float((np.abs(error)/actual<=.05).mean()*100),r2=float(1-np.sum(error**2)/denominator) if denominator else None,directional_accuracy_percent=float((np.sign(predicted[moving]-previous[moving])==np.sign(actual[moving]-previous[moving])).mean()*100) if moving.any() else None,direction_n=int(moving.sum()))

def run(sessions=63):
    out=ROOT/'evaluation';out.mkdir(exist_ok=True)
    all_rows=[];results=[]
    for symbol in snapshot_symbols():
        data=get_data(symbol);rows=[]
        # Indicator calculations are causal. Scaling sees only the prefix
        # available before the target; its extrema never see future rows.
        for i in range(max(60,len(data)-sessions),len(data)):
            history=data.iloc[:i]
            rows.append(dict(symbol=symbol,currency=data.attrs['currency'],origin_date=f'{history.index[-1]:%Y-%m-%d}',target_date=f'{data.index[i]:%Y-%m-%d}',previous_close=float(history.Close.iloc[-1]),actual_close=float(data.Close.iloc[i]),model_close=predict(history),momentum_close=float(history.Close.iloc[-1]**2/history.Close.iloc[-2])))
        frame=pd.DataFrame(rows);all_rows.extend(rows)
        moving=frame.actual_close!=frame.previous_close
        up=float((frame.loc[moving,'actual_close']>frame.loc[moving,'previous_close']).mean()*100)
        results.append(dict(symbol=symbol,currency=data.attrs['currency'],first_target=rows[0]['target_date'],last_target=rows[-1]['target_date'],model=scores(frame.actual_close,frame.model_close,frame.previous_close),persistence=scores(frame.actual_close,frame.previous_close,frame.previous_close),last_return=scores(frame.actual_close,frame.momentum_close,frame.previous_close),always_up_direction_percent=up,always_down_direction_percent=100-up,dataset_sha256=hashlib.sha256((ROOT/'data'/f'{symbol}.csv').read_bytes()).hexdigest()))
        print(symbol,results[-1]['model'],flush=True)
    report=dict(protocol='Expanding-history, next-session rolling diagnostic of current app preprocessing',training_overlap='UNKNOWN: original training period and dataset not recovered; this is not a verified independent holdout',model_sha256=hashlib.sha256((ROOT/'model3.h5').read_bytes()).hexdigest(),sessions_per_symbol=sessions,baseline='Persistence: tomorrow close = last observed close; direction abstention counts as incorrect on nonzero actual moves',scaling='MinMax fitted separately on each available historical prefix, matching the current app; original training scaler unavailable',aggregation='Per-symbol price errors retain local currency. Macro MAPE is an unweighted mean of per-symbol percentage errors. No pooled price-unit errors.',macro_model_mape_percent=float(np.mean([r['model']['mape_percent'] for r in results])),macro_persistence_mape_percent=float(np.mean([r['persistence']['mape_percent'] for r in results])),results=results)
    pd.DataFrame(all_rows).to_csv(out/'predictions.csv',index=False)
    pooled=pd.DataFrame(all_rows);moving=pooled.actual_close!=pooled.previous_close
    # Pool only dimensionless hit rates, never MAE/RMSE in mixed USD/INR units.
    report['pooled_direction_targets']=int(moving.sum())
    report['pooled_model_direction_percent']=float((np.sign(pooled.loc[moving,'model_close']-pooled.loc[moving,'previous_close'])==np.sign(pooled.loc[moving,'actual_close']-pooled.loc[moving,'previous_close'])).mean()*100)
    report['pooled_always_up_direction_percent']=float((pooled.loc[moving,'actual_close']>pooled.loc[moving,'previous_close']).mean()*100)
    report['pooled_last_return_direction_percent']=float((np.sign(pooled.loc[moving,'momentum_close']-pooled.loc[moving,'previous_close'])==np.sign(pooled.loc[moving,'actual_close']-pooled.loc[moving,'previous_close'])).mean()*100)
    report['pooled_model_within_5_percent']=float(((pooled.model_close-pooled.actual_close).abs()/pooled.actual_close<=.05).mean()*100)
    report['pooled_persistence_within_5_percent']=float(((pooled.previous_close-pooled.actual_close).abs()/pooled.actual_close<=.05).mean()*100)
    (out/'metrics.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    return report

if __name__=='__main__':run()
