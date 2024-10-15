"""
ai对数据进行处理
 提取标签方便搜索
 文章转化向量存入向量数据库
"""
import argparse
import math
import json
from pymilvus import DataType, FieldSchema

from tools.utils import logger
from models import quantclass
from database import get_db, get_redis
from media_platform.quantclass.service import ArticleSummaryService, ArticleContentService
from ai_toolkit.ai_process import AIProcess
from ai_toolkit.prompt_manager import PromptManager
from ai_toolkit import pymilvus_db

db = get_db()
redis = get_redis()

summary_service = ArticleSummaryService(db, redis)
content_service = ArticleContentService(db)

ai_process = AIProcess('zhipu', 'glm-4-plus')
prompt_manager = PromptManager()


def get_prompt_content(file_path):
    # 加载并格式化Markdown提示词文件
    try:
        return prompt_manager.get_prompt(file_path)
    except ValueError as e:
        logger.error('[scripts.qtc.ai_process_content.get_prompt_content] 读取prompt模版失败')
        raise FileNotFoundError('读取prompt模版失败')


tag_prompt = get_prompt_content('qtc_article_tag.md')


# =========================================== 大模型文章标签提取 ====================================#

def extract_tags():
    """
    利用大模型提取文字的标签
    """
    query = db.query(quantclass.QtcArticleSummary).where(quantclass.QtcArticleSummary.is_essence == 1,
                                                         quantclass.QtcArticleSummary.tags == '')
    amount = query.count()
    if amount == 0:
        logger.info("[scripts.qtc.ai_process_content.extract_tags] 没有要处理的文章了")
        return

    limit = 30
    max_page = math.ceil(amount / limit)
    logger.debug(f"[scripts.qtc.ai_process_content.extract_tags] 一共有{amount}条数据需要处理，需要循环{max_page}次")

    for page in range(0, max_page):
        logger.debug(f"[scripts.qtc.ai_process_content.extract_tags] 当前处理第{page + 1}页数据，1页处理{limit}条数据")
        start_page = page * limit
        summary_list = query.limit(limit).offset(start_page).all()
        logger.debug(
            f"[scripts.qtc.ai_process_content.extract_tags] {len(summary_list)}条数据,limit={limit},offset={start_page}")
        ai_extract_tags(summary_list)


def ai_extract_tags(summaries):
    for summary in summaries:
        tags_str = ai_process.ai_extract_tags(summary.title, summary.summary)
        try:
            tags_json = json.loads(tags_str)
            tag = ','.join(tags_json['tags'])
            summary.tags = tag
            db.commit()
            logger.debug(f'[scripts.qtc.ai_process_content.ai_extract_tags],id={summary.id}. ai转换标签[{tag}]')
        except Exception as e:
            logger.error(f'[scripts.qtc.ai_process_content.ai_extract_tags] 转换json格式失败. {tags_str}')
            return False


# =========================================== 大模型段落分割 ====================================#
def segmentation():
    """
    把文章的内容，利用大模型进行段落分割，并存入数据库的文章段落表
    """
    query = (db.query(quantclass.QtcArticleSummary)
             .where(quantclass.QtcArticleSummary.is_essence == 1,
                    quantclass.QtcArticleSummary.fetch == 2,
                    quantclass.QtcArticleSummary.segmentation == 0
                    )
             )
    amount = query.count()
    if amount == 0:
        logger.info("[scripts.qtc.ai_process_content.segmentation] 没有要处理的文章了")
        return
    limit = 30
    max_page = math.ceil(amount / limit)
    logger.debug(f"[scripts.qtc.ai_process_content.segmentation] 一共有{amount}条数据需要处理，需要循环{max_page}次")

    for page in range(0, max_page):
        logger.debug(f"[scripts.qtc.ai_process_content.segmentation] 当前处理第{page + 1}页数据，1页处理{limit}条数据")
        start_page = page * limit
        summary_list = query.limit(limit).offset(start_page).all()
        logger.debug(
            f"[scripts.qtc.ai_process_content.segmentation] {len(summary_list)}条数据,limit={limit},offset={start_page}")

        for summary in summary_list:
            content = db.query(quantclass.QtcArticleContent).where(
                quantclass.QtcArticleContent.aid == summary.aid).first()
            if content is None:
                continue
            ai_segmentation(summary.aid, content.content)


def ai_segmentation(aid: int, content: str):
    """
    利用AI对文章进行分割
    """
    logger.debug(f"[scripts.qtc.ai_process_content.ai_segmentation] 对文章{aid}进行AI段落分割")

    ai_process.change_big_model('zhipu', 'GLM-4-plus')
    part_str = ai_process.ai_article_segmentation(content)
    part_str = part_str.replace("json", "")
    part_str = part_str.replace("```", "")
    try:
        part = json.loads(part_str)
        if len(part['content']) > 1:
            add_db_segmentation(aid, part['content'])
        else:
            logger.error(f"解析文章错误，只有一个数组")
    except Exception as e:
        print(e)


def add_db_segmentation(aid: int, content: list):
    """
    文章分段后的数据写入数据库中
    """
    logger.debug(f"[scripts.qtc.ai_process_content.ai_segmentation] {aid}文章存入段落表.一共{len(content)}条数据")

    seq = 1
    for c in content:
        content_service.add_segmentation(quantclass.ArticleSegmentation(
            aid=aid,
            content=c,
            seq=seq
        ))
        seq += 1
    # 设置已分段
    summary_service.set_segmentation(aid)


# =========================================== 文章段落存入向量数据库 ====================================#
def init_vector_db(qtc_collection_name):
    """
    初始化向量数据库的集合
    """
    dimension = 2048
    fields = [
        FieldSchema(name='id', dtype=DataType.INT64, description='id', is_primary=True, auto_id=False),  # 主键字段
        FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=dimension)  # 向量字段
    ]
    pymilvus_db.create_collection(qtc_collection_name, dimension, fields)
    pymilvus_db.create_index(qtc_collection_name)


def embedding(collection_name):
    query = db.query(quantclass.ArticleSegmentation).where(quantclass.ArticleSegmentation.embedding == 0)
    amount = query.count()
    if amount == 0:
        logger.info("[scripts.qtc.ai_process_content.embedding] 没有要处理的文章段落了")
        return
    limit = 30
    max_page = math.ceil(amount / limit)
    logger.debug(f"[scripts.qtc.ai_process_content.segmentation] 一共有{amount}条数据需要处理，需要循环{max_page}次")

    for page in range(0, max_page):
        logger.debug(f"[scripts.qtc.ai_process_content.segmentation] 当前处理第{page + 1}页数据，1页处理{limit}条数据")
        start_page = page * limit
        segment_list = query.limit(limit).offset(start_page).all()
        logger.debug(
            f"[scripts.qtc.ai_process_content.segmentation] {len(segment_list)}条数据,limit={limit},offset={start_page}")

        for segment in segment_list:
            try:
                # text转换向量
                emb = ai_process.ai_text_to_vector([segment.content])

                # 插入向量数据库
                data = [
                    {
                        "id": segment.id,
                        "vector": emb.data[0].embedding,
                    }
                ]
                pymilvus_db.insert_data(collection_name, data)
            except Exception as e:
                logger.error(f"[scripts.qtc.ai_process_content.segmentation] 转换向量{segment.id}失败.{e}")
                continue


def ask(question: str):
    """
    基于向量数据库，谁用本地数据来回答问题
    """
    query_emb = ai_process.ai_text_to_vector([question])

    result = pymilvus_db.query_vectors(qtc_collection_name, [query_emb.data[0].embedding], 3)
    aids = [r.id for r in result.pop()]
    r = content_service.get_segmentation_by_ids(aids)

    content = ''
    for con in r:
        content += con.content
    ai_process.change_big_model('openai', 'gpt-4o')
    return ai_process.ai_article_answer(question, content)


if __name__ == '__main__':
    aid = 36400
    qtc_collection_name = "qtc_article"
    segmentation()
