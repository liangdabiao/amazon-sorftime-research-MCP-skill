from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta


class BaseScenario(ABC):
    """场景基类"""

    NAME = ""
    DESCRIPTION = ""
    REQUIRED_PARAMS = []

    def __init__(self):
        self.current_date = datetime.now()
        self.default_end_date = self.current_date.strftime('%Y-%m-%d')
        self.default_start_date = (self.current_date - timedelta(days=30)).strftime('%Y-%m-%d')
        self.default_end_month = self.current_date.strftime('%Y-%m')
        self.default_start_month = (self.current_date - timedelta(days=90)).strftime('%Y-%m')

    @abstractmethod
    def get_mcp_tools(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        获取需要调用的MCP工具列表

        Args:
            params: 用户输入参数

        Returns:
            list: MCP工具调用列表，每个元素包含 tool_name 和 arguments
        """
        pass

    @abstractmethod
    def aggregate_data(self, raw_data: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        """
        聚合MCP返回的数据

        Args:
            raw_data: MCP工具返回的原始数据
            params: 用户输入参数

        Returns:
            dict: 聚合后的结构化数据
        """
        pass

    @abstractmethod
    def generate_insights(self, data: Dict[str, Any]) -> List[str]:
        """
        生成关键洞察

        Args:
            data: 聚合后的数据

        Returns:
            list: 洞察列表
        """
        pass

    def validate_params(self, params: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        验证参数

        Args:
            params: 用户输入参数

        Returns:
            tuple: (is_valid, missing_params)
        """
        missing = []
        for param in self.REQUIRED_PARAMS:
            if param not in params or not params[param]:
                missing.append(param)
        return len(missing) == 0, missing

    def get_scenario_info(self) -> Dict[str, str]:
        """获取场景信息"""
        return {
            'name': self.NAME,
            'description': self.DESCRIPTION,
            'required_params': self.REQUIRED_PARAMS
        }
