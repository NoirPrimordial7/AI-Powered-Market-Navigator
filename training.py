"""A NEW reproducible training recipe, not the missing original notebook.

Never modifies model3.h5. Outputs go into a newly created directory.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from research import read_prices
from market import FEATURES,ROOT,model_resource
from evaluate import scores

def prepare(frame,window=30):
    clean=frame[FEATURES].ffill().dropna()
    n=len(clean);train_end=int(n*.7);validation_end=int(n*.85)
    if train_end<window+20 or n-validation_end<10:raise ValueError('Use at least 150 daily rows for chronological training, validation and testing.')
    # The last training target is train_end-1. Validation/test cannot alter scaling.
    scaler=MinMaxScaler().fit(clean.iloc[:train_end])
    values=scaler.transform(clean).astype('float32')
    x=np.stack([values[i-window:i] for i in range(window,n)])
    y=values[window:,FEATURES.index('Close')]
    targets=np.arange(window,n)
    masks=[targets<train_end,(targets>=train_end)&(targets<validation_end),targets>=validation_end]
    return clean,scaler,[(x[m],y[m]) for m in masks],targets,[train_end,validation_end]

def train(csv,output,epochs=100):
    from keras.models import clone_model
    from keras.optimizers import Adam
    from keras.callbacks import EarlyStopping
    from keras.utils import set_random_seed
    set_random_seed(42)
    path=Path(csv);content=path.read_bytes();frame=read_prices(content)
    clean,scaler,parts,targets,bounds=prepare(frame)
    out=Path(output).resolve()
    if out==ROOT.resolve() or out.exists():raise ValueError('Choose a new output directory; existing artifacts are never overwritten.')
    if epochs<1 or epochs>500:raise ValueError('Epoch count must be 1–500.')
    original,_=model_resource();model=clone_model(original) # fresh weights
    model.compile(optimizer=Adam(learning_rate=.001),loss='mean_squared_error')
    # Explicit tf.data thread bounds keep the CPU demonstration portable.
    import tensorflow as tf
    options=tf.data.Options();options.threading.private_threadpool_size=1
    def dataset(part):return tf.data.Dataset.from_tensor_slices(part).batch(32).with_options(options)
    history=model.fit(dataset(parts[0]),validation_data=dataset(parts[1]),epochs=epochs,callbacks=[EarlyStopping(monitor='val_loss',patience=10,restore_best_weights=True)],verbose=2)
    test_x,_=parts[2];scaled=np.asarray(model(test_x,training=False)).reshape(-1)
    column=FEATURES.index('Close');predicted=(scaled-scaler.min_[column])/scaler.scale_[column]
    test_target=targets[targets>=bounds[1]]
    actual=clean.Close.iloc[test_target].to_numpy();previous=clean.Close.iloc[test_target-1].to_numpy()
    out.mkdir(parents=True)
    model.save(out/'retrained.keras')
    scaler_state=dict(features=FEATURES,scale=scaler.scale_.tolist(),min=scaler.min_.tolist(),data_min=scaler.data_min_.tolist(),data_max=scaler.data_max_.tolist(),n_samples_seen=int(scaler.n_samples_seen_))
    (out/'scaler.json').write_text(json.dumps(scaler_state,indent=2)+'\n')
    report=dict(status='New recipe run; NOT original model training history',seed=42,architecture='Clone of serialized model3.h5 architecture with fresh weights',dataset_sha256=hashlib.sha256(content).hexdigest(),original_model_sha256=hashlib.sha256((ROOT/'model3.h5').read_bytes()).hexdigest(),feature_order=FEATURES,window=30,optimizer='Adam lr=0.001',loss='MSE',batch_size=32,shuffle=False,requested_epochs=epochs,completed_epochs=len(history.history['loss']),early_stopping='Validation loss, patience 10, restore best weights',row_ranges=dict(training=[str(clean.index[0]),str(clean.index[bounds[0]-1])],validation=[str(clean.index[bounds[0]]),str(clean.index[bounds[1]-1])],test=[str(clean.index[bounds[1]]),str(clean.index[-1])]),sample_counts=dict(zip(['training','validation','test'],[len(x) for x,y in parts])),history=history.history,test_model=scores(actual,predicted,previous),test_persistence=scores(actual,previous,previous))
    (out/'run.json').write_text(json.dumps(report,indent=2)+'\n')
    import pandas as pd
    pd.DataFrame(dict(target_date=clean.index[test_target],previous_close=previous,actual_close=actual,model_close=predicted)).to_csv(out/'test-predictions.csv',index=False)
    return report

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--csv',required=True);parser.add_argument('--output',required=True);parser.add_argument('--epochs',type=int,default=100)
    args=parser.parse_args();train(args.csv,args.output,args.epochs)
