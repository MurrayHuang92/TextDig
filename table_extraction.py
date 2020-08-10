from docx import Document
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.table import _Cell, Table
from docx.text.paragraph import Paragraph
import re
from pandas import DataFrame
import numpy as np
import docx
from functools import reduce
import pandas as pd



# 方法iter_block_items， read_table， trim_table_to_df， notes_extraction相关问题请咨询：王正亭WANGZHENGTING612

def iter_block_items(file):
	"""
	获取Word当中的表格及段落并维持其原本的段落顺序.
	首先获取docx文档中的每个element
	将Paragraph对象的文本提取出来保存在结果列表中
	将Table对象保存在结果列表中,Table对象的值需要逐个Cell读取
	"""
	res = []
	for child in file.element.body:
		if isinstance(child, CT_P):
			res.append(Paragraph(child, Document).text)
		elif isinstance(child, CT_Tbl):
			res.append(Table(child, Document))
	return res

def read_table(table):
	""""逐行读取Table中的Cell对象文本属性,将结果存在一个二维列表当中"""
	res = []
	for row in table.rows:
		tmp = []
		for cell in row.cells:
			tmp.append(cell.text)
		res.append(tmp)
	return res

def trim_table_to_df(table):
	
	if len(table) == 0:
		return DataFrame()
	
	# locate the row that data appears
	namePattern = re.compile(u"[\u4e00-\u9fa5]+")
	data_start_idx = 0
	for row in range(len(table)):
		for col in range(1,len(table[row])):
			if not namePattern.search(str(table[row][col])):
				data_start_idx = row
				break
		if not namePattern.search(str(table[row][col])):
			break
				

	header_list = []
	
	for col in range(0,len(table[row])):
		curr_col = ''
		aggr_col = ''
		for row in range(data_start_idx):
			if curr_col != table[row][col]:
				if aggr_col == '':
					aggr_col = table[row][col]
				else:
					aggr_col = aggr_col + '-' + table[row][col]
				curr_col = table[row][col]
		header_list += [aggr_col]
	
	table_list = []
	for row in range(data_start_idx, len(table)):
		row_list = []
		for col in range(len(table[row])):
			row_list += [table[row][col]]
		table_list += [row_list]
	
	df = DataFrame(table_list,columns=header_list)
	return df

def notes_extraction(file_name):
	
	
	document = Document(file_name)
	
	block_list = iter_block_items(document)

	result_list = []
	table_cnt = 0
	
	for index in range(2,len(block_list)):
		
		table = block_list[index]
		table_name = []
		df = DataFrame()
		if type(table) == type(Table('',CT_Tbl)):
			table_fmt = read_table(table)
			df = trim_table_to_df(table_fmt)
#             if (block_list[index-1] == '（续）' or block_list[index-1] == '' )and type(block_list[index-2]) == type(Table('',CT_Tbl)):
			if (block_list[index-1] == '') and type(block_list[index-2]) == type(Table('',CT_Tbl)):
				table_ext = read_table(block_list[index-2])
				df = trim_table_to_df(table_ext)
				result_list += [(file_name, result_list[table_cnt-1][1], df)]
			elif type(block_list[index-1]) == type('') and type(block_list[index-2]) == type(Table('',CT_Tbl)):
				table_name = [block_list[index-1]]
				result_list += [(file_name, table_name, df)]
			elif type(block_list[index-1]) == type('') and type(block_list[index-2]) == type(''):
				table_name = [block_list[index-2],block_list[index-1]]
				result_list += [(file_name, table_name, df)]
			table_cnt += 1

	return result_list






# 下面所有方法有问题找我：黄旷HUANGKUANG359


#标题寻址方法区
level1 = re.compile('^第[一二三四五六七八九十]{1,3}节|^(附注[一二三四五六七八九十]{1,3}、)')
level2 = re.compile('^[一二三四五六七八九十]{1,3}、')
level3 = re.compile('^（[一二三四五六七八九十]{1,3}）')
level4 = re.compile('^\d{1,2}、')
level5 = re.compile('^（\d{1,2}）')
level6 = re.compile('^\d{1,2}）')
level7 = re.compile('^[①②③④⑤⑥⑦⑧⑨⑩]')
level_list=[level1, level2, level3, level4, level5, level6, level7]

# 取标题的层级级数
def find_level(title):
	global level_list
	if len(level_list) == 0:
		print('层级规则列表未初始化')
		return -1
	result_list = list(map(lambda x: True if x>0 else False, [len(re.findall(pat, title)) for pat in level_list]))
#     print(result_list)
	if any(result_list):
		return result_list.index(True)
	# 非标题，用于跳过
	return -1

# 向上（段落上方）追溯标题，相邻标题
def last_title(title, index=-1):
	# index为-1是首次调用方法last_title,非-1为递归调用last_title
	if title.replace('\n','').strip()=='' and index==-1:
		print('不接受首个输入参数为空值')
		return None
	if find_level(title)==-1 and index==-1:
		print('不接受首个输入参数为非标题')
		return None
	try:
		#通过值去找index是不靠谱的，应按照首次确定的索引连续向前递归
		if index == -1:
			current_index = paras.index(title)
		else:
			current_index = index
		potencial_index = current_index-1
		if potencial_index < 0:
			print('index超出，上溯强制结束')
			# 跳出界的不应该是返回为空，而是返回'end'作为特殊结果
			return 'end'
		potencial_title = paras[potencial_index]
		if find_level(potencial_title)==-1:
			return last_title(potencial_title, potencial_index)
		else:
			return potencial_title
	except:
		print(f'{title}在原文中未定位准确')
		return None
	
# 向根节点追溯（向层级高阶方向）
def dateback_to_root(current_nearest_title, title_chain=[]):
	if title_chain==[]:
		title_chain.append(current_nearest_title)
	level = find_level(current_nearest_title)
	if level == -1:
		print(f'输入[{current_nearest_title}]不是标题')
		return title_chain
	
	if level != 0:# 未抵达根结点标题
		#寻找最邻近高阶标题
		
		
		lasttitle = current_nearest_title
		while True:# 如何保证死循环的上限
			lasttitle = last_title(lasttitle)
			if lasttitle=='end':
				return title_chain
			neighbor_level = find_level(lasttitle)
			if lasttitle == None:
				print('上溯出错')
				return title_chain
			if neighbor_level<level: # 找到邻近高阶
				title_chain.append(lasttitle)
				break
		return dateback_to_root(lasttitle, title_chain)            
	else:
		print('抵达根节点')
		return title_chain

# 条目抽取
# 优先假设一： 首列的内容是科目，跳过<投资性房地产>,<固定资产>,<无形资产>等特殊附注表格考虑转置
# 重要假设二： -号连接的列头具有层级包含关系
# 重要假设三： 所有财务类附注都在附注五，其他附注均为无用附注
def need_transpose(elemt):
	if type(elemt)!=tuple:
		print('请传入提取结果列表内容')
		return None
	topics = elemt[1]
	# 这个逻辑判断不准确， 暂【搁置】
	if any([('投资性房地产' in e) for e in topics]) or any([('固定资产' in e) for e in topics]) or any([('无形资产' in e) for e in topics]):
		return True
	return False

def T(df):
	dt = df.transpose()
	firstrow=list(dt.iloc[0])
	dt.columns=firstrow
	dt.drop(dt.index[0],inplace=True)
	dt.rename(columns={'index':list(d.columns)[0]},inplace=True,level=0)
	return dt

def need_add_header(df):
	return ''.join(list(df.columns)).strip()==''

def add_header(df):
	df.columns=list(df.loc[0,:])
	df.drop(0,inplace=True)
	df.reset_index(inplace=True)
	df.drop(columns=['index'],axis=1,inplace=True)
	return df

# 判断表前的语句是否包含新topic
def need_new_topic(elemt):
	pass

# 粗topic列表转化为全话题链条
def topic_chain(topics:list):
	# 最重要的是确定列表中最小标题的那一个
	if len(topics)==0:
		return '无topic'
	
	topics = [t.replace(' ','').strip() for t in topics]
#     print(topics)
	smallest_topic=''
	if len(topics)==1:
		smallest_topic = topics[0]
		if find_level(smallest_topic)==-1:
			return smallest_topic
		else:
			return ' <--- '.join(dateback_to_root(smallest_topic,[]))
	else:
		# level 排序问题
		dark_list=[(find_level(title),title) for title in topics]
		tt=max(dark_list)
		smallest_topic = tt[1]
		print(smallest_topic)
		return ' <--- '.join(dateback_to_root(smallest_topic,[]))
		
	# 假设一：无编号标题是离表最近的描述性语句
	# 在有编号的标题中找到level最大的

def extract(docx_filepath):	
	result_list=notes_extraction(docx_filepath)
	df_lists=[]
	for index, (_,topics,df) in enumerate(result_list):
		try:
			if '' in topics:
				topics.remove('')
			if topics==['（续）'] or topics==['（续表）']:#续表继承前表topic
				topics=result_list[index-1][1]
			item_dim=df.columns[0]
			item_list = []
			# 判断是否需要转置
		#     if (need_transpose(result_list[index])):
		#         df = T(df)
			# 判断无头df
			if need_add_header(df):
				df = add_header(df)
			
			# cell 级别 唯一过滤规则 空值不取
			# 需求点：按照列的顺序排列
			table_headers = df.columns
	#         for rowindex in range(len(df)):
	#             table_row=[]
	#             row = df.loc[rowindex, item_dim]
	#             # 分列成cell
	#             for header in table_headers[1:]: #除开科目dim
	#                 cell_dict={}
	#                 # 按模板定义的命令规则切勿混淆
	#                 cell_dict['col']=header
	#                 cell_dict['row']=row
	#                 cell_dict['val']=df.loc[rowindex, header]
	#                 if cell_dict['val'].strip()=='' or cell_dict['val'].strip()=='-':#跳过空值
	#                     continue
	#                 table_row.append(cell_dict)
	#             item_list.extend(table_row)
			for col_item in table_headers[1:]:
				col_dict={}
				col_dict['col']=col_item
				col_rows=[]
				for rowindex in range(len(df)):
					row_dict={}
					row_dict['row']=df.loc[rowindex, item_dim]
					row_dict['val']=df.loc[rowindex, col_item]
					col_rows.append(row_dict)
				
				col_dict['rows']=col_rows
				item_list.append(col_dict)
			
			row_list=[index, topic_chain(topics), item_dim, item_list]
			df_lists.append(row_list)
			result_df = pd.DataFrame(columns=['item_index','topic_chain','item_dim','eles'], data=df_lists)
			result_df.to_excel('raw_result.xlsx',index=False)
			print(f'结果已写至raw_result.xlsx')
		except:
			# 调试阶段可能会屏蔽许多错误，应在debug阶段注释掉
			print(f'something goes wrong about this dataframe, index at: {index}')
