# CN Futures CSV 数据集成方案

## 目标

把 `cnenkandle/data_prod/` 下的本地 CSV 数据（AG/ag2606 和 AU/au2606 的15min/60min K线）接入 equitiesbeat 系统，在 CN_FUT 板块中实时显示。

---

## 一、关键发现

### 数据流追踪结论

```
CSV 文件 → DataProvider → BaseMarket.symbols[] → API → 前端表格 → 模态框图表
```

**最重要的发现：图表只需要 `symbol.ohlcv` 数组。**

- K线图（Panel 1）：从 `ohlcv` 取 `{o,h,l,c,v}` 画蜡烛图 + MA/BOLL
- 成交量（Panel 2）：从 `ohlcv` 取 `v`
- 副图（Panel 3）：MACD/RSI/KDJ/OBV 全部由前端 `ChartUtil` 从 `close` 价格序列实时计算
- 信号检测：后端 `detect_signals(ohlcv)` 预计算，前端展示

这意味着：**只要把 CSV 数据转换成正确的 ohlcv 格式填入 symbol 对象，所有图表和指标自动工作，不需要改前端。**

### CSV 数据现状

| 文件 | 合约 | 周期 | 行数 | 数据范围 | 最新价 |
|------|------|------|------|----------|--------|
| AG_ag2606_15min.csv | 银 | 15min | 1023 | 2026-05-06 → 06-15 | 16800 |
| AG_ag2606_60min.csv | 银 | 60min | 1023 | 2026-01-08 → 06-15 | 16800 |
| AU_au2606_15min.csv | 金 | 15min | 1028 | 2026-04-30 → 06-17 | 553.64 |
| AU_au2606_60min.csv | 金 | 60min | 1023 | 2026-01-08 → 06-15 | 934.8 |

**注意：** AU 60min 价格区间(887-1258)与其他周期不同，因为它覆盖的是年初高价期。AU 1min/15min 覆盖近期低价期(545-554)。

---

## 二、方案设计

### Phase 1: 静态加载（立即可用）

**不做任何架构改动，只替换数据源。**

#### 2.1 新增 `core/csv_loader.py`

```python
"""从本地 CSV 文件加载 OHLCV 数据"""

class CSVLoader:
    """
    职责：
    1. 根据合约代码找到对应的 CSV 文件
    2. 解析 CSV 为 ohlcv 数组
    3. 提取最新报价 (price, high, low, volume, openInterest)
    """
    
    # 合约代码 → CSV 文件名映射
    CONTRACT_MAP = {
        'ag2506': {'prefix': 'AG', 'contract': 'ag2606'},   # 银
        'au2506': {'prefix': 'AU', 'contract': 'au2606'},   # 金
    }
    
    def load_ohlcv(self, csv_dir, contract_code, timeframe='60min'):
        """
        加载指定合约+周期的 K线数据
        返回: {
            'ohlcv': [{'o':..,'h':..,'l':..,'c':..,'v':..,'t':..}, ...],
            'latest': {'price', 'open', 'high', 'low', 'volume', 'openInterest'},
            'prevClose': float
        }
        """
```

**CSV 行 → ohlcv 条目转换：**
```
CSV: datetime,open,high,low,close,volume,hold
→ ohlcv: {'o': float(open), 'h': float(high), 'l': float(low), 'c': float(close), 'v': int(volume), 't': datetime}
→ symbol.openInterest = float(hold)
```

#### 2.2 修改 `markets/cn_futures.py`

在 `BASE_SYMBOLS` 中标记哪些合约有 CSV 数据：

```python
BASE_SYMBOLS = [
    # 有 CSV 数据的合约
    {'code':'ag2506', ..., 'csvData': True, 'csvTimeframe': '60min'},
    {'code':'au2506', ..., 'csvData': True, 'csvTimeframe': '60min'},
    # 其他合约继续用模拟数据
    ...
]
```

#### 2.3 修改 `markets/base.py` 的 `initialize()` 方法

```python
async def initialize(self):
    templates = self.get_symbol_list()
    
    for t in templates:
        if t.get('csvData'):
            # 从 CSV 加载真实数据
            csv_result = CSVLoader.load_ohlcv(
                csv_dir=self.CSV_DIR,
                contract_code=t['code'],
                timeframe=t.get('csvTimeframe', '60min')
            )
            symbol = self._build_symbol(t, csv_result['latest'], csv_result['ohlcv'], is_sim=False)
        else:
            # 继续用模拟数据
            sim = DataProvider.simulate_quote(t, self.SIMULATION_VOL)
            symbol = self._build_symbol(t, sim, sim['ohlcv'], is_sim=True)
        
        self.symbols.append(symbol)
    
    self._loaded = True
```

#### 2.4 修改 `config.py`

```python
class Config:
    # ... existing ...
    
    # CN Futures 本地 CSV 数据路径
    CN_FUT_CSV_DIR = r"E:\aiprojects\kandlecnen\cnenkandle\data_prod"
    CN_FUT_CSV_ENABLED = True  # 总开关
```

### Phase 2: 增量更新（后续扩展）

**当 CSV 被 pipeline 追加新数据时自动检测并更新。**

#### 2.5 新增 `core/csv_watcher.py`

```python
"""监控 CSV 文件变化，增量推送新K线"""

class CSVWatcher:
    """
    每30秒扫描 CSV 文件：
    1. 记录每文件的行数 + 最后一行时间戳
    2. 对比上次快照，发现新增行
    3. 解析新行为 ohlcv 条目
    4. 追加到对应 symbol 的 ohlcv 数组
    5. 重新计算 signals
    6. 通过 WebSocket 推送 quote_update
    """
```

#### 2.6 修改 `app.py` 的 lifespan

```python
@asynccontextmanager
async def lifespan(app):
    # ... existing tasks ...
    
    if Config.CN_FUT_CSV_ENABLED:
        watcher = CSVWatcher(Config.CN_FUT_CSV_DIR)
        watch_task = asyncio.create_task(watcher.watch_loop())
    
    yield
    
    # cleanup
```

---

## 三、文件变更清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `config.py` | 修改 | 添加 `CN_FUT_CSV_DIR` 和 `CN_FUT_CSV_ENABLED` |
| `core/csv_loader.py` | **新建** | CSV 解析 + ohlcv 转换 |
| `core/csv_watcher.py` | **新建** | 增量监控 + WebSocket 推送 |
| `markets/base.py` | 修改 | `initialize()` 支持 CSV 数据源 |
| `markets/cn_futures.py` | 修改 | 标记有 CSV 数据的合约 |
| `app.py` | 修改 | lifespan 启动 watcher |

**前端不需要任何改动。**

---

## 四、实现顺序

### Step 1: `core/csv_loader.py`
- CSV 解析器（支持7列和8列格式）
- 合约代码 → 文件名映射
- ohlcv 格式转换
- 单元测试

### Step 2: `config.py` + `markets/cn_futures.py`
- 添加配置项
- 标记 ag2506/au2506 使用 CSV 数据
- 设置正确的基础价格（AG=16800, AU=548.5）

### Step 3: `markets/base.py` 修改
- `initialize()` 中检测 `csvData` 标记
- 有 CSV 的用 `CSVLoader` 加载，没有的用模拟
- `USE_REAL_DATA = True` 对有 CSV 的合约

### Step 4: 验证
- 启动服务
- 打开 CN_FUT 标签
- 点击 ag2506/au2606 查看图表
- 确认 K线、成交量、MACD/RSI/KDJ 正常显示

### Step 5: `core/csv_watcher.py`（可选，后续）
- 增量检测
- WebSocket 推送
- 信号重算

---

## 五、风险点与对策

| 风险 | 影响 | 对策 |
|------|------|------|
| AU 60min 价格区间异常 | 图表显示高价期数据 | 只用15min周期数据（与1min一致），或合并多周期 |
| AG 基础价格偏差2.44x | 模拟数据与CSV数据不匹配 | CSV 加载后覆盖 base 价格 |
| CSV 文件不存在 | 启动失败 | 优雅降级到模拟数据 |
| 中文表头 vs 英文表头 | 解析失败 | 统一用索引访问列，不依赖列名 |

---

## 六、预期效果

完成后，用户打开 equitiesbeat：
1. 切换到 CN_FUT 标签页
2. 看到 ag2506(Silver) 和 au2506(Gold) 显示 **LIVE** 标签
3. 点击合约弹出图表，显示真实的15min/60min K线
4. MA/MA20/BOLL/MACD/RSI/KDJ 全部基于真实数据计算
5. 表格中的价格、涨跌幅、成交量都是真实的
6. 其他44个合约仍然显示模拟数据（SIM）
