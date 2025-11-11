import random
import math
import copy
from typing import Dict, List, Tuple

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from cognitive_map import MapElement, District, Relation, Reference, CognitiveMap
from map_visualizer import MapVisualizer

class MapGenerator:

    def __init__(self, elements, objects, relations): # the goal is to set positions of objects
        self.elements = elements.copy()
        self.objects = objects.copy() # objects of this level
        self.all_objects = [] # all objects in the map (including children. This list is updated recursively later)
        self.relations = relations.copy()
        
        # --- Configuration and Constants ---
        self.MAP_WIDTH = 800
        self.MAP_HEIGHT = 800
        self.INITIAL_ITERATIONS = 1000  # Phase 1: Iterations for the force-directed simulation
        self.GROWTH_STEPS = 300         # Phase 2: Number of steps to reach full size (smooth growth)
        self.ADJACENCY_BUFFER = 30      # Minimum required spacing between adjacent objects
        self.BORDER_BUFFER = 50         # Minimum required spacing for borders
        self.MAX_ASPECT_RATIO = 1.5    # Max aspect ratio of width/height or height/width

        # Force constants for positioning objects (focusing on directional pull)
        self.INITIAL_SEPARATION = 100.0 # Fixed target separation distance for directional constraints
        self.MOVEMENT_THRESHOLD = 1.0   # Stop criteria
        self.GLOBAL_ATTRACTION_FACTOR = 0.0003  # Pull toward map center
        self.REPULSION_CONSTANT = 1000.0        # Constant for generalized repulsion (1/dist^2)
        self.DIRECTIONAL_PULL_MULTIPLIER = 0.03 # Strong force to satisfy relations

        # District Growth and Collision Constants
        self.ADJUSTMENT_ITER_PER_STEP = 10 # How many clustering iterations run at each growth step
        self.DIRECTIONAL_PULL_MULTIPLIER_2 = 0.01 # Slightly less aggressive pull in Phase 2
        self.COLLISION_REPULSION_MAGNITUDE = 1.0 # Multiplier for hard collision correction
        self.ADJACENCY_REPULSION = 3000.0 # NEW: Force magnitude for soft repulsion

        # Direction vectors for relations (x, y)
        self.DIRECTION_VECTORS = {
            "north": (0, 1), "south": (0, -1), "east": (1, 0), "west": (-1, 0),
            "north-east": (1, 1), "north-west": (-1, 1), "south-east": (1, -1),
            "south-west": (-1, -1), "near": (0,0)
        }

    def initialize_random_centers(self):
        """Initializes all movable centers to random positions."""
        for d in self.objects:
            # Place randomly but with some margin
            d.center = (
                random.uniform(self.BORDER_BUFFER, self.MAP_WIDTH - self.BORDER_BUFFER),
                random.uniform(self.BORDER_BUFFER, self.MAP_HEIGHT - self.BORDER_BUFFER)
            )
            if d.type == "Reference":
                if d.hint == 'East':
                    d.center = (self.MAP_WIDTH - self.BORDER_BUFFER, self.MAP_HEIGHT / 2)
                elif d.hint == 'West':
                    d.center = (self.BORDER_BUFFER, self.MAP_HEIGHT / 2)
                elif d.hint == 'North':
                    d.center = (self.MAP_WIDTH / 2, self.MAP_HEIGHT - self.BORDER_BUFFER)
                elif d.hint == 'South':
                    d.center = (self.MAP_WIDTH / 2, self.BORDER_BUFFER)
                else: # Default center
                    d.center = (self.MAP_WIDTH / 2, self.MAP_HEIGHT / 2)

    def solve_initial_placement(self):
        """
        Phase 1: Determine initial centers based ONLY on directional relations.
        This ignores district size and only solves for relative positioning.
        """
        print("\n1. Phase 1: Starting force-directed simulation to find stable center points...")
        
        # 1. Initialize randomly
        self.initialize_random_centers()

        map_center_x, map_center_y = self.MAP_WIDTH / 2, self.MAP_HEIGHT / 2
        
        # 2. Iterate to find stable relational placement
        for iteration in range(self.INITIAL_ITERATIONS):
            new_centers = {}
            total_movement = 0.0

            for d in self.objects:
                force_x, force_y = 0.0, 0.0
                
                # Global attraction to center (Keeps the map clustered)
                dx_center = map_center_x - d.center[0]
                dy_center = map_center_y - d.center[1]
                force_x += dx_center * self.GLOBAL_ATTRACTION_FACTOR
                force_y += dy_center * self.GLOBAL_ATTRACTION_FACTOR

                # Directional Attraction (Strongest Force)
                for rel in self.relations:
                    # Check relations where 'd' is the subject OR the object
                    
                    # Case 1: d is the subject of a directional relation
                    if rel.subject_id == d.id and rel.type in self.DIRECTION_VECTORS:
                        obj = self.elements.get(rel.object_id)
                        if obj:
                            vx, vy = self.DIRECTION_VECTORS[rel.type]
                            
                            # Target position is the object's center + fixed separation in the direction
                            target_cx = obj.center[0] + vx * self.INITIAL_SEPARATION / rel.weight
                            target_cy = obj.center[1] + vy * self.INITIAL_SEPARATION / rel.weight
                            
                            dx_pull = target_cx - d.center[0]
                            dy_pull = target_cy - d.center[1]
                            
                            # Apply a strong force towards the target
                            force_x += dx_pull * rel.weight * self.DIRECTIONAL_PULL_MULTIPLIER
                            force_y += dy_pull * rel.weight * self.DIRECTIONAL_PULL_MULTIPLIER

                    # Case 2: d is the object of a directional relation (e.g., if NY is North of VA, VA is South of NY)
                    elif rel.object_id == d.id and rel.type in self.DIRECTION_VECTORS:
                         subj = self.elements.get(rel.subject_id)
                         if subj:
                            # Invert the direction vector to find the subject's target position relative to d
                            vx, vy = self.DIRECTION_VECTORS[rel.type]
                            inv_vx, inv_vy = -vx, -vy # E.g., if relation is 'north', pull subject 'south' of object

                            # Target position is the subject's center - fixed separation in the direction
                            target_cx = subj.center[0] + inv_vx * self.INITIAL_SEPARATION / rel.weight
                            target_cy = subj.center[1] + inv_vy * self.INITIAL_SEPARATION / rel.weight
                            
                            dx_pull = target_cx - d.center[0]
                            dy_pull = target_cy - d.center[1]

                            # Apply a strong force towards the target
                            force_x += dx_pull * rel.weight * self.DIRECTIONAL_PULL_MULTIPLIER
                            force_y += dy_pull * rel.weight * self.DIRECTIONAL_PULL_MULTIPLIER

                # Proposed new center
                proposed_cx = d.center[0] + force_x
                proposed_cy = d.center[1] + force_y
                
                # Clamp to boundaries
                # Use a small arbitrary size (50) for clamping to give a border
                final_cx = max(self.BORDER_BUFFER, min(self.MAP_WIDTH - self.BORDER_BUFFER, proposed_cx))
                final_cy = max(self.BORDER_BUFFER, min(self.MAP_HEIGHT - self.BORDER_BUFFER, proposed_cy))
                
                new_centers[d.id] = (final_cx, final_cy)
                
                # Calculate total movement for convergence check
                movement = math.sqrt((d.center[0] - final_cx)**2 + (d.center[1] - final_cy)**2)
                total_movement += movement

            # Apply updates
            for d in self.objects:
                d.center = new_centers[d.id]

            # # Convergence Check
            # if total_movement < MOVEMENT_THRESHOLD:
            #     print(f"   Stabilized after {iteration+1} iterations. Total movement was {total_movement:.2f}.")
            #     break
            
        print("   Final Center Positions Determined.")
        

    # --- PHASE 2: Growth and Collision ---
    def grow_and_cluster_objects(self):
        """
        Phase 2a: Gradual growth, collision, and clustering using force-directed layout.
        objects grow from 10% size to 100%.
        """
        print("\n2. Phase 2: Starting iterative growth and collision management...")
        
        # Start at 10% scale to give room for initial forces to resolve
        start_scale = 0.1
        
        for step in range(self.GROWTH_STEPS):
            # Increase scale gradually, ensure we reach 1.0 at the final step
            current_scale = start_scale + (1.0 - start_scale) * (step / self.GROWTH_STEPS)
            
            # Run clustering iterations for stability at the current size
            total_movement = 0.0
            for iter_num in range(self.ADJUSTMENT_ITER_PER_STEP):
                total_movement = self.adjust_centers(current_scale)
                # if total_movement < 0.1 and iter_num > 0:
                #     break
            
            # Print progress
            if (step + 1) % 100 == 0 or step == self.GROWTH_STEPS - 1:
                print(f"   Growth Step {step+1}/{self.GROWTH_STEPS} (Scale: {current_scale:.2f}) | Movement: {total_movement:.2f}")

        print("   Phase 2: District growth and collision resolution complete.")

    def adjust_centers(self, scale: float) -> float:
        """
        Calculates forces (attraction, repulsion, constraints) and updates centers for the current scale.
        This is the core of the collision/growth simulation.
        """
        new_updates: Dict[str, Tuple[float, float, float, float]] = {} # Store (cx, cy, w, h)
        map_center_x, map_center_y = self.MAP_WIDTH / 2, self.MAP_HEIGHT / 2
        total_movement = 0.0

        for d in self.objects:
            # Start from current center
            current_cx, current_cy = d.center
            final_cx, final_cy = current_cx, current_cy
            new_w, new_h = d.w, d.h

            # --- 1. Force Calculation based on relations (Pull forces) ---
            force_x, force_y = 0.0, 0.0
            
            if d.type != "Reference":
                # Global attraction (Keeps the map centered)
                force_x += (map_center_x - current_cx) * self.GLOBAL_ATTRACTION_FACTOR
                force_y += (map_center_y - current_cy) * self.GLOBAL_ATTRACTION_FACTOR
            
            # Directional Constraint Force (Strong pull to enforce relational structure)
            for rel in self.relations:
                elements_to_check = []
                if rel.subject_id == d.id and rel.type in self.DIRECTION_VECTORS:
                    elements_to_check.append((self.DIRECTION_VECTORS[rel.type][0], self.DIRECTION_VECTORS[rel.type][1], self.elements.get(rel.object_id), rel.weight))
                elif rel.object_id == d.id and rel.type in self.DIRECTION_VECTORS:
                    elements_to_check.append((-self.DIRECTION_VECTORS[rel.type][0],-self.DIRECTION_VECTORS[rel.type][1], self.elements.get(rel.subject_id), rel.weight))

                for vx, vy, obj, weight in elements_to_check:
                    if obj:
                        if vx == 0 and vy == 0: # no direction "near" condition
                            vx = current_cx - obj.center[0]
                            vy = current_cy - obj.center[1]
                            while vx * vx + vy * vy < 1e-3: vx = random.random(); vy = random.random()
                            distance = math.sqrt(vx * vx + vy * vy)
                            vx /= distance
                            vy /= distance
                        
                        # Target position is the object's center + current scaled adjacency
                        target_dist_x = (d.w * scale + obj.w * scale) / 2 + self.ADJACENCY_BUFFER
                        target_dist_y = (d.h * scale + obj.h * scale) / 2 + self.ADJACENCY_BUFFER

                        target_cx = obj.center[0] + vx * target_dist_x
                        target_cy = obj.center[1] + vy * target_dist_y

                        dx_pull = target_cx - current_cx
                        dy_pull = target_cy - current_cy
                        
                        # Apply force towards the relational target position
                        force_x += dx_pull * weight * self.DIRECTIONAL_PULL_MULTIPLIER_2
                        force_y += dy_pull * weight * self.DIRECTIONAL_PULL_MULTIPLIER_2

            # Apply forces for an intermediate proposed position
            final_cx += force_x
            final_cy += force_y

            # --- 2. Soft Repulsion for Non-Related Objects ---
            
            # This applies a soft force to push non-related objects away from each other, 
            # improving layout clarity without enforcing a hard collision boundary.
            new_repulsion_x, new_repulsion_y = 0.0, 0.0

            for other_d in self.objects:
                if d.id == other_d.id: continue
                
                # Check if the pair is related (using the pre-calculated canonical set)
                # canonical_pair = tuple(sorted((d.id, other_d.id)))
                
                # Only apply soft repulsion if they are NOT directly related
                # if canonical_pair not in self.related_pairs:
                dx = other_d.center[0] - d.center[0]
                dy = other_d.center[1] - d.center[1]
                dist_sq = dx**2 + dy**2
                
                # Prevent extreme forces at very close distances (set a floor distance)
                min_dist_sq = max(( (d.w + other_d.w) * 0.5 ) ** 2, 1e-6) # Based on approximate size
                if dist_sq < min_dist_sq: dist_sq = min_dist_sq
                
                dist = math.sqrt(dist_sq)

                # Apply repulsion (Inverse square distance model)
                repulsion = - self.ADJACENCY_REPULSION / dist_sq
                new_repulsion_x += repulsion * dx / dist
                new_repulsion_y += repulsion * dy / dist
            
            final_cx += new_repulsion_x
            final_cy += new_repulsion_y

            # --- 3. Hard Collision Correction (Push forces) ---
            
            # We use a temporary object for collision checking
            d_temp = MapElement(d.id, d.name, d.type)
            d_temp.w, d_temp.h = d.w, d.h
            
            # Iterate through all other objects to resolve overlaps based on current scale
            for other_d in self.objects:
                if d.id == other_d.id: continue
                
                # Update temporary position for checking
                d_temp.center = (final_cx, final_cy)

                rect1 = self.get_rect_bounds(d_temp, scale)
                rect2 = self.get_rect_bounds(other_d, scale)
                
                overlap_x = max(0, min(rect1[2], rect2[2]) - max(rect1[0], rect2[0]))
                overlap_y = max(0, min(rect1[3], rect2[3]) - max(rect1[1], rect2[1]))
                
                if overlap_x > 0 and overlap_y > 0: # Collision detected
                    
                    if overlap_x < overlap_y:
                        # Horizontal Collision: smaller w and larger h
                        correction = overlap_x * self.COLLISION_REPULSION_MAGNITUDE
                        
                        # Position Correction (Repulsion)
                        if d_temp.center[0] > other_d.center[0]:
                            final_cx += correction
                        else:
                            final_cx -= correction
                        
                        if d.type == "District":
                            new_w *= 0.999 # make the width a little bit smaller
                            new_h = d.target_area / new_w # calculate h, make sure the area won't change
                            
                    else:
                        # Vertical Collision: smaller h and larger w
                        correction = overlap_y * self.COLLISION_REPULSION_MAGNITUDE
                        
                        # Position Correction (Repulsion)
                        if d_temp.center[1] > other_d.center[1]:
                            final_cy += correction
                        else:
                            final_cy -= correction
                        
                        if d.type == "District":
                            new_h *= 0.999 # make the height a little bit smaller
                            new_w = d.target_area / new_h # calculate width, make sure the area won't change
                        
                    if d.type == "District":
                        # control the ratio of width/height
                        if new_w / new_h > self.MAX_ASPECT_RATIO:
                            new_w = math.sqrt(d.target_area * self.MAX_ASPECT_RATIO)
                            new_h = d.target_area / new_w
                        elif new_h / new_w > self.MAX_ASPECT_RATIO:
                            new_h = math.sqrt(d.target_area * self.MAX_ASPECT_RATIO)
                            new_w = d.target_area / new_h
                
            # --- 3. Boundary Clamping ---
            # Use the new, potentially changed dimensions for clamping
            half_w = new_w * scale / 2
            half_h = new_h * scale / 2
            final_cx = max(half_w + self.BORDER_BUFFER, min(self.MAP_WIDTH - half_w - self.BORDER_BUFFER, final_cx))
            final_cy = max(half_h + self.BORDER_BUFFER, min(self.MAP_HEIGHT - half_h - self.BORDER_BUFFER, final_cy))
            
            # Store all updates (Center and Shape)
            new_updates[d.id] = (final_cx, final_cy, new_w, new_h)
            total_movement += math.sqrt((d.center[0] - final_cx)**2 + (d.center[1] - final_cy)**2)

        # Apply updates
        for d in self.objects:
            final_cx, final_cy, new_w, new_h = new_updates[d.id]
            d.center = (final_cx, final_cy)
            d.w = new_w
            d.h = new_h
            
        return total_movement
    
    # --- Geometry and Utility Functions ---

    def get_rect_bounds(self, element: 'MapElement', scale: float = 1.0) -> Tuple[float, float, float, float]:
        """
        Calculates the (x_min, y_min, x_max, y_max) bounds 
        for an element at a given scale, crucial for collision detection.
        """
        cx, cy = element.center
        half_w = (element.w * scale) / 2
        half_h = (element.h * scale) / 2
        return (cx - half_w, cy - half_h, cx + half_w, cy + half_h)

    def overlap_area(self, rect1: Tuple[float, float, float, float], rect2: Tuple[float, float, float, float]) -> float:
        """Calculates the area of overlap between two rectangles."""
        x_min1, y_min1, x_max1, y_max1 = rect1
        x_min2, y_min2, x_max2, y_max2 = rect2
        
        overlap_x = max(0, min(x_max1, x_max2) - max(x_min1, x_min2))
        overlap_y = max(0, min(y_max1, y_max2) - max(y_min1, y_min2))
        return overlap_x * overlap_y

    def scale(self, rect_bounds):
        x_min, y_min, x_max, y_max = rect_bounds
        scale_x = (x_max - x_min) / self.MAP_WIDTH
        scale_y = (y_max - y_min) / self.MAP_HEIGHT
        for object in self.all_objects:
            cx, cy = object.center
            object.center = (cx * scale_x + x_min, cy * scale_y + y_min)
            if object.type == "District":
                object.w *= scale_x
                object.h *= scale_y

    def run(self):
        # Phase 1: center points generates the visualization.
        self.solve_initial_placement()
        # Phase 2: Grow objects, handle collision, and maintain directional constraints
        self.grow_and_cluster_objects()
        # Phase 3: Run recursively for children elements
        self.all_objects = self.objects.copy()
        for object in self.objects:
            if object.type == "District" and object.children:
                generator = MapGenerator(self.elements, object.children, self.relations)
                generator.run()
                generator.scale(self.get_rect_bounds(object))
                self.all_objects += generator.all_objects


    def visualize_initial_placement(self):
        visualizer = MapVisualizer(self, self.MAP_WIDTH, self.MAP_HEIGHT)
        svg_output = visualizer.generate_svg_centers() # Generate SVG visualization
        with open("output/initial_placement.svg", "w") as f:
            f.write(svg_output)

    def visualize_objects(self):
        visualizer = MapVisualizer(self, self.MAP_WIDTH, self.MAP_HEIGHT)
        svg_output = visualizer.generate_svg_map() # Generate SVG visualization of the map
        with open("output/map.svg", "w") as f:
            f.write(svg_output)


if __name__ == '__main__':

    with open("ccm/we_us.xml", "r") as xml_file:
        ccm = CognitiveMap(xml_file.read()) # Read the entire file into a string

    # Run the generator
    generator = MapGenerator(ccm.elements, ccm.children, ccm.relations)
    generator.run()
    generator.visualize_objects()
