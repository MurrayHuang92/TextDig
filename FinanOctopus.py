# -*- coding: utf-8 -*- 
import numpy as np
import re
import jieba
import jieba.posseg as pseg

# 分词，POS标签，预处理
def sep_flag_pre(sentence:str):
	# preprocessing
	sentence=sentence.replace(' ','').strip()
	sentence=sentence.replace('；','，').replace('：','，')
	if sentence[-1]=='。':#去除句尾的句号
		sentence=sentence[:-1]
	if sentence[-1]=='，':#去除句尾的逗号
		sentence=sentence[:-1]
	#找到数值中间的逗号
	patcommainnumber = re.compile('(\d,\d)')
	# matcher = re.findall(patcommainnumber,sentence)
	#消除数字中的逗号
	while True:
		m = re.search(patcommainnumber,sentence)
		if m==None:
			break
		s,e = m.span()
		sentence = sentence[:s+1]+sentence[e-1:]
	# 单值子句要为没有谓语的句子的数值前加上谓语
	s_p = sentence.split('，')
	ms = [re.findall(pat_value_word, p) for p in s_p]
	for mi in range(len(ms)):
		if ms[mi]!=[] and len(ms[mi])==1:
			single_value = re.search(pat_value_word, s_p[mi]).group()
			value_index = s_p[mi].index(single_value)
			word_before_value = s_p[mi][value_index-1]
			if word_before_value!='为':
				print(f'[method:sep_flag_pre]已为无谓语句式[{s_p[mi]}]添加谓词前置')
				s_p[mi] = s_p[mi].replace(single_value, '为'+single_value)
				
	sentence = '，'.join(s_p)
	# get pos tags out of sub sentences
	parse_words=[]
	parse_wordsequences=[]
	parse_flagsequences=[]
	sub_sentences = sentence.split('，')
	for sub in sub_sentences:
		words = pseg.cut(sub)
		wordl = '|'.join([x+'【'+y+'】' for x,y in list(words)])
		parse_words.append(wordl)
		wordsequence='|'.join([i[:i.index('【')] for i in wordl.split('|')])
		parse_wordsequences.append(wordsequence)
		# 为了与wordsequence中的下标完全对应
		flagsequence='|'.join([i[i.index('【')+1:i.index('】')] for i in wordl.split('|')])
		parse_flagsequences.append(flagsequence)
	
	return ' '.join(parse_flagsequences), ' '.join(parse_wordsequences), sentence

# 是否需要加入dp前缀，待后设计决定
pat_multi_value = re.compile('((x?mm?x)*x?mm?cx?mm?)')
pat_multi_rate = re.compile('((x?mxx)*x?mxcx?mx)')# 这种情况可能有潜在公式 需再度判断句子是否含有占比前缀（v*ujn）

# 单值赋值
pat_single_value = re.compile('([lvnt]*p((x?mm)|(x?mx)))|(((x?mm)|(x?mx))p[lvnt]*)')

# 带主语的多值
pat_multi_subject_value = re.compile('(([lvnthujxd]*mmx)*[lvnthujxd]*mmc[lvnthujxd]*mm)')

# 是否需要加入dp后缀，待后设计决定
# 占比句子特征：*占*的比重
pat_take_percentage = re.compile('(v[lvnt]*ujn)')

# 假设：值都是有小数点的，此正则针对的是词
pat_value_word = re.compile('(-?\d+\.\d{1,2}%?(万元)?(亿元)?(元)?)')

# 需要转义时间句子特征
cover_time_sample_flags=['lcmt','lcd','fmcmt','fmcd','tcd','tcmt','fmt','fm','nrt']
cover_time_regx='|'.join(cover_time_sample_flags)
pat_cover_time = re.compile(cover_time_regx) # 对应关系后续针对性解析
# 不需转义时间句子特征
# 样例
uncover_time_sample=['2019年1-6月','2016','2017-12-31','2017','2019-6-30','2018年度', '2017年度', '20190106', '2016年度', '2018-12-31', '2016-12-31', '2018','2018 年', '2017年', '2019年6月30日', '2016年', '2018年', '2007年7月', '2007年07月', '2018-12-31/2018年度', '2016-12-31/2016年度', '2019-6-30/2019年1-6月', '2019-06-03/2019年度', '2017-12-31/2017年度', '2017 年', '2018年第 2 季度', '2019 年 1-6 月', '2016 年', '2017年度期末', '2019年6月末', '2016年末', '2018年末', '2017年末', '2019 年 6 月末', '2016年9月7日', '2016年09月07日']
# 消除生成的不稳定的模式的情况，原因：单个数字在-符号中间被标记为x，这是不愿看到的
pat_dateformat = re.compile('(\d{4}-\d{1,2}-\d{1,2})')
def date_standardize(datestring):
    m = re.search(pat_dateformat, datestring)
    if m==None:
        return datestring
    #xxxx-xx-xx xxxx-x-xx xxxx-xx-x xxxx-x-x
    date = m.group(0)
    dates = date.split('-')
    month = dates[1]
    day = dates[2]
    if len(month)!=2:
        month = '0'+month
    if len(day)!=2:
        day = '0'+day
    return datestring.replace(date, '-'.join([dates[0], month, day]))


uncover_time_sample_flags = []
for t in uncover_time_sample:
    flags, _, _ = sep_flag_pre(date_standardize(t))
    flags = flags.replace('|','')
    uncover_time_sample_flags.append(flags)
# 所有样例形成的时间POS组合库, 这将作为规则来找寻时间
uncover_time_sample_flags = list(set(uncover_time_sample_flags))
# 重排序保证优先匹配长规则
uncover_time_sample_flags.sort(key=lambda x: len(x), reverse=True)
# 形成uncover时间正则规则
uncover_time_regx = '|'.join(uncover_time_sample_flags)
pat_uncover_time = re.compile(uncover_time_regx)

# 值变动类句子特征(需要结合uncover的时间正则) 
pat_change_value1 = re.compile('(d('+uncover_time_regx+')vmm)') #日期1科目x较日期2增加/减少数值
# 这种变动类包含取值类句子特征
pat_change_value2 = re.compile('(p('+uncover_time_regx+')ujmmvp('+uncover_time_regx+')ujmm)') #从2014年末的数值1增长/减少至2016年末的数值2
# 比例变动类句子特征(需要结合uncover的时间正则)
pat_change_rate = re.compile('(d('+uncover_time_regx+')vmx)') #日期1科目x较日期2增加/减少比例
# 值与比例形成的公式完全不同



def re_extractor(pat, flags_plain, delimiter, in_model_matrix=True): 
    r=[] 
    for f in flags_plain.split(delimiter):
        blocklist = re.findall(pat, f) 
        if blocklist != []: 
            blocklist=list(map(lambda x: max(x, key=lambda y: len(y)) if type(x)==tuple else x, blocklist)) 
        else: 
            r.append(None) 
            continue 
        
        if len(blocklist)==1: 
            r.append(blocklist[0]) 
        else: 
            if in_model_matrix == True: 
                r.append(blocklist[0]) 
            else: 
                r.append(blocklist) 
        
    return r

# 找第no个ujn
def find_ujn(l, no=1):
    b_no = no
    for i,flag in enumerate(l):
        if flag=='uj' and l[i+1]=='n':
            if no==1:
                return i
            else:
                no -= 1
    print(f'第{b_no}个ujn不存在于该列表中')
    return None


def locate_itemindex_in_take_percentage(flags, index_block, current_regx):
    original_span = current_regx[1: current_regx.index('ujn')]
    print(f'original_span={original_span}')
    # 定位文本对象
    sub_flags=flags.split(' ')[index_block].split('|')
    try:
    # 找到所有可能的ujn
        for hypo in range(1, len(sub_flags)+1):
            index_ujn=find_ujn(sub_flags ,hypo)
            # 比对中间片段
            for i,flag in enumerate(sub_flags):
                if flag=='v':
                    if i<index_ujn:
                        # 取中间字符串
                        middle_span = ''.join(sub_flags[i+1:index_ujn])
                        print(f'当前middle_span={middle_span}')
                        if original_span == middle_span:
                            print(f'found!')
                            return i+1, index_ujn
                    else:
                        print(f'index为{index_ujn}的ujn无效,跳过')
                        break
    except:
        print('something wrong, no output')
    return None


# 方法与上相同
# 如果应用在主语上难以保证general_regx的唯一性，这个方法仅用于时间的挖取
# no代表第no个匹配项
def locate_itemindex_general(flags, index_block, general_regx, no=1):
	#print(f'flags:{flags} index_block:{index_block} general_regx:{general_regx} no:{no}')
	if type(general_regx) == list:
		print('出现了一个多具体时间的列表')
		res_index_list = []
		for rg in general_regx:
			res_index_list.append(locate_itemindex_general(flags, index_block, rg, no))
		return res_index_list
	
	span_len = len(general_regx)
	sub_flags=flags.split(' ')[index_block].split('|')
	try:
		count = 0
		for i,flag in enumerate(sub_flags):
			# 错误的解法 因为不是所有flag都是1位，2位就会扰乱这个逻辑
#             for block in range(span_len):
#                 if flag==general_regx[block]:
#                     # 向后验证
#                     flag=sub_flags[i+1]
#                 else:
#                     break
#                 # 当前循环完美走完说明匹配项找到
#                 return i, i+span_len
			# 反向验证
			move_step = 1
			move_span = ''.join(sub_flags[i: i+move_step])
			while move_span in general_regx:
				if move_span == general_regx:
					count = count + 1
					if no == count:
						return i, i+move_step      
				move_step+=1
				move_span = ''.join(sub_flags[i: i+move_step])
	except:
		print('something wrong, no output')
	
	print(f'第{index_block}句{general_regx}的时间未找到')
	return None
	

# 占比特征识别出时寻找主语（分子）
# 这是一个需要不断扩充的函数
def locate_numeratorindex_in_take_percentage(words, flags, index_block, take_percentage_start_index):
    # 目前考虑四种情况：1.主语全部罗列在本句；2.单主语，需要按照时间展开，在本句
    #                3.非本句，全罗列；   4.单主语，需要按照时间展开，非本句
    res_index=[]
    
    if take_percentage_start_index-1 == 0: #“占”在句首
        # 这得跨句子找
        # 重要假设：所在分句子value数对应
        index_block = index_block - 1
        print(f'向前检查第{index_block}子句')
        last_sent_first_word = words.split(' ')[index_block].split('|')[0]
        print(f'该句句首:{last_sent_first_word}')
        if last_sent_first_word != '占':
            return locate_subjectindex_general(words, flags, index_block)
        return locate_numeratorindex_in_take_percentage(words, flags, index_block, 1)
    else:
        # 切分新子句
        before_subflags = flags.split(' ')[index_block].split('|')[0:take_percentage_start_index-1]
        # 是否有多值
        expr = before_subflags.count('c')>=1 and before_subflags.count('x')>=1
#         if m!=None:# 有多值 不以正则表达式作为判断依据
        if expr:
            # 挖值
            # 取末尾连接符  方法locate_itemindex_general无意义
#             last_c_index = sub_regx[::-1].index('c')
#             subject_flag_list = sub_regx[:len(sub_regx)-last_c_index-1].split('x')
#             subject_flag_list.append(sub_regx[len(sub_regx)-last_c_index:])
#             print(f'多值主语flags: {subject_flag_list}')
#             for subject_flag in subject_flag_list:
#                 res_index.append(locate_itemindex_general(index_block, subject_flag))
            base_index = 0 # 这也是一种极端假设
            # how many x there are?
            num_x = before_subflags.count('x')+1
            for i in range(num_x):
                if i == 0:
                    print('first')
                    s_i = base_index
                    e_i = before_subflags.index('x')
                    
                else:
                    try:
                        print('middle')
                        s_i = e_i + 1
                        e_i = s_i + before_subflags[s_i: ].index('x')
                        
                    except:
                        print('end')
                        s_i = e_i + 1
                        e_i = s_i + before_subflags[::-1].index('x') - before_subflags[::-1].index('c') - 1
                        res_index.append((s_i, e_i))
                        s_i = e_i + 1
                        e_i = s_i + before_subflags[::-1].index('c')
                        res_index.append((s_i, e_i))
                        break
                res_index.append((s_i, e_i))
            return index_block, res_index
        else: # 单值, 要按照时间scale up, 在gearup函数中
            base_index = 0 # 这也是一种极端假设
            return index_block, (base_index, take_percentage_start_index-1)


def locate_subjectindex_general(words, flags, index_block, baseindex=0,no=1): # 粗略地确定一个分句的主语
	print(f'[method:locate_subjectindex_general]开始定位第{index_block}句主语')
	#baseindex=0 # 重要假设：主语从句首开始
	sub_flags = flags.split(' ')[index_block].split('|')
	count = 0
	def return_subjectindex(words, index_block, baseindex, i, no):
		# 得到的主语索引需要验证，如果clean后的主语变空了则需要往后找谓语前的名词
		if baseindex<i:
			name = from_index_to_span(words, index_block, (baseindex, i))
			if clean_subject(name) == '':
				no += 1
				return locate_subjectindex_general(words, flags, index_block, baseindex, no)
			return index_block, (baseindex, i)
		else:
			name = from_index_to_span(words, index_block, (i+1, baseindex))
			if clean_subject(name) == '':
				no += 1
				return locate_subjectindex_general(words, flags, index_block, baseindex, no)
			return index_block, (i+1, baseindex)
		
	# 主语规则： 在dp,bp,d或p前的子句部分 类似于一种公式中的等式和集合中的从属符号
	for i,flag in enumerate(sub_flags):
		if flag == 'd' and sub_flags[i+1] == 'p':
			print('[method:locate_subjectindex_general]优先匹配dp前字段')
			if i==0: # 句首 则 跳句
				index_block = index_block - 1
				return locate_subjectindex_general(words, flags, index_block, baseindex)
			count += 1
			if count == no:
				return return_subjectindex(words, index_block, baseindex, i, no)
		
	for i,flag in enumerate(sub_flags):
		if flag == 'b' and sub_flags[i+1] == 'p':
			print('[method:locate_subjectindex_general]次优先匹配bp前字段')
			if i==0: # 句首 则 跳句
				index_block = index_block - 1
				return locate_subjectindex_general(words, flags, index_block, baseindex)
			count += 1
			if count == no:
				return return_subjectindex(words, index_block, baseindex, i, no)
	
	for i,flag in enumerate(sub_flags):
		if flag == 'p':
			print('[method:locate_subjectindex_general]再次先匹配p前字段')
			if i==0: # 句首 则 跳句
				index_block = index_block - 1
				return locate_subjectindex_general(words, flags, index_block, baseindex)
			count += 1
			if count == no:
				return return_subjectindex(words, index_block, baseindex, i, no)
	
	for i,flag in enumerate(sub_flags):
		if flag == 'd':
			print('[method:locate_subjectindex_general]再次匹配d前字段')
			if i==0: # 句首 则 跳句
				index_block = index_block - 1
				return locate_subjectindex_general(words, flags, index_block, baseindex)
			count += 1
			if count == no:
				return return_subjectindex(words, index_block, baseindex, i, no)
	
	
	# 没有谓语 继续向前
	index_block = index_block - 1
	return locate_subjectindex_general(words, flags, index_block, baseindex)


def from_index_to_span(words, index_block, args):
	words_list = words.split(' ')[index_block].split('|')
	if type(args)==tuple:
		start_index, end_index = args
		res_string = ''.join(words_list[start_index: end_index])
		return res_string
	
	if type(args)==list:
		res_list = []
		for start_index, end_index in args:
			res_list.append(''.join(words_list[start_index: end_index]))
		return res_list
	
	print('Unknown type args: {args}')
	return None


def pick_value_regx_out(value_block):
    if value_block==None:
        return value_block
    if type(value_block) == str:
        value_block = [value_block]
        
    return [''.join([y for x,y in list(pseg.cut(value))]) for value in value_block]


def find_time_regx(values, flags_plain, index_block, pat_time, pat_type):
	print(f'[method:find_time_regx->start]---pat_time:{pat_time} pat_type:{pat_type}')
	time_regx_list=re_extractor(pat_time, flags_plain, ' ', pat_type) 
	if pat_type==False: #uncover
		# 取出 index_block前所有的value的regx
		value_block_regx_list_before_indexblock = [pick_value_regx_out(values[ib]) for ib in range(index_block+1)]
		print(f'[method:find_time_regx]---value_block_regx_list_before_indexblock:{value_block_regx_list_before_indexblock}')
		# 把value regx都扣掉
		time_regx_list=re_extractor(pat_time, flags_plain, ' ', pat_type)
		print(f'[method:find_time_regx]---扣值前time_regx_list:{time_regx_list}')
		time_regx_list_temp=[]
		for irl in range(index_block+1):
			if value_block_regx_list_before_indexblock[irl] != None:
				for r in value_block_regx_list_before_indexblock[irl]:
					print(f'[method:find_time_regx]----从当前值正则列表中取出{r}')
					# mx 的值在原句中识别为单m 
					if r == 'mx' or r == 'xmx':
						r = 'm'
					if r == 'xmm':
						r = 'mm'
					try:
						print(f'[method:find_time_regx]----当前time_regx_list[{irl}]是{time_regx_list[irl]}')
						if type(time_regx_list[irl]) == list:
							time_regx_list[irl].remove(r)
						else:
							if time_regx_list[irl]==r:
								time_regx_list[irl] = None
					except:
						print(f'[method:find_time_regx]-----{r} 不在')
						if r == 'mx':
							time_regx_list[irl].remove('m')
				if time_regx_list[irl] == []:
					time_regx_list[irl] = None
				if time_regx_list[irl] != None and len(time_regx_list[irl])==1:
					time_regx_list[irl] = time_regx_list[irl][0]
			time_regx_list_temp.append(time_regx_list[irl])
		time_regx_list = time_regx_list_temp
		print(f'[method:find_time_regx]---扣值后time_regx_list:{time_regx_list}')
	
	else: # cover
		if not any(time_regx_list):
			print('[method:find_time_regx]---无模糊时间匹配，说明有具体时间线')
			return find_time_regx(values, flags_plain, index_block, pat_uncover_time, False)
			
	def find_time_regx_sub(index_block, pat_time): # pat_type 为True表示 cover time    
		print(f'[method:find_time_regx_sub]---time_regx_list:{time_regx_list}, index_block:{index_block}')
		time_regx = time_regx_list[index_block]
		if index_block == 0:
			if type(time_regx)==str:
				return time_regx, index_block
			else:
				print(f'[method:find_time_regx_sub]----time_regx:{time_regx} 是列表')
				return time_regx, index_block

		if time_regx != None:
			return time_regx, index_block
		return find_time_regx_sub(index_block-1, pat_time)
	
	print('[method:find_time_regx->end]')
	return find_time_regx_sub(index_block, pat_time)


def clean_subject(subjectname):
	# 主语优化
	if type(subjectname) == str:
		if subjectname[0:3]=='发行人':
			subjectname = subjectname[3:]
		if subjectname[0:3]=='本公司':
			subjectname = subjectname[3:]
		if subjectname[0:3]=='该公司':
			subjectname = subjectname[3:]
		if subjectname[0:2]=='实现':
			subjectname = subjectname[2:]
		if subjectname[0:2]=='公司':
			subjectname = subjectname[2:]
		if subjectname[0:2]=='其中':
			return clean_subject(subjectname[2:])
		if subjectname!='' and subjectname[-1]=='占':
			subjectname = subjectname[:-1]
	else:
		new_subjectname = []
		for s in subjectname:
			s = clean_subject(s)
			new_subjectname.append(s)
		return new_subjectname
	
	return subjectname

# 模式找寻
# 公式一-占比类： 占x的比重是目前唯一出现需要判断公式的地方
# 公式二-变动类： 日期1科目x较日期2增加/减少数值/比例
# 主语继承，主语穿透
# 归因总结语句假设不重要
# 子句主语识别，以value数为主语数基准
def gearup(flags, words, values, flags_plain, quadraples, index_block, value_block, subjectname, has_formula, related_subjectname=None):
	# 这个方法聚合四元组并解析时间
	print(f'[method:gearup->start]---value_block:{value_block} subjectname:{subjectname} has_formula:{has_formula} related_subjectname:{related_subjectname} ')
	# 对输入进行校验
	if has_formula and related_subjectname==None:
		print('公式涉及元素不全')
		return None
	
	subjectname = clean_subject(subjectname)
	
	if related_subjectname != None:
		related_subjectname = clean_subject(related_subjectname)
	
	# 情况1： 多个主语，那么时间是复用的（找到唯一时间）。重要假设：这种情况的时间是uncover_time
	if type(subjectname) == list:
		print('[method:gearup]----情况1')
		# 从本句开始向前子句找
		time_regx, target_indexblock = find_time_regx(values, flags_plain, index_block, pat_uncover_time, False)
		time_string = from_index_to_span(words, target_indexblock, locate_itemindex_general(flags, target_indexblock, time_regx))
		print(f'[method:gearup]----多主语对应具体时间为: {time_string}')
		if time_string in subjectname:
				subjectname = subjectname.replace(time_string, '')
				subjectname = clean_subject(subjectname)
		# 整理结果
		for ni in range(len(subjectname)):
			quadraple_dict={}
			if has_formula:
				quadraple_dict['item'] = subjectname[ni] + '/' + related_subjectname
			else:
				quadraple_dict['item'] = subjectname[ni]
			quadraple_dict['time'] = time_string
			quadraple_dict['value'] = value_block[ni] # potencial error
			quadraples.append(quadraple_dict)
			
	# 情况2： 单分子/单主语，时间是展开的。重要假设：这种情况的时间是cover_time
	# 情况3： 单主语为变动类模式下，时间是uncover_time
	# 情况4： 单主语为单值模式，时间是uncover_time，无公式
	else:
		print(f'[method:gearup]---related_subjectname:{related_subjectname}, subjectname:{subjectname}, has_formula:{has_formula}')
		#情况3
		if related_subjectname != None and related_subjectname == subjectname: # 变动类 相关主语为其他时间下的subjectname
			print('[method:gearup]----情况3')
			time_regx, target_indexblock = find_time_regx(values, flags_plain, index_block, pat_uncover_time, False)
			print(f'[method:gearup]----单主语[变动特征]对应具体时间正则为: {time_regx}')
			if type(time_regx) == list:
				time_string1 = from_index_to_span(words, target_indexblock, locate_itemindex_general(flags, target_indexblock, time_regx[0], 1))
				time_string2 = from_index_to_span(words, target_indexblock, locate_itemindex_general(flags, target_indexblock, time_regx[1], 2))
			else:
				time_string2 = from_index_to_span(words, target_indexblock, locate_itemindex_general(flags, target_indexblock, time_regx))
				# 以 has_formula 区分是否是 变动1类(True)或者变动2类(False)
				if has_formula:
					# 向前找具体时间
					time_regx, target_indexblock = find_time_regx(values, flags_plain, index_block-1, pat_uncover_time, False)
					if type(time_regx) != list:
						time_string1 = from_index_to_span(words, target_indexblock, locate_itemindex_general(flags, target_indexblock, time_regx))
					else:
						time_string1 = from_index_to_span(words, target_indexblock, locate_itemindex_general(flags, target_indexblock, time_regx[0]))
				else:
					if value_block[-1] != '%': # 以值是百分比还是数额 区分补充语句是独立还是继承
						print('[method:gearup]-----补充语句为独立语句不再上溯时间')
						time_string1 = '无'
					else:
						print('[method:gearup]-----补充语句为进一步解释性语句，沿用变动1类时间以及主语')
#                         time_regx, target_indexblock = find_time_regx(values, flags_plain, index_block-1, pat_uncover_time, False)
						# 默认为 变动1类
#                         time_string1 = from_index_to_span(target_indexblock, locate_itemindex_general(target_indexblock, time_regx))
#                         time_string2 = time_string1
						time_string1 = '沿用'
						time_string2 = '沿用'
					
			print(f'[method:gearup]----单主语[变动特征]对应具体时间为: {time_string1} 和 {time_string2}')
			# 主语中由于是基于假设从句首开始，需要屏蔽时间开头
			if time_string1 in subjectname or time_string2 in subjectname:
				subjectname = subjectname.replace(time_string1, '').replace(time_string2, '')
				subjectname = clean_subject(subjectname)
				
			# 判断变动类型
			if type(value_block) == list: # 多值域的不变动类是值变动类2
				time_strings = [time_string1, time_string2]
				for vi in range(len(value_block)):
					quadraple_dict={}
					quadraple_dict['item'] = subjectname
					quadraple_dict['time'] = time_strings[vi]
					quadraple_dict['value'] = value_block[vi]
					quadraples.append(quadraple_dict)
			else:
				quadraple_dict={}
				if not has_formula: # 补充句式
					if value_block[-1] != '%':
						quadraple_dict['item'] = subjectname
						quadraple_dict['time'] = time_string2
						quadraple_dict['value'] = value_block
						quadraples.append(quadraple_dict)
					else:
						last_quadraple_dict = quadraples[-1]
						quadraple_dict['item'] = last_quadraple_dict['item'].split(' ')[0] + ' 的 ' +  subjectname
						quadraple_dict['time'] = last_quadraple_dict['time']
						quadraple_dict['value'] = value_block
						quadraples.append(quadraple_dict)
				else:
					# 变动类一定是公式 且均为单个值
					word_list = words.split(' ')[index_block].split('|')
					if value_block[-1] == '%' or value_block[-1] == '元':
						v = value_block[:-1]
					if value_block[-1] == '元' and (value_block[-2] == '万' or value_block[-2] == '亿'):
						v = value_block[:-2]

					verb_index = word_list.index(v)
					verb = word_list[verb_index-1]
					print(f'[method:gearup]-----数值{v}前的动词:{verb}')
					quadraple_dict['item'] = subjectname + ' 的 ' + verb
					quadraple_dict['time'] = time_string2 + ' 至 ' + time_string1
					quadraple_dict['value'] = value_block
					quadraples.append(quadraple_dict)
					
		else:
			#情况4
			if related_subjectname==None and not has_formula and type(value_block)==str:
				print('[method:gearup]----情况4')
				time_regx, target_indexblock = find_time_regx(values, flags_plain, index_block, pat_uncover_time, False)
				time_string = from_index_to_span(words, target_indexblock, locate_itemindex_general(flags, target_indexblock, time_regx))
				print(f'[method:gearup]----单主语[单值特征]对应具体时间为: {time_string}')
				if len(quadraples) != 0:
					is_first = True
					
					for qi in range(len(quadraples)+1): # 逆向遍历
						if is_first:
							each_previous_subjectname =subjectname
							is_first=False
						else:
							each_previous_subjectname = quadraples[::-1][qi-1]['item']
						
						while each_previous_subjectname.count(time_string) != 0 and each_previous_subjectname.index(time_string) > 0 or time_string=='一年内':
							print(f'[method:gearup]-----{time_string}在主语中需跳过')
							index_block = index_block - 1 
							time_regx, target_indexblock = find_time_regx(values, flags_plain, index_block, pat_uncover_time, False)
							time_string = from_index_to_span(words, target_indexblock, locate_itemindex_general(flags, target_indexblock, time_regx))
							print(f'[method:gearup]-----单主语[单值特征]再次确认的对应具体时间为: {time_string}')
				else:
					while subjectname.count(time_string) != 0 and subjectname.index(time_string) > 0:
						print(f'[method:gearup]-----{time_string}在主语中需跳过')
						index_block = index_block - 1 
						time_regx, target_indexblock = find_time_regx(values, flags_plain, index_block, pat_uncover_time, False)
						time_string = from_index_to_span(words, target_indexblock, locate_itemindex_general(flags, target_indexblock, time_regx))
						print(f'[method:gearup]-----单主语[单值特征]再次确认的对应具体时间为: {time_string}')
				
				if time_string in subjectname and subjectname.index(time_string) == 0:
					subjectname = subjectname.replace(time_string, '')
					subjectname = clean_subject(subjectname)
				quadraple_dict={}
				quadraple_dict['item'] = subjectname
				quadraple_dict['time'] = time_string
				quadraple_dict['value'] = value_block
				quadraples.append(quadraple_dict)
			else:#情况2
				print('[method:gearup]----情况2')
				time_regx, target_indexblock = find_time_regx(values, flags_plain, index_block, pat_cover_time, True)
				time_string = from_index_to_span(words, target_indexblock, locate_itemindex_general(flags, target_indexblock, time_regx))
				if type(time_string) == str and type(value_block) == list:
					print(f'[method:gearup]-----单主语对应模糊时间为: {time_string}')
					if time_string in subjectname:
						subjectname = subjectname.replace(time_string, '')
						subjectname = clean_subject(subjectname)
					# 暂时不转译模糊时间，原因：赶紧写个大概总纲，细节以后丰富
					for vi in range(len(value_block)):
						quadraple_dict={}
						if has_formula:
							quadraple_dict['item'] = subjectname + '/' + related_subjectname
						else:
							quadraple_dict['item'] = subjectname
						quadraple_dict['time'] = time_string + str(vi) +'<待解析>'
						quadraple_dict['value'] = value_block[vi]
						quadraples.append(quadraple_dict)
				else:
					if type(time_string) == list and type(value_block) == list:
						print(f'[method:gearup]-----单主语对应多具体时间为: {time_string}')
						if time_string[-1] in subjectname:
							subjectname = subjectname[subjectname.index(time_string[-1])+len(time_string[-1]):]
							subjectname = clean_subject(subjectname)
						for vi in range(len(value_block)):
							quadraple_dict={}
							if has_formula:
								quadraple_dict['item'] = subjectname + '/' + related_subjectname
							else:
								quadraple_dict['item'] = subjectname
							quadraple_dict['time'] = time_string[vi]
							quadraple_dict['value'] = value_block[vi]
							quadraples.append(quadraple_dict)
					elif type(time_string) == str and type(value_block) == str:
						print(f'[method:gearup]-----单主语对应单个具体时间为: {time_string}')
						if time_string in subjectname:
							subjectname = subjectname[subjectname.index(time_string)+len(time_string):]
							subjectname = clean_subject(subjectname)
						quadraple_dict={}
						if has_formula:
							quadraple_dict['item'] = subjectname + '/' + related_subjectname
						else:
							quadraple_dict['item'] = subjectname
						quadraple_dict['time'] = time_string
						quadraple_dict['value'] = value_block
						quadraples.append(quadraple_dict)
						
				
	
	print('[method:gearup->end]')


# 按顺序放入规则列表
pat_repository = [pat_multi_value, pat_multi_rate, pat_change_value1, pat_change_value2, pat_change_rate, pat_take_percentage, pat_single_value, pat_multi_subject_value]
# 由值出发，为值匹配公式或者（科目，时间）
# 找值
def dragout(flags, words, sentence):
	quadraples=[]
	# flags, words, sentence 是 sep_flag_pre的结果
	flags_plain = flags.replace('|','')
	print(f'[method:dragout->start]--words:{words} flags:{flags} flags_plain:{flags_plain} sentence:{sentence}')
	pattern_matrix = np.mat([re_extractor(pat, flags_plain, ' ') for pat in pat_repository])
	# 规则组装器
	values = re_extractor(pat_value_word, sentence, '，', False)
	print(f'[method:dragout]--全句值域:{values}')
	for index_block, value_block in enumerate(values):
		# 分子句值集合
		if value_block != None:
			# 寻找对应模式
			match_patterns = [(index_pat, mp) for index_pat, mp in enumerate(pattern_matrix[:,index_block].transpose().getA()[0].tolist()) if mp != None]
			match_patterns_dict = dict(match_patterns)
			match_pattern_index_set = set(match_patterns_dict.keys()) # 模式的判断依据
			
			print(f'[method:dragout]---match_pattern_index_set: {match_pattern_index_set}')
			
			if  match_pattern_index_set=={1,5,6,7}:# 规则一：“占比特征”与“多比例特征”在同一子句中,被认定为同一组合
				print(f'[method:dragout]----子句：{sentence.split("，")[index_block]} 击中正则 pat_multi_rate（多比例） -> {match_patterns_dict[1]} 和 pat_take_percentage（占比） -> {match_patterns_dict[5]}')
				print(f'[method:dragout]----占比公式值为: {value_block}')
				# 得出具体情况下的占比特征的flags
				perctg_regx = match_patterns_dict[5]
				# 确认分母
				take_percentage_start_index, take_percentage_end_index = locate_itemindex_in_take_percentage(flags, index_block, perctg_regx)
				denominator = from_index_to_span(words, index_block, (take_percentage_start_index, take_percentage_end_index))
				print(f'[method:dragout]----占比公式分母为: {denominator}')
				
				# 确认分子/主语 可能跳句
				target_block, numerator_index = locate_numeratorindex_in_take_percentage(words, flags, index_block, take_percentage_start_index)
				numerator = from_index_to_span(words, target_block, numerator_index)
				print(f'[method:dragout]----占比公式分子为: {numerator}')
				
				gearup(flags, words, values, flags_plain, quadraples, index_block, value_block, numerator, True, denominator)
			
			if match_pattern_index_set=={5,6}:
				print(f'[method:dragout]----子句：{sentence.split("，")[index_block]} 击中正则 pat_take_percentage（占比） -> {match_patterns_dict[5]}')
				print(f'[method:dragout]----占比公式值为: {value_block}')
				# 得出具体情况下的占比特征的flags
				perctg_regx = match_patterns_dict[5]
				# 确认分母
				take_percentage_start_index, take_percentage_end_index = locate_itemindex_in_take_percentage(flags, index_block, perctg_regx)
				denominator = from_index_to_span(words, index_block, (take_percentage_start_index, take_percentage_end_index))
				print(f'[method:dragout]----占比公式分母为: {denominator}')
				
				# 确认分子/主语 可能跳句
				target_block, numerator_index = locate_numeratorindex_in_take_percentage(words, flags, index_block, take_percentage_start_index)
				numerator = from_index_to_span(words, target_block, numerator_index)
				print(f'[method:dragout]----占比公式分子为: {numerator}')
				
				gearup(flags, words, values, flags_plain, quadraples, index_block, value_block, numerator, True, denominator)
				
			
			if match_pattern_index_set=={0,6,7}: # 规则二：“多值特征”
				print(f'[method:dragout]----子句：{sentence.split("，")[index_block]} 击中正则 pat_multi_value（多值） -> {match_patterns_dict[0]}')
				print(f'[method:dragout]----并列多值为: {value_block}')
				# 确认主语
				target_block, (name_start_index, name_end_index) = locate_subjectindex_general(words, flags, index_block)
				name = from_index_to_span(words, target_block, (name_start_index, name_end_index))
				print(f'[method:dragout]----分句主语为: {name}')
				
				gearup(flags, words, values, flags_plain, quadraples, index_block, value_block, name, False)
				
			if match_pattern_index_set=={1,6}: # 规则三：“多比例特征”
				print(f'[method:dragout]----子句：{sentence.split("，")[index_block]} 击中正则 pat_multi_value（多比例） -> {match_patterns_dict[1]}')
				print(f'[method:dragout]----并列多百分比为: {value_block}')
				target_block, (name_start_index, name_end_index) = locate_subjectindex_general(words, flags, index_block)
				name = from_index_to_span(words, target_block, (name_start_index, name_end_index))
				print(f'[method:dragout]----分句主语为: {name}')
				
				gearup(flags, words, values, flags_plain, quadraples, index_block, value_block, name, False)
				
			if match_pattern_index_set=={2} or match_pattern_index_set=={4}: # 规则四： “值/比例变动特征” # 可能会在后续的子句中有变动的百分比
				print(f'[method:dragout]----子句：{sentence.split("，")[index_block]} 击中正则 pat_change_value1/rate（值变动1/比例变动） -> {match_patterns_dict}')
				print(f'[method:dragout]----变动值为: {value_block}')
				target_block, (name_start_index, name_end_index) = locate_subjectindex_general(words, flags, index_block)
				name = from_index_to_span(words, target_block, (name_start_index, name_end_index))
				print(f'[method:dragout]----分句主语为: {name}')
				
				gearup(flags, words, values, flags_plain, quadraples, index_block, value_block, name, True, name)
				
			if match_pattern_index_set=={3}: # 规则五：“值变动+值赋值（变动类的第二种）”
				print(f'[method:dragout]----子句：{sentence.split("，")[index_block]} 击中正则 pat_change_value2（值变动2） -> {match_patterns_dict[3]}')
				print(f'[method:dragout]----变动值为: {value_block}')
				target_block, (name_start_index, name_end_index) = locate_subjectindex_general(words, flags, index_block)
				name = from_index_to_span(words, target_block, (name_start_index, name_end_index))
				print(f'[method:dragout]----分句主语为: {name}')
                
				gearup(flags, words, values, flags_plain, quadraples, index_block, value_block, name, True, name)
				
			if match_pattern_index_set=={6}: # 规则六：单值赋值
				print(f'[method:dragout]----子句：{sentence.split("，")[index_block]} 击中正则 pat_single_value（单值） -> {match_patterns_dict[6]}')
				print(f'[method:dragout]----单值为: {value_block}')
				target_block, (name_start_index, name_end_index) = locate_subjectindex_general(words, flags, index_block)
				name = from_index_to_span(words, target_block, (name_start_index, name_end_index))
				print(f'[method:dragout]----单值主语为: {name}')
				if clean_subject(name) == value_block:
					print(f'[method:dragout]-----主语需要倒置，{value_block}不可作为主语')
					target_block, (name_start_index, name_end_index) = locate_subjectindex_general(words, flags, index_block, len(flags.split(' ')[index_block].split('|')))
					name = from_index_to_span(words, target_block, (name_start_index, name_end_index))
					print(f'[method:dragout]-----单值再次确认主语为: {name}')
				
				gearup(flags, words, values, flags_plain, quadraples, index_block, value_block, name, False)
				
			if match_pattern_index_set=={7}: # 规则七： 多值，多主语， 转化为单值模式
				print(f'[method:dragout]----子句：{sentence.split("，")[index_block]} 击中正则 pat_multi_subject_value（多值多主语） -> {match_patterns_dict[7]}')
				print(f'[method:dragout]----多值为: {value_block}')
				
				sentences = sentence.split("，")
				current_subsentence = sentence.split("，")[index_block]
				parts = current_subsentence.split('、')
				lat = parts[-1].split('和',1)
				parts.pop(-1)
				parts.extend(lat)
				parts = [p.replace(re.search(pat_value_word, p).group(), '为'+re.search(pat_value_word, p).group()) for p in parts ]
				sentence = sentence.replace(current_subsentence, '，'.join(parts))
				
				print(f'[method:dragout]----句子已改造为：{sentence}')
				if quadraples != []:
					quadraples = []
				return extract(sentence)
				
			if len(match_pattern_index_set)==0: # 规则八：有值域无特征，是对前述特征句子的补充，主语沿用最近的特征句子的主语
				print(f'[method:dragout]----子句：{sentence.split("，")[index_block]} 无正则击中，为补充句式')
				print(f'[method:dragout]----补充值为: {value_block}')
				target_block, (name_start_index, name_end_index) = locate_subjectindex_general(words, flags, index_block)
				name = from_index_to_span(words, target_block, (name_start_index, name_end_index))
				print(f'[method:dragout]----补充句主语为: {name}')
				
				gearup(flags, words, values, flags_plain, quadraples, index_block, value_block, name, False, name)
	
	print('[method:dragout->end]')
	return quadraples

def extract(sentence):
	if sentence==None or sentence.strip() == '':
		print('输入不可为空')
		return
	flags, words, sentence = sep_flag_pre(sentence)
	return dragout(flags, words, sentence)
	

