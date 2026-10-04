"""Check saved observations and compare them with a fresh provider download.

Run manually; never modifies the saved histories. A provider match is not an
independent exchange audit or proof that training used these observations.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
import yfinance as yf

ROOT=Path(__file__).resolve().parent
COLUMNS=['Open','High','Low','Close','Volume']

def check_frame(frame, today):
    prices=frame[COLUMNS[:4]]
    errors={
        'duplicate_dates':int(frame.index.duplicated().sum()),
        'out_of_order_dates':int(not frame.index.is_monotonic_increasing),
        'future_dates':int((frame.index.normalize()>pd.Timestamp(today)).sum()),
        'nonfinite_cells':int((~np.isfinite(frame[COLUMNS].to_numpy(dtype=float))).sum()),
        'nonpositive_prices':int((prices<=0).sum().sum()),
        'negative_volume':int((frame.Volume<0).sum()),
        'fractional_volume':int((frame.Volume%1!=0).sum()),
        'invalid_high_low_rows':int(((frame.High<prices.max(axis=1)-1e-7)|(frame.Low>prices.min(axis=1)+1e-7)).sum()),
    }
    return {'rows':len(frame),'first_date':str(frame.index.min().date()),'last_date':str(frame.index.max().date()),'errors':errors,'structural_checks_pass':not any(errors.values())}

def run():
    now=datetime.now(timezone.utc)
    cache=ROOT/'.cache'/'yfinance';cache.mkdir(parents=True,exist_ok=True)
    yf.set_tz_cache_location(str(cache))
    results=[]
    for path in sorted((ROOT/'data').glob('*.csv')):
        saved=pd.read_csv(path,index_col=0,parse_dates=True)
        result={'symbol':path.stem,'dataset_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),**check_frame(saved,now.date())}
        try:
            instrument=yf.Ticker(path.stem)
            fresh=instrument.history(start=str(saved.index.min().date()),end=str((saved.index.max()+pd.Timedelta(days=1)).date()),interval='1d',auto_adjust=True,prepost=False,timeout=15,raise_errors=True)
            if fresh.empty:raise ValueError('Provider returned no rows')
            fresh.index=fresh.index.tz_localize(None)
            common=saved.index.intersection(fresh.index)
            price_diff=(saved.loc[common,COLUMNS[:4]]-fresh.loc[common,COLUMNS[:4]]).abs()
            volume_diff=(saved.loc[common,'Volume']-fresh.loc[common,'Volume']).abs()
            price_match=np.isclose(saved.loc[common,COLUMNS[:4]],fresh.loc[common,COLUMNS[:4]],rtol=1e-7,atol=1e-5)
            result['provider_comparison']={
                'common_rows':len(common),'saved_dates_missing_from_provider':len(saved.index.difference(fresh.index)),
                'provider_dates_missing_from_saved':len(fresh.index.difference(saved.index)),
                'price_cells_outside_tolerance':int((~price_match).sum()),
                'price_cells_different_by_more_than_one_cent':int((price_diff>.01).sum().sum()),
                'volume_rows_different':int((volume_diff!=0).sum()),
                'max_price_difference':float(price_diff.max().max()) if len(common) else None,
                'max_volume_difference':float(volume_diff.max()) if len(common) else None,
                'currency':instrument.history_metadata.get('currency'),
                'all_saved_observations_match':bool(len(common)==len(saved) and len(fresh)==len(saved) and price_match.all() and (volume_diff==0).all()),
            }
        except Exception as exc:
            result['provider_comparison']={'verified':False,'error_type':type(exc).__name__}
        results.append(result)
        print(json.dumps(result),flush=True)
    report={'checked_at':now.isoformat(),'source':'Fresh Yahoo Finance via yfinance, explicit saved date ranges, auto_adjust=True','tolerance':'Prices: rtol=1e-7, atol=1e-5; volume and dates: exact','limitations':'Same-provider consistency check, not independent exchange verification; adjustments and vendor revisions may change historical values. Original training data remains unknown.','results':results}
    (ROOT/'evaluation'/'data-audit.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    return report

if __name__=='__main__':run()
