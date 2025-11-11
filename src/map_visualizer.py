class MapVisualizer:

    def __init__(self, map_generator, MAP_WIDTH, MAP_HEIGHT):
        self.mg = map_generator
        self.MAP_WIDTH = MAP_WIDTH
        self.MAP_HEIGHT = MAP_HEIGHT

    def generate_svg_centers(self) -> str:
        """Generates an SVG visualization showing only the calculated centers."""
        
        svg_content = [
            f'<svg width="{self.MAP_WIDTH}" height="{self.MAP_HEIGHT}" viewBox="0 0 {self.MAP_WIDTH} {self.MAP_HEIGHT}" xmlns="http://www.w3.org/2000/svg" style="border: 1px solid #ccc; font-family: Inter, sans-serif;">',
            f'<!-- Background -->',
            f'<rect width="{self.MAP_WIDTH}" height="{self.MAP_HEIGHT}" fill="#f5f5f5" />',
            f'<text x="20" y="30" font-size="20" font-weight="bold" fill="#333">District Centers (Directional Placement)</text>',
        ]
        
        # 1. References (Fixed Anchors)
        for r in [e for e in self.mg.all_objects if e.type == 'Reference']:
            svg_cy = self.MAP_HEIGHT - r.center[1] # SVG uses top-down Y, map uses bottom-up Y
            svg_content.append(
                f'<circle cx="{r.center[0]}" cy="{svg_cy}" r="10" fill="#90a4ae" opacity="0.5" />'
            )
            svg_content.append(
                f'<text x="{r.center[0]}" y="{svg_cy + 25}" font-size="12" text-anchor="middle" fill="#607d8b">{r.name}</text>'
            )

        # 2. Objects (Nodes and Districts)
        for d in self.mg.all_objects:
            if d.type != "Node" and d.type != "District": continue

            svg_cy = self.MAP_HEIGHT - d.center[1]
            
            # Center point
            svg_content.append(
                f'<circle cx="{d.center[0]}" cy="{svg_cy}" r="8" fill="#3f51b5" stroke="#ffffff" stroke-width="2" />'
            )
            # Label
            svg_content.append(
                f'<text x="{d.center[0]}" y="{svg_cy - 15}" font-size="14" font-weight="bold" text-anchor="middle" fill="#3f51b5">{d.name}</text>'
            )

        # 3. Relations (Lines between related centers)
        svg_content.append('\n<!-- Directional Constraints (Visualized as lines) -->')
        for rel in self.mg.relations:
            subj = self.mg.elements.get(rel.subject_id)
            obj = self.mg.elements.get(rel.object_id)
            
            if subj and obj:
                y1_svg = self.MAP_HEIGHT - subj.center[1]
                y2_svg = self.MAP_HEIGHT - obj.center[1]
                
                # Draw a line between the two centers
                svg_content.append(
                    f'<line x1="{subj.center[0]}" y1="{y1_svg}" x2="{obj.center[0]}" y2="{y2_svg}" '
                    f'stroke="#ff9800" stroke-width="1.5" stroke-opacity="0.6" stroke-dasharray="4 2" />'
                )
                
                # Add text label for the relation type near the line center
                mid_x = (subj.center[0] + obj.center[0]) / 2
                mid_y_svg = (y1_svg + y2_svg) / 2
                
                svg_content.append(
                    f'<text x="{mid_x}" y="{mid_y_svg}" font-size="10" text-anchor="middle" fill="#e65100" '
                    f'style="filter: drop-shadow(0 0 1px white);">{rel.type.upper()}</text>'
                )


        svg_content.append('</svg>')
        return "\n".join(svg_content)


    # --- SVG Visualization (draw rectangles) ---
    def generate_svg_map(self) -> str:
        """Generates an SVG visualization showing the calculated centers and scaled objects."""
        
        svg_content = [
            f'<svg width="{self.MAP_WIDTH}" height="{self.MAP_HEIGHT}" viewBox="0 0 {self.MAP_WIDTH} {self.MAP_HEIGHT}" xmlns="http://www.w3.org/2000/svg" style="border: 1px solid #ccc; font-family: Inter, sans-serif;">',
            f'<!-- Background -->',
            f'<rect width="{self.MAP_WIDTH}" height="{self.MAP_HEIGHT}" fill="#f0f4f8" />',
            f'<text x="20" y="30" font-size="20" font-weight="bold" fill="#333">Random Map of Objects</text>'
        ]
        
        # Store all label bounding boxes for collision detection
        label_bboxes = []
        
        def get_text_bbox(text, x, y, font_size=12, font_weight="normal"):
            """Estimate text bounding box"""
            # Simple estimation: assume average character width is font_size * 0.6
            text_width = len(text) * font_size * 0.6
            text_height = font_size
            padding = font_size * 0.5  # Add some padding
            
            return {
                'x': x - text_width / 2 - padding,  # Assuming text-anchor="middle"
                'y': y - text_height / 2 - padding,
                'width': text_width + padding * 2,
                'height': text_height + padding * 2,
                'text': text,
                'original_x': x,
                'original_y': y
            }
        
        def bbox_overlap(bbox1, bbox2):
            """Check if two bounding boxes overlap"""
            return not (bbox1['x'] + bbox1['width'] < bbox2['x'] or
                    bbox2['x'] + bbox2['width'] < bbox1['x'] or
                    bbox1['y'] + bbox1['height'] < bbox2['y'] or
                    bbox2['y'] + bbox2['height'] < bbox1['y'])
        
        def find_best_label_position(original_bbox, max_attempts=20):
            """Find the best position for a label to avoid overlaps"""
            bbox = original_bbox.copy()
            
            # Position offsets to try (relative to original position)
            position_offsets = [
                (0, 0),  # Original position
                (0, -bbox['height'] * 1.5),  # Above
                (0, bbox['height'] * 1.5),   # Below
                (-bbox['width'] * 1.2, 0),   # Left
                (bbox['width'] * 1.2, 0),    # Right
                (-bbox['width'] * 0.8, -bbox['height'] * 1.2),  # Top-left
                (bbox['width'] * 0.8, -bbox['height'] * 1.2),   # Top-right
                (-bbox['width'] * 0.8, bbox['height'] * 1.2),   # Bottom-left
                (bbox['width'] * 0.8, bbox['height'] * 1.2),    # Bottom-right
            ]
            
            # Spiral search pattern (used when main directions are occupied)
            spiral_steps = [(dx, dy) for dx in range(-3, 4) for dy in range(-3, 4) 
                        if (dx, dy) != (0, 0)]
            spiral_steps.sort(key=lambda p: abs(p[0]) + abs(p[1]))
            
            for offset_x, offset_y in position_offsets:
                test_bbox = bbox.copy()
                test_bbox['x'] += offset_x
                test_bbox['y'] += offset_y
                
                # Check boundaries
                if (test_bbox['x'] < 0 or test_bbox['x'] + test_bbox['width'] > self.MAP_WIDTH or
                    test_bbox['y'] < 0 or test_bbox['y'] + test_bbox['height'] > self.MAP_HEIGHT):
                    continue
                
                # Check if overlaps with existing labels
                overlap = any(bbox_overlap(test_bbox, existing_bbox) for existing_bbox in label_bboxes)
                if not overlap:
                    return test_bbox, (offset_x, offset_y)
            
            # If main positions don't work, try spiral search
            for step_x, step_y in spiral_steps[:max_attempts]:
                offset_x = step_x * bbox['width'] * 0.8
                offset_y = step_y * bbox['height'] * 0.8
                
                test_bbox = bbox.copy()
                test_bbox['x'] += offset_x
                test_bbox['y'] += offset_y
                
                # Check boundaries
                if (test_bbox['x'] < 0 or test_bbox['x'] + test_bbox['width'] > self.MAP_WIDTH or
                    test_bbox['y'] < 0 or test_bbox['y'] + test_bbox['height'] > self.MAP_HEIGHT):
                    continue
                
                # Check if overlaps with existing labels
                overlap = any(bbox_overlap(test_bbox, existing_bbox) for existing_bbox in label_bboxes)
                if not overlap:
                    return test_bbox, (offset_x, offset_y)
            
            # If all attempts fail, return original position (allow overlap)
            return original_bbox, (0, 0)

        # 1. Relations (Lines between centers)
        for rel in self.mg.relations:
            subj = self.mg.elements.get(rel.subject_id)
            obj = self.mg.elements.get(rel.object_id)
            if subj and obj:
                y1_svg = self.MAP_HEIGHT - subj.center[1]
                y2_svg = self.MAP_HEIGHT - obj.center[1]
                svg_content.append(
                    f'<line x1="{subj.center[0]}" y1="{y1_svg}" x2="{obj.center[0]}" y2="{y2_svg}" '
                    f'stroke="#ff9800" stroke-width="1.5" stroke-opacity="0.4" stroke-dasharray="4 2" />'
                )

        # 2. Districts (Rectangles)
        colors = ["#f7fcf0", "#e0f3db", "#ccebc5", "#a8ddb5", "#7bccc4", "#4eb3d3", "#2b8cbe", "#0868ac", "#084081"]
        
        for i, d in enumerate(self.mg.all_objects):
            if d.type != "District": continue
            color = colors[i % len(colors)]
            x_min, y_min, x_max, y_max = self.mg.get_rect_bounds(d)
            width = x_max - x_min
            height = y_max - y_min
            
            svg_y = self.MAP_HEIGHT - y_max 
            
            svg_content.append(
                f'<rect x="{x_min}" y="{svg_y}" width="{width}" height="{height}" rx="5" ry="5" '
                f'fill="{color}" opacity="0.6" stroke="#333" stroke-width="2" />'
            )
            
            # District Label with collision avoidance
            label_y = self.MAP_HEIGHT - d.center[1] + 5
            original_bbox = get_text_bbox(d.name, d.center[0], label_y, font_size=14, font_weight="bold")
            best_bbox, offset = find_best_label_position(original_bbox)
            
            # Add pointer line if label was moved
            if offset != (0, 0):
                line_end_x = best_bbox['x'] + best_bbox['width'] / 2
                line_end_y = best_bbox['y'] + best_bbox['height'] / 2
                svg_content.append(
                    f'<line x1="{d.center[0]}" y1="{label_y}" x2="{line_end_x}" y2="{line_end_y}" '
                    f'stroke="#666" stroke-width="1" stroke-dasharray="2 2" opacity="0.6" />'
                )
            
            label_bboxes.append(best_bbox)
            svg_content.append(
                f'<text x="{best_bbox["x"] + best_bbox["width"] / 2}" y="{best_bbox["y"] + best_bbox["height"] / 2 + 4}" '
                f'font-size="14" text-anchor="middle" fill="#000" font-weight="bold">{d.name}</text>'
            )

        # 3. Nodes (Points)
        for n in [e for e in self.mg.all_objects if e.type == 'Node']:
            svg_cy = self.MAP_HEIGHT - n.center[1]
            # Center point
            svg_content.append(
                f'<circle cx="{n.center[0]}" cy="{svg_cy}" r="8" fill="#3f51b5" stroke="#ffffff" stroke-width="2" />'
            )
            
            # Node Label with collision avoidance
            label_y = svg_cy - 15
            original_bbox = get_text_bbox(n.name, n.center[0], label_y, font_size=14, font_weight="bold")
            best_bbox, offset = find_best_label_position(original_bbox)
            
            # Add pointer line if label was moved
            if offset != (0, 0):
                line_end_x = best_bbox['x'] + best_bbox['width'] / 2
                line_end_y = best_bbox['y'] + best_bbox['height'] / 2
                svg_content.append(
                    f'<line x1="{n.center[0]}" y1="{svg_cy - 8}" x2="{line_end_x}" y2="{line_end_y}" '
                    f'stroke="#3f51b5" stroke-width="1" stroke-dasharray="2 2" opacity="0.6" />'
                )
            
            label_bboxes.append(best_bbox)
            svg_content.append(
                f'<text x="{best_bbox["x"] + best_bbox["width"] / 2}" y="{best_bbox["y"] + best_bbox["height"] / 2 + 4}" '
                f'font-size="14" font-weight="bold" text-anchor="middle" fill="#3f51b5">{n.name}</text>'
            )

        # 4. References (Fixed Anchors)
        for r in [e for e in self.mg.all_objects if e.type == 'Reference']:
            svg_cy = self.MAP_HEIGHT - r.center[1]
            svg_content.append(
                f'<circle cx="{r.center[0]}" cy="{svg_cy}" r="10" fill="#90a4ae" opacity="0.5" />'
            )
            
            # Reference Label with collision avoidance
            label_y = svg_cy + 25
            original_bbox = get_text_bbox(r.name, r.center[0], label_y, font_size=12, font_weight="normal")
            best_bbox, offset = find_best_label_position(original_bbox)
            
            # Add pointer line if label was moved
            if offset != (0, 0):
                line_end_x = best_bbox['x'] + best_bbox['width'] / 2
                line_end_y = best_bbox['y'] + best_bbox['height'] / 2
                svg_content.append(
                    f'<line x1="{r.center[0]}" y1="{svg_cy + 10}" x2="{line_end_x}" y2="{line_end_y}" '
                    f'stroke="#90a4ae" stroke-width="1" stroke-dasharray="2 2" opacity="0.6" />'
                )
            
            label_bboxes.append(best_bbox)
            svg_content.append(
                f'<text x="{best_bbox["x"] + best_bbox["width"] / 2}" y="{best_bbox["y"] + best_bbox["height"] / 2 + 3}" '
                f'font-size="12" text-anchor="middle" fill="#607d8b">{r.name}</text>'
            )

        svg_content.append('</svg>')
        return "\n".join(svg_content)
    