#include <iostream>
#include <fstream>
#include <vector>
#include <string>
#include <map>
#include <set>
#include <cmath>
#include <algorithm>
#include <iomanip>
#include <chrono>
#include <nlohmann/json.hpp>
#include <getopt.h>

static int  NIterations{1000};
static bool ModifiedBehavior{false};
static bool LoggingMode{false};
static bool BenchmarkMode{false};

#define LOG(CMD) if (LoggingMode) { CMD }
#define BENCHMARK(CMD) if (BenchmarkMode) {                                                 \
        auto start = std::chrono::high_resolution_clock::now();                             \
        CMD                                                                                 \
        auto end = std::chrono::high_resolution_clock::now();                               \
        auto duration = std::chrono::duration_cast<std::chrono::microseconds>(end - start); \
        std::cout << "Время выполнения: " << duration.count() << " мкс\n";                  \
    } else {                                                                                \
        CMD                                                                                 \
    }


struct Node {
    int x;
    int y;
    int id;
    std::string type;
    std::vector<int> edges;
    
    Node() 
    : id(0)
    , x(0)
    , y(0)
    , type("") 
    {}
    
    Node(int _id, int _x, int _y, const std::string& _type) 
    : id(_id)
    , x(_x)
    , y(_y)
    , type(_type) 
    {}

    ~Node() = default;
};

struct Edge {
    int id;
    int vertex1;
    int vertex2;
    int length;
    
    Edge()
    : id(0)
    , vertex1(0)
    , vertex2(0)
    , length(0)
    {}
    
    Edge(int _id, int v1, int v2, int len)
    : id(_id)
    , vertex1(v1)
    , vertex2(v2)
    , length(len)
    {}

    ~Edge() = default;
};

class DSU { // непересекающиеся множества (для Mst)
private:
    std::vector<int> parent;
    std::vector<int> rank;
    
public:
    DSU(int n) {
        parent.resize(n);
        rank.resize(n, 0);
        for (int i = 0; i < n; i++) {
            parent[i] = i;
        }
    }
    
    int find(int x) {
        if (parent[x] != x) {
            parent[x] = find(parent[x]);
        }
        return parent[x];
    }
    
    bool unite(int x, int y) {
        int rootX = find(x);
        int rootY = find(y);
        
        if (rootX == rootY) return false;
        
        if (rank[rootX] < rank[rootY]) {
            parent[rootX] = rootY;
        } else if (rank[rootX] > rank[rootY]) {
            parent[rootY] = rootX;
        } else {
            parent[rootY] = rootX;
            rank[rootX]++;
        }
        return true;
    }
};

class Graph {
private:
    std::map<int, Node> _nodes;
    std::map<int, Edge> _edges;
    int _nextEdgeId;
    int _nextNodeId;
    
public:
    using json = nlohmann::json;

    Graph() : _nextEdgeId(1000), _nextNodeId(100) {}

    bool load(const std::string& filename) {
        std::ifstream file(filename);
        if (!file.is_open()) {
            std::cerr << "Ошибка: не удалось открыть файл " << filename << std::endl;
            return false;
        }
        
        json data;
        try {
            file >> data;
        } catch (const json::parse_error& e) {
            std::cerr << "Ошибка парсинга JSON: " << e.what() << std::endl;
            return false;
        }
        
        _nodes.clear();
        
        if (data.contains("node") && data["node"].is_array()) {
            for (const auto& nodeJson : data["node"]) {
                Node node;
                node.x = nodeJson["x"];
                node.y = nodeJson["y"];
                node.id = nodeJson["id"];
                node.type = nodeJson["type"];
                _nodes[node.id] = node;
            }
        }
        
        if (data.contains("edge") && data["edge"].is_array()) {
            for (const auto& edgeJson : data["edge"]) {
                Edge edge;
                edge.id = edgeJson["id"];
                edge.vertex1 = edgeJson["vertices"][0];
                edge.vertex2 = edgeJson["vertices"][1];
                
                auto it1 = _nodes.find(edge.vertex1);
                auto it2 = _nodes.find(edge.vertex2);
                if (it1 != _nodes.end() && it2 != _nodes.end()) {
                    edge.length = manhattanDistance(it1->second, it2->second);
                }
                
                _edges[edge.id] = edge;
                
                if (_nodes.find(edge.vertex1) != _nodes.end()) {
                    _nodes[edge.vertex1].edges.push_back(edge.id);
                }
                if (_nodes.find(edge.vertex2) != _nodes.end()) {
                    _nodes[edge.vertex2].edges.push_back(edge.id);
                }
            }
        }
        
        int maxId = 0;
        for (const auto& [id, node] : _nodes) {
            maxId = std::max(maxId, id);
        }
        _nextNodeId = maxId + 100;
        _nextEdgeId = maxId + 1000;
        
        LOG(std::cout << "Загружено " << _nodes.size() << " вершин и " << _edges.size() << " рёбер" << std::endl;)
        return true;
    }
    
    bool save(const std::string& filename) const {
        json output;
        
        json nodesArray = json::array();
        for (const auto& [id, node] : _nodes) {
            json nodeJson;
            nodeJson["x"] = node.x;
            nodeJson["y"] = node.y;
            nodeJson["id"] = node.id;
            nodeJson["type"] = node.type;
            
            if (!node.edges.empty()) {
                nodeJson["edges"] = node.edges;
            }
            
            nodesArray.push_back(nodeJson);
        }
        output["node"] = nodesArray;
        
        json edgesArray = json::array();
        for (const auto& [id, edge] : _edges) {
            json edgeJson;
            edgeJson["id"] = edge.id;
            edgeJson["vertices"] = {edge.vertex1, edge.vertex2};
            edgesArray.push_back(edgeJson);
        }
        output["edge"] = edgesArray;
        
        std::ofstream file(filename);
        if (!file.is_open()) {
            std::cerr << "Ошибка: не удалось создать файл " << filename << std::endl;
            return false;
        }
        
        file << output.dump(1);
        LOG(std::cout << "Граф сохранён в " << filename << std::endl;)
        return true;
    }
    
    std::vector<Node> getAllNodes() const {
        std::vector<Node> allNodes;
        for (const auto& [id, node] : _nodes) {
            allNodes.push_back(node);
        }
        return allNodes;
    }

    void print() {
        std::cout << "Вершины (" << _nodes.size() << "):\n";
        for (const auto& [id, node] : _nodes) {
            std::cout << "  ID: " << node.id 
                      << ", (" << node.x << ", " << node.y << ")"
                      << ", type: " << node.type
                      << ", edges: [";
            for (size_t i = 0; i < node.edges.size(); ++i) {
                std::cout << node.edges[i];
                if (i < node.edges.size() - 1) std::cout << ", ";
            }
            std::cout << "]\n";
        }
        
        std::cout << "Рёбра (" << _edges.size() << "):\n";
        for (const auto& [id, edge] : _edges) {
            std::cout << "  ID: " << edge.id 
                      << ", vertices: [" << edge.vertex1 << ", " << edge.vertex2 << "]"
                      << ", length: " << edge.length << "\n";
        }
        std::cout << "\n";
    }
    
    int manhattanDistance(const Node& a, const Node& b) {
        return std::abs(a.x - b.x) + std::abs(a.y - b.y);
    }

    struct TmpEdge {
        int v1, v2; // индексы вершин в nodeList
        int length;
    };

    std::vector<Edge> buildMst(const std::vector<Node>& nodeList) { // построение Minimum Spanning Tree по заданным вершинам с минимизацией эвриситки manhattanDistance
        int n = nodeList.size();
        if (n <= 1) return {};

        std::vector<TmpEdge> tmp;
        tmp.reserve(n * (n - 1) / 2);
        for (int i = 0; i < n; ++i) {
            for (int j = i + 1; j < n; ++j) {
                int d = manhattanDistance(nodeList[i], nodeList[j]);
                tmp.push_back(TmpEdge{i, j, d});
            }
        }

        std::sort(tmp.begin(), tmp.end(), [](const TmpEdge& a, const TmpEdge& b){ return a.length < b.length; });

        DSU dsu(n);
        std::vector<Edge> mst;
        int edgeId = 1;
        for (const auto& edge : tmp) {
            if (dsu.unite(edge.v1, edge.v2)) {
                mst.push_back(Edge(edgeId++, nodeList[edge.v1].id, nodeList[edge.v2].id, edge.length));
                
                if (mst.size() == n - 1) {
                    break;
                }
            }
        }
        return mst;
    }

    // оптимизация: инкрементальное обновление MST при добавлении точки, а не создание каждывй раз с унля
    std::vector<Edge> buildMstIncremental(const std::vector<Edge>& currentMst, const std::vector<Node>& nodeList, const Node& newNode) {
        int n = nodeList.size();
        int newNodeIndex = n;
        
        struct CandidateEdge {
            int v1, v2;
            int length;
        };
        
        std::vector<CandidateEdge> candidates;
        candidates.reserve(n);
        for (int i = 0; i < n; ++i) {
            candidates.push_back({newNodeIndex, i, manhattanDistance(nodeList[i], newNode)});
        }
        
        std::vector<CandidateEdge> allEdges;
        allEdges.reserve(currentMst.size() + n);
        
        for (const auto& edge : currentMst) {
            int u = -1, v = -1;
            for (int i = 0; i < n; ++i) {
                if (nodeList[i].id == edge.vertex1) u = i;
                if (nodeList[i].id == edge.vertex2) v = i;
            }
            if (u != -1 && v != -1) {
                allEdges.push_back({u, v, edge.length});
            }
        }
        
        allEdges.insert(allEdges.end(), candidates.begin(), candidates.end());
        
        std::sort(allEdges.begin(), allEdges.end(), [](const CandidateEdge& a, const CandidateEdge& b) { return a.length < b.length; });
        
        DSU dsu(n + 1);
        std::vector<Edge> newMst;
        int edgeId = currentMst.empty() ? 1 : 
                    (*std::max_element(currentMst.begin(), currentMst.end(),
                        [](const Edge& a, const Edge& b) { return a.id < b.id; })).id + 1;
        
        for (const auto& edge : allEdges) {
            if (dsu.unite(edge.v1, edge.v2)) {
                if (edge.v1 == newNodeIndex) {
                    newMst.push_back(Edge(edgeId++, newNode.id, nodeList[edge.v2].id, edge.length));
                } else if (edge.v2 == newNodeIndex) {
                    newMst.push_back(Edge(edgeId++, nodeList[edge.v1].id, newNode.id, edge.length));
                } else {
                    newMst.push_back(Edge(edgeId++, nodeList[edge.v1].id, nodeList[edge.v2].id, edge.length));
                }
                
                if (newMst.size() == n) {
                    break;
                }
            }
        }
        
        return newMst;
    }

    int totalLength(const std::vector<Edge>& edges) const {
        int length = 0;
        for (const auto& e : edges) {
            length += e.length;
        }
        return length;
    }

    std::vector<std::pair<int,int>> hananGrid(const std::vector<Node>& nodes) const {
        std::set<int> xSet, ySet;
        for (const auto& node : nodes) { 
            xSet.insert(node.x);
            ySet.insert(node.y);
        }

        // строим решётку из всех пересечений горизонтальных и вертикальных прямых - получится n^2 точек
        std::vector<std::pair<int,int>> grid;
        for (int x : xSet) {
            for (int y : ySet) {
                grid.push_back({x, y});
            }
        }

        return grid;
    }

    void buildIterated1Steiner(int maxIterations = 10000) {
        LOG(std::cout << "Алгооритм I1S\n";)

        // _edges.clear();
        // std::map<int, Node> terminals;
        // for (const auto& [id, n] : _nodes)
        //     if (n.type == "t") {
        //         Node clean = n; clean.edges.clear();
        //         terminals[id] = clean;
        //     }
        // _nodes = terminals;
        LOG(std::cout << "Терминалов: " << _nodes.size() << "\n";)

        std::vector<Node> currentNodes = getAllNodes();
        std::vector<Edge> currentMst = buildMst(currentNodes);

        int currentLen = totalLength(currentMst);

        LOG(std::cout << "Начальная длина MST: " << currentLen << "\n";)

        // итеративный алгоритм пока при довалении точки Штейцнера не перестанет улучшаться эвристика
        int steinerCount = 0;
        for (int iter = 0; iter < maxIterations; ++iter) {
            LOG(
                std::cout << "\nИтерация " << (iter + 1) << "\n";
                std::cout << "  Узлов: " << currentNodes.size() << "  (Штейнера: " << steinerCount << ")\n";
            )

            // строим решётку Ханана
            auto candidates = hananGrid(currentNodes);
            LOG(std::cout << "  Кандидатов на решётке Ханана: " << candidates.size() << "\n";)

            int maxDiff = 0;
            std::optional<int> bestCandIdx = std::nullopt;
            std::optional<int> bestCandNodeId = std::nullopt;
            std::vector<Edge> bestMST;
            std::vector<Node> bestNodes;

            // ищем оптимальный узел Штейнера
            int tempIdBase = _nextNodeId;
            for (int ci = 0; ci < candidates.size(); ++ci) {
                int cx = candidates[ci].first;
                int cy = candidates[ci].second;
                
                Node candidate(tempIdBase + ci, cx, cy, "s");
                std::vector<Edge> testMst;
                std::vector<Node> testNodes = currentNodes;
                testNodes.push_back(candidate);
                
                if (not ModifiedBehavior) {
                    testMst = buildMst(testNodes);
                } else {
                    testMst = buildMstIncremental(currentMst, currentNodes, candidate);
                }

                LOG(    // валидация MST
                    if (testMst.size() != testNodes.size() - 1) {
                        std::cout << "  Ошибка: построено " << testMst.size() << " рёбер, нужно " << testNodes.size() - 1 << std::endl;
                        continue;
                    }
                )

                int diff = currentLen - totalLength(testMst);
                
                if (diff > maxDiff) {
                    maxDiff = diff;
                    bestCandIdx = ci;
                    bestCandNodeId = candidate.id;
                    bestMST = testMst;
                    bestNodes = testNodes;
                }
            }

            if (not bestCandIdx.has_value()) {
                LOG(std::cout << "  Улучшение не найдено. Алгоритм завершён.\n\n";)
                break;
            }

            // добавляем найденный узел в основной список узлов
            int cx = candidates[bestCandIdx.value()].first;
            int cy = candidates[bestCandIdx.value()].second;

            Node steiner(bestCandNodeId.value(), cx, cy, "s");
            _nodes[steiner.id] = steiner;
            _nextNodeId = bestCandNodeId.value() + 1;

            currentNodes = bestNodes;
            currentMst = bestMST;
            currentLen = totalLength(currentMst);
            steinerCount++;

            LOG(
                std::cout << "  Добавлена точка Штейнера ID=" << steiner.id
                        << " (" << cx << ", " << cy << ")\n";
                std::cout << "  Уменьшение эвристики: " << maxDiff
                        << "  Новая длина: " << currentLen << "\n";
            )
        }

        _edges.clear();
        for (auto& [id, n] : _nodes) n.edges.clear();

        // пере-связываем полученные узлы с рёбрами
        int eid = 1;
        for (const auto& e : currentMst) {
            if (!_nodes.count(e.vertex1) or !_nodes.count(e.vertex2)) continue;
            Edge newEdge(eid++, e.vertex1, e.vertex2, manhattanDistance(_nodes[e.vertex1], _nodes[e.vertex2]));
            _edges[newEdge.id] = newEdge;
            _nodes[e.vertex1].edges.push_back(newEdge.id);
            _nodes[e.vertex2].edges.push_back(newEdge.id);
        }

        LOG(
            std::cout << "Результат:\n";
            std::cout << "  Терминалов      : " << countTerminals() << "\n";
            std::cout << "  Точек Штейнера  : " << steinerCount << "\n";
            std::cout << "  Всего вершин    : " << _nodes.size() << "\n";
            std::cout << "  Рёбер           : " << _edges.size() << "\n";
            std::cout << "  Длина дерева    : " << currentLen << "\n";
            std::cout << std::endl;
        )
    }

    int countTerminals() const {
        int count = 0;
        for (const auto& [id, node] : _nodes) {
            if (node.type == "t") count++;
        }
        return count;
    }
};

std::string getOutputFilename(const std::string& inputFilename) {
    size_t lastSlash = inputFilename.find_last_of("/\\");
    size_t lastDot = inputFilename.find_last_of('.');
    
    if (lastDot != std::string::npos && (lastSlash == std::string::npos || lastDot > lastSlash)) {
        std::string path = (lastSlash != std::string::npos) ? inputFilename.substr(0, lastSlash + 1) : "";
        std::string baseName = inputFilename.substr(lastSlash + 1, lastDot - lastSlash - 1);
        std::string extension = inputFilename.substr(lastDot);
        return "./" + baseName + "_out" + extension;
    } else {
        return inputFilename + "_out.json";
    }
}

int main(int argc, char* argv[]) {
    std::string inputFilename;
    int opt;
    
    while ((opt = getopt(argc, argv, "mlti:")) != -1) {
        switch (opt) {
            case 'm':
                ModifiedBehavior = true;
                break;
            case 'l':
                LoggingMode = true;
                break;
            case 't':
                BenchmarkMode = true;
                break;
            case 'i':
                NIterations = std::atoi(optarg);
                if (NIterations < 0) {
                    std::cerr << "Ошибка: число итераций должно быть неотрицательным" << std::endl;
                    return 1;
                }
                break;
            default:
                std::cerr << "Использование: " << argv[0] << " [-m] [-l] [-t] [-i число] <filename.json>" << std::endl;
                return 1;
        }
    }
    
    if (optind < argc) {
        inputFilename = argv[optind];
    } else {
        std::cerr << "Ошибка: не указан входной файл" << std::endl;
        return 1;
    }
            
    Graph graph;

    if (!graph.load(inputFilename)) {
        std::cerr << "Ошибка загрузки файла " << inputFilename << std::endl;
        return 1;
    }

    LOG(std::cout << "Исходный граф:" << std::endl;)
    LOG(graph.print();)
    
    LOG(
        std::cout << "Запуск ";
        if (ModifiedBehavior) {
            std::cout << "модифицированного ";
        } else {
            std::cout << "немодифицированного ";
        }
        std::cout << "алгоритма" << std::endl;
    )

    BENCHMARK(graph.buildIterated1Steiner(NIterations);)

    LOG(std::cout << "Результирующее дерево Штейнера:" << std::endl;)
    LOG(graph.print();)

    std::string outputFilename = getOutputFilename(inputFilename);
    if (!graph.save(outputFilename)) {
        std::cerr << "Ошибка сохранения в файл " << outputFilename << std::endl;
        return 1;
    }
    
    return 0;
}