import random
import time

# === 钛媒体风格：高级大纲模板库 ===
TEMPLATES = {
    "借势营销": [
        "【核心切入】从 {event} 的爆火现象切入，引出 {keyword} 的品牌动作",
        "【深度关联】分析为何 {keyword} 与该热点具有天然的契合度（用户画像/品牌精神）",
        "【差异化打法】对比竞品在同类事件中的反应，突出 {keyword} 的“神来之笔”",
        "【数据验证】引用行业数据或舆情指数，佐证这一策略的有效性",
        "【行业启示】总结 {keyword} 给整个 {industry} 行业带来的营销新思路"
    ],
    "竞品对标": [
        "【市场格局】当前 {industry} 赛道正处于激烈的存量博弈阶段",
        "【事件还原】{event} 发生后，市场风向发生的微妙变化",
        "【硬核对比】{keyword} vs 竞品：在技术/定价/渠道上的多维攻防战",
        "【胜负手】分析 {keyword} 此次应对策略中的关键得分点与失分点",
        "【终局推演】预测这场战役对未来半年市场排名的影响"
    ],
    "深度复盘": [
        "【现象回顾】{event} 并非偶然，而是草蛇灰线，伏脉千里",
        "【关键转折点】梳理 {keyword} 在事件发展过程中的三个关键决策时刻",
        "【内幕深挖】透过现象看本质：是技术突破？还是资本运作？",
        "【舆情反转】分析公众情绪如何从 A 态势转变为 B 态势",
        "【价值沉淀】该事件将成为 {industry} 发展史上的一个里程碑"
    ],
    "危机预警": [
        "【风险暴露】{event} 揭开了 {industry} 行业长期被忽视的隐患",
        "【波及范围】为何 {keyword} 即使未直接卷入，也无法独善其身？",
        "【合规审视】从法律法规与道德伦理双重维度，审视当前业务模式",
        "【应对策略】{keyword} 当前的公关口径是否得当？应该如何切割风险？",
        "【警钟长鸣】给行业其他玩家的避坑指南"
    ],
    "默认通用": [
        "【背景引入】介绍 {event} 的最新进展及其全网热度",
        "【核心冲突】分析事件背后的主要矛盾点",
        "【角色分析】{keyword} 在该事件中扮演了什么角色？",
        "【深度观点】跳出事件本身，探讨其社会或商业价值",
        "【未来展望】预测事态的下一步走向"
    ]
}

def generate_smart_outline(title, angle, context_info=""):
    """
    生成高质量大纲
    """
    # 模拟 AI 思考时间
    time.sleep(1) 
    
    # 1. 确定模板类型
    template_key = "默认通用"
    for key in TEMPLATES.keys():
        if key in str(angle):
            template_key = key
            break
            
    raw_points = TEMPLATES[template_key]
    
    # 2. 提取变量 (简单的模拟提取)
    keyword = "该品牌"
    event = "该事件"
    industry = "相关"
    
    # 3. 填充内容并生成详细子要点
    outline_structure = []
    
    for i, point in enumerate(raw_points):
        # 简单的文本替换
        main_point = point.format(keyword=keyword, event=event, industry=industry)
        
        # 为每个大点生成 2-3 个子要点 (模拟 AI 生成)
        sub_points = []
        if i == 0:
            sub_points = [
                f"引用最新数据：{event} 在全网的热度已突破千万。",
                "通过极具画面感的细节描写，快速抓住读者注意力。"
            ]
        elif i == len(raw_points) - 1:
            sub_points = [
                "不仅要看热闹，更要看门道：总结商业逻辑。",
                "金句收尾，引发读者转发欲望。"
            ]
        else:
            sub_points = [
                "展开分析...", 
                "引用专家观点或财报数据支持论点。"
            ]

        outline_structure.append({
            "section": f"第 {i+1} 部分",
            "title": main_point, # 大标题
            "sub_points": sub_points # 子要点
        })

    return {
        "meta": {
            "template_used": template_key,
            "tone": "专业、犀利、深度"
        },
        "structure": outline_structure
    }

# === 新增：全自动文章生成器 ===

def generate_full_article(title, outline, context_info=""):
    """
    根据大纲生成 1000 字文章
    """
    
    full_content = []
    
    # 1. 生成引言 (开篇)
    intro = f"""
【导语】
{context_info[:50] if context_info else '近日'}... 当下，"{title}" 正成为全网热议的焦点。这不仅是一次简单的热点事件，更折射出行业深层的变革逻辑。本文将透过现象看本质，为您深度复盘这一事件背后的商业脉络。
"""
    full_content.append(intro)

    # 2. 根据大纲分段生成
    for section in outline:
        # 兼容处理：有些 outline 可能是对象，有些可能是字典，视前端传参而定
        # 这里假设是字典格式
        if isinstance(section, dict):
            section_title = section.get('title', '')
            points = section.get('sub_points', [])
        else:
            continue
            
        paragraph = f"\n### {section_title}\n\n"
        
        if len(points) > 0:
            paragraph += f"首先，我们需要关注的是{points[0].replace('引用', '可以看到')}。据相关数据显示，这一趋势并非偶然，而是长期积累的结果。在当前的背景下，这种变化显得尤为关键。\n\n"
            
        if len(points) > 1:
            paragraph += f"其次，{points[1]}。这一点在业内引发了广泛讨论。如果不理解这一层逻辑，就很难看清未来的竞争格局。这就好比我们在迷雾中航行，必须找到那个关键的灯塔。\n\n"
            
        paragraph += f"从更宏观的视角来看，这一现象实际上反映了市场对于确定性的渴求。无论是资本端还是用户端，大家都在用脚投票。这也解释了为什么在事件发生后，舆论会呈现出如此一边倒的态势。\n"
        
        full_content.append(paragraph)

    # 3. 生成结语
    conclusion = f"""
### 结语：风起于青萍之末

综上所述，"{title}" 这一选题的价值远不止于热点本身。它提醒我们，在快速变化的时代，唯有保持敏锐的洞察力，才能在不确定性中找到确定的增长机会。

对于所有关注此领域的从业者而言，现在或许就是最好的入局（或破局）时刻。
"""
    full_content.append(conclusion)

    return "\n".join(full_content)