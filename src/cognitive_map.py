import xml.etree.ElementTree as ET
import random
import math
from typing import Dict, List, Tuple

class MapElement:
    """Base class for Districts and References."""
    def __init__(self, element_id, name, element_type):
        self.id = element_id
        self.name = name
        self.type = element_type
        self.parent = None
        self.center = (0.0, 0.0) # This is what we solve for
        self.w = 0.0 # Full width
        self.h = 0.0 # Full height
        
    def __repr__(self):
        return f"<{self.type} {self.id} @ ({self.center[0]:.0f}, {self.center[1]:.0f})>"

class Path:
    def __init__(self, element):
        self.type = element.get('pathType')
        #TODO: self.subject = 
        #TODO: self.elements = 
        #TODO: self.activities = 

class Node(MapElement):
    def __init__(self, element, parent = None):
        super().__init__(element.get('id'), element.get('name'), 'Node')
        self.parent = parent
        self.quantity = element.get('quantity', 1)
        self.w = 1
        self.h = 1

class District(MapElement):
    def __init__(self, element, parent = None):
        super().__init__(element.get('id'), element.get('name'), 'District')
        self.size_type = element.get('size', 'medium')
        self.parent = parent
        self.children = []
        self.quantity = element.get('quantity', 1)
        # District Dimensions
        # DEFAULT_DISTRICT_SIZE = {"small": 100, "medium": 200, "large": 300, "huge":500} # coffee shop (should be defined by context)
        DEFAULT_DISTRICT_SIZE = {"very small":10, "small": 50, "medium": 80, "large": 100, "huge":150} # Western Europe
        base_size = DEFAULT_DISTRICT_SIZE.get(self.size_type, 100)
        self.target_area = base_size * base_size
        root_area = math.sqrt(self.target_area)
        ratio_fudge = random.uniform(0.9, 1.1)
        self.w = root_area * ratio_fudge
        self.h = self.target_area / self.w
        
class Relation:
    def __init__(self, element):
        self.type = element.get('relationType')  # north, east, on, in, etc.
        self.subject_id = element.get('subjectId')
        self.object_id = element.get('objectId')
        self.weight = float(element.get('weight', 1.0))

class Edge:
    def __init__(self, element):
        self.type = element.get('edgeType') # passable or not
        self.groups = {"GroupA":[], "GroupB":[]}
        for group in element:
            if group.tag == "GroupA" or group.tag == "GroupB":
                for e in group:
                    self.groups[group.tag].append(e.get('id'))

class Reference(MapElement):
    def __init__(self, element, parent = None):
        super().__init__(element.get('id'), element.get('name'), 'Reference')
        self.hint = element.get('locationHint')
        self.parent = parent

class CognitiveMap:
    def __init__(self, xml_string: str):
        self.xml_string = xml_string
        self.elements: Dict[str, MapElement] = {}
        self.relations: List[Relation] = []
        self._parse_xml()
        self.districts = [e for e in self.elements.values() if e.type == 'District']
        self.references = [e for e in self.elements.values() if e.type == 'Reference']
        self.nodes = [e for e in self.elements.values() if e.type == 'Node']
        self.children = [e for e in self.elements.values() if (e.type == 'Node' or e.type == 'Reference' or e.type == 'District') and e.parent is None]
        self.grid = None

    def _add_map_element(self, element, parent = None):
        # 1. Node
        if element.tag == 'Node':
            node = Node(element, parent)
            self.elements[node.id] = node
            return node

        # 2. References
        if element.tag == 'Reference':
            ref = Reference(element, parent)
            self.elements[ref.id] = ref
            return ref

        # 3. Districts
        if element.tag == 'District':
            district = District(element, parent)
            self.elements[district.id] = district
            
            for child in element:
                e = self._add_map_element(child, element)
                if not e is None:
                    district.children.append(e)
            return district
        
        return None


    def _parse_xml(self):
        """Parses the XML string into structured objects."""
        print("0. Parsing XML...")
        root = ET.fromstring(self.xml_string)
        
        # Nodes, References, Districts
        for child in root:
            self._add_map_element(child)
            
        # Relations
        for r_el in root.findall('Relation'):
            self.relations.append(Relation(r_el))
        
        # Edges
        for e_el in root.findall('Edge'):
            self.relations.append(Relation(e_el))
