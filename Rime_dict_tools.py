import tkinter as tk
from tkinter import messagebox, filedialog
from tkinter import ttk
import os
import re
import subprocess
import configparser



# 默认 Rime 用户词典路径
default_rime_user_dict_path = os.path.expanduser(r"G:/save/rime")

# 配置文件路径
config_path = os.path.expanduser(r"D:/soft/rime/rime_dict_manager_config.ini")

BG_COLOR = "#f0f0f0"  # 浅灰色背景
PADDING = 5  # 统一内边距
FONT_FAMILY = "Microsoft YaHei UI"  # 微软雅黑 UI
FONT_SIZE = 10  # 字体大小
DEFAULT_FONT = (FONT_FAMILY, FONT_SIZE)
HEADING_FONT = (FONT_FAMILY, FONT_SIZE, "bold")  # 用于标题和重要文本

def load_config():
    """加载配置文件"""
    config = configparser.ConfigParser()
    if os.path.exists(config_path):
        try:
            config.read(config_path)
            if "Dictionaries" in config:
                # 将词典文件路径存储为列表
                return config["Dictionaries"].get("paths", "").split("|")
        except configparser.DuplicateOptionError:
            # 如果配置文件格式错误，返回空列表
            return []
    return []


def save_config(dictionaries):
    """保存配置文件"""
    config = configparser.ConfigParser()
    config["Dictionaries"] = {
        # 将词典文件路径存储为以 | 分隔的字符串
        "paths": "|".join(dictionaries)
    }
    with open(config_path, "w", encoding="utf-8") as f:
        config.write(f)


def get_latest_dict(dictionaries):
    """获取最近修改的词典文件"""
    latest_dict = None
    latest_time = 0
    for dict_path in dictionaries:
        if os.path.exists(dict_path):
            mod_time = os.path.getmtime(dict_path)
            if mod_time > latest_time:
                latest_time = mod_time
                latest_dict = dict_path
    return latest_dict


def load_dict_entries(dict_path, switch_order=False, enable_code2=False):
    """加载词典文件中的词、编码、编码2和权重，并提取文件头部（包括分隔符如 '...' 及其之前的所有内容）"""
    if not os.path.exists(dict_path):
        print(f"词典文件不存在: {dict_path}")  # 调试信息
        return [], "", ""

    entries = []
    header = ""
    first_entry = ""  # 第一条词条
    
    # 尝试不同的编码方式读取文件
    encodings = ['utf-8', 'gbk', 'gb18030', 'utf-16']
    content = None
    
    for encoding in encodings:
        try:
            with open(dict_path, "r", encoding=encoding) as f:
                content = f.read()
                break  # 如果成功读取，跳出循环
        except UnicodeDecodeError:
            continue
    
    if content is None:
        messagebox.showerror("错误", "无法正确读取文件，请检查文件编码")
        return [], "", ""

    # 处理文件内容
    lines = content.splitlines()
    header_found = False
    
    # 根据文件扩展名判断处理方式
    file_ext = os.path.splitext(dict_path)[1].lower()
    
    # 处理头部和词条
    for line in lines:
        if not header_found:
            if file_ext == '.yaml' and line.strip() == "...":  # YAML 格式使用 ... 分隔
                header += line + "\n"
                header_found = True
            elif file_ext == '.txt':  # TXT 格式直接处理词条
                if line.startswith('#'):  # 保存注释作为头部
                    header += line + "\n"
                else:
                    header_found = True
                    # 不跳过当前行，继续处理
                    if line.strip() and not line.strip().startswith("#"):
                        parts = line.strip().split("\t")
                        if len(parts) >= 2:
                            word = parts[0].strip()
                            second_field = parts[1].strip()
                            if re.match(r"^\d+$", second_field):
                                weight = second_field
                                code = parts[2].strip() if len(parts) >= 3 else ""
                                code2 = parts[3].strip() if len(parts) >= 4 and enable_code2 else ""
                            else:
                                code = second_field
                                weight = parts[2].strip() if len(parts) >= 3 else "100"
                                code2 = parts[3].strip() if len(parts) >= 4 and enable_code2 else ""
                            entry = (word, weight, code, code2) if switch_order else (word, code, weight, code2)
                            entries.append(entry)
                            if not first_entry:
                                first_entry = "\t".join(entry)
            continue
        
        # 处理非头部内容
        if line.strip() and not line.strip().startswith("#"):
            parts = line.strip().split("\t")
            if len(parts) >= 2:
                word = parts[0].strip()
                second_field = parts[1].strip()
                if re.match(r"^\d+$", second_field):
                    weight = second_field
                    code = parts[2].strip() if len(parts) >= 3 else ""
                    code2 = parts[3].strip() if len(parts) >= 4 and enable_code2 else ""
                else:
                    code = second_field
                    weight = parts[2].strip() if len(parts) >= 3 else "100"
                    code2 = parts[3].strip() if len(parts) >= 4 and enable_code2 else ""
                entry = (word, weight, code, code2) if switch_order else (word, code, weight, code2)
                entries.append(entry)
                if not first_entry:
                    first_entry = "\t".join(entry)

    return entries, header, first_entry


def save_dict_entries(dict_path, new_entries, header="", append=False, switch_order=False, enable_code2=False):
    """保存词典条目到文件，先写入文件头部，再追加词条"""
    mode = "w"  # 总是覆盖模式，先写入文件头部
    with open(dict_path, mode, encoding="utf-8") as f:
        # 写入文件头部
        if header:
            f.write(header)
        # 写入词条
        for entry in new_entries:
            if switch_order:
                # 切换次序：词汇 权重 编码 编码2
                if enable_code2:
                    f.write(f"{entry[0]}\t{entry[1]}\t{entry[2]}\t{entry[3]}\n")
                else:
                    f.write(f"{entry[0]}\t{entry[1]}\t{entry[2]}\n")
            else:
                # 默认次序：词汇 编码 权重 编码2
                if enable_code2:
                    f.write(f"{entry[0]}\t{entry[1]}\t{entry[2]}\t{entry[3]}\n")
                else:
                    f.write(f"{entry[0]}\t{entry[1]}\t{entry[2]}\n")


def check_existing_code(code, dict_path):
    """检查是否存在相同编码的词，并返回其行号和权重"""
    entries, _, _ = load_dict_entries(dict_path)
    for i, entry in enumerate(entries):
        if entry[1] == code:
            return i, entry[2]  # 返回权重
    return None, None


def add_word_to_rime(word, code, code2, weight, dict_path, switch_order=False, enable_code2=False):
    """添加新词或更新已有词的权重"""
    entries, header, _ = load_dict_entries(dict_path, switch_order, enable_code2)
    if enable_code2:
        entries.append((word, code, str(weight), code2))  # 确保编码2被添加
    else:
        entries.append((word, code, str(weight)))
    save_dict_entries(dict_path, entries, header, switch_order=switch_order, enable_code2=enable_code2)
    messagebox.showinfo("成功", f"已成功添加词汇: {word} ({code}, {code2}), 权重: {weight}")


def update_word_in_rime(word, code, code2, weight, dict_path, original_code, switch_order=False, enable_code2=False):
    """修改已有词条"""
    entries, header, _ = load_dict_entries(dict_path, switch_order, enable_code2)

    # 检查新编码是否已存在
    new_code_exists = any(entry[1] == code for entry in entries)
    if new_code_exists and code != original_code:
        confirm = messagebox.askyesno("确认", f"编码 '{code}' 已存在。是否覆盖？")
        if not confirm:
            return

    # 更新词条
    for i, entry in enumerate(entries):
        if entry[1] == original_code:
            if enable_code2:
                entries[i] = (word, code, str(weight), code2)
            else:
                entries[i] = (word, code, str(weight))
            break

    save_dict_entries(dict_path, entries, header, switch_order=switch_order, enable_code2=enable_code2)
    messagebox.showinfo("成功", f"已成功修改词汇: {word} ({code}, {code2}), 权重: {weight}")


def delete_word_from_rime(dict_path, selected_items, switch_order=False, enable_code2=False):
    """删除选中的词条"""
    if not selected_items:
        messagebox.showwarning("警告", "请选择要删除的词条")
        return

    # 如果是单个选择，转换为列表
    if not isinstance(selected_items, list):
        selected_items = [selected_items]

    # 构建确认消息
    items_text = "\n".join([f"{item[0]} ({item[1]})" for item in selected_items])
    confirm = messagebox.askyesno("确认", f"确定要删除以下词汇吗？\n{items_text}")
    
    if confirm:
        entries, header, _ = load_dict_entries(dict_path, switch_order, enable_code2)
        # 创建要删除的条目集合
        entries = [entry for entry in entries if not any(
            (entry[0] == item[0] and entry[1] == item[1] and 
             entry[2] == item[2] and entry[3] == item[3])
            for item in selected_items
        )]
        
        save_dict_entries(dict_path, entries, header, switch_order=switch_order, enable_code2=enable_code2)
        messagebox.showinfo("成功", f"已成功删除 {len(selected_items)} 个词条")


def deploy_rime():
    """部署 Rime 输入法"""
    try:
        # 尝试使用注册表找到小狼毫安装路径
        import winreg
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\\Rime\Weasel", 0, winreg.KEY_READ)
            weasel_path = winreg.QueryValueEx(key, "WeaselRoot")[0]
            deployer_path = os.path.join(weasel_path, "WeaselDeployer.exe")
        except:
            # 如果注册表查找失败，使用默认路径
            deployer_path = r"D:\\soft\\Rime\Weasel-0.16.3\\WeaselDeployer.exe"
        
        if not os.path.exists(deployer_path):
            raise FileNotFoundError(f"找不到小狼毫部署程序: {deployer_path}")
            
        subprocess.run([deployer_path, "/deploy"], check=True)
        messagebox.showinfo("成功", "小狼毫部署成功！")
    except FileNotFoundError as e:
        messagebox.showerror("错误", str(e))
    except subprocess.CalledProcessError as e:
        messagebox.showerror("错误", f"部署失败: {e}")
    except Exception as e:
        messagebox.showerror("错误", f"未知错误: {e}")


def on_add_button_click():
    word = entry_word.get().strip()
    code = entry_code.get().strip()
    code2 = entry_code2.get().strip()
    weight = entry_weight.get().strip()
    dict_path = combo_dict.get()  # 获取词典文件路径

    if not word or not code:
        messagebox.showwarning("警告", "请填写词汇和编码")
        return

    if not dict_path or not os.path.exists(dict_path):
        messagebox.showwarning("警告", "请选择有效的词典文件")
        return

    # 默认权重为 100
    weight = int(weight) if weight.isdigit() else 100

    # 检查是否已存在相同编码的词
    line_num, existing_weight = check_existing_code(code, dict_path)
    if line_num is not None:
        # 弹出选项对话框
        choice = messagebox.askquestion("编码重复", f"编码 '{code}' 已存在，当前权重为 {existing_weight}。请选择操作：",
                                        icon='warning', type='yesnocancel',
                                        default='cancel', detail="选择 '是' 覆盖，'否' 添加，'取消' 放弃操作。")
        if choice == 'yes':  # 覆盖
            update_word_in_rime(word, code, code2, weight, dict_path, code, switch_order=switch_order.get(),
                                enable_code2=enable_code2.get())
        elif choice == 'no':  # 添加
            add_word_to_rime(word, code, code2, weight, dict_path, switch_order=switch_order.get(),
                             enable_code2=enable_code2.get())
        else:  # 取消
            return
    else:
        # 如果编码不存在，直接添加
        add_word_to_rime(word, code, code2, weight, dict_path, switch_order=switch_order.get(),
                         enable_code2=enable_code2.get())

    # 清空输入框
    entry_word.delete(0, tk.END)
    entry_code.delete(0, tk.END)
    entry_code2.delete(0, tk.END)
    entry_weight.delete(0, tk.END)

    # 刷新词典条目列表
    refresh_dict_entries(dict_path)


def on_modify_button_click():
    """修改选中的词条"""
    dict_path = combo_dict.get()  # 获取词典文件路径
    selected_item = tree.item(tree.selection(), "values") if tree.selection() else None

    if not selected_item:
        messagebox.showwarning("警告", "请选择要修改的词条")
        return

    word = entry_word.get().strip()
    code = entry_code.get().strip()
    code2 = entry_code2.get().strip()
    weight = entry_weight.get().strip()
    original_code = selected_item[1] # 获取原始编码

    if not word or not code:
        messagebox.showwarning("警告", "请填写词汇和编码")
        return

    # 默认权重为 100
    weight = int(weight) if weight.isdigit() else 100

    # 修改词条
    update_word_in_rime(word, code, code2, weight, dict_path, original_code, switch_order=switch_order.get(),
                        enable_code2=enable_code2.get())

    # 清空输入框
    entry_word.delete(0, tk.END)
    entry_code.delete(0, tk.END)
    entry_code2.delete(0, tk.END)
    entry_weight.delete(0, tk.END)

    # 刷新词典条目列表
    refresh_dict_entries(dict_path)


def on_delete_button_click():
    """删除选中的词条"""
    dict_path = combo_dict.get()  # 获取词典文件路径
    selected_items = [tree.item(item, "values") for item in tree.selection()]
    delete_word_from_rime(dict_path, selected_items, switch_order=switch_order.get(), enable_code2=enable_code2.get())
    refresh_dict_entries(dict_path)


def on_deploy_button_click():
    """部署 Rime 输入法"""
    deploy_rime()


def on_save_button_click():
    """保存当前词典条目到文件"""
    dict_path = combo_dict.get()  # 获取词典文件路径
    if not dict_path or not os.path.exists(dict_path):
        messagebox.showwarning("警告", "请选择有效的词典文件")
        return

    # 加载当前显示的条目
    entries = []
    for item in tree.get_children():
        values = tree.item(item)["values"]
        if enable_code2.get():
            entries.append((values[0], values[1], values[2], values[3]))
        else:
            entries.append((values[0], values[1], values[2]))

    # 获取原文件的头部信息
    _, header, _ = load_dict_entries(dict_path, switch_order=switch_order.get(), enable_code2=enable_code2.get())
    
    try:
        save_dict_entries(dict_path, entries, header, switch_order=switch_order.get(), enable_code2=enable_code2.get())
        messagebox.showinfo("成功", "词典条目已保存！")
        # 保存后刷新显示
        refresh_dict_entries(dict_path)
    except Exception as e:
        messagebox.showerror("错误", f"保存失败: {str(e)}")


def on_choose_dict_button_click():
    """选择词典文件"""
    dict_path = filedialog.askopenfilename(
        title="选择 Rime 用户词典文件",
        initialdir=os.path.dirname(default_rime_user_dict_path),
        filetypes=[("Text Files", "*.txt"), ("YAML Files", "*.yaml")],
    )
    if dict_path:
        dictionaries = load_config()
        if dict_path not in dictionaries:
            dictionaries.append(dict_path)
            save_config(dictionaries)
            update_combo_dict()
        combo_dict.set(dict_path)
        refresh_dict_entries(dict_path)  # 确保调用刷新函数


def on_clear_button_click():
    """清空下拉菜单中的所有词典文件记录"""
    save_config([])
    update_combo_dict()
    combo_dict.set("")
    messagebox.showinfo("成功", "已清空下拉菜单")


def on_tree_select(event=None):  # 添加事件参数
    """选中词条时填充到输入框"""
    selected_item = tree.item(tree.selection(), "values") if tree.selection() else None
    if selected_item:
        entry_word.delete(0, tk.END)
        entry_word.insert(0, selected_item[0])
        entry_code.delete(0, tk.END)
        entry_code.insert(0, selected_item[1])
        entry_weight.delete(0, tk.END)
        entry_weight.insert(0, selected_item[2])
        entry_code2.delete(0, tk.END)
        entry_code2.insert(0, selected_item[3])


def refresh_dict_entries(dict_path):
    """刷新词典条目列表"""
    print(f"刷新词典文件: {dict_path}")  # 调试信息
    for row in tree.get_children():
        tree.delete(row)  # 清空表格
    entries, _, first_entry = load_dict_entries(dict_path, switch_order=switch_order.get(), enable_code2=enable_code2.get())  # 加载词典条目
    print(f"加载的条目数量: {len(entries)}")  # 调试信息
    for entry in entries:
        tree.insert("", tk.END, values=entry)  # 插入新条目
    # 更新第一条词条显示
    label_first_entry.config(text=f"第一条词条: {first_entry}" if first_entry else "第一条词条: 无")


def update_combo_dict():
    """更新下拉菜单中的词典文件"""
    dictionaries = load_config()
    combo_dict["values"] = dictionaries
    # 设置默认词典文件为最近修改的文件
    latest_dict = get_latest_dict(dictionaries)
    if latest_dict:
        combo_dict.set(latest_dict)
        # 确保 tree 已定义后再调用 refresh_dict_entries
        if 'tree' in globals():
            refresh_dict_entries(latest_dict)  # 刷新条目列表


def on_query_button_click():
    """查询功能：根据输入内容查询词条"""
    query_text = entry_query.get().strip()  # 获取查询内容
    dict_path = combo_dict.get()  # 获取词典文件路径

    if not dict_path or not os.path.exists(dict_path):
        messagebox.showwarning("警告", "请选择有效的词典文件")
        return

    # 加载词典条目
    entries, _, first_entry = load_dict_entries(dict_path, switch_order=switch_order.get(), enable_code2=enable_code2.get())

    # 如果查询内容为空，显示所有词条
    if not query_text:
        results = entries
    else:
        # 根据匹配模式查询
        if match_mode.get() == "exact":
            # 全匹配
            results = [entry for entry in entries if query_text == entry[0] or query_text == entry[1]]
        else:
            # 部分匹配
            results = [entry for entry in entries if query_text in entry[0] or query_text in entry[1]]

    # 清空表格并显示查询结果
    for row in tree.get_children():
        tree.delete(row)
    if results:
        for result in results:
            tree.insert("", tk.END, values=result)
    else:
        messagebox.showinfo("提示", "未找到匹配的词条")
    # 更新第一条词条显示
    label_first_entry.config(text=f"第一条词条: {first_entry}" if first_entry else "第一条词条: 无")


# 在文件开头添加常量定义
BG_COLOR = "#f0f0f0"  # 浅灰色背景
PADDING = 5  # 统一内边距

# 主窗口设置
root = tk.Tk()
root.title("Rime 词典管理程序 by Boldan")
root.configure(bg=BG_COLOR)    

# 设置默认字体
root.option_add("*Font", DEFAULT_FONT)
style = ttk.Style()
style.configure(".", font=DEFAULT_FONT)  # 设置 ttk 控件的默认字体

# 添加变量定义
switch_order = tk.BooleanVar(value=False)
enable_code2 = tk.BooleanVar(value=False)
match_mode = tk.StringVar(value="exact")  # 添加匹配模式变量

# 添加变量定义
switch_order = tk.BooleanVar(value=False)
enable_code2 = tk.BooleanVar(value=False)
match_mode = tk.StringVar(value="exact")  # 添加匹配模式变量

# 创建顶部框架来容纳第1、2行
top_frame = ttk.Frame(root)
top_frame.grid(row=0, rowspan=2, column=0, columnspan=6, sticky='nsew', padx=PADDING, pady=PADDING)

# 配置top_frame的列权重

top_frame.grid_columnconfigure(1, weight=5)  # 第一列权重为5
top_frame.grid_columnconfigure(2, weight=3)  # 第二列权重为3
top_frame.grid_columnconfigure(3, weight=2)  # 第三列权重为2

# 在top_frame中重新布局第1行控件
label_dict = ttk.Label(top_frame, text="词       典:")
label_dict.grid(row=0, column=0, padx=PADDING, pady=PADDING, sticky='e')

combo_dict = ttk.Combobox(top_frame, width=40)
combo_dict.grid(row=0, column=1, padx=PADDING, pady=PADDING, sticky='ew')
# 添加下拉菜单选择事件绑定
combo_dict.bind('<<ComboboxSelected>>', lambda e: refresh_dict_entries(combo_dict.get()))

button_choose_dict = ttk.Button(top_frame, text="选择文件", command=on_choose_dict_button_click)
button_choose_dict.grid(row=0, column=2, padx=PADDING, pady=PADDING, sticky='ew')

button_clear = ttk.Button(top_frame, text="清空历史", command=on_clear_button_click)
button_clear.grid(row=0, column=3, padx=PADDING, pady=PADDING, sticky='ew')

# 在top_frame中重新布局第2行控件
label_query = ttk.Label(top_frame, text="编码/词汇:")
label_query.grid(row=1, column=0, padx=PADDING, pady=PADDING, sticky='e')

entry_query = ttk.Entry(top_frame)
entry_query.grid(row=1, column=1, padx=PADDING, pady=PADDING, sticky='ew')

match_mode_frame = ttk.Frame(top_frame)
match_mode_frame.grid(row=1, column=2, padx=PADDING, pady=PADDING, sticky='ew')

exact_match_radio = ttk.Radiobutton(match_mode_frame, text="全匹配", variable=match_mode, value="exact")
partial_match_radio = ttk.Radiobutton(match_mode_frame, text="部分匹配", variable=match_mode, value="partial")
exact_match_radio.pack(side=tk.LEFT, padx=2)
partial_match_radio.pack(side=tk.LEFT, padx=2)

button_query = ttk.Button(top_frame, text="查询", command=on_query_button_click)
button_query.grid(row=1, column=3, padx=PADDING, pady=PADDING, sticky='ew')

# 创建一个框架来容纳所有按钮，使它们居中对齐
button_frame = ttk.Frame(root)  # 改用ttk.Frame
button_frame.grid(row=7, column=0, columnspan=6, pady=PADDING*2)  # 扩大columnspan

# 使用ttk.Button替换tk.Button，并增加按钮宽度
button_add = ttk.Button(button_frame, text="添加", command=on_add_button_click, width=15)
button_add.pack(side=tk.LEFT, padx=PADDING*3)

button_modify = ttk.Button(button_frame, text="修改", command=on_modify_button_click, width=15)
button_modify.pack(side=tk.LEFT, padx=PADDING*3)

button_delete = ttk.Button(button_frame, text="删除", command=on_delete_button_click, width=15)
button_delete.pack(side=tk.LEFT, padx=PADDING*3)

button_save = ttk.Button(button_frame, text="保存", command=on_save_button_click, width=15)
button_save.pack(side=tk.LEFT, padx=PADDING*3)

button_deploy = ttk.Button(button_frame, text="部署", command=on_deploy_button_click, width=15)
button_deploy.pack(side=tk.LEFT, padx=PADDING*3)

# 配置根窗口的列权重，使布局更加灵活
root.grid_columnconfigure(1, weight=1)

# 在查询（编码或词条）下方显示原词典的第一条词条
label_first_entry = tk.Label(root, text="第一条词条: 无", fg="red", font=DEFAULT_FONT)
label_first_entry.grid(row=2, column=0, columnspan=4, padx=5, pady=5)

# 创建词典条目显示部分
columns = ("词汇（text）", "编码（code）", "权重（weight）", "编码2（stem）")
tree = ttk.Treeview(root, columns=columns, show="headings", height=8, selectmode='extended')  # 添加 selectmode='extended'
style = ttk.Style()
style.configure("Treeview.Heading", font=HEADING_FONT)  # 设置所有表头的字体
style.configure("Treeview", font=DEFAULT_FONT)         # 设置表格内容的字体

for col in columns:
    tree.heading(col, text=col)  # 移除了直接设置字体的部分
tree.grid(row=3, column=0, columnspan=4, padx=5, pady=5)
tree.bind("<<TreeviewSelect>>", on_tree_select)

# 创建一个框架来容纳输入部分
input_frame = ttk.Frame(root)
input_frame.grid(row=4, rowspan=2, column=0, columnspan=6, sticky='ew', padx=PADDING, pady=PADDING)

# 配置input_frame的列权重
input_frame.grid_columnconfigure(1, weight=2)  # 第一个输入框列
input_frame.grid_columnconfigure(3, weight=2)  # 第二个输入框列
input_frame.grid_columnconfigure(5, weight=1)  # 切换按钮列

# 在input_frame中重新布局输入控件
label_word = ttk.Label(input_frame, text="词汇:")
label_word.grid(row=0, column=0, padx=PADDING, pady=PADDING, sticky='e')

entry_word = ttk.Entry(input_frame)
entry_word.grid(row=0, column=1, padx=PADDING, pady=PADDING, sticky='ew')

label_code = ttk.Label(input_frame, text="编  码:")
label_code.grid(row=0, column=2, padx=PADDING, pady=PADDING, sticky='e')

entry_code = ttk.Entry(input_frame)
entry_code.grid(row=0, column=3, padx=PADDING, pady=PADDING, sticky='ew')

label_weight = ttk.Label(input_frame, text="权重:")
label_weight.grid(row=1, column=0, padx=PADDING, pady=PADDING, sticky='e')

entry_weight = ttk.Entry(input_frame)
entry_weight.grid(row=1, column=1, padx=PADDING, pady=PADDING, sticky='ew')

label_code2 = ttk.Label(input_frame, text="编码2:")
label_code2.grid(row=1, column=2, padx=PADDING, pady=PADDING, sticky='e')

entry_code2 = ttk.Entry(input_frame)
entry_code2.grid(row=1, column=3, padx=PADDING, pady=PADDING, sticky='ew')

# 切换按钮放在input_frame中
switch_button = ttk.Checkbutton(input_frame, text="编码-权重", variable=switch_order,
                               command=lambda: refresh_dict_entries(combo_dict.get()))
switch_button.grid(row=0, column=5, padx=PADDING, pady=PADDING, sticky='w')

enable_code2_button = ttk.Checkbutton(input_frame, text="显示编码2", variable=enable_code2,
                                     command=lambda: refresh_dict_entries(combo_dict.get()))
enable_code2_button.grid(row=1, column=5, padx=PADDING, pady=PADDING, sticky='w')


# 主循环开始前调用更新函数
update_combo_dict() 

# 运行主循环
root.mainloop()
