import os
import inspect
from string import Template

prompt_directory = os.path.join(os.getcwd(), "prompts")

class PromptManager:
    def __init__(self):
        # 获取类定义文件的绝对路径
        self.file_path = os.path.abspath(inspect.getfile(self.__class__))
        # 获取类定义文件的目录
        self.directory = os.path.dirname(self.file_path)
        # 使用当前工作目录下的 prompts 目录
        self.prompt_directory = os.path.join(self.directory, "prompts")

    def get_prompt(self, file_name, **kwargs):
        """
        读取 markdown 文件中的提示词并用给定的键值对替换占位符，返回整个内容作为字符串。
        """
        file_path = os.path.join(self.prompt_directory, file_name)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File {file_name} not found in {self.prompt_directory}.")

        with open(file_path, 'r', encoding='utf-8') as file:
            markdown_content = file.read()

        if not kwargs:
            return markdown_content

        # 替换占位符
        try:
            formatted_content = Template(markdown_content).substitute(**kwargs)
        except KeyError as e:
            raise ValueError(f"Missing value for placeholder: {e}")

        return formatted_content


# 示例：使用PromptManager
if __name__ == "__main__":
    # 创建PromptManager实例，使用当前目录下的 prompts 目录
    prompt_manager = PromptManager()

    # 定义要替换的占位符及其对应的值
    values = {
        "博主姓名": "Alice",
        "数量": 5,
        "推特内容": "这是一条非常有用的区块链推特内容。"
    }

    # 加载并格式化Markdown提示词文件
    try:
        prompt_data = prompt_manager.get_prompt("filter_market_noise.md")
        # 打印格式化后的提示词
        print(prompt_data)
    except ValueError as e:
        print(e)
