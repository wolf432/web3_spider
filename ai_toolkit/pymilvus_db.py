from pymilvus import Collection, CollectionSchema, DataType, FieldSchema, connections
from pymilvus import utility, MilvusException
from tools.utils import logger

# 连接到 Milvus 服务
connections.connect(alias="default", host='127.0.0.1', port=19530)


def create_collection(collection_name, dimension, fields=None):
    """
    创建一个集合，包含一个向量字段和一个主键字段。

    参数:
    - collection_name: 集合的名称
    - dimension: 向量的维度.
    智普支持的向量是，256、512、1024、2048
    - fields: 可选，自定义字段结构
    """
    # 检查集合是否已存在
    if utility.has_collection(collection_name):
        logger.debug(f"Collection '{collection_name}' already exists.")
        return

    # 如果没有自定义字段，则创建默认字段 (ID 为主键 + 向量字段)
    if fields is None:
        fields = [
            FieldSchema(name='id', dtype=DataType.INT64, description='id', is_primary=True, auto_id=True),  # 主键字段
            FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=dimension)  # 向量字段
        ]

    # 输出字段信息用于调试
    logger.debug(f"Fields defined for collection '{collection_name}': {fields}")

    # 检查主键字段是否存在且设置正确
    primary_key_defined = any(field.is_primary for field in fields)
    if not primary_key_defined:
        raise ValueError("Schema must have a primary key field. Fields provided: {fields}")

    # 定义集合的 schema
    schema = CollectionSchema(fields)
    logger.debug(f"Schema created for collection '{collection_name}': {schema}")

    # 创建集合
    collection = Collection(name=collection_name, schema=schema)
    logger.debug(f"Collection '{collection_name}' created.")


def insert_data(collection_name, data):
    """
    向集合中插入数据。

    参数:
    - collection_name: 集合的名称
    - data: 要插入的数据，必须是符合 schema 的列表
    """
    # 检查集合是否存在
    if not utility.has_collection(collection_name):
        raise MilvusException(1, f"Collection '{collection_name}' does not exist.")

    # 插入数据到集合
    collection = Collection(name=collection_name)
    collection.insert(data)

    # 刷新集合以确保数据持久化
    collection.flush()
    logger.debug(f"Inserted data into collection '{collection_name}'.")


def create_index(collection_name):
    """
    为集合创建向量索引，提升搜索性能。

    参数:
    - collection_name: 集合的名称
    """
    # 获取集合
    collection = Collection(name=collection_name)

    # 定义索引参数
    index_params = {
        "index_type": "IVF_FLAT",  # 使用 IVF_FLAT 索引类型
        "metric_type": "L2",  # L2 为欧几里得距离度量
        "params": {"nlist": 128}  # nlist 参数用于确定索引的分桶数
    }

    # 创建索引
    collection.create_index(field_name="vector", index_params=index_params)
    logger.debug(f"Index created for collection '{collection_name}'.")


def query_vectors(collection_name, _query_vectors, top_k=10):
    """
    执行向量查询，返回最相似的 top_k 个结果。

    参数:
    - collection_name: 集合的名称
    - query_vectors: 查询的向量
    - top_k: 返回的最相似结果的数量
    """
    # 检查集合是否存在
    if not utility.has_collection(collection_name):
        raise MilvusException(1, f"Collection '{collection_name}' does not exist.")

    # 获取集合
    collection = Collection(name=collection_name)

    # 加载集合到内存中以便执行搜索
    collection.load()

    # 定义搜索参数
    search_params = {"metric_type": "L2", "params": {"nprobe": 10}}  # nprobe 控制搜索精度

    # 执行向量搜索
    return collection.search(
        _query_vectors,
        anns_field="vector",  # anns_field 表示用于比较的向量字段
        param=search_params,
        limit=top_k
    )


def delete_data(collection_name, ids):
    """
    根据 ID 删除集合中的数据。

    参数:
    - collection_name: 集合的名称
    - ids: 要删除的数据 ID 列表
    """
    # 检查集合是否存在
    if not utility.has_collection(collection_name):
        raise MilvusException(1, f"Collection '{collection_name}' does not exist.")

    # 获取集合
    collection = Collection(name=collection_name)

    # 构造删除条件表达式
    expr = f"id in [{', '.join(map(str, ids))}]"

    # 执行删除操作
    collection.delete(expr)

    # 刷新集合以确保删除操作完成
    collection.flush()
    logger.debug(f"Deleted data with ids {ids} from collection '{collection_name}'.")


def delete_collection(collection_name):
    """
    删除指定的集合。

    参数:
    - collection_name: 集合的名称
    """
    # 检查集合是否存在
    if utility.has_collection(collection_name):
        utility.drop_collection(collection_name)  # 删除集合
        logger.debug(f"Collection '{collection_name}' deleted.")
    else:
        logger.debug(f"Collection '{collection_name}' does not exist.")


# 使用示例
if __name__ == "__main__":
    example_collection_name = "example_collection"
    example_dimension = 128

    # 创建集合
    create_collection(example_collection_name, example_dimension)

    # 创建索引
    create_index(example_collection_name)

    # 插入一些随机数据
    import numpy as np

    vectors = np.random.random((10, example_dimension)).tolist()  # 生成随机向量数据
    insert_data(example_collection_name, vectors)

    # 查询
    query_data = np.random.random((1, example_dimension)).tolist()  # 生成随机查询向量
    results = query_vectors(example_collection_name, query_data)  # 执行查询
    print("Query results:", results)

    # 删除数据
    ids_to_delete = [1, 2, 3]  # 要删除的 ID 列表
    delete_data(example_collection_name, ids_to_delete)

    # 删除集合
    delete_collection(example_collection_name)
