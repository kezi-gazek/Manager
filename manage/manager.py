import json
import requests
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta

# 需要排除的非活动字段
EXCLUDED_FIELDS = [
    "您的微信号", "想说的话", "判断", "扫码交社费", 
    "您来到爱心社希望收获", "您来到爱心社希望收获：其他","（旧题）",
    "主要活动的部组（多选）", "骨干", "入社日期", "姓名", "学号", "年级", "性别", "院系"
]

# 活动到反馈表的映射
ACTIVITY_FEEDBACK_MAP = {
    "2025暑修社史": "tblwatMzzNIg79pp",
    '2025秋社刊美编':'tblu7KQSebGtkPbY',
    '9.09手工x海淀团委':'tblV3D5hQtH2u7y9',
    "2025秋百团大战":"tblr5kAZxK0eU3ZN",
    "2025秋迎新大会":"tbleSdFN5iQ5hqql",
    "2025秋社庆":"tbl6CN0bIuUvpH5c",
    "2025秋收衣服":"tbl2b6lTEihx5MMs",
    "2025秋定向越野":"tblDT2e4VYVRXxxx",
    "2025秋社办整理":"tblLhFZDP3Smm6j2",
    "2025秋周边征订与发放":"tblnXVc3VQDhjwn0",
    "2025秋游":"tbljB20axcFQLyga",
    "2025暑苹果北大行":"tblgCIUX1f3Masm5",
    "2025暑资助部电访":"tblmBaPRWLMMDWgT",
    '2025暑王搏计划走访':'tblG5s8CyTQFd1Oe',
    "2025秋河北计划十一走访":"tblohlhZpCL4tCuK",
    "2025秋联络资助人":"tblqs99pEzh7XQmi",
    "2025秋友伴我行书信活动":"tblZ7gn7VIut1w8g",
    "2025秋友伴我行线下活动":"tblhZAbDiqnOhZ2f",
    "2025秋王搏计划影展":"tbli1bx3nSLbW1uX",
    "2025秋河北计划讲座":"tblu55MQza5nG4s9",
    "2025蒲公英支教":"tblSAg9XFeDDCemv",
    "2025儿童之家":"tbleo0cd0JCWqjao",
    "2025同心活动":"tblaiSue8q3UL0Xk",
    "2025心障关怀":"tbl0vRlv9k1C21ad",
    "2025海豚乐乐":"tbl25fXAzpa1vktZ",
    "2025乡镇学堂":"tbl5X2BndS1SE0gj",
    "2025秋中医药文化进校园活动":"tbl0coPekbAr8D92",
    "2025秋敬老院活动":"tblZpgbczef3891J",
    "2025秋智能手机教学":"tblJa0JBjkEYvXYO",
    "2025秋入户陪伴活动":"tblQgWfWcJ1tWwoz",
    "2025秋护老周":"tblumfhfNHjaQQRq",
    "2025秋人生回忆录":"tblPrN3wxvRyOEzC",
    "2025秋视频拍摄&剪辑培训":"tblI4hJryPqBZcHZ",
    "9.13守望星空影展":"tblj972yK3WmBLC3",
    "2025秋金盲杖":"tblB74WxX7708aKd",
    "2025秋温馨家园":"tblHyvs5bWUwKgEd",
    "2025秋教英语":"tbloJuVXxu7Mk9We",
    "2025秋图书校对":"tblbJgXM8ez2hIQK",
    "2025秋无障碍茶会":"tblFnwoiVE4C0QJ1",
    "2025秋盲文小团":"tblLboOXFqwTHo81",
    "2025秋守望星空":"tblQrJ0NajzSvd2O",
    "2025秋无障碍素拓":"tblRTFLHDADtOlax",
    "2025秋罕见病群体交流":"tblwOmSFeQNiNkXn",
    "9.20北京天文馆无障碍交流活动":"tbl1ifyIewQaqtRt",
    "9.12-9.14福祉博览会展览":"tblcIDBLNKMQ2U47",
    "2025秋百团快闪":"tblsVkYmBLyQcGFT",
    "2025秋再回首手语班":"tblr2zj9g5f7GqSu",
    "2025秋聋听交流":"tblGsO4jYiAaoi5q",
    "2025秋燕园浮生手语班":"tbleB7SQQOUsKfVE",
    "2025秋手随歌舞手语角":"tblHeNUD64rj5s3C",
    "2025秋初相见手语班":"tbldAv2wNn3VMet8",
    "2025秋第二十九届万里行茶话会":"tblhMI9ExnSS0PW8",
    "2025秋万里行茶话会":"tblLTQBetLiw0ecx",
    "2025秋项目组面试":"tblaRILhQasCbOCE",
    "2025秋万里行纪念品制作":"tblOPr3RxhG5DTJ0",
    "2025秋项目组修史":"tblxdgjpH3clJXnj",
    "2025万里行学校征集":"tblacJmKsE51nXQK",
    "2025万里行学校考察":"tblq44HLbcAMZV2w"
}

def get_tenant_access_token(app_id, app_secret):
    """获取飞书访问令牌"""
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    payload = json.dumps({
        "app_id": app_id,
        "app_secret": app_secret
    })
    headers = {'Content-Type': 'application/json'}
    response = requests.request("POST", url, headers=headers, data=payload)
    result = response.json()
    if result.get("code") == 0:
        return result['tenant_access_token']
    else:
        raise Exception(f"获取访问令牌失败: {result.get('msg')}")

def get_bitable_datas(tenant_access_token, app_token, table_id, page_token='', page_size=500):
    """获取多维表格数据（支持分页）"""
    # 使用URL参数而不是请求体传递分页参数
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/search?page_size={page_size}"
    
    if page_token:
        url += f"&page_token={page_token}"
    
    # 添加user_id_type参数
    url += "&user_id_type=user_id"
    
    # 使用空请求体
    payload = json.dumps({})
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {tenant_access_token}'
    }
    
    response = requests.request("POST", url, headers=headers, data=payload)
    result = response.json()
    return result

def get_all_records_from_table(tenant_access_token, app_token, table_id):
    """从指定表格获取所有记录（使用分页机制）"""
    all_items = []
    page_token = ''
    has_more = True
    page_count = 0
    
    # 使用while循环获取所有分页数据
    while has_more:
        page_count += 1
        st.info(f"正在获取第 {page_count} 页数据...")
        
        # 获取当前页数据
        result = get_bitable_datas(tenant_access_token, app_token, table_id, page_token)
        
        if result.get("code") != 0:
            error_msg = result.get("msg", "未知错误")
            raise Exception(f"获取数据失败 (第{page_count}页): {error_msg}")
        
        data = result.get("data", {})
        items = data.get("items", [])
        all_items.extend(items)
        
        # 检查是否有更多数据
        has_more = data.get("has_more", False)
        page_token = data.get("page_token", '')
        
        # 添加短暂延迟避免API限制
        import time
        time.sleep(0.05)
        
        # 安全限制：最多获取25页数据（2500条记录）
        if page_count >= 25:
            st.warning("已达到最大页数限制（25页），停止获取更多数据")
            break
    
    return all_items

def extract_text_from_field(value):
    """从飞书字段中提取纯文本"""
    if value is None:
        return ""
    
    # 如果是列表，处理每个元素
    if isinstance(value, list):
        texts = []
        for item in value:
            if isinstance(item, dict) and 'text' in item:
                texts.append(item['text'])
            elif isinstance(item, str):
                texts.append(item)
        return ", ".join(texts)
    
    # 如果是字典，尝试提取text字段
    if isinstance(value, dict) and 'text' in value:
        return value['text']
    
    # 其他情况，直接转换为字符串
    return str(value)

def parse_date(date_str):
    """解析日期字符串，支持多种格式"""
    if not date_str:
        return None

    # 转换为秒级时间戳（除以1000）
    timestamp_seconds = int(date_str) / 1000

    # 转换为datetime对象（默认使用本地时区）
    dt_object = datetime.fromtimestamp(timestamp_seconds)

    # 格式化为 "XXXX/XX/XX" 格式
    formatted_date = dt_object.strftime("%Y/%m/%d")
    date_obj = datetime.strptime(formatted_date, "%Y/%m/%d")
    try:
        return date_obj
    except ValueError:
        return None

def get_activity_records_in_timeframe(tenant_access_token, app_token, activity_name, table_id, start_date, end_date):
    """获取指定时间段内的活动记录"""
    # 获取该活动的所有记录
    all_items = get_all_records_from_table(tenant_access_token, app_token, table_id)
  
    # 筛选在指定时间段内的记录
    filtered_items = []
    for item in all_items:
        fields = item.get("fields", {})

        record_date_str = fields.get("填写日期", "")
        
        # st.write(record_date_str)
        if not record_date_str:
            continue
            
        record_date = parse_date(str(record_date_str))
        # st.write(record_date)

        if record_date and start_date <= record_date <= end_date:
            # 提取参与者信息
            name_data = fields.get("姓名", [{}])
            name = name_data[0].get("text", "") if name_data and isinstance(name_data, list) else ""
            
            student_id = fields.get("学号", "")
            
            # 提取反馈内容
            problem = extract_text_from_field(fields.get("遇到的问题", ""))
            problem_other = extract_text_from_field(fields.get("遇到的问题-其他", ""))
            improvement = extract_text_from_field(fields.get("具体问题/改进措施", ""))
            
            # 提取感想内容（查找包含"感想"的字段）
            reflection = ""
            for key, value in fields.items():
                if "感想" in key:
                    reflection = extract_text_from_field(value)
                    break
            
            # 提取志愿学时
            volunteer_hours = extract_text_from_field(fields.get("志愿学时", ""))
            
            filtered_items.append({
                "活动名称": activity_name,
                "填写日期": record_date,
                "姓名": name,
                "学号": student_id,
                "遇到的问题": problem,
                "遇到的问题-其他": problem_other,
                "具体问题/改进措施": improvement,
                "感想": reflection,
                "志愿学时": volunteer_hours
            })
    
    return filtered_items

# Streamlit界面
st.set_page_config(page_title="社团活动记录查询系统（组织者版）", layout="wide")
st.title("🎯 社团活动记录查询系统（组织者版）")

# 应用配置
app_id = 'cli_a84f183c3ff8100d'
app_secret = 'b8ELILD9IqaaYFbOOB6L2cyX6oODLczj'
app_token = 'NPcMbmMI6a06jmsaXoscwLcqnBf'

# 初始化session state
if 'tenant_access_token' not in st.session_state:
    st.session_state.tenant_access_token = None
if 'activity_records' not in st.session_state:
    st.session_state.activity_records = None

# 查询界面
st.subheader("活动记录查询")
st.info("请选择时间段查询活动记录")

# 日期选择器
col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("开始日期", datetime.now() - timedelta(days=30))
with col2:
    end_date = st.date_input("结束日期", datetime.now())

# 活动选择（多选）
selected_activities = st.multiselect(
    "选择要查询的活动（不选则查询所有活动）",
    list(ACTIVITY_FEEDBACK_MAP.keys()),
    default=[]
)

# 搜索功能
if st.button("查询活动记录"):
    with st.spinner("正在查询..."):
        try:
            # 获取访问令牌
            if st.session_state.tenant_access_token is None:
                st.session_state.tenant_access_token = get_tenant_access_token(app_id, app_secret)
            
            # 确定要查询的活动
            activities_to_query = selected_activities if selected_activities else list(ACTIVITY_FEEDBACK_MAP.keys())
            
            # 获取所有选定活动的记录
            all_records = []
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i, activity_name in enumerate(activities_to_query):
                table_id = ACTIVITY_FEEDBACK_MAP.get(activity_name)
                if not table_id:
                    continue
                
                status_text.text(f"正在查询 {activity_name} 的记录...")
                progress_bar.progress((i + 1) / len(activities_to_query))
                
                records = get_activity_records_in_timeframe(
                    st.session_state.tenant_access_token,
                    app_token,
                    activity_name,
                    table_id,
                    datetime.combine(start_date, datetime.min.time()),
                    datetime.combine(end_date, datetime.max.time())
                )
                
                all_records.extend(records)
            
            progress_bar.empty()
            status_text.empty()
            
            # 保存到session state
            st.session_state.activity_records = all_records
            
            if all_records:
                st.success(f"成功获取 {len(all_records)} 条活动记录")
            else:
                st.info("在选定时间段内未找到活动记录")
        
        except Exception as e:
            st.error(f"查询过程中发生错误: {e}")

# 显示查询结果
if st.session_state.activity_records is not None:
    st.subheader("查询结果")
    
    if st.session_state.activity_records:
        # 转换为DataFrame以便显示和导出
        df = pd.DataFrame(st.session_state.activity_records)
        
        # 显示数据
        st.dataframe(df)
        
        # 统计信息
        st.subheader("统计信息")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("总记录数", len(df))
        with col2:
            st.metric("活动数量", df["活动名称"].nunique())
        with col3:
            st.metric("参与人数", df["姓名"].nunique())
        
        # 按活动分组的统计
        st.subheader("按活动分组统计")
        activity_stats = df.groupby("活动名称").agg({
            "姓名": "count",
            "志愿学时": lambda x: sum(pd.to_numeric(x, errors='coerce').fillna(0))
        }).rename(columns={"姓名": "参与人次", "志愿学时": "总学时"})
        st.dataframe(activity_stats)
        
        # 导出功能
        st.subheader("导出数据")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("导出所有记录"):
                csv = df.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label="下载CSV文件",
                    data=csv,
                    file_name=f"活动记录_{start_date}_{end_date}.csv",
                    mime="text/csv"
                )
        
        with col2:
            if st.button("导出统计信息"):
                csv = activity_stats.to_csv(encoding='utf-8-sig')
                st.download_button(
                    label="下载统计CSV",
                    data=csv,
                    file_name=f"活动统计_{start_date}_{end_date}.csv",
                    mime="text/csv"
                )
    else:
        st.info("在选定时间段内未找到活动记录")

# 添加使用说明
st.sidebar.title("使用说明")
st.sidebar.info("""
1. 选择要查询的时间段
2. 可选择特定活动或查询所有活动
3. 点击"查询活动记录"按钮获取数据
4. 查看结果并可以导出为CSV文件

**注意**：系统会查询所有选定活动的反馈记录，可能需要一些时间。
""")

# 添加隐私声明
st.sidebar.title("隐私声明")
st.sidebar.warning("""
本系统仅用于社团内部管理，请妥善保管查询到的信息。
个人信息将严格保密，不得用于其他用途。
""")

# 添加重置按钮
if st.sidebar.button("重置查询"):
    st.session_state.activity_records = None

    st.experimental_rerun()
