import json
import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, List, Tuple
import sys
import os

class GraphVisualizer:
    def __init__(self, json_file: str):
        """Загрузка графа из JSON файла"""
        with open(json_file, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
        
        self.nodes = {}
        self.edges = []
        
        for node in self.data.get('node', []):
            self.nodes[node['id']] = {
                'id': node['id'],
                'x': node['x'],
                'y': node['y'],
                'type': node.get('type', 'unknown')
            }
        
        for edge in self.data.get('edge', []):
            vertices = edge['vertices']
            if len(vertices) == 2:
                self.edges.append({
                    'id': edge['id'],
                    'v1': vertices[0],
                    'v2': vertices[1]
                })
        
        print(f"Загружено {len(self.nodes)} вершин и {len(self.edges)} рёбер")
    
    def draw_grid(self, figsize=(10, 8), show_grid=True, show_labels=True):
        
        fig, ax = plt.subplots(figsize=figsize)
        
        if show_grid:
            ax.grid(True, linestyle='--', alpha=0.7, color='gray', linewidth=0.5)
        
        all_x = [node['x'] for node in self.nodes.values()]
        all_y = [node['y'] for node in self.nodes.values()]
        
        if all_x and all_y:
            x_min, x_max = min(all_x), max(all_x)
            y_min, y_max = min(all_y), max(all_y)
            x_padding = max(1, (x_max - x_min) * 0.1)
            y_padding = max(1, (y_max - y_min) * 0.1)
            
            ax.set_xlim(x_min - x_padding, x_max + x_padding)
            ax.set_ylim(y_min - y_padding, y_max + y_padding)
        
        for edge in self.edges:
            v1 = self.nodes.get(edge['v1'])
            v2 = self.nodes.get(edge['v2'])
            
            if v1 and v2:
                x_coords = [v1['x'], v2['x']]
                y_coords = [v1['y'], v2['y']]
                
                ax.plot(x_coords, y_coords, 'b-', linewidth=2, alpha=0.7, zorder=1)
                
                if show_labels:
                    mid_x = (v1['x'] + v2['x']) / 2
                    mid_y = (v1['y'] + v2['y']) / 2
                    ax.text(mid_x, mid_y, str(edge['id']), 
                           fontsize=5, ha='center', va='center',
                           bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7),
                           zorder=3)
        
        for node_id, node in self.nodes.items():
            if node['type'] == 't':
                color = 'red'
                marker = 'o'
                size = 30
                edge_color = 'darkred'
            elif node['type'] == 's':
                color = 'green'
                marker = 'o' #'s'
                size = 30
                edge_color = 'darkgreen'
            else:
                color = 'blue'
                marker = 'o'
                size = 20
                edge_color = 'navy'
            
            ax.scatter(node['x'], node['y'], s=size, c=color, 
                      marker=marker, edgecolors=edge_color, 
                      linewidth=2, zorder=2)
            
            if show_labels:
                ax.text(node['x'], node['y'], str(node_id), 
                       fontsize=7, ha='center', va='center',
                       fontweight='bold', color='white', zorder=3)
        
        ax.set_xlabel('X координата', fontsize=12)
        ax.set_ylabel('Y координата', fontsize=12)
        ax.set_title(f'Граф с {len(self.nodes)} вершинами и {len(self.edges)} рёбрами', 
                    fontsize=14, fontweight='bold')
        
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor='red', edgecolor='darkred', label='Терминальная вершина (t)'),
            Patch(facecolor='green', edgecolor='darkgreen', label='Штейнеровская вершина (s)'),
            # Patch(facecolor='blue', edgecolor='navy', label='Другая вершина')
        ]
        ax.legend(handles=legend_elements, loc='upper left', framealpha=0.9)
        
        ax.set_aspect('equal')
        
        plt.tight_layout()
        return fig, ax
    
    def print_graph_info(self):
        print("\n" + "="*60)
        print("ИНФОРМАЦИЯ О ГРАФЕ")
        print("="*60)
        
        print(f"\nВершины ({len(self.nodes)} шт.):")
        print("-" * 60)
        for node_id, node in self.nodes.items():
            print(f"  ID: {node_id:3d} | Тип: {node['type']} | Координаты: ({node['x']:6.2f}, {node['y']:6.2f})")
        
        print(f"\nРёбра ({len(self.edges)} шт.):")
        print("-" * 60)
        for edge in self.edges:
            v1 = self.nodes[edge['v1']]
            v2 = self.nodes[edge['v2']]
            length = np.sqrt((v1['x'] - v2['x'])**2 + (v1['y'] - v2['y'])**2)
            print(f"  ID: {edge['id']:3d} | {edge['v1']:3d} — {edge['v2']:3d} | Длина: {length:6.2f}")
        
        print("="*60 + "\n")
    
    def save_to_image(self, output_file: str, dpi=150):
        fig, _ = self.draw_grid(show_grid=True, show_labels=False)
        fig.savefig(output_file, dpi=dpi, bbox_inches='tight')
        plt.close(fig)
        print(f"Граф сохранён в {output_file}")
    
    def show_interactive(self):
        fig, ax = self.draw_grid()
        plt.show()
    
    def export_coordinates(self, output_file: str):
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("ID\tX\tY\tType\n")
            for node_id, node in self.nodes.items():
                f.write(f"{node_id}\t{node['x']}\t{node['y']}\t{node['type']}\n")
        print(f"Координаты экспортированы в {output_file}")

def main():
    if len(sys.argv) < 3:
        print("Использование: python graph_visualizer.py <input_json_file> <output_dir_path>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_dir = sys.argv[2] + "/"

    os.makedirs('./test/img', exist_ok=True)
    base_name = os.path.basename(input_file)
    filename_without_ext = os.path.splitext(base_name)[0]
    os.makedirs(output_dir, exist_ok=True)
    output_file = output_dir + filename_without_ext
    
    if not os.path.exists(input_file):
        print(f"Ошибка: файл {input_file} не найден!")
        sys.exit(1)
    
    try:
        visualizer = GraphVisualizer(input_file)
        visualizer.print_graph_info()
        
        visualizer.save_to_image(output_file)
        coords_file = os.path.splitext(output_file)[0] + "_coords.txt"
        visualizer.export_coordinates(coords_file)
    
    except json.JSONDecodeError as e:
        print(f"Ошибка парсинга JSON: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()