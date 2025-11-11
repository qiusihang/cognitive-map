import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.inter_rater import fleiss_kappa
from scipy.stats import binomtest

def simulation_analysis():
    groups = []
    groups.append( pd.read_csv('output/stat_rag_mission1_50.csv') )
    groups.append( pd.read_csv('output/stat_rag_mission2_50.csv') )
    groups.append( pd.read_csv('output/stat_no_rag_mission1_50.csv') )
    groups.append( pd.read_csv('output/stat_no_rag_mission2_50.csv') )

    groups_steps = []

    for i in range(4):
        steps = [s for s in groups[i]['steps'] if s < 31]
        # print(stats.shapiro(steps))
        print(np.average(steps), np.std(steps), len(steps)/len(groups[i]['steps']))
        groups_steps.append(steps)

    for i in range(3):
        for j in range(i+1,4):
            results = stats.mannwhitneyu(groups_steps[i], groups_steps[j])
            print(i,j,results)


def calculate_percent_agreement(frequency_table):
    raters_per_subject = frequency_table.sum(axis=1)
    m = raters_per_subject.max()
    total_possible_pairs = (raters_per_subject * (raters_per_subject - 1)).sum()
    if total_possible_pairs == 0:
        return 1.0
    total_agreeing_pairs = (frequency_table * (frequency_table - 1)).sum()
    percent_agreement = total_agreeing_pairs / total_possible_pairs
    
    return percent_agreement


def frequency_table(data):
    # Convert strings to numbers
    all_ratings = [r for subject in data for r in subject]
    unique_cats = sorted(set(all_ratings))
    cat_to_num = {cat: i for i, cat in enumerate(unique_cats)}
    
    # Create numeric matrix for Fleiss' Kappa
    n_subjects = len(data)
    n_cats = len(unique_cats)
    numeric_matrix = np.zeros((n_subjects, n_cats))
    
    for i, subject_ratings in enumerate(data):
        for rating in subject_ratings:
            numeric_matrix[i, cat_to_num[rating]] += 1

    return numeric_matrix.astype(int)


def crowdsourcing_reliability(csvfile, n_participant):
    df = pd.read_csv(csvfile)
    table = []
    for index, row in df.iterrows():
        if 'why' in f'{row['qid']}':
            continue
        table.append(row[[f'P{i}' for i in range(n_participant)]].to_numpy())
    table = np.array(table)
    frequency = frequency_table(table)
    print(f'Fleiss Kappa: {fleiss_kappa(frequency)}')
    print(f'Percent Agreement: {calculate_percent_agreement(frequency)}')


def comparison_analysis():
    df = pd.read_csv('data/aggregated_results_task3.csv')
    for metrics in ["contextual_richness", "spatial_coherence", "functional_plausibility"]:
        strings = df[metrics].to_numpy()
        print(metrics)
        k = 0
        n = 0
        for s in strings:
            left, sign, right = s.split(' ')
            if sign == '=':
                continue
            n += 1
            if 'noccm' in right:
                k += 1
        print( binomtest(k, n) )


if __name__ == "__main__":
    # simulation_analysis()

    # crowdsourcing_reliability('data/aggregated_results_task1.csv', 10)
    # crowdsourcing_reliability('data/aggregated_results_task2_UK.csv', 3)
    # crowdsourcing_reliability('data/aggregated_results_task2_US.csv', 3)

    comparison_analysis()
