# Qshot —— 带噪感知的 Shots 数量推荐器

Qshot 用来回答这样一个问题：**给定一个量子电路和一份后端噪声快照，要跑多少 shots（测量重复次数）才能让测量结果的保真度达到目标水平？**
输入：`QuantumCircuit` + 噪声 JSON
输出：一个整数 shots 值 + 该 shots 下的预测保真度

本目录是 Qshot 研究代码的**集成交付版本**，只包含推理所需的部分，不含训练、评估、实验脚本。

---

## 目录结构

```
Qshot_handover/
├── README.md                 # 英文版
├── README_zh.md              # 本文件
├── requirements.txt
├── example_usage.py          # 端到端调用示例
├── src/
│   ├── recommend_shots_v4.py # 主引擎 + Python API
│   ├── dual_gnn_model.py     # GNN 架构（离群兜底模型）
│   ├── show_dag.py           # QASM → graph 转换（GNN 用）
│   └── train_dual_gnn.py     # GNN fallback 加载时被引用
├── data/
│   ├── shots_dataset_historic*/       # 12 个目录，共约 3280 条记录
│   └── noise_json/           # 6 份 IBM 噪声快照
└── checkpoint/
    └── best_model.pt         # 训练好的 GNN fallback 权重（约 4.3 MB）
```

`data/` 和 `checkpoint/` 下的路径在 `recommend_shots_v4.py` 导入时会**自动发现**，不需要你显式传。

---

## 安装

开发和测试环境是 **Python 3.9**。

```bash
python3.9 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

`torch-scatter` 和 `torch-sparse` 需要匹配你 PyTorch + CUDA 版本的 wheel。如果这两行装不上，去 PyG 官方 wheel index 找对应版本（见 `requirements.txt` 里的注释）。

---

## 快速开始

```bash
cd Qshot_handover/
python example_usage.py
```

预期行为：打印进度 → 加载数据库 + 聚类（30–60 秒） → 打印推荐 shots。

---

## Python API

两个入口，都在 `src/recommend_shots_v4.py` 里。

### `QshotRecommender` —— 一次加载多次查询（**服务化推荐用这个**）

```python
from recommend_shots_v4 import QshotRecommender

# 构造慢（~30-60 秒），服务启动时只做一次
recommender = QshotRecommender()          # 自动使用 bundled 数据 + checkpoint
# 也可以覆盖：
# recommender = QshotRecommender(
#     dataset_dirs=[...], gnn_ckpt="path/to/best_model.pt")

# 每次 .predict() 很快（数秒，主要耗时在 pilot 测量）
result = recommender.predict(
    circuit=my_quantum_circuit,       # QuantumCircuit 对象或 .qpy 路径
    noise_json="path/to/noise.json",  # 路径或已加载的 dict
    alpha=0.95,                       # 目标保真度比例
)
```

### `predict_shots()` —— 一次性调用

```python
from recommend_shots_v4 import predict_shots

result = predict_shots(circuit, noise_json_path, alpha=0.95)
```

这个函数每次都会新建一个 `QshotRecommender`。**只适合一次性脚本**，服务化部署请用上面的 class。

---

## 输入 / 输出

### `circuit`
可以是 `qiskit.QuantumCircuit` 对象（**不要**自己加 `measure_all()`，推荐器会自己加），也可以是 `.qpy` 文件路径。

### `noise_json`
可以是文件路径（str 或 `pathlib.Path`），也可以是已加载的 dict。

本项目自带的 6 份噪声 JSON 遵循 IBM 预处理噪声 schema。必须包含 `noise_summary` 字段，至少要有：
- `twoq_gate_error_mean`、`readout_mean` 或（`prob_meas0_prep1_mean` + `prob_meas1_prep0_mean`）
- `T2_mean`
- `sx_gate_error_mean`、`T1_mean` 等（噪声模型构造要用）

要接入其他后端，**把噪声 JSON 按自带的格式仿一份就行**。

### 返回值

dict，字段如下：

| key | 类型 | 含义 |
|---|---|---|
| `recommended_shots` | `int` | 实际跑电路时传给 `shots=` 的值 |
| `method` | `str` | `"regression"`（聚类+曲线拟合）或 `"gnn_fallback"`（离群兜底）|
| `predicted_fidelity` | `float` | 在该 shots 下的预测保真度 |
| `predicted_std` | `float` | 上述预测的标准差 |
| `cluster_label` | `int` | 命中的 HDBSCAN 簇编号（`-1` 表示离群）|
| `tier` | `int` | 簇内的 shots 规模层级 |
| `n_matched` | `int` | 参与曲线拟合的邻居数 |
| `fit` | `dict` | 拟合原始参数（`F_inf`, `a`, `b`, `target`, ...）|

推荐失败返回 `None`（看日志找原因）。

---

## 工作原理（简述）

两条路径，按 query 自动选：

1. **主路径（回归）**：提取 9 个特征（6 电路 + 3 噪声） → 找最近的 HDBSCAN 簇 → kNN 投票选 tier → 在 tier 对应 shots 跑 pilot 试测 → 在簇内用 pilot 的 PF 曲线做 kNN 匹配 → 在匹配到的邻居上拟合 `F(s) = F_inf - a/s^b` → 解满足 `F(s) - z·σ ≥ α·F_conv` 的最小 `s`。

2. **兜底路径（GNN）**：如果电路不属于任何簇，用双图 GINEConv 网络（`dual_gnn_model.py`，权重在 `checkpoint/best_model.pt`）从 (电路 DAG 图, 硬件耦合图) 预测完整的 fidelity 曲线，再用同样的阈值逻辑选 `s`。

---

## 性能说明

- **冷启动**：~30–60 秒（加载 3280 条记录 + HDBSCAN 聚类 + GNN 权重）。**服务启动时做一次**，不要每个请求都做。
- **每次查询**：主要耗时在 pilot 测量，几秒到几十秒（看电路规模和 pilot 配置）。
- **内存**：< 1 GB。推理不需要 GPU（GNN fallback 默认在 CPU 上跑；如果你装了 CUDA 版 PyTorch 它能自动用上 GPU 加速）。

---

## 适用范围 / 局限

- **比特数**：训练数据覆盖 5–8 比特。超出范围时 GNN fallback 会外推但精度未验证。
- **硬件类型**：训练数据只含 IBM Marrakesh 和 Pittsburgh。其他厂商的噪声 JSON 需要 schema 映射。
- **电路类型**：QAOA-like、HEA brickwall、半随机分层、完全随机电路效果最好。强结构的算法电路（QFT、Grover、纠错码等）属于分布外。
- **Transpile**：推荐器内部用 `optimization_level=1`、`seed_transpiler=1234` 自己 transpile，**不要先自己 transpile 过**再传进来。

---

## 修改代码时要注意的不变量

- `recommend_shots_v4.py` 里两个 shots 序列（`SHOTS_SEQUENCE_QAOA`、`SHOTS_SEQUENCE_DEFAULT`）必须和训练数据集构建时的序列一致。不要随便改，改了就要重建数据集。
- `CIRCUIT_FEATURE_KEYS`（6 个）和 `NOISE_FEATURE_KEYS`（3 个）定义聚类特征空间，改了所有 bundled 数据都废。
- 训练/测试划分是确定性的：`test_ratio=0.1, seed=42`。推荐器内部用 90% 训练数据做聚类。
- 训练集的 `record_id` 哈希包含噪声文件名。**12 个数据集目录不能互相替换**，要当成一个整体一起加载。
- 记录里的 `base.qasm` 可能是 OpenQASM 3，加载路径会回退到一个子集 QASM3→QASM2 转换器（`_qasm3_to_qasm2`）。

---

## 可以忽略的文件

`train_dual_gnn.py` 只是被间接引用（GNN fallback 用了里面的几个常量），**推理不用它**。
`show_dag.py` 虽然有 CLI，但在本项目中主要是给 GNN fallback 提供 `qasm_to_graph_data()` 这个 helper。

---

## 联系方式

关于模型、数据集、算法的问题：李彤（`tli24@gmu.edu`）。
