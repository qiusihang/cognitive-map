import xml.etree.ElementTree as ET
import os
import csv
import json

# --- Configuration ---
XML_FILE = 'ccm/crowdsourced_cafe.xml'
CSV_FILE = 'output/questions.csv'
TXT_FILE = 'output/knowledge.txt'
# Note: Random elements are still used sparingly to pick 'incorrect' options,
# but the iteration over map elements is now comprehensive.

def load_xml_data(file_path):
    """
    Parses the XML file and extracts all structural, relation, edge, and path data.
    Returns a dictionary containing all processed data structures.
    """
    if not os.path.exists(file_path):
        print(f"Error: XML file '{file_path}' not found.")
        return None

    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
    except ET.ParseError as e:
        print(f"Error parsing XML file: {e}")
        return None

    data = {
        'elements': {},  # id -> {name, type, parent_id (if district child)}
        'districts': [], # List of District elements
        'relations': [], # List of Relation elements
        'edges': [],     # List of Edge elements
        'paths': [],     # List of Path elements
    }

    # Helper to map IDs to Names and Types
    def process_structural_elements(element, parent_id=None):
        tag_name = element.tag
        if 'id' in element.attrib and 'name' in element.attrib:
            el_id = element.attrib['id']
            data['elements'][el_id] = {
                'name': element.attrib['name'],
                'type': tag_name,
                'parent_id': parent_id,
                'element': element
            }

        if tag_name == 'District':
            data['districts'].append(element)
            # Recursively process children
            for child in element:
                if child.tag in ['Node', 'Reference', 'District']:
                    process_structural_elements(child, parent_id=el_id)
        elif tag_name in ['Node', 'Reference']:
            pass # Already processed above

    # 1. Process all structural elements (Node, Reference, District) to create the ID map
    for element in root:
        if element.tag in ['Node', 'Reference', 'District']:
            process_structural_elements(element)

    # 2. Process Relations, Edges, and Paths
    for element in root:
        if element.tag == 'Relation':
            data['relations'].append(element)
        elif element.tag == 'Edge':
            data['edges'].append(element)
        elif element.tag == 'Path':
            data['paths'].append(element)

    return data

def get_element_info(data, element_id):
    """Retrieves the name and type of an element by its ID."""
    return data['elements'].get(element_id, {'name': f"Unknown Element ({element_id})", 'type': 'Unknown'})

def format_question_list(items):
    """Formats a list of names for inclusion in the question string."""
    return ", ".join([f"'{item}'" for item in items])

# --- Question Generation Functions ---

def generate_all_type_i_questions(data):
    """
    Question Type I: Element verification (District content).
    """
    questions = []
    knowledge = []

    for district_el in data['districts']:
        district_name = district_el.attrib['name']
        
        # Get all immediate children names
        all_children = [
            get_element_info(data, child.attrib['id'])['name']
            for child in district_el
            if child.tag in ['Node', 'Reference', 'District'] and 'id' in child.attrib
        ]
        all_ids = [child.attrib['id'] for child in district_el
                   if child.tag in ['Node', 'Reference', 'District'] and 'id' in child.attrib]
        all_ids.append(district_el.attrib['id'])

        if not all_children:
            continue

        question_list_str = format_question_list(all_children)
        question = (
            f"Does the '{district_name}' area contain the following: {question_list_str}? "
        )
        questions.append({
            'Type': 'Type I (Element verification)',
            'ID': f"I_{len(questions)}",
            'Question': question,
            'Answers': r"#Yes, it does%%Yes#No, it doesn't%%No#It contains more%%Other",
            'IDs': format_question_list(all_ids)
        })
        sentence = (
            f"The '{district_name}' area usually contain the following: {question_list_str}. "
        )
        knowledge.append({
            'Type': 'Type I (Element Belonging)',
            'Knowledge': sentence
        })

    return questions, knowledge


def generate_all_type_ii_questions(data):
    """
    Question Type II: Relation/Edge verification.
    A. Relation: Generate questions for every Relation.
    B. Edge: Generate separation verification and type questions for every Edge.
    """
    questions = []
    knowledge = []

    # --- A. Relation Verification (Two questions per Relation) ---
    for relation_el in data['relations']:
        subject_id = relation_el.attrib['subjectId']
        object_id = relation_el.attrib['objectId']
        relation_type = relation_el.attrib['relationType']

        subject_name = get_element_info(data, subject_id)['name']
        object_name = get_element_info(data, object_id)['name']

        # 1. Relationship Check
        q_rel = (
            f"Is the relationship between '{subject_name}' (subject) and '{object_name}' (object): "
            f"'{relation_type}'?"
        )
        questions.append({
            'Type': 'Type II-A (Relation Check)',
            'ID': f"II_{len(questions)}",
            'Question': q_rel,
            'Answers': f"#Yes, it is%%Yes#No, it isn't%%No#Not only {relation_type}%%Other",
            'IDs': format_question_list([relation_el.attrib['id'], subject_id, object_id])
        })
        sentence = (
            f"The relationship between '{subject_name}' (subject) and '{object_name}' (object) is "
            f"'{relation_type}'"
        )
        knowledge.append({
            'Type': 'Type II-A (Relation)',
            'Knowledge': sentence,
        })

    # 2. Non-Relationship Check
    for district_el in data['districts']:
        # Get all immediate children names
        all_children = [child for child in district_el if child.tag in ['Node', 'Reference', 'District'] and 'id' in child.attrib]

        if not all_children: continue

        for i in range(len(all_children)):
            for j in range(i+1, len(all_children)):
                subject_id = all_children[i].attrib['id']
                object_id = all_children[j].attrib['id']
                subject_name = get_element_info(data, all_children[i].attrib['id'])['name']
                object_name = get_element_info(data, all_children[j].attrib['id'])['name']
                flag = False
                for relation_el in data['relations']:
                    if (subject_id == relation_el.attrib['subjectId'] and object_id == relation_el.attrib['objectId']):
                        flag = True
                        break
                    if (object_id == relation_el.attrib['subjectId'] and subject_id == relation_el.attrib['objectId']):
                        flag = True
                        break
                if flag:
                    continue
                q_non_rel = (
                    f"At the location '{district_el.attrib['name']}', it seems that '{subject_name}' and '{object_name}' don't have a fixed spatial relationship (random and inconsistent). "
                    f"Is that correct?"
                )
                questions.append({
                    'Type': 'Type II-A (Non-Relation Check)',
                    'ID': f"II_{len(questions)}",
                    'Question': q_non_rel,
                    'Answers': r"#Correct%%Yes#Not true%%No#Partially correct%%Other",
                    'IDs': format_question_list([subject_id, object_id])
                })
                sentence = (
                    f"At the location '{district_el.attrib['name']}', it seems that '{subject_name}' and '{object_name}' don't have a fixed spatial relationship (random and inconsistent)."
                )
                knowledge.append({
                    'Type': 'Type II-A (Non-Relation)',
                    'Knowledge': sentence,
                })

    # --- B. Edge Verification (Two questions per Edge) ---
    for edge_el in data['edges']:
        edge_name = edge_el.attrib['name']
        edge_type = edge_el.attrib['edgeType']

        group_a_ids = [el.text for el in edge_el.find('GroupA') if el.tag == 'ElementId' and el.text]
        group_b_ids = [el.text for el in edge_el.find('GroupB') if el.tag == 'ElementId' and el.text]

        all_ids = group_a_ids + group_b_ids
        all_ids.append(edge_el.attrib['id'])

        if not (group_a_ids and group_b_ids):
            continue

        # Get the name of the first element in each group for the question text
        group_a_name = ''
        group_b_name = ''
        for i in range(len(group_a_ids)):
            group_a_name += (', ' if i > 0 else '') + get_element_info(data, group_a_ids[i])['name']
        for i in range(len(group_b_ids)):
            group_b_name += (', ' if i > 0 else '') + get_element_info(data, group_b_ids[i])['name']

        # 1. Verify the separation
        q_separation = (
            f"Does the '{edge_name}' separate '{group_a_name}' from '{group_b_name}'? "
        )
        questions.append({
            'Type': 'Type II-B (Edge: Separation)',
            'ID': f"II_{len(questions)}",
            'Question': q_separation,
            'Answers': r"#Yes, it does%%Yes#No, it doesn't%%No#Partially correct%%Other",
            'IDs': format_question_list(all_ids)
        })
        sentence = (
            f"The '{edge_name}' separates '{group_a_name}' from '{group_b_name}'."
        )
        knowledge.append({
            'Type': 'Type II-B (Edge Separation)',
            'Knowledge': sentence,
        })

        # 2. Verify the type
        q_type_check = (
            f"For the '{edge_name}' (which separates '{group_a_name}' from '{group_b_name}'), is it '{edge_type}'?"
            # f"If not, what is its type?"
        )
        questions.append({
            'Type': 'Type II-B (Edge: Type Check)',
            'ID': f"II_{len(questions)}",
            'Question': q_type_check,
            'Answers': f"#Yes, it is%%Yes#No, it isn't%%No#Not only {edge_type}%%Other",
            'IDs': format_question_list(all_ids)
        })
        sentence = (
            f"For the '{edge_name}' (which separates '{group_a_name}' from '{group_b_name}') is '{edge_type}'."
        )
        knowledge.append({
            'Type': 'Type II-B (Edge Type)',
            'Knowledge': sentence,
        })

    return questions, knowledge


def generate_all_type_iii_questions(data):
    """
    Question Type III: Path verification (verify each step transition).
    Generates transition questions for every step in every path.
    """
    questions = []
    knowledge = []
    
    # Filter for paths with at least 2 steps (to check a transition)
    verifiable_paths = [
        p for p in data['paths'] if len(list(p.findall('Step'))) >= 2
    ]

    for path_el in verifiable_paths:
        path_name = path_el.attrib['name']
        role = path_el.attrib['subject']
        steps = path_el.findall('Step')
        
        for step_index in range(len(steps) - 1):
            current_step = steps[step_index]
            next_step_correct = steps[step_index + 1]

            # Info for Current Step (i)
            activity_i = current_step.attrib['activity']
            location_i_id = current_step.attrib['elementId']
            location_i_name = get_element_info(data, location_i_id)['name']

            # Info for Correct Next Step (i+1)
            activity_i_plus_1 = next_step_correct.attrib['activity']
            location_i_plus_1_id = next_step_correct.attrib['elementId']
            location_i_plus_1_name = get_element_info(data, location_i_plus_1_id)['name']

            all_ids = [path_el.attrib['id'], location_i_id, location_i_plus_1_id]

            # Transition Question
            question = (
                f"When you perform the activity '{path_name}' as the '{role}', after you "
                f"'{activity_i}' at the '{location_i_name}', "
                f"you usually '{activity_i_plus_1}' at the '{location_i_plus_1_name}'. Is that correct? "
                # f"If not, what is the next step and where does it happen?"
            )
            questions.append({
                'Type': 'Type III (Path)',
                'ID': f"III_{len(questions)}",
                'Question': question,
                'Answers': r"#Yes, correct%%Yes#No, not true%%No#Partially correct%%Other",
                'IDs': format_question_list(all_ids)
            })
            sentence = (
                f"When you perform the activity '{path_name}' as the '{role}', after you "
                f"'{activity_i}' at the '{location_i_name}', "
                f"you usually '{activity_i_plus_1}' at the '{location_i_plus_1_name}'."
            )
            knowledge.append({
                'Type': 'Type III (Path)',
                'Knowledge': sentence,
            })

    return questions, knowledge


def write_to_csv(questions, csv_file=CSV_FILE):
    """Writes the list of question dictionaries to a CSV file."""
    fieldnames = ['Type', 'ID', 'Question', 'Answers', 'IDs'] # "IDs" means all XML IDs related to this question
    
    try:
        with open(csv_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(questions)
        print(f"Successfully generated {len(questions)} questions into '{CSV_FILE}'.")
    except Exception as e:
        print(f"Error writing to CSV file: {e}")


def csv_to_json(csv_file, json_file):
    with open(csv_file) as f:
        json.dump(list(csv.DictReader(f)), open(json_file, 'w'))


def write_to_txt(knowledge,knowledge_file=TXT_FILE):
    """Writes the list of knowledge dictionaries to a TXT file."""
    fieldnames = ['Type', 'Knowledge']
    
    try:
        with open(knowledge_file, 'w', encoding='utf-8') as txtfile:
            for k in knowledge:
                txtfile.write(k['Knowledge'])
                txtfile.write("\n")

        print(f"Successfully generated {len(knowledge)} knowledge sentences into '{TXT_FILE}'.")
    except Exception as e:
        print(f"Error writing to TXT file: {e}")


# --- Main Execution ---
def cafe_questions():
    """Main function to load data, generate all questions, and save to CSV."""
    print(f"Attempting to load data from: {XML_FILE}")
    data = load_xml_data(XML_FILE)

    if not data:
        print("\nCould not load or parse XML data. Exiting.")
        return

    print("Generating comprehensive set of verification questions...")

    all_questions = []
    all_knowledge = []

    # Generate Question Type I
    q1_list, k1_list = generate_all_type_i_questions(data)
    all_questions.extend(q1_list)
    all_knowledge.extend(k1_list)

    # Generate Question Type II
    q2_list, k2_list = generate_all_type_ii_questions(data)
    all_questions.extend(q2_list)
    all_knowledge.extend(k2_list)

    # Generate Question Type III
    q3_list, k3_list = generate_all_type_iii_questions(data)
    all_questions.extend(q3_list)
    all_knowledge.extend(k3_list)
    
    # Save results
    
    # For crowdsourcing:
    # write_to_csv(all_questions)
    # csv_to_json(CSV_FILE, 'output/questions.json')
    
    # After crowdsourcing:
    write_to_txt(all_knowledge)



def question_generation_from_scratch(element_list = [
    'Austria','Belgium','France','Germany','Liechtenstein','Luxembourg','Monaco','Netherlands','Switzerland'
    ]):
    # Type I: element properties
    questions = []
    for e in element_list:
        question = (
            f"How large is the area of {e} compared to other Western European countries?"
        )
        questions.append({
            'Type': 'Type I',
            'ID': f"{len(questions)}",
            'Question': question,
            'Answers': f"#Very large#Large#Medium#Small#Very small#I'm not familiar with {e}%%Unknown"
        })
    # Type II: element relations
    for i in range(len(element_list)):
        for j in range(i+1, len(element_list)):
            e1 = element_list[i]
            e2 = element_list[j]
            question = (
                f"Are {e1} and {e2} neighboring countries? "
                "If they are neighboring countries, what is their positional relationship?"
            )
            questions.append({
                'Type': 'Type II',
                'ID': f"{len(questions)}",
                'Question': question,
                'Answers': (f"#They are not neighboring countries%%No"
                            f"#{e1}: North of {e2}%%North"
                            f"#{e1}: South of {e2}%%South"
                            f"#{e1}: East of {e2}%%East"
                            f"#{e1}: West of {e2}%%West"
                            f"#{e1}: North-East of {e2}%%North-East"
                            f"#{e1}: North-West of {e2}%%North-West"
                            f"#{e1}: South-East of {e2}%%South-East"
                            f"#{e1}: South-West of {e2}%%South-West"
                            f"#I'm not familiar with it%%Unknown"
                )
            })
    # Save results
    write_to_csv(questions, 'output/questions2.csv')
    csv_to_json('output/questions2.csv', 'output/questions2.json')


if __name__ == '__main__':
    cafe_questions()
    # question_generation_from_scratch()

    