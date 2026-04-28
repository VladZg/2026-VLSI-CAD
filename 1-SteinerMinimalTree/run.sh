#!/bin/bash

GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

SMT_BENCHMARKS="./SMT-benchmarks"
TEST_GRAPHS="./test/graphs"
TEST_IMG="./test/img"
STEINER_PROG="./Steiner"
VISUALIZER_PROG="python3 visualizer.py"
BENCHMARK_LOG="./test/benchmark/benchmark.txt"

# Создаём папки для результатов, если их нет
mkdir -p "$TEST_GRAPHS"
mkdir -p "$(dirname "$BENCHMARK_LOG")"

# Очищаем файл лога перед записью
> "$BENCHMARK_LOG"

# Функция для записи в лог и вывода в терминал
log() {
    echo -e "$1"
}

# Функция для записи только в лог (без вывода в терминал)
log_only() {
    echo -e "$1" >> "$BENCHMARK_LOG"
}

log "${BLUE}========================================${NC}"
log "${BLUE}Запуск обработки SMT benchmarks${NC}"
log "${BLUE}========================================${NC}\n"

# Счётчики для каждого режима
total=0
success_normal=0
failed_normal=0
success_modified=0
failed_modified=0

# Массивы для хранения имён файлов с ошибками
failed_files_normal=()
failed_files_modified=()

# Обрабатываем каждый JSON файл в папке SMT-benchmarks
for json_file in "$SMT_BENCHMARKS"/*.json; do
    # Проверяем, есть ли файлы
    if [ ! -f "$json_file" ]; then
        log "${RED}Файлы не найдены в $SMT_BENCHMARKS${NC}"
        exit 1
    fi
    
    total=$((total + 1))
    
    # Получаем имя файла без пути
    filename=$(basename "$json_file")
    filename_without_ext="${filename%.json}"
    
    log "\n${YELLOW}========================================${NC}"
    log "${YELLOW}[$total] Обработка: $filename${NC}"
    log "${YELLOW}========================================${NC}"
    
    log_only "Файл $filename\n"

    # === ЗАПУСК БЕЗ ФЛАГА -m (стандартный режим) ===
    log "\n${BLUE}--- Режим: СТАНДАРТНЫЙ (без -m) ---${NC}"
    log_only "Стандартный режим (без -m):"
    
    output_file_normal="./${filename_without_ext}_out.json"
    
    log "  ${BLUE}→${NC} Запуск Steiner (стандартный режим)..."
    
    mkdir -p "${TEST_GRAPHS}/${filename_without_ext}"

    # Запускаем программу и сохраняем вывод в лог
    if "$STEINER_PROG" -t "$json_file" >> "$BENCHMARK_LOG" 2>&1; then
        log "  ${GREEN}✓${NC} Steiner завершил работу"
        
        # Проверяем, создался ли выходной файл
        if [ -f "$output_file_normal" ]; then

            # Перемещаем в папку test/graphs/${filename_without_ext} с суффиксом _out
            mv "$output_file_normal" "$TEST_GRAPHS/${filename_without_ext}/${filename_without_ext}_out.json"
            log "  ${GREEN}✓${NC} Файл перемещён в $TEST_GRAPHS/${filename_without_ext}/${filename_without_ext}_out.json"

            mkdir -p "$TEST_IMG/${filename_without_ext}"

            # Запускаем визуализатор для результата
            log "  ${BLUE}→${NC} Запуск визуализатора для немодифицированного результата..."
            
            if $VISUALIZER_PROG "$TEST_GRAPHS/${filename_without_ext}/${filename_without_ext}_out.json" "$TEST_IMG/${filename_without_ext}" > "/dev/null" 2>&1; then
                log "  ${GREEN}✓${NC} Визуализатор завершил работу"
                success_normal=$((success_normal + 1))
            else
                log "  ${RED}✗${NC} Ошибка при запуске визуализатора"
                failed_normal=$((failed_modified + 1))
                failed_files_modified+=("$filename (стандартный)")
            fi
        else
            log "  ${RED}✗${NC} Выходной файл не создан: $output_file_normal"
            failed_normal=$((failed_normal + 1))
            failed_files_normal+=("$filename (стандартный)")
        fi
    else
        log "  ${RED}✗${NC} Ошибка при запуске Steiner"
        failed_normal=$((failed_normal + 1))
        failed_files_normal+=("$filename (стандартный)")
    fi
    
    # === ЗАПУСК С ФЛАГОМ -m (модифицированный режим) ===
    log "\n${BLUE}--- Режим: МОДИФИЦИРОВАННЫЙ (с -m) ---${NC}"
    log_only "Модифицированный режим (с -m):"
    
    output_file_modified="./${filename_without_ext}_out.json"
    
    log "  ${BLUE}→${NC} Запуск Steiner (модифицированный режим)..."
    
    # Удаляем выходной файл, если он остался от предыдущего запуска
    rm -f "$output_file_modified"
    
    # Запускаем программу с флагом -m и сохраняем вывод в лог
    if "$STEINER_PROG" -m -t "$json_file" >> "$BENCHMARK_LOG" 2>&1; then
        log "  ${GREEN}✓${NC} Steiner завершил работу"
        
        # Проверяем, создался ли выходной файл
        if [ -f "$output_file_modified" ]; then
            # Перемещаем в папку test/graphs /<filename>с суффиксом _modified_out
            mv "$output_file_modified" "$TEST_GRAPHS/${filename_without_ext}/${filename_without_ext}_modified_out.json"
            log "  ${GREEN}✓${NC} Файл перемещён в $TEST_GRAPHS/${filename_without_ext}_modified_out.json"
            
            # Запускаем визуализатор для модифицированного результата
            log "  ${BLUE}→${NC} Запуск визуализатора для модифицированного результата..."

            if $VISUALIZER_PROG "$TEST_GRAPHS/${filename_without_ext}/${filename_without_ext}_modified_out.json" "$TEST_IMG/${filename_without_ext}" > "/dev/null" 2>&1; then
                log "  ${GREEN}✓${NC} Визуализатор завершил работу"
                success_modified=$((success_modified + 1))
            else
                log "  ${RED}✗${NC} Ошибка при запуске визуализатора"
                failed_modified=$((failed_modified + 1))
                failed_files_modified+=("$filename (модифицированный)")
            fi
        else
            log "  ${RED}✗${NC} Выходной файл не создан: $output_file_modified"
            failed_modified=$((failed_modified + 1))
            failed_files_modified+=("$filename (модифицированный)")
        fi
    else
        log "  ${RED}✗${NC} Ошибка при запуске Steiner"
        failed_modified=$((failed_modified + 1))
        failed_files_modified+=("$filename (модифицированный)")
    fi
    
    # Запускаем программу с флагом -d и сохраняем вывод в лог (конструирование неоптимизированных деревьев без узлов Штейнера)
    if "$STEINER_PROG" -i 0 "$json_file" >> "$BENCHMARK_LOG" 2>&1; then
        log "  ${GREEN}✓${NC} Steiner завершил работу"
        
        # Проверяем, создался ли выходной файл
        if [ -f "$output_file_modified" ]; then
            # Перемещаем в папку test/graphs /<filename> с суффиксом _modified_out
            mv "$output_file_modified" "$TEST_GRAPHS/${filename_without_ext}/${filename_without_ext}_default_out.json"
            # log "  ${GREEN}✓${NC} Файл перемещён в $TEST_GRAPHS/${filename_without_ext}_default_out.json"
            
            # Запускаем визуализатор для модифицированного результата
            # log "  ${BLUE}→${NC} Запуск визуализатора для модифицированного результата..."

            if $VISUALIZER_PROG "$TEST_GRAPHS/${filename_without_ext}/${filename_without_ext}_default_out.json" "$TEST_IMG/${filename_without_ext}" > "/dev/null" 2>&1; then
                log "  ${GREEN}✓${NC} Визуализатор завершил работу"
                # success_default=$((success_default + 1))
            else
                log "  ${RED}✗${NC} Ошибка при запуске визуализатора"
                # failed_default=$((failed_default + 1))
                # failed_files_default+=("$filename (модифицированный)")
            fi
        else
            log "  ${RED}✗${NC} Выходной файл не создан: $output_file_default"
            # failed_default=$((failed_default + 1))
            # failed_files_default+=("$filename (модифицированный)")
        fi
    else
        log "  ${RED}✗${NC} Ошибка при запуске Steiner"
        # failed_default=$((failed_default + 1))
        # failed_files_default+=("$filename (модифицированный)")
    fi


    # Разделитель в логе
    log_only ""
    log_only "----------------------------------------"
    log_only ""
    
    log ""
done

# Итоговая статистика
log "\n${BLUE}========================================${NC}"
log "${BLUE}ИТОГОВЫЕ РЕЗУЛЬТАТЫ${NC}"
log "${BLUE}========================================${NC}"

log "\n${YELLOW}СТАНДАРТНЫЙ РЕЖИМ (без -m):${NC}"
log "  ${GREEN}Успешно: $success_normal${NC}"
log "  ${RED}Ошибок: $failed_normal${NC}"

log "\n${YELLOW}МОДИФИЦИРОВАННЫЙ РЕЖИМ (с -m):${NC}"
log "  ${GREEN}Успешно: $success_modified${NC}"
log "  ${RED}Ошибок: $failed_modified${NC}"

log "\n${YELLOW}ОБЩАЯ СТАТИСТИКА:${NC}"
log "  ${BLUE}Всего файлов: $total${NC}"
log "  ${GREEN}Всего успешных запусков: $((success_normal + success_modified))${NC}"
log "  ${RED}Всего ошибок: $((failed_normal + failed_modified))${NC}"

# Выводим список файлов с ошибками, если они есть
if [ ${#failed_files_normal[@]} -gt 0 ]; then
    log "\n${RED}Файлы с ошибками (стандартный режим):${NC}"
    for file in "${failed_files_normal[@]}"; do
        log "  - $file"
    done
fi

if [ ${#failed_files_modified[@]} -gt 0 ]; then
    log "\n${RED}Файлы с ошибками (модифицированный режим):${NC}"
    for file in "${failed_files_modified[@]}"; do
        log "  - $file"
    done
fi

log "\n${BLUE}========================================${NC}"
log "${BLUE}Лог сохранён в: $BENCHMARK_LOG${NC}"
log "${BLUE}========================================${NC}"

# Возвращаем код ошибки, если были неудачи в любом из режимов
if [ $failed_normal -gt 0 ] || [ $failed_modified -gt 0 ]; then
    exit 1
fi

exit 0