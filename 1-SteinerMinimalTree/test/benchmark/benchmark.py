import re
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats
import os
import sys

def parse_data_from_file(filename):
    """Считывает данные из файла benchmark.py"""
    points = []
    standard_times = []
    modified_times = []
    
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Ищем все блоки с результатами
        # Паттерн для поиска: Файл XXXX_0000.json ... Время выполнения: XXX мкс
        pattern = r'Файл\s+(\d+)_0000\.json.*?Стандартный режим.*?Время выполнения:\s+(\d+)\s+мкс.*?Модифицированный режим.*?Время выполнения:\s+(\d+)\s+мкс'
        
        matches = re.findall(pattern, content, re.DOTALL)
        
        for match in matches:
            num_points = int(match[0])
            std_time = int(match[1])
            mod_time = int(match[2])
            
            points.append(num_points)
            standard_times.append(std_time)
            modified_times.append(mod_time)
        
        # Сортируем по количеству точек
        sorted_indices = np.argsort(points)
        points = np.array(points)[sorted_indices].tolist()
        standard_times = np.array(standard_times)[sorted_indices].tolist()
        modified_times = np.array(modified_times)[sorted_indices].tolist()
        
        print(f"Успешно загружено {len(points)} измерений")
        print(f"Диапазон точек: от {min(points)} до {max(points)}")
        
        return points, standard_times, modified_times
        
    except FileNotFoundError:
        print(f"Ошибка: Файл {filename} не найден!")
        return [], [], []
    except Exception as e:
        print(f"Ошибка при чтении файла: {e}")
        return [], [], []

def plot_comparison(points, standard_times, modified_times):
    """Строит графики сравнения"""
    if not points:
        print("Нет данных для построения графиков")
        return
    
    # Настройка стиля
    plt.style.use('seaborn-v0_8-darkgrid')
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # График 1: Линейный масштаб
    ax1.plot(points, standard_times, 'o-', label='Стандартный режим (без -m)', 
             linewidth=2, markersize=8, color='red', alpha=0.7)
    ax1.plot(points, modified_times, 's-', label='Модифицированный режим (с -m)', 
             linewidth=2, markersize=8, color='blue', alpha=0.7)
    
    ax1.set_xlabel('Количество точек', fontsize=12)
    ax1.set_ylabel('Время выполнения (мкс)', fontsize=12)
    ax1.set_title('Сравнение времени выполнения (линейный масштаб)', fontsize=14)
    ax1.legend(fontsize=10)
    ax1.grid(True, alpha=0.3)
    
    # График 2: Логарифмический масштаб для лучшей визуализации
    ax2.plot(points, standard_times, 'o-', label='Стандартный режим (без -m)', 
             linewidth=2, markersize=8, color='red', alpha=0.7)
    ax2.plot(points, modified_times, 's-', label='Модифицированный режим (с -m)', 
             linewidth=2, markersize=8, color='blue', alpha=0.7)
    
    ax2.set_xlabel('Количество точек', fontsize=12)
    ax2.set_ylabel('Время выполнения (мкс) - логарифмическая шкала', fontsize=12)
    ax2.set_title('Сравнение времени выполнения (логарифмический масштаб)', fontsize=14)
    ax2.set_yscale('log')
    ax2.legend(fontsize=10)
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('time_comparison.png', dpi=300, bbox_inches='tight')
    plt.show()

def plot_speedup(points, standard_times, modified_times):
    """Строит график ускорения"""
    if not points:
        return
    
    plt.figure(figsize=(10, 6))
    
    speedup = [std / mod if mod > 0 else 0 for std, mod in zip(standard_times, modified_times)]
    
    plt.plot(points, speedup, 'g^-', linewidth=2, markersize=8, alpha=0.7)
    plt.axhline(y=1, color='red', linestyle='--', label='Базовый уровень (без ускорения)', alpha=0.5)
    
    plt.xlabel('Количество точек', fontsize=12)
    plt.ylabel('Ускорение (раз)', fontsize=12)
    plt.title('Ускорение модифицированного режима относительно стандартного', fontsize=14)
    plt.grid(True, alpha=0.3)
    plt.legend()
    
    # Добавление значений на график
    for i, (x, y) in enumerate(zip(points, speedup)):
        plt.annotate(f'{y:.1f}x', (x, y), xytext=(5, 5), 
                    textcoords='offset points', fontsize=8, alpha=0.7)
    
    plt.tight_layout()
    plt.savefig('speedup.png', dpi=300, bbox_inches='tight')
    plt.show()

def analyze_complexity(points, standard_times, modified_times):
    """Анализирует временную сложность алгоритмов"""
    if len(points) < 2:
        print("Недостаточно данных для анализа сложности")
        return
    
    # Преобразуем в numpy массивы
    x = np.array(points)
    y_std = np.array(standard_times)
    y_mod = np.array(modified_times)
    
    # Аппроксимируем степенной зависимостью (O(n^k))
    log_x = np.log(x)
    log_y_std = np.log(y_std)
    log_y_mod = np.log(y_mod)
    
    # Линейная регрессия
    slope_std, intercept_std, r_value_std, p_value_std, std_err_std = stats.linregress(log_x, log_y_std)
    slope_mod, intercept_mod, r_value_mod, p_value_mod, std_err_mod = stats.linregress(log_x, log_y_mod)
    
    print("\n=== Анализ временной сложности ===")
    print(f"Стандартный режим: O(n^{slope_std:.2f}) (R² = {r_value_std**2:.3f})")
    print(f"Модифицированный режим: O(n^{slope_mod:.2f}) (R² = {r_value_mod**2:.3f})")
    
    # Дополнительная статистика
    speedups = [s/m for s,m in zip(standard_times, modified_times)]
    print("\n=== Статистика ===")
    print(f"Всего измерений: {len(points)}")
    print(f"Диапазон точек: от {min(points)} до {max(points)}")
    print(f"Среднее ускорение: {np.mean(speedups):.2f}x")
    print(f"Медианное ускорение: {np.median(speedups):.2f}x")
    print(f"Максимальное ускорение: {max(speedups):.2f}x")
    print(f"Минимальное ускорение: {min(speedups):.2f}x")
    
    # Прогноз для больших значений
    if len(points) > 5:
        print("\n=== Прогноз для 50 и 100 точек ===")
        pred_50_std = np.exp(intercept_std + slope_std * np.log(50))
        pred_50_mod = np.exp(intercept_mod + slope_mod * np.log(50))
        pred_100_std = np.exp(intercept_std + slope_std * np.log(100))
        pred_100_mod = np.exp(intercept_mod + slope_mod * np.log(100))
        
        print(f"Для 50 точек:")
        print(f"  Стандартный режим: ~{pred_50_std:.0f} мкс")
        print(f"  Модифицированный режим: ~{pred_50_mod:.0f} мкс")
        print(f"  Ожидаемое ускорение: ~{pred_50_std/pred_50_mod:.1f}x")
        print(f"\nДля 100 точек:")
        print(f"  Стандартный режим: ~{pred_100_std:.0f} мкс")
        print(f"  Модифицированный режим: ~{pred_100_mod:.0f} мкс")
        print(f"  Ожидаемое ускорение: ~{pred_100_std/pred_100_mod:.1f}x")

def plot_combined(points, standard_times, modified_times):
    """Строит комбинированный график с двумя осями Y"""
    if not points:
        return
    
    fig, ax1 = plt.subplots(figsize=(12, 7))
    
    # Левая ось - время выполнения
    color_std = 'red'
    color_mod = 'blue'
    
    ax1.plot(points, standard_times, 'o-', color=color_std, linewidth=2, 
             markersize=8, label='Стандартный режим (без -m)', alpha=0.7)
    ax1.plot(points, modified_times, 's-', color=color_mod, linewidth=2, 
             markersize=8, label='Модифицированный режим (с -m)', alpha=0.7)
    ax1.set_xlabel('Количество точек', fontsize=12)
    ax1.set_ylabel('Время выполнения (мкс)', fontsize=12, color='black')
    ax1.tick_params(axis='y', labelcolor='black')
    ax1.grid(True, alpha=0.3)
    
    # Правая ось - ускорение
    ax2 = ax1.twinx()
    speedup = [std / mod for std, mod in zip(standard_times, modified_times)]
    color_speedup = 'green'
    ax2.plot(points, speedup, 'd--', color=color_speedup, linewidth=2, 
             markersize=6, label='Ускорение', alpha=0.7)
    ax2.set_ylabel('Ускорение (раз)', fontsize=12, color=color_speedup)
    ax2.tick_params(axis='y', labelcolor=color_speedup)
    
    # Добавляем горизонтальную линию y=1
    ax2.axhline(y=1, color='gray', linestyle=':', alpha=0.5)
    
    # Легенда
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=10)
    
    plt.title('Сравнение производительности стандартного и модифицированного режимов', fontsize=14)
    plt.tight_layout()
    plt.savefig('combined_comparison.png', dpi=300, bbox_inches='tight')
    plt.show()

def plot_efficiency_ratio(points, standard_times, modified_times):
    """Строит график эффективности (отношение времени к количеству точек)"""
    if not points:
        return
    
    plt.figure(figsize=(10, 6))
    
    std_per_point = [t / p for t, p in zip(standard_times, points)]
    mod_per_point = [t / p for t, p in zip(modified_times, points)]
    
    plt.plot(points, std_per_point, 'o-', label='Стандартный режим (без -m)', 
             linewidth=2, markersize=8, color='red', alpha=0.7)
    plt.plot(points, mod_per_point, 's-', label='Модифицированный режим (с -m)', 
             linewidth=2, markersize=8, color='blue', alpha=0.7)
    
    plt.xlabel('Количество точек', fontsize=12)
    plt.ylabel('Время на точку (мкс/точку)', fontsize=12)
    plt.title('Эффективность алгоритмов (время на одну точку)', fontsize=14)
    plt.legend(fontsize=10)
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('efficiency_ratio.png', dpi=300, bbox_inches='tight')
    plt.show()

def main():
    if len(sys.argv) < 2:
        print("Использование: python graph_visualizer.py <input_json_file>")
        sys.exit(1)
    
    benchmark_file = sys.argv[1]
    
    # Проверяем существование файла
    if not os.path.exists(benchmark_file):
        print(f"Файл {benchmark_file} не найден!")
        print("Пожалуйста, убедитесь, что файл существует и содержит данные измерений.")
        return
    
    # Считываем данные
    points, standard_times, modified_times = parse_data_from_file(benchmark_file)
    
    if not points:
        print("Не удалось извлечь данные из файла.")
        print("Убедитесь, что файл содержит данные в формате:")
        print("Файл XXXX_0000.json")
        print("Стандартный режим (без -m): Время выполнения: XXX мкс")
        print("Модифицированный режим (с -m): Время выполнения: XXX мкс")
        return
    
    # Создаем директорию для графиков (если нужно)
    plots_dir = './plots'
    if not os.path.exists(plots_dir):
        os.makedirs(plots_dir)
        print(f"Создана директория {plots_dir}")
    
    # Сохраняем текущую директорию
    original_dir = os.getcwd()
    os.chdir(plots_dir)
    
    # Строим все графики
    print("\nПостроение графиков...")
    plot_comparison(points, standard_times, modified_times)
    plot_speedup(points, standard_times, modified_times)
    plot_combined(points, standard_times, modified_times)
    plot_efficiency_ratio(points, standard_times, modified_times)
    
    # Анализ сложности
    analyze_complexity(points, standard_times, modified_times)
    
    # Возвращаемся в исходную директорию
    os.chdir(original_dir)
    
    print(f"\nГрафики сохранены в директорию {plots_dir}:")
    print("- time_comparison.png")
    print("- speedup.png")
    print("- combined_comparison.png")
    print("- efficiency_ratio.png")

if __name__ == "__main__":
    main()