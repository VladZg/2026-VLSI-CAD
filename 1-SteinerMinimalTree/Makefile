CXX = clang++
CXXFLAGS = -std=c++17

JSON_PATH = $(shell brew --prefix nlohmann-json)
INCLUDES = -I$(JSON_PATH)/include

TARGET = Steiner
SRC = Steiner.cpp

$(TARGET): $(SRC)
	$(CXX) $(SRC) $(INCLUDES) $(CXXFLAGS) -o $(TARGET)

clean:
	rm -f $(TARGET)

rebuild: clean $(TARGET)

run: $(TARGET)
	./$(TARGET) $(ARG)

check:	# для Mac
	@echo "Проверка зависимостей..."
	@brew --prefix nlohmann-json > /dev/null 2>&1 || (echo "Ошибка: nlohmann-json не установлен. Установите: brew install nlohmann-json" && exit 1)
	@echo "✓ nlohmann-json найден по пути: $(JSON_PATH)"

.PHONY: clean rebuild run check help