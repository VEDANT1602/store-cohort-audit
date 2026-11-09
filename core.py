"""Comparable-store standardization with explicit support and paired store uncertainty."""
import math
import random


def count(value,name):
    if isinstance(value,bool) or not isinstance(value,int) or value<0:
        raise ValueError(name+" must be a nonnegative integer")
    return value


def aggregate(rows):
    groups={};seen=set()
    for row in rows:
        store=row['store'];period=row['period'];day=row['day']
        if not isinstance(store,str) or not store or period not in {'before','after'}:
            raise ValueError("invalid store or period")
        count(day,"day");n=count(row['accepted'],"accepted");y=count(row['completed'],"completed")
        if y>n:raise ValueError("completed cannot exceed accepted")
        key=(store,period,day)
        if key in seen:raise ValueError("duplicate store-period-day")
        seen.add(key)
        group=groups.setdefault((store,period),[0,0]);group[0]+=n;group[1]+=y
    return groups


def quantile(values,q):
    ordered=sorted(values);position=(len(ordered)-1)*q
    lo=int(position);fraction=position-lo
    return ordered[lo]*(1-fraction)+ordered[min(lo+1,len(ordered)-1)]*fraction


def paired_interval(pairs,seed=1602,repetitions=2000):
    if len(pairs)<2:raise ValueError("at least two supported stores required for this interval")
    if isinstance(repetitions,bool) or not isinstance(repetitions,int) or repetitions<100:
        raise ValueError("at least100bootstrap repetitions required")
    for pair in pairs:
        for key in ['weight','difference']:
            value=pair[key]
            if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value):
                raise ValueError("bootstrap weights/differences must be finite")
        if pair['weight']<=0:raise ValueError("bootstrap weights must be positive")
    rng=random.Random(seed);values=[]
    for _ in range(repetitions):
        sample=[pairs[rng.randrange(len(pairs))] for _ in pairs]
        denom=sum(p['weight'] for p in sample)
        values.append(sum(p['weight']*p['difference'] for p in sample)/denom)
    return [quantile(values,.025),quantile(values,.975)]


def audit(rows,reference_weights,min_support=50):
    if count(min_support,"min_support")==0:raise ValueError("positive support threshold required")
    groups=aggregate(rows)
    stores={store for store,_ in groups}
    if set(reference_weights)!=stores:raise ValueError("reference weights must cover exactly the declared store universe")
    for weight in reference_weights.values():
        if isinstance(weight,bool) or not isinstance(weight,(int,float)) or not math.isfinite(weight) or weight<=0:
            raise ValueError("reference weights must be finite and positive")
    eligible=[];excluded=[]
    for store in sorted(stores):
        before=groups.get((store,'before'),[0,0]);after=groups.get((store,'after'),[0,0])
        if min(before[0],after[0])<min_support:
            excluded.append({'store':store,'before_accepted':before[0],'after_accepted':after[0],
                             'reason':'insufficient support in at least one period'})
            continue
        eligible.append({'store':store,'before_accepted':before[0],'after_accepted':after[0],
                         'before_completed':before[1],'after_completed':after[1],
                         'before_rate':before[1]/before[0],'after_rate':after[1]/after[0],
                         'difference':after[1]/after[0]-before[1]/before[0],
                         'weight':reference_weights[store]})
    if not eligible:raise ValueError("no common supported population; do not report a comparable rate")
    weight_sum=sum(p['weight'] for p in eligible)
    standardized={period:sum(p['weight']*p[period+'_rate'] for p in eligible)/weight_sum for period in ['before','after']}
    common={period:sum(p[period+'_completed'] for p in eligible)/sum(p[period+'_accepted'] for p in eligible)
            for period in ['before','after']}
    raw={period:sum(v[1] for (s,p),v in groups.items() if p==period)/sum(v[0] for (s,p),v in groups.items() if p==period)
         for period in ['before','after']}
    coverage={period:sum(p[period+'_accepted'] for p in eligible)/sum(v[0] for (s,p),v in groups.items() if p==period)
              for period in ['before','after']}
    result={'stores':len(stores),'supported_common_stores':len(eligible),'minimum_accepted_per_period':min_support,
            'raw_all_stores':{**raw,'difference':raw['after']-raw['before']},
            'raw_common_stores':{**common,'difference':common['after']-common['before']},
            'standardized_common_stores':{**standardized,'difference':standardized['after']-standardized['before']},
            'accepted_order_coverage':coverage,'retained_reference_weight_fraction':weight_sum/sum(reference_weights.values())}
    return result,eligible,excluded


def generate():
    rng=random.Random(1602);rows=[];weights={}
    for i in range(20):
        store=f'store-{i:02d}';weights[store]=1/20
        base=.86 if i<10 else .46
        for period in ['before','after']:
            n=(80 if i<10 else 12) if period=='before' else (12 if i<10 else 80)
            if i==19:n=4 if period=='before' else 1
            probability=base+(.03 if period=='after' else 0)
            for day in range(10):
                completed=sum(rng.random()<probability for _ in range(n))
                rows.append({'store':store,'period':period,'day':day,'accepted':n,'completed':completed})
    return {'rows':rows,'reference_weights':weights,'seed':1602,
            'measure':'completed accepted orders / accepted orders; no treatment assignment'}


def experiment(data):
    metrics,pairs,excluded=audit(data['rows'],data['reference_weights'])
    metrics['paired_store_percentile_interval_95']=paired_interval(pairs)
    metrics['bootstrap']={'unit':'store pair','repetitions':2000,'seed':1602,'interpretation':'descriptive; not a causal interval'}
    raw=metrics['raw_common_stores']['difference'];fixed=metrics['standardized_common_stores']['difference']
    report=f"""# Store composition and the decision

Topic: retail operations. Decision: distinguish a change inside comparable stores from a change in the order mix.

The generator shifts volume from high-completion stores toward lower-completion stores while modestly improving each store's latent probability. My audit requires support in both periods, keeps the same common stores in both comparisons, and applies predeclared equal-store reference weights. Unsupported stores are reported instead of extrapolated.

Among {metrics['supported_common_stores']} common supported stores, the raw completion difference is {raw*100:.2f} percentage points. Fixed-mix standardization gives {fixed*100:.2f} points; the paired-store descriptive95%interval is [{metrics['paired_store_percentile_interval_95'][0]*100:.2f},{metrics['paired_store_percentile_interval_95'][1]*100:.2f}] points. Reference-weight retention is {metrics['retained_reference_weight_fraction']:.3f}. The excluded store and period coverage are preserved in decisions.json and metrics.json.

The sign reversal is a composition effect in an original simulation. These are observed before/after quantities, not an experiment or treatment effect. Equal-store weighting answers a different policy question from order-weighted averages. Stores are the resampling unit, and only nineteen supported stores limit uncertainty estimates. Next, I would agree the reference mix and population with operations owners before interpreting a region-wide dashboard.
"""
    return metrics,{'supported_pairs':pairs,'excluded':excluded},None,report
