import csv
import json
import os
import sys
import re
import pandas as pd
from dotenv import load_dotenv
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from agent import Agent

def read_csv_and_load_json(csv_file_path, userid_column='Participant id', json_directory='./'):
    """
    Read CSV file and load corresponding JSON files for each user ID
    
    Args:
        csv_file_path (str): Path to the CSV file
        userid_column (str): Name of the column containing user IDs
        json_directory (str): Directory where JSON files are stored
    
    Returns:
        list: List of dictionaries with JSON data merged
    """
    results = []
    
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            
            for row_num, row in enumerate(csv_reader, 1):
                userid = row.get(userid_column)
                
                if not userid:
                    print(f"Warning: No userid found in row {row_num}")
                    continue
                
                # Construct JSON file path
                json_filename = f"{userid}.json"
                json_file_path = os.path.join(json_directory, json_filename)
                
                # Load JSON data
                json_data = {}
                if os.path.exists(json_file_path):
                    try:
                        with open(json_file_path, 'r', encoding='utf-8') as json_file:
                            json_data = json.load(json_file)
                    except json.JSONDecodeError as e:
                        print(f"Error: Invalid JSON in file {json_file_path}: {e}")
                    except Exception as e:
                        print(f"Error reading JSON file {json_file_path}: {e}")
                else:
                    print(f"Warning: JSON file not found: {json_file_path}")
                
                # Merge CSV row with JSON data
                merged_data = {
                    **row,  # Original CSV data
                    'answers': json_data  # Loaded JSON data
                }
                
                results.append(merged_data)
        
        return results
    
    except FileNotFoundError:
        print(f"Error: CSV file '{csv_file_path}' not found.")
        return []
    except Exception as e:
        print(f"Error processing files: {e}")
        return []


def aggregate_results(results, agg_results = {}):
    aggregated_results = agg_results.copy()
    for i, result in enumerate(results, 1):
        # print(f"\n--- Record {i} ---")
        # print(f"Participant {result['Participant id']} Answers : {result['answers']['answers']}")
        answers = result['answers']['answers']
        for qid in answers:
            if qid == 'intro' or 'why' in qid:
                continue
            if qid in aggregated_results:
                n = len(aggregated_results[qid])
                aggregated_results[qid][ f'P{n}' ] = answers[qid]
                if qid+'_why' in answers:
                    aggregated_results[qid+'_why'][ f'P{n}' ] = answers[qid+'_why'] if answers[qid] != 'Yes' else ''
            else:
                aggregated_results[qid] = { 'P0': answers[qid] }
                if qid+'_why' in answers:
                    aggregated_results[qid+'_why']= { 'P0': answers[qid+'_why'] } if answers[qid] != 'Yes' else { 'P0': '' }
    
    return aggregated_results


def save_aggregated_results(agg_results, filename = 'data/aggregated_results.csv'):
    # sorted_results = dict(sorted(agg_results.items(), key=lambda x: x[0].replace('_', ''))) # task 1
    sorted_results = dict(sorted(agg_results.items(), key=lambda x: int(x[0]))) # task 2
    df = pd.DataFrame.from_dict(sorted_results, orient='index').reset_index()
    df = df.rename(columns={'index': 'qid'})
    df.to_csv(filename, index=False)
    print("CSV file created successfully!")


def list2string(items):
    if items:
        return ", ".join([f"'{item}'" for item in items])
    else:
        return 'None'


def generate_prompt(ids, feedback, xml, xsd):
    prompt = """
You are tasked with improving an XML file that was created according to the provided XSD schema.
Your focus is on the following element IDs: [IDS]

Please follow this process:
- Analyze the feedback from people: [FEEDBACK]
- Identify common themes and consensus in the feedback (at least proposed by two people simultaneously)
- Check whether the content of the feedback has similar or conflicting meanings with existing elements. If so, do not consider this feedback.
- Determine the required actions: decide whether to add, update, or delete the specified elements based on the feedback analysis
- Implement changes: modify the target elements and update any other elements that reference them
- Ensure compliance: all modifications must adhere to the XSD schema

Materials provided:
Complete XML file:
<XMLFILE>

XSD schema:
<XSDFILE>

Return the improved XML file with your changes implemented.
    """
    prompt = prompt.replace('IDS', ids)
    prompt = prompt.replace('[FEEDBACK]', list2string(feedback))
    prompt = prompt.replace('<XMLFILE>', xml)
    prompt = prompt.replace('<XSDFILE>', xsd)
    return prompt


def load_data_cafe():
    results_UK = read_csv_and_load_json('data/task1/prolific_demographic_UK.csv', userid_column='Participant id', json_directory='data/task1/data/')
    results_US = read_csv_and_load_json('data/task1/prolific_demographic_US.csv', userid_column='Participant id', json_directory='data/task1/data/')

    aggregated_results = aggregate_results(results_UK)
    aggregated_results = aggregate_results(results_US, aggregated_results)

    # Save the aggregated results. The original demographic data won't be uploaded as promised to the participants!
    save_aggregated_results(aggregated_results)


def load_data_WE(country = 'all'):
    if country == 'UK' or country == 'all':
        results_UK = read_csv_and_load_json('data/task2/prolific_demographic_UK.csv', userid_column='Participant id', json_directory='data/task2/data/')
    if country == 'US' or country == 'all':
        results_US = read_csv_and_load_json('data/task2/prolific_demographic_US.csv', userid_column='Participant id', json_directory='data/task2/data/')

    aggregated_results = {}
    if country == 'UK' or country == 'all':
        aggregated_results = aggregate_results(results_UK, aggregated_results)
    if country == 'US' or country == 'all':
        aggregated_results = aggregate_results(results_US, aggregated_results)

    # Save the aggregated results. The original demographic data won't be uploaded as promised to the participants!
    save_aggregated_results(aggregated_results, filename=f'data/aggregated_results_task2_{country}.csv')



def analysis_data_cafe(csvfile = 'data/aggregated_results_task1.csv'):
    df = pd.read_csv(csvfile)
    questions = pd.read_csv('output/questions.csv')
    
    aggregated_results = {}

    for index, row in df.iterrows():
        qid = row['qid']
        aggregated_results[qid] = [row[col] for col in df.columns if col != 'qid' and not pd.isna(row[col])]

    final_ids = []

    for qid in aggregated_results:
        if not "why" in qid:
            if sum([ int(ans=='Yes') for ans in aggregated_results[qid] ]) < 8: # three or more workers disagree --> let LLM improve the CCM
                print('Processing '+qid+"...")
                ids = 'None'
                for index, row in questions.iterrows():
                    if row['ID'] == qid:
                        ids = row['IDs']
                feedback = aggregated_results[qid+"_why"]
                for id in ids.split(','):
                    if not id in final_ids:
                        final_ids.append(id)
    print(final_ids)


def process_data_cafe(csvfile = 'data/aggregated_results_task1.csv'):
    df = pd.read_csv(csvfile)
    questions = pd.read_csv('output/questions.csv')
    with open("ccm/cafe.xml", "r") as xml_file:
        ccm = xml_file.read() # Read the entire file into a string
    with open("ccm/ccm.xsd", "r") as xsd_file:
        xsd = xsd_file.read() # Read the entire file into a string
    
    # Initialize RAG system
    load_dotenv()
    OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
    if OPENROUTER_API_KEY is None:
        print("API Key isn't found.")
        exit(0)
    agent = Agent(openrouter_api_key=OPENROUTER_API_KEY) #, model='google/gemini-2.5-pro')
    responses = []

    aggregated_results = {}

    for index, row in df.iterrows():
        qid = row['qid']
        aggregated_results[qid] = [row[col] for col in df.columns if col != 'qid' and not pd.isna(row[col])]

    for qid in aggregated_results:
        if not "why" in qid:
            if sum([ int(ans=='Yes') for ans in aggregated_results[qid] ]) < 8: # three or more workers disagree --> let LLM improve the CCM
                print('Processing '+qid+"...")
                ids = 'None'
                for index, row in questions.iterrows():
                    if row['ID'] == qid:
                        ids = row['IDs']
                feedback = aggregated_results[qid+"_why"]
                prompt = generate_prompt(ids, feedback, ccm, xsd)

                while True:
                    agent.clear_conversation_history()
                    response = agent.generate_response(prompt)
                    responses.append(response)

                    pattern = r'<\?xml.*?</CognitiveMap>'
                    matches = re.findall(pattern, response, re.DOTALL)
                    if matches:
                        ccm = matches[0]
                        break
                    else:
                        print("No XML file provided by LLM")

    # Write JSON to a file
    with open("output/LLM_reasoning.json", "w") as file:
        json.dump(responses, file)

    with open("output/crowdsourced_ccm.xml", "w") as file:
        file.write(ccm)


import math
def average_direction(directions):
    dir_map = {"north":0, "north-east":1, "east":2, "south-east":3,
               "south":4, "south-west":5, "west":6, "north-west":7}
    
    # Convert to vectors and average
    vectors = [(math.cos(d*math.pi/4), math.sin(d*math.pi/4)) 
               for d in [dir_map[d] for d in directions]]
    avg_x, avg_y = sum(v[0] for v in vectors)/len(vectors), sum(v[1] for v in vectors)/len(vectors)
    
    # Convert back to direction
    angle = math.atan2(avg_y, avg_x)
    idx = round(angle/(math.pi/4)) % 8
    return list(dir_map.keys())[list(dir_map.values()).index(idx)]


def average_size(sizes):
    size_map = {"very small":0, "small":1, "medium":2, "large":3, "very large":4}
    sizes_num = [size_map[s] for s in sizes]
    average_size = int(sum(sizes_num)/len(sizes_num))
    map_size = {0:"very small", 1:"small", 2:"medium", 3:"large", 4:"huge"} # change to huge for CM implementation
    return map_size[average_size]


def process_data_WE(csvfile, ccmfile):
    df = pd.read_csv(csvfile)
    element_list = ['Austria','Belgium','France','Germany','Liechtenstein','Luxembourg','Monaco','Netherlands','Switzerland']
    ids = []
    for e in element_list:
        ids.append(e)
    for i in range(len(element_list)):
        for j in range(i+1, len(element_list)):
            ids.append((element_list[i], element_list[j]))

    xml_string = '''<?xml version="1.0" encoding="utf-8"?>
<CognitiveMap xsi:noNamespaceSchemaLocation="ccm.xsd"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
'''

    aggregated_results = {}

    for index, row in df.iterrows():
        qid = row['qid']
        aggregated_results[qid] = [row[col] for col in df.columns if col != 'qid' and not pd.isna(row[col])]

    known_country_list = []
    rels = {}

    for qid in aggregated_results:
        if aggregated_results[qid].count("No") >=2: continue
        if int(qid) < 9:
            country = element_list[int(qid)]
            known_country_list.append(country)
            sizes = [s.lower() for s in aggregated_results[qid] if s!="No" and s!="Unknown"]
            answer = average_size(sizes)
            xml_string += f'<District id="{country}" name="{country}" size="{answer}" districtType="open"/>\n'
        else:
            c1 = ids[int(qid)][0]
            c2 = ids[int(qid)][1]
            dirs = [d.lower() for d in aggregated_results[qid] if d!="No" and d!="Unknown"]
            if not dirs: continue
            answer = average_direction(dirs)
            for d in dirs:
                if dirs.count(d) >= 2: answer = d
            if c1 in known_country_list and c2 in known_country_list:
                if c1 in rels:
                    rels[c1].append( (c2, answer) )
                else:
                    rels[c1]= [ (c2, answer) ]

                if c2 in rels:
                    rels[c2].append( (c1, "inverse") )
                else:
                    rels[c2]= [ (c1, "inverse") ]
    
    rid = 0
    for c1 in rels:
        for r in rels[c1]:
            rid += 1
            c2 = r[0]
            answer = r[1]
            weight = max(1/len(rels[c1]), 1/len(rels[c2]))
            if answer == "inverse": continue
            xml_string += f'<Relation id="R{rid}" subjectId="{c1}" objectId="{c2}" relationType="{answer}" weight="{weight:.2f}"/>\n'
    
    xml_string += "</CognitiveMap>\n"

    print("CCM exported")

    with open(ccmfile, "w") as file:
        file.write(xml_string)


def load_data_comparison():
    results = read_csv_and_load_json('data/task3/prolific_demographic.csv', userid_column='Participant id', json_directory='data/task3/data/')
    res = {"contextual_richness" : [], "spatial_coherence" : [], "functional_plausibility" : []}
    for i, result in enumerate(results, 1):
        if not 'answers' in result['answers']: continue
        answers = result['answers']['answers']
        res["contextual_richness"].append( answers[0].replace('./imgs/','').replace('.jpg','') )
        res["spatial_coherence"].append( answers[1].replace('./imgs/','').replace('.jpg','') )
        res["functional_plausibility"].append( answers[2].replace('./imgs/','').replace('.jpg','') )
    df = pd.DataFrame(res)
    df.to_csv('data/aggregated_results_task3.csv', index=False)

if __name__ == "__main__":
    # load_data_cafe()
    # process_data_cafe()
    analysis_data_cafe()

    # load_data_WE('UK')
    # load_data_WE('US')
    # process_data_WE('data/aggregated_results_task2_UK.csv', 'ccm/we_uk.xml')
    # process_data_WE('data/aggregated_results_task2_US.csv', 'ccm/we_us.xml')

    # load_data_comparison()
