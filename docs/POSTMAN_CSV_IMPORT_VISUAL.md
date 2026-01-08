# Postman CSV导入 - 详细操作步骤（带截图说明）

## 📸 Postman界面说明

### 步骤1: 选择Body标签页

在Postman请求中，点击 **Body** 标签页（在Params、Authorization、Headers旁边）

### 步骤2: 选择form-data

你会看到几个选项：
- ○ none
- ○ form-data  ← **选择这个**
- ○ x-www-form-urlencoded
- ○ raw
- ○ binary
- ○ GraphQL

**点击 form-data 前面的圆圈**

### 步骤3: 添加文件字段

选择form-data后，你会看到表格：

#### 新版本Postman（有Type列）:
```
┌─────────┬──────────┬──────────────────┐
│ Key     │ Type     │ Value            │
├─────────┼──────────┼──────────────────┤
│ file    │ [Text▼]  │ [点击选择File]   │
└─────────┴──────────┴──────────────────┘
```

**操作**:
1. 在Key列输入: `file`
2. 在Type列，点击下拉菜单，选择 **File**
3. 在Value列，点击 **Select Files** 按钮，选择CSV文件

#### 旧版本Postman（只有Key和Value列）:
```
┌─────────┬──────────────────────────┐
│ Key     │ Value                    │
├─────────┼──────────────────────────┤
│ file    │ [Text ▼] [Select Files]  │
└─────────┴──────────────────────────┘
```

**操作**:
1. 在Key列输入: `file`
2. 在Value列，你会看到右侧有下拉菜单或图标
3. 点击下拉菜单，选择 **File**（不是Text）
4. 选择File后，会出现 **Select Files** 按钮
5. 点击 **Select Files**，选择你的CSV文件

---

## 🔍 如果看不到File选项怎么办？

### 方法1: 检查是否选择了form-data

确保你点击了 **form-data** 选项，而不是其他选项。

### 方法2: 查看Value列的右侧

在Value列中，右侧通常有：
- 一个下拉菜单图标（▼）
- 或者一个文件夹图标
- 或者 "Text" 字样

点击这些元素，应该会出现选项菜单。

### 方法3: 尝试不同的操作

1. **点击Value列右侧的下拉箭头**:
   ```
   Value: [_____________] [▼]
                            ↑
                        点击这里
   ```

2. **右键点击Value列**:
   可能弹出菜单，选择 "File" 或 "Change to File"

3. **双击Value列**:
   某些版本可能会弹出选择对话框

### 方法4: 使用键盘快捷键

在某些Postman版本中：
- 点击Value列
- 按 `Tab` 键
- 可能会切换到文件选择模式

---

## 📝 详细操作步骤（文字版）

### 完整流程：

1. **打开Postman**
   - 创建新请求或选择现有请求

2. **设置Method和URL**
   - Method: `POST`
   - URL: `http://localhost:8000/api/admin/stores/import`

3. **设置Headers**
   - 点击 **Headers** 标签
   - 添加: `Authorization: Bearer {你的token}`

4. **设置Body**
   - 点击 **Body** 标签
   - 选择 **form-data**（点击前面的圆圈）

5. **添加文件字段**
   - 在Key列输入: `file`
   - 在Value列：
     - **如果看到下拉菜单**: 点击下拉菜单，选择 **File**
     - **如果看到图标**: 点击图标，选择 **File**
     - **如果只看到输入框**: 尝试点击输入框右侧的任何元素

6. **选择文件**
   - 选择File类型后，会出现 **Select Files** 或 **Choose Files** 按钮
   - 点击按钮，浏览并选择你的CSV文件

7. **发送请求**
   - 点击 **Send** 按钮

---

## 🎯 不同Postman版本的界面差异

### Postman Web版本
- 通常有Type列
- File选项在下拉菜单中

### Postman Desktop版本（较新）
- 可能有Type列
- 或者Value列右侧有图标

### Postman Desktop版本（较旧）
- 可能只有Key和Value列
- Value列右侧有下拉菜单

---

## ✅ 验证配置是否正确

配置正确后，你应该看到：

1. **Key列**: `file`
2. **Value列**: 显示你的文件名，例如 `stores.csv`
3. **类型指示**: 可能显示 "File" 或文件图标

**错误配置**（不会工作）:
- Value列显示的是文本内容（CSV的文本）
- 或者显示 "Text" 类型

**正确配置**（会工作）:
- Value列显示文件名
- 或者显示文件图标
- 或者Type列显示 "File"

---

## 🆘 如果还是不行

### 替代方案1: 使用curl命令

```bash
curl -X POST "http://localhost:8000/api/admin/stores/import" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@/path/to/your/stores.csv"
```

### 替代方案2: 检查Postman版本

更新Postman到最新版本：
- Help → Check for Updates
- 或者从官网下载最新版本

### 替代方案3: 使用其他工具

- **Insomnia**: 类似Postman，界面可能更清晰
- **HTTPie**: 命令行工具
- **curl**: 命令行工具

---

## 📞 需要帮助？

如果按照上述步骤还是无法找到File选项，请告诉我：
1. 你使用的Postman版本（Help → About Postman）
2. Body标签页中你看到的具体界面（有几列？有什么按钮？）
3. Value列右侧有什么元素？

我可以根据你的具体情况提供更精确的指导。

